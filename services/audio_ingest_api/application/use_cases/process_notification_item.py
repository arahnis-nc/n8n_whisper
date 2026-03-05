from audio_ingest_api.application.dto import NotificationProcessResult
from audio_ingest_api.application.ports import EmailSenderPort, NotificationOutboxRepositoryPort


class ProcessNotificationItemUseCase:
    def __init__(self, notification_repository: NotificationOutboxRepositoryPort, sender: EmailSenderPort):
        self._notification_repository = notification_repository
        self._sender = sender

    def execute(self, notification_id: str) -> NotificationProcessResult:
        item = self._notification_repository.mark_sending(notification_id)
        subject = "Файл принят к обработке"
        body = (
            "Файл принят к обработке.\n"
            "Письмо отправлено автоматически, отвечать на него не нужно.\n\n"
            f"event_id: {item.event_id}\n"
            f"secret: {item.access_secret}\n"
            f"Страница проверки: /audio-status?event_id={item.event_id}\n\n"
            "Саммари придет на эту почту и будет доступно на странице проверки."
        )
        try:
            self._sender.send(recipient=item.email, subject=subject, body=body)
            sent = self._notification_repository.mark_sent(notification_id)
            return NotificationProcessResult(
                id=sent.id,
                status=sent.status,
                attempts=sent.attempts,
                last_error=sent.last_error,
            )
        except Exception as err:
            pending = self._notification_repository.mark_retry(notification_id, str(err))
            return NotificationProcessResult(
                id=pending.id,
                status=pending.status,
                attempts=pending.attempts,
                last_error=pending.last_error,
            )
