"""Transactional outbox, consent and durable send attempts. No message-body storage."""
from datetime import datetime, timedelta, timezone
import hashlib
import os

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from vitta_one.auth.authorization import require_authenticated
from vitta_one.auth.roles import Role
from vitta_one.models.auth import User
from vitta_one.models.appointment import Consultation, ConsultationScheduleChange
from vitta_one.models.patient_queue import Patient
from vitta_one.models.financial import FinancialCharge, now
from vitta_one.models.notification import (NotificationPreference, NotificationPreferenceChange, EmailNotification,
                                         EmailAttempt, EmailWebhookEvent, EmailRetryRequest)
from vitta_one.appointment_scheduling.settings import clinic_timezone
from . import resend
from .templates import render


def recipient_hash(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()


def begin_access(db: Session, *, kind: str, event_key: str, entity_id: int, email: str, patient_id=None):
    """Access flows already authorized the operation and committed the credential hash."""
    key = recipient_hash(email)
    row = db.exec(select(EmailNotification).where(EmailNotification.event_key == event_key,
                    EmailNotification.recipient_hash == key).with_for_update()).first()
    if row:
        return row, None
    row = EmailNotification(kind=kind, event_key=event_key, entity_id=entity_id, patient_id=patient_id,
                            recipient_hash=key, status="SENDING")
    try:
        db.add(row)
        db.flush()
        attempt = EmailAttempt(notification_id=row.id)
        db.add(attempt)
        db.commit()
    except IntegrityError:
        db.rollback()
        row = db.exec(select(EmailNotification).where(EmailNotification.event_key == event_key,
                     EmailNotification.recipient_hash == key)).one()
        return row, None
    return row, attempt


def finish_access(db: Session, row: EmailNotification, attempt: EmailAttempt, delivery: resend.EmailDelivery):
    row.status, row.updated_at = delivery.status, now()
    attempt.status, attempt.message_id, attempt.finished_at = delivery.status, delivery.message_id, now()
    db.add(row)
    db.add(attempt)
    db.commit()


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def set_preferences(db: Session, *, token: str, patient_id: int, agenda: bool, financial: bool, confirmed: bool):
    user = require_authenticated(db, token)
    patient = db.exec(select(Patient).where(Patient.id == patient_id).with_for_update()).first()
    if (user.must_change_password or patient is None or user.role not in {Role.PACIENTE, Role.RECEPCIONISTA}
            or user.role == Role.PACIENTE and patient.user_id != user.id):
        raise PermissionError("Não é possível alterar esta preferência.")
    if confirmed is not True or type(agenda) is not bool or type(financial) is not bool:
        raise ValueError("Confirme expressamente a escolha de comunicação do paciente.")
    pref = db.exec(select(NotificationPreference).where(NotificationPreference.patient_id == patient_id)).first()
    if pref is None:
        pref = NotificationPreference(patient_id=patient_id, changed_by=user.id)
    pref.agenda_enabled, pref.financial_enabled = agenda, financial
    pref.changed_by, pref.changed_at = user.id, now()
    db.add(pref)
    db.add(NotificationPreferenceChange(patient_id=patient_id, changed_by=user.id,
                                        agenda_enabled=agenda, financial_enabled=financial))
    db.commit()


def contact(db: Session, patient_id: int) -> tuple[Patient | None, str]:
    patient = db.get(Patient, patient_id)
    account = db.get(User, patient.user_id) if patient and patient.user_id else None
    email = account.email if account and account.role == Role.PACIENTE.value else ""
    return patient, email if resend.valid_recipient(email) else ""


def enqueue(db: Session, *, kind: str, event_key: str, entity_id: int, patient_id: int, revision=""):
    # Hook participates in the business transaction; no commit or provider call here.
    pref = db.exec(select(NotificationPreference).where(NotificationPreference.patient_id == patient_id)).first()
    allowed = pref and (pref.agenda_enabled if kind.startswith("booking_") else pref.financial_enabled)
    if not allowed:
        return None
    _, email = contact(db, patient_id)
    if not email:
        return None
    key = recipient_hash(email)
    existing = db.exec(select(EmailNotification).where(EmailNotification.event_key == event_key,
                                                       EmailNotification.recipient_hash == key)).first()
    if existing:
        return existing
    row = EmailNotification(kind=kind, event_key=event_key, entity_id=entity_id,
                            patient_id=patient_id, recipient_hash=key, revision=revision)
    # A savepoint closes concurrent insertion without rolling back clinical changes.
    try:
        with db.begin_nested():
            db.add(row)
            db.flush()
    except IntegrityError:
        row = db.exec(select(EmailNotification).where(EmailNotification.event_key == event_key,
                                                     EmailNotification.recipient_hash == key)).first()
    return row


def schedule_revision(db: Session, consultation: Consultation) -> str:
    latest = db.exec(select(ConsultationScheduleChange.id).where(ConsultationScheduleChange.consultation_id == consultation.id).order_by(ConsultationScheduleChange.id.desc()).limit(1)).first()
    return f"{_utc(consultation.scheduled_at).isoformat()}/{latest or 0}"


def enqueue_booking(db: Session, consultation: Consultation, kind: str, change_id: int | None = None):
    db.flush()
    revision = schedule_revision(db, consultation)
    return enqueue(db, kind=kind, event_key=f"{kind}/{consultation.id}/{change_id or revision}",
                   entity_id=change_id if kind == "booking_rescheduled" else consultation.id,
                   patient_id=consultation.patient_id, revision=revision)


def enqueue_financial(db: Session, charge: FinancialCharge, kind: str, change_id: int):
    consultation = db.get(Consultation, charge.consultation_id)
    suffix = "first" if kind == "payment_received" else str(change_id)
    return enqueue(db, kind=kind, event_key=f"{kind}/{charge.id}/{suffix}", entity_id=charge.id,
                   patient_id=consultation.patient_id)


def enqueue_reminders(db: Session, *, timestamp: datetime | None = None) -> int:
    timestamp = _utc(timestamp or now())
    rows = db.exec(select(Consultation).where(Consultation.status.in_(["AGENDADA", "CONFIRMADA"]),
                   Consultation.scheduled_at >= timestamp + timedelta(hours=23),
                   Consultation.scheduled_at <= timestamp + timedelta(hours=24))).all()
    count = 0
    for consultation in rows:
        if enqueue_booking(db, consultation, "booking_reminder"):
            count += 1
    db.commit()
    return count


def _eligible_content(db: Session, notification: EmailNotification, timestamp: datetime):
    patient, email = contact(db, notification.patient_id)
    pref = db.exec(select(NotificationPreference).where(NotificationPreference.patient_id == notification.patient_id)).first()
    agenda = notification.kind.startswith("booking_")
    if (not patient or not email or recipient_hash(email) != notification.recipient_hash or not pref
            or not (pref.agenda_enabled if agenda else pref.financial_enabled)):
        return None
    # Complaints and permanent delivery failures suppress future automatic messages.
    failed = db.exec(select(EmailNotification.id).where(EmailNotification.recipient_hash == notification.recipient_hash,
                 EmailNotification.error_code.in_(["email.complained", "email.bounced"]))).first()
    if failed:
        return None
    public = os.getenv("VITTA_ONE_PUBLIC_URL", "")
    if agenda:
        change = db.get(ConsultationScheduleChange, notification.entity_id) if notification.kind == "booking_rescheduled" else None
        consultation = db.get(Consultation, change.consultation_id if change else notification.entity_id)
        if not consultation or consultation.patient_id != notification.patient_id:
            return None
        if notification.kind != "booking_cancelled" and (consultation.status == "CANCELADA" or schedule_revision(db, consultation) != notification.revision):
            return None
        if notification.kind == "booking_cancelled" and consultation.status != "CANCELADA":
            return None
        if notification.kind == "booking_reminder":
            remaining = _utc(consultation.scheduled_at) - timestamp
            if consultation.status not in {"AGENDADA", "CONFIRMADA"} or not timedelta(hours=23) <= remaining <= timedelta(hours=24):
                return None
        when = _utc(consultation.scheduled_at).astimezone(clinic_timezone()).strftime("%d/%m/%Y às %H:%M")
        previous = _utc(change.previous_scheduled_at).astimezone(clinic_timezone()).strftime("%d/%m/%Y às %H:%M") if change else ""
        return email, render(notification.kind, name=patient.name, when=when, previous=previous, url=public)
    charge = db.get(FinancialCharge, notification.entity_id)
    if not charge or (notification.kind == "payment_received" and charge.status != "RECEIVED"):
        return None
    if notification.kind == "charge_available" and charge.status not in {"PENDING", "OVERDUE", "CONFIRMED"}:
        return None
    return email, render(notification.kind, name=patient.name, value=f"{charge.value:.2f}".replace(".", ","),
                         due=charge.due_date.strftime("%d/%m/%Y"), url=charge.invoice_url or charge.boleto_url)


def process_outbox(db: Session, *, limit=20, timestamp: datetime | None = None) -> int:
    timestamp = _utc(timestamp or now())
    # A stale send is uncertain, never automatically requeued.
    stale = db.exec(select(EmailAttempt).where(EmailAttempt.status == "SENDING",
                         EmailAttempt.started_at < timestamp - timedelta(minutes=2)).with_for_update(skip_locked=True)).all()
    for attempt in stale:
        attempt.status, attempt.finished_at = "UNKNOWN", timestamp
        notification = db.get(EmailNotification, attempt.notification_id)
        notification.status = "UNKNOWN"
        db.add(attempt)
        db.add(notification)
    db.commit()
    count = 0
    for _ in range(min(max(limit, 1), 100)):
        row = db.exec(select(EmailNotification).where(EmailNotification.status == "PENDING").order_by(
            EmailNotification.id).with_for_update(skip_locked=True).limit(1)).first()
        if row is None:
            db.rollback()
            break
        try:
            content = _eligible_content(db, row, timestamp)
        except ValueError:
            content = None
        if not content:
            row.status, row.error_code = "SUPPRESSED", "INELIGIBLE"
            db.add(row)
            db.commit()
            continue
        previous = db.exec(select(EmailAttempt).where(EmailAttempt.notification_id == row.id).order_by(EmailAttempt.sequence.desc())).first()
        attempt = EmailAttempt(notification_id=row.id, sequence=previous.sequence + 1 if previous else 1)
        row.status = "SENDING"
        db.add(row)
        db.add(attempt)
        db.commit()
        email, (subject, html, plain) = content
        delivery = resend.send(email=email, subject=subject, html=html, text=plain, idempotency_key=attempt.idempotency_key)
        attempt.status, attempt.message_id, attempt.finished_at = delivery.status, delivery.message_id, now()
        row.status, row.updated_at = delivery.status, now()
        db.add(attempt)
        db.add(row)
        db.commit()
        apply_delivery_events(db)
        count += 1
    return count


def manual_retry(db: Session, *, token: str, notification_id: int, reason: str, uncertainty_reviewed=False):
    identity = require_authenticated(db, token)
    row = db.exec(select(EmailNotification).where(EmailNotification.id == notification_id).with_for_update()).first()
    if not row:
        raise ValueError("Notificação não encontrada.")
    if row.kind in {"medical_access", "patient_access"}:
        raise ValueError("Reemita o acesso pelo fluxo original para invalidar o segredo anterior.")
    allowed = {Role.RECEPCIONISTA} if row.kind.startswith("booking_") else {Role.ADMINISTRADOR, Role.FINANCEIRO}
    if identity.must_change_password or identity.role not in allowed:
        raise PermissionError("Reenvio não autorizado.")
    if not 3 <= len(reason.strip()) <= 240 or row.status not in {"FAILED", "NOT_CONFIGURED", "UNKNOWN"}:
        raise ValueError("Reenvio indisponível. Confirme o motivo e consulte a situação.")
    if row.status == "UNKNOWN" and uncertainty_reviewed is not True:
        raise ValueError("Revise o resultado no provedor antes de autorizar outro envio.")
    if not _eligible_content(db, row, now()):
        raise ValueError("Destinatário ou evento deixou de ser elegível.")
    db.add(EmailRetryRequest(notification_id=row.id, requested_by=identity.id,
                            reason=reason.strip(), uncertainty_reviewed=uncertainty_reviewed is True))
    # Actor/reason belongs in metadata, never message content.
    row.error_code = f"MANUAL_BY_{identity.id}"
    row.status = "PENDING"
    row.updated_at = now()
    db.add(row)
    db.commit()


def apply_delivery_events(db: Session):
    rows = db.exec(select(EmailWebhookEvent).where(EmailWebhookEvent.status == "PENDING").order_by(
        EmailWebhookEvent.occurred_at, EmailWebhookEvent.id).with_for_update(skip_locked=True).limit(100)).all()
    mapping = {"email.delivered": "DELIVERED", "email.bounced": "FAILED", "email.failed": "FAILED", "email.complained": "SUPPRESSED"}
    for event in rows:
        attempt = db.exec(select(EmailAttempt).where(EmailAttempt.message_id == event.message_id).with_for_update()).first()
        if not attempt:
            continue
        row = db.exec(select(EmailNotification).where(EmailNotification.id == attempt.notification_id).with_for_update()).one()
        status = mapping.get(event.event_type)
        if status:
            # Bounce/complaint evidence cannot be erased by a late delivery event.
            if row.error_code not in {"email.complained", "email.bounced", "email.failed"} or status in {"FAILED", "SUPPRESSED"}:
                row.status, attempt.status = status, status
                row.error_code = event.event_type
                row.updated_at = now()
        event.status = "PROCESSED"
        db.add(event)
        db.add(row)
        db.add(attempt)
    db.commit()
