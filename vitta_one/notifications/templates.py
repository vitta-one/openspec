"""Whitelisted transactional content, escaped HTML and readable plain text."""
from html import escape
from urllib.parse import urlsplit

from vitta_one.financial.asaas import payment_url

SUBJECTS = {
    "booking_confirmed": "Sua consulta está agendada",
    "booking_rescheduled": "Sua consulta foi reagendada",
    "booking_cancelled": "Sua consulta foi cancelada",
    "booking_reminder": "Lembrete da sua consulta",
    "charge_available": "Sua cobrança está disponível",
    "payment_received": "Pagamento confirmado",
}


def public_url(value: str) -> str:
    parsed = urlsplit(value)
    local = parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if (not parsed.netloc or parsed.username or parsed.password or not (parsed.scheme == "https" or local)
            or parsed.query or parsed.fragment):
        raise ValueError("Configure uma URL pública segura no servidor.")
    return value.rstrip("/")


def layout(title: str, paragraphs: list[str], *, url="", link_label="Abrir Vitta-One") -> tuple[str, str]:
    body = "".join(f"<p style=\"line-height:1.6\">{escape(line)}</p>" for line in paragraphs)
    link = f'<p><a href="{escape(url, quote=True)}">{escape(link_label)}</a></p>' if url else ""
    html = ('<!doctype html><html lang="pt-BR"><meta name="viewport" content="width=device-width, initial-scale=1">'
            '<body style="margin:0;background:#f5f7fa;color:#152c3b;font-family:Arial,sans-serif">'
            '<main style="box-sizing:border-box;max-width:600px;width:100%;padding:24px;margin:auto;background:white">'
            f'<p>Vitta-One</p><h1 style="font-size:24px">{escape(title)}</h1>{body}{link}'
            '<p style="font-size:14px">Mensagem transacional da clínica. Para dúvidas, entre em contato com a Recepção.</p>'
            '</main></body></html>')
    return html, title + "\n\n" + "\n\n".join(paragraphs) + ("\n" + url if url else "")


def render(kind: str, *, name: str, when="", previous="", value="", due="", url="") -> tuple[str, str, str]:
    if kind not in SUBJECTS:
        raise ValueError("Template não homologado.")
    lines = [f"Olá, {name}."]
    if kind.startswith("booking_"):
        lines.append(f"Consulta: {when}.")
        if kind == "booking_rescheduled":
            lines.append(f"Horário anterior: {previous}.")
        if kind == "booking_cancelled":
            lines.append("Este agendamento foi cancelado. Se precisar, fale com a Recepção.")
        else:
            lines.append("Confira o horário e entre em contato com a Recepção se precisar de ajuda.")
        url = public_url(url) + "/paciente" if url else ""
        label = "Consultar minhas consultas"
    else:
        lines.append(f"Valor: R$ {value}.")
        if kind == "charge_available":
            lines.append(f"Vencimento: {due}.")
            url = payment_url(url)
        else:
            lines.append("O recebimento foi confirmado. Esta mensagem não é um recibo fiscal.")
            url = ""
        label = "Acessar pagamento"
    html, text = layout(SUBJECTS[kind], lines, url=url, link_label=label)
    return SUBJECTS[kind], html, text
