# Supabase (через Kong)

Публичные точки входа с хоста:

- Kong API Gateway: `http://localhost:8000`
- Studio: `http://localhost:3000`

## Быстрая проверка

```bash
curl -sS http://localhost:8000/auth/v1/health
```

## Основные маршруты через Kong

- `http://localhost:8000/auth/v1/...`
- `http://localhost:8000/rest/v1/...`
- `http://localhost:8000/storage/v1/...`
- `http://localhost:8000/functions/v1/...`

## Авторизация

Для защищенных маршрутов нужен API-ключ:

- `ANON_KEY` — пользовательский контекст
- `SERVICE_ROLE_KEY` — сервисный контекст (повышенные права)

Пример с anon-ключом:

```bash
curl -sS http://localhost:8000/rest/v1/ \
  -H "apikey: ${ANON_KEY}" \
  -H "Authorization: Bearer ${ANON_KEY}"
```
