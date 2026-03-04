# Audio Ingest API

Сервис: `services/audio_ingest_api`  
Внутренний URL в docker-сети: `http://audio-ingest:8000`

## Эндпоинты

- `GET /health` — проверка состояния
- `POST /ingest` — загрузка файла и создание outbox-события (`pending`)
- `GET /outbox/{event_id}/status?secret=...` — безопасная проверка статуса

## Контракт `POST /ingest`

Формат: `multipart/form-data`

- `email` — email пользователя
- `file` — загружаемый файл (видео или аудио)

Пример:

```bash
curl -sS -X POST http://audio-ingest:8000/ingest \
  -F "email=user@example.com" \
  -F "file=@/path/to/sample.mp4"
```

Ответ:

```json
{
  "event_id": "c8b9...",
  "status": "pending",
  "secret": "base64url-secret"
}
```

`secret` возвращается один раз при загрузке и нужен для последующей проверки статуса.

## Контракт `GET /outbox/{event_id}/status?secret=...`

Пример:

```bash
curl -sS "http://audio-ingest:8000/outbox/c8b9.../status?secret=base64url-secret"
```

Ответ:

```json
{
  "event_id": "c8b9...",
  "status": "processing",
  "audio_ready": false,
  "created_at": "2026-03-03T15:00:00+00:00"
}
```

## Outbox-first обработка

1. API сохраняет входной файл в `runtime/audio/inbox`.
2. API создает запись в SQLite `runtime/audio/outbox/outbox.db` со статусом `pending`.
3. API добавляет запись в `notification_outbox` для отправки email о принятии файла.
4. `audio-ingest-worker` периодически берет `pending` задачи:
   - если входной файл `video` — извлекает дорожку через `ffmpeg`;
   - если входной файл `audio` — копирует как есть.
5. Готовый аудиофайл сохраняется в `runtime/audio/processed`.
6. Outbox-запись получает:
   - `status=ready` и `audio_path`, либо
   - `status=failed` при ошибке.
7. `audio-notify-worker` отправляет email по SMTP асинхронно:
   - тема: `Файл принят к обработке`;
   - в письме: `event_id`, `secret`, ссылка на страницу проверки;
   - текст содержит, что письмо автоматическое, отвечать на него не нужно;
   - при ошибке отправки запись возвращается в `pending`, увеличивается `attempts`, воркер повторяет попытку.

## SMTP переменные

- `SMTP_HOST` — хост SMTP сервера (обязательно)
- `SMTP_PORT` — порт SMTP (`587` по умолчанию)
- `SMTP_USERNAME` / `SMTP_PASSWORD` — учетные данные (если нужны)
- `SMTP_FROM` — email отправителя
- `SMTP_USE_STARTTLS` — `true/false`, включение STARTTLS

## Базовый health-check

```bash
curl -sS http://audio-ingest:8000/health
```

