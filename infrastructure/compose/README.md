# Compose Layout

Проект использует единый compose-файл:

- `docker-compose.yml` — весь audio-only стек (`nginx`, `whisper`, `parakeet`, `audio-ingest`, `audio-ingest-worker`).

## Run Stack

```bash
docker compose up -d --build
```

