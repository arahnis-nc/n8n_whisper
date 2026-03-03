# Как вызывать сервисы

Этот файл — навигация по отдельным документам сервисов.

## Быстрый старт

Полный стек:

```bash
docker compose -f docker-compose.base.yml -f docker-compose.automation.yml -f docker-compose.supabase.yml up -d
```

Только automation-контекст:

```bash
docker compose -f docker-compose.base.yml -f docker-compose.automation.yml up -d
```

## Документация по сервисам

- `docs/services/n8n.md`
- `docs/services/whisper.md`
- `docs/services/parakeet.md`
- `docs/services/supabase.md`

## Сетевые адреса (кратко)

С хоста:
- `n8n`: `http://localhost:5678`
- `nginx`: `http://localhost:8080`
- `supabase kong`: `http://localhost:8000`
- `supabase studio`: `http://localhost:3000`

Внутри docker-сети `n8nnet`:
- `whisper`: `http://whisper:8000`
- `parakeet`: `http://parakeet:8000`
- `kong`: `http://kong:8000`
