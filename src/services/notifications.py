import json
import smtplib
from email.message import EmailMessage
from typing import Optional

import requests

from src.config import settings


def send_email(to: str, subject: str, body: str) -> bool:
    smtp_host = getattr(settings, "smtp_host", "") or ""
    smtp_port = getattr(settings, "smtp_port", 587)
    smtp_user = getattr(settings, "smtp_user", "") or ""
    smtp_pass = getattr(settings, "smtp_pass", "") or ""
    from_addr = getattr(settings, "smtp_from", "") or "noreply@cybersec.local"

    if not smtp_host:
        return False

    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            if smtp_user:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return True
    except Exception:
        return False


def send_slack(webhook_url: str, message: str) -> bool:
    try:
        resp = requests.post(webhook_url, json={"text": message}, timeout=10)
        return resp.ok
    except Exception:
        return False


def send_discord(webhook_url: str, message: str) -> bool:
    try:
        resp = requests.post(webhook_url, json={"content": message}, timeout=10)
        return resp.ok
    except Exception:
        return False


def send_webhook(url: str, payload: dict) -> bool:
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.ok
    except Exception:
        return False


def send_notification(user_id: int, event: str, data: dict) -> list[dict]:
    from src.database import get_db

    results = []
    with get_db() as conn:
        configs = conn.execute(
            "SELECT channel, config FROM notifications WHERE user_id = ? AND event IN (?, '*') AND enabled = 1",
            (user_id, event),
        ).fetchall()

        for row in configs:
            cfg = json.loads(row["config"]) if isinstance(row["config"], str) else row["config"]
            channel = row["channel"]
            message = f"[{event}] {json.dumps(data, indent=2)}"

            ok = False
            if channel == "email":
                ok = send_email(cfg.get("to", ""), f"Alert: {event}", message)
            elif channel == "slack":
                ok = send_slack(cfg.get("webhook_url", ""), message)
            elif channel == "discord":
                ok = send_discord(cfg.get("webhook_url", ""), message)
            elif channel == "teams":
                ok = send_webhook(cfg.get("webhook_url", ""), {"text": message})
            elif channel == "webhook":
                ok = send_webhook(cfg.get("url", ""), {"event": event, "data": data})

            results.append({"channel": channel, "success": ok})

    return results
