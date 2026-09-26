import os
import smtplib
from datetime import datetime
from email.message import EmailMessage


def _message(subject, body, to):
    msg = EmailMessage()
    msg["From"] = os.environ.get("NOTIFY_FROM", "website@maplerow.example")
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    return msg


def send(subject, body, to=None):
    to = to or os.environ.get("NOTIFY_TO", "reception@maplerow.example")
    msg = _message(subject, body, to)
    mode = os.environ.get("NOTIFY_MODE", "file")
    if mode == "smtp":
        with smtplib.SMTP(os.environ.get("SMTP_HOST", "smtp.maplerow.example")) as smtp:
            smtp.send_message(msg)
        return None
    outbox = os.environ.get("OUTBOX_DIR", "outbox")
    os.makedirs(outbox, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    path = os.path.join(outbox, f"{stamp}.eml")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(msg.as_string())
    return path
