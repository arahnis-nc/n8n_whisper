import os
import smtplib
from email.message import EmailMessage


class SmtpSummaryEmailSender:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
        sender_email: str,
        use_starttls: bool,
    ):
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._sender_email = sender_email
        self._use_starttls = use_starttls

    @classmethod
    def from_env(cls) -> "SmtpSummaryEmailSender":
        host = os.getenv("SMTP_HOST", "").strip()
        port = int(os.getenv("SMTP_PORT", "587"))
        username = os.getenv("SMTP_USERNAME")
        password = os.getenv("SMTP_PASSWORD")
        sender_email = os.getenv("SMTP_FROM", "no-reply@example.com").strip()
        use_starttls = os.getenv("SMTP_USE_STARTTLS", "true").lower() in {"1", "true", "yes"}
        if not host:
            raise RuntimeError("SMTP_HOST is required")
        return cls(
            host=host,
            port=port,
            username=username,
            password=password,
            sender_email=sender_email,
            use_starttls=use_starttls,
        )

    def send_summary(self, *, recipient: str, event_id: str | None, summary: str) -> None:
        subject = "Саммари встречи по аудиозаписи"
        body = (
            "Отправляем саммари по итогам обработки аудиозаписи.\n"
            "Письмо отправлено автоматически, отвечать на него не нужно.\n\n"
            f"event_id: {event_id or 'unknown'}\n\n"
            f"{summary}"
        )
        message = EmailMessage()
        message["From"] = self._sender_email
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(self._host, self._port, timeout=30) as smtp:
            smtp.ehlo()
            if self._use_starttls:
                smtp.starttls()
                smtp.ehlo()
            if self._username:
                smtp.login(self._username, self._password or "")
            smtp.send_message(message)


class NoopSummaryEmailSender:
    def send_summary(self, *, recipient: str, event_id: str | None, summary: str) -> None:
        return None
