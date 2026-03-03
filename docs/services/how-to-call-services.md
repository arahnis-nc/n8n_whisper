# Как вызывать сервисы

Этот файл — навигация по отдельным документам сервисов audio-only стека.

## Быстрый старт

```bash
docker compose up -d --build
```

## Документация по сервисам

- `docs/services/whisper.md`
- `docs/services/parakeet.md`
- `docs/services/audio-ingest.md`

## Сетевые адреса (кратко)

С хоста:
- `nginx`: `http://localhost:8080`
- UI загрузки: `http://localhost:8080/audio-upload`
- `audio-ingest` через gateway: `http://localhost:8080/audio-ingest/health`
- `whisper` через gateway: `http://localhost:8080/whisper/health`
- `parakeet` через gateway: `http://localhost:8080/parakeet/health`

Внутри docker-сети `audionet`:
- `whisper`: `http://whisper:8000`
- `parakeet`: `http://parakeet:8000`
- `audio-ingest`: `http://audio-ingest:8000`

