# Audio Ingest API

Сервис: `services/audio_ingest_api`  
Внутренний URL в docker-сети: `http://audio-ingest:8000`

## Эндпоинты

- `GET /health` — проверка состояния
- `POST /ingest` — загрузка файла и создание outbox-события (`pending`)
- `GET /outbox/{event_id}` — статус события

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
  "status": "pending"
}
```

## Outbox-first обработка

1. API сохраняет входной файл в `runtime/audio/inbox`.
2. API создает запись в SQLite `runtime/audio/outbox.db` со статусом `pending`.
3. `audio-ingest-worker` периодически берет `pending` задачи:
   - если входной файл `video` — извлекает дорожку через `ffmpeg`;
   - если входной файл `audio` — копирует как есть.
4. Готовый аудиофайл сохраняется в `runtime/audio/processed`.
5. Outbox-запись получает:
   - `status=ready` и `audio_path`, либо
   - `status=failed` при ошибке.

## Базовый health-check

```bash
curl -sS http://audio-ingest:8000/health
```

