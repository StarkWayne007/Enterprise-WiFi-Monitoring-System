import smtplib
from email.message import EmailMessage

from app.core.config import settings


class NotificationService:

    async def notify_alert(
        self,
        alert,
        recipient_email: str | None = None,
    ) -> None:

        # Use the database-configured technician email when provided.
        # Fall back to the .env recipient for compatibility.
        to_email = recipient_email or settings.alert_email_recipient

        message = EmailMessage()

        message["Subject"] = (
            f"[Wi-Fi Security Alert] {alert.alert_type} "
            f"({alert.severity})"
        )
        message["From"] = settings.smtp_username
        message["To"] = to_email

        message.set_content(
            f"""Enterprise Wi-Fi Monitoring System

Security Alert Detected

Alert ID: {alert.id}
Alert Type: {alert.alert_type}
Severity: {alert.severity}
Device MAC: {alert.device_mac}

Description:
{alert.description}

Created At:
{alert.created_at}

Please investigate this alert through the monitoring dashboard.
"""
        )

        try:
            with smtplib.SMTP(
                settings.smtp_host,
                settings.smtp_port,
                timeout=10,
            ) as server:
                server.starttls()
                server.login(
                    settings.smtp_username,
                    settings.smtp_password,
                )
                server.send_message(message)

            print(
                f"[EMAIL] Alert #{alert.id} sent successfully "
                f"to {to_email}."
            )

        except Exception as exc:
            print(
                f"[EMAIL ERROR] Failed to send alert "
                f"#{alert.id}: {exc}"
            )

