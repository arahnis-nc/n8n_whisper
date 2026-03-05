# Audio Processing Stack (локальный стек)

Репозиторий поднимает локальный audio-only стек из:
- `Whisper Chunk API`
- `Parakeet API`
- `Audio Ingest API` + polling worker
- `nginx` gateway + статический UI загрузки

## Структура проекта

- `services/` — прикладные сервисы (`whisper_chunk_api`, `parakeet_api`, `audio_ingest_api`)
- `infrastructure/` — compose, gateway, env-шаблоны, служебные скрипты
- `runtime/` — локальные данные (`records`, `audio`)
- `qa/` — тесты
- `docs/` — архитектура и инструкции по сервисам

## Быстрый запуск

1) Создайте `.env` в корне (или скопируйте шаблон):

```bash
cp .env.example .env
```

2) Создайте файл Basic Auth для `nginx`:

```bash
printf "admin:$(openssl passwd -apr1 'admin')\n" > infrastructure/gateway/nginx/.htpasswd
```

Можно заменить `admin/admin` на свои значения логина и пароля.

3) Поднимите стек:

```bash
docker compose up -d --build
```

4) Проверка:

```bash
curl -u admin:admin -sS http://localhost:8080/audio-upload
curl -u admin:admin -sS http://localhost:8080/audio-ingest/health
curl -u admin:admin -sS http://localhost:8080/whisper/health
curl -u admin:admin -sS http://localhost:8080/parakeet/health
```

## Env-переменные

- `PARAKEET_MODEL`
- `PARAKEET_DEVICE`
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_WHISPER_MODEL`
- `AUDIO_OUTBOX_POLL_SECONDS`
- `AUDIO_OUTBOX_BATCH_SIZE`

## Документация

- `docs/services/how-to-call-services.md`
- `docs/services/whisper.md`
- `docs/services/parakeet.md`
- `docs/services/audio-ingest.md`
- `docs/architecture/clean-architecture.md`

