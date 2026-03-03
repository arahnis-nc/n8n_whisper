# n8n + ASR + Supabase (локальный стек)

Этот репозиторий поднимает локальный стек из:
- `n8n`
- `Whisper Chunk API`
- `Parakeet API`
- `Supabase` (через `Kong`)

## Структура проекта

- `services/` — прикладные сервисы (`whisper_chunk_api`, `parakeet_api`)
- `infrastructure/` — compose, gateway, env-шаблоны, supabase-ресурсы
- `runtime/` — локальные данные (`n8n_data`, `records`, `audio`)
- `qa/` — тесты
- `docs/` — архитектура и инструкции по сервисам

## Быстрый запуск

1) Создайте `.env` в корне:

```bash
cat infrastructure/env/automation/.env.example infrastructure/env/supabase/.env.example > .env
```

2) Поднимите нужный контекст:

Полный стек:

```bash
docker compose -f docker-compose.base.yml -f docker-compose.automation.yml -f docker-compose.supabase.yml up -d
```

Только automation (`n8n`, `whisper`, `parakeet`, `nginx`):

```bash
docker compose -f docker-compose.base.yml -f docker-compose.automation.yml up -d
```

Только supabase:

```bash
docker compose -f docker-compose.base.yml -f docker-compose.supabase.yml up -d
```

3) Проверка:

```bash
curl -sS http://localhost:5678/healthz
curl -sS http://localhost:8000/auth/v1/health
```

## Все env-переменные

Источник шаблонов:
- `infrastructure/env/automation/.env.example`
- `infrastructure/env/supabase/.env.example`

### n8n

- `N8N_VERSION` — версия образа `n8n`
- `N8N_BASIC_AUTH_USER` — логин basic auth
- `N8N_BASIC_AUTH_PASSWORD` — пароль basic auth
- `N8N_SECURE_COOKIE` — secure-cookie режим
- `N8N_PAYLOAD_SIZE_MAX` — лимит payload
- `N8N_HOST` — внешний хост n8n
- `N8N_PROTOCOL` — протокол (`http/https`)
- `N8N_EDITOR_BASE_URL` — базовый URL editor
- `WEBHOOK_URL` — базовый URL webhook
- `N8N_PROXY_HOPS` — число proxy hops
- `N8N_DEFAULT_BINARY_DATA_MODE` — режим хранения бинарных данных

### ASR (Whisper/Parakeet)

- `PARAKEET_MODEL` — модель Parakeet по умолчанию
- `PARAKEET_DEVICE` — устройство (`cpu/cuda`)
- `OPENAI_API_KEY` — ключ OpenAI для cloud-режима Whisper
- `OPENAI_BASE_URL` — альтернативный base URL OpenAI-совместимого API
- `OPENAI_WHISPER_MODEL` — облачная модель Whisper по умолчанию

### URLs

- `SITE_URL` — базовый URL Studio
- `API_EXTERNAL_URL` — внешний URL API gateway
- `SUPABASE_PUBLIC_URL` — публичный URL Supabase
- `ADDITIONAL_REDIRECT_URLS` — allow-list redirect URL

### Postgres

- `POSTGRES_HOST` — хост Postgres
- `POSTGRES_PORT` — порт Postgres
- `POSTGRES_DB` — имя БД
- `POSTGRES_PASSWORD` — пароль БД
- `PGRST_DB_SCHEMAS` — схемы для PostgREST

### Studio

- `STUDIO_DEFAULT_ORGANIZATION` — организация по умолчанию
- `STUDIO_DEFAULT_PROJECT` — проект по умолчанию

### JWT / ключи

- `JWT_SECRET` — JWT secret
- `ANON_KEY` — anon API key
- `SERVICE_ROLE_KEY` — service-role API key
- `PG_META_CRYPTO_KEY` — ключ pg-meta
- `SECRET_KEY_BASE` — secret key realtime
- `VAULT_ENC_KEY` — ключ vault
- `LOGFLARE_PUBLIC_ACCESS_TOKEN` — токен public analytics
- `LOGFLARE_PRIVATE_ACCESS_TOKEN` — токен private analytics

### Auth

- `DISABLE_SIGNUP` — отключение регистрации
- `JWT_EXPIRY` — TTL JWT
- `ENABLE_EMAIL_SIGNUP` — email signup
- `ENABLE_ANONYMOUS_USERS` — anonymous users
- `ENABLE_EMAIL_AUTOCONFIRM` — email auto-confirm
- `ENABLE_PHONE_SIGNUP` — phone signup
- `ENABLE_PHONE_AUTOCONFIRM` — phone auto-confirm

### SMTP

- `SMTP_ADMIN_EMAIL` — email админа
- `SMTP_HOST` — SMTP host
- `SMTP_PORT` — SMTP port
- `SMTP_USER` — SMTP user
- `SMTP_PASS` — SMTP password
- `SMTP_SENDER_NAME` — sender name
- `MAILER_URLPATHS_INVITE` — путь invite
- `MAILER_URLPATHS_CONFIRMATION` — путь confirmation
- `MAILER_URLPATHS_RECOVERY` — путь recovery
- `MAILER_URLPATHS_EMAIL_CHANGE` — путь email change

### Storage

- `STORAGE_TENANT_ID` — tenant id
- `REGION` — регион
- `GLOBAL_S3_BUCKET` — bucket
- `S3_PROTOCOL_ACCESS_KEY_ID` — access key id
- `S3_PROTOCOL_ACCESS_KEY_SECRET` — access key secret
- `IMGPROXY_ENABLE_WEBP_DETECTION` — webp detection

### Functions

- `FUNCTIONS_VERIFY_JWT` — проверка JWT в edge functions

### Kong dashboard

- `DASHBOARD_USERNAME` — логин dashboard
- `DASHBOARD_PASSWORD` — пароль dashboard

## Документация по сервисам

- `docs/services/how-to-call-services.md`
- `docs/services/n8n.md`
- `docs/services/whisper.md`
- `docs/services/parakeet.md`
- `docs/services/supabase.md`
- `docs/architecture/clean-architecture.md`
