# Соглашения по Clean Architecture

Репозиторий организован как единый модульный монорепозиторий с явными границами контекстов.

## Границы контекстов

- `automation` — оркестрация и прикладной поток (`n8n`, API распознавания).
- `services` — прикладные сервисы (`services/whisper_chunk_api`, `services/parakeet_api`).
- `supabase` — инфраструктурный стек в `infrastructure/supabase`.
- `infrastructure` — compose-конфиги, gateway, env-шаблоны, служебные скрипты.
- `runtime` — изменяемые локальные данные (`runtime/n8n_data`, `runtime/records`, `runtime/audio`).
- `qa` — тесты и артефакты верификации (`qa/tests`).

## Слои Python-сервисов

Каждый сервис в `services/*` следует схеме:

- `entrypoints/` — транспортные адаптеры (HTTP-роуты, парсинг запросов, маппинг ответов).
- `application/` — use case, DTO, порты, ошибки уровня приложения.
- `infrastructure/` — адаптеры к SDK/FS/процессам/внешним библиотекам.
- `main.py` — только composition root (связывание зависимостей и запуск приложения).

## Правило зависимостей

- `entrypoints -> application`
- `infrastructure -> application`
- `application` не должен импортировать `fastapi`, `nemo`, `openai`, `whisper`, `subprocess` и другие инфраструктурные зависимости.

## Структура Compose

- `docker-compose.base.yml` — общие сети и volume.
- `docker-compose.automation.yml` — контекст automation.
- `docker-compose.supabase.yml` — контекст supabase.
- `docker-compose.yml` — legacy-совместимость на период миграции.

## Definition of Done для изменений

1. Внешний API-контракт совместим (если не согласовано версионирование).
2. Для use case есть unit/contract-тесты.
3. Compose smoke-check проходит для затронутого контекста.
4. Runtime-данные не попадают в git.
