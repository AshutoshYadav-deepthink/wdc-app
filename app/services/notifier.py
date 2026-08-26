"""
WDC App — Notifier service
Handles email + (stubbed) browser push. In-app is stored in the DB by routers.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List

from ..config import settings


def send_email(to_list: List[str], subject: str, body: str, html: str = None):
    """Send an email via SMTP. If SMTP_HOST is empty, prints to console (stub mode)."""
    if not settings.smtp_host:
        print(f"\n[EMAIL STUB] to={to_list} subject={subject}\n{body}\n")
        return {"ok": True, "stub": True}

    msg = MIMEMultipart("alternative")
    msg["From"] = settings.email_from
    msg["To"] = ", ".join(to_list)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    if html:
        msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.email_from, to_list, msg.as_string())
        return {"ok": True}
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return {"ok": False, "error": str(e)}


def send_push_subscription(title: str, body: str, subscription: dict = None):
    """Browser push stub — real implementation needs pywebpush + VAPID keys.
    For the college demo this just logs."""
    print(f"[PUSH STUB] title={title} body={body} sub={subscription}")
    return {"ok": True, "stub": True}
