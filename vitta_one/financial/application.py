"""Authorized, bounded SQL projections for the financial workspace."""
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func
from sqlmodel import Session, select

from vitta_one.appointment_scheduling.settings import clinic_timezone
from vitta_one.models.appointment import Consultation
from vitta_one.models.patient_queue import Patient
from vitta_one.models.financial import FinancialCharge, FinancialChange
from .asaas import FinancialError
from .service import authorize

LABELS = {"NEW": "Preparando", "SENDING": "Emissão em andamento", "UNKNOWN": "Resultado desconhecido",
          "PENDING": "Aguardando pagamento", "CONFIRMED": "Confirmado, aguardando disponibilidade",
          "RECEIVED": "Pago", "OVERDUE": "Vencido", "CANCELLED": "Cancelado", "REFUNDED": "Estornado",
          "REFUND_PENDING": "Estorno em processamento", "REVIEW": "Revisão necessária"}


def brl(value) -> str:
    return f"R$ {Decimal(value or 0):,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def snapshot(db: Session, *, token: str, search="", status="", start: date, end: date, page=1):
    authorize(db, token)
    if start > end or (end - start).days > 366 or len(search) > 160 or page < 1 or page > 100000:
        raise FinancialError("Informe um período de até 366 dias e filtros válidos.")
    if status and status not in LABELS:
        raise FinancialError("Situação financeira inválida.")
    common = []
    if search.strip():
        common.append(Patient.name.ilike("%" + search.strip().replace("%", "\\%").replace("_", "\\_") + "%", escape="\\"))
    if status:
        common.append(FinancialCharge.status == status)
    base = select(FinancialCharge, Patient).join(Consultation, Consultation.id == FinancialCharge.consultation_id).join(Patient, Patient.id == Consultation.patient_id)
    conditions = [*common, FinancialCharge.due_date >= start, FinancialCharge.due_date <= end]
    count_stmt = select(func.count(FinancialCharge.id)).join(Consultation, Consultation.id == FinancialCharge.consultation_id).join(Patient, Patient.id == Consultation.patient_id).where(*conditions)
    total = db.exec(count_stmt).one()
    page = min(page, max(1, (total + 19) // 20))
    rows = db.exec(base.where(*conditions).order_by(FinancialCharge.created_at.desc(), FinancialCharge.id.desc()).offset((page - 1) * 20).limit(20)).all()
    zone = clinic_timezone()
    lower = datetime.combine(start, time.min, tzinfo=zone)
    upper = datetime.combine(end + timedelta(days=1), time.min, tzinfo=zone)
    totals = {}
    for state in ("RECEIVED", "PENDING", "OVERDUE", "CONFIRMED"):
        period = [FinancialCharge.received_at >= lower, FinancialCharge.received_at < upper] if state == "RECEIVED" else [FinancialCharge.due_date >= start, FinancialCharge.due_date <= end]
        stmt = select(func.coalesce(func.sum(FinancialCharge.value), 0)).join(Consultation, Consultation.id == FinancialCharge.consultation_id).join(Patient, Patient.id == Consultation.patient_id).where(*common, FinancialCharge.status == state, *period)
        totals[state] = brl(db.exec(stmt).one())
    # Group persisted amounts by local day; PostgreSQL performs the timezone aggregation.
    bind = db.get_bind()
    day = func.date(func.timezone(str(zone), FinancialCharge.received_at)) if bind.dialect.name == "postgresql" else func.date(FinancialCharge.received_at)
    evolution = db.exec(select(day.label("day"), func.sum(FinancialCharge.value)).join(Consultation, Consultation.id == FinancialCharge.consultation_id).join(Patient, Patient.id == Consultation.patient_id).where(
        *common, FinancialCharge.status == "RECEIVED", FinancialCharge.received_at >= lower, FinancialCharge.received_at < upper).group_by(day).order_by(day)).all()
    candidates = db.exec(select(Consultation, Patient).join(Patient, Patient.id == Consultation.patient_id).where(Consultation.status != "CANCELADA", *([Patient.name.ilike(f"%{search}%")] if search else [])).order_by(Consultation.scheduled_at.desc()).limit(100)).all()
    return {
        "rows": [{"id": str(c.id), "patient": p.name, "consultation": str(c.consultation_id), "value": brl(c.value),
                  "due": c.due_date.strftime("%d/%m/%Y"), "method": c.method, "status": LABELS.get(c.status, "Revisão necessária")} for c, p in rows],
        "totals": totals, "total": total, "page": page,
        "evolution": [{"day": str(d), "value": brl(v)} for d, v in evolution],
        "candidates": [f"{c.id} · {p.name} · {c.scheduled_at.astimezone(zone).strftime('%d/%m/%Y %H:%M')}" for c,p in candidates],
    }


def charge_detail(db: Session, *, token: str, charge_id: int):
    authorize(db, token)
    row = db.exec(select(FinancialCharge, Patient).join(Consultation, Consultation.id == FinancialCharge.consultation_id).join(Patient, Patient.id == Consultation.patient_id).where(FinancialCharge.id == charge_id)).first()
    if not row:
        raise FinancialError("Cobrança não encontrada.")
    charge, patient = row
    history = db.exec(select(FinancialChange).where(FinancialChange.charge_id == charge_id).order_by(FinancialChange.occurred_at, FinancialChange.id)).all()
    return {"id": str(charge.id), "external_id": charge.provider_id or "Ainda não vinculado", "patient": patient.name,
            "consultation": str(charge.consultation_id), "value": brl(charge.value), "method": charge.method,
            "status": LABELS.get(charge.status, "Revisão necessária"), "due": charge.due_date.strftime("%d/%m/%Y"),
            "url": charge.invoice_url or charge.boleto_url,
            "history": [{"status": LABELS.get(h.status, h.status), "source": h.source,
                         "when": h.occurred_at.isoformat(), "actor": str(h.actor_id or "Provedor"), "reason": h.reason} for h in history]}
