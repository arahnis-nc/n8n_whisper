# Соглашения по Clean Architecture

Репозиторий организован как модульный монорепозиторий с явными границами контекстов.

## Границы контекстов

- `services` — прикладные сервисы (`services/whisper_chunk_api`, `services/parakeet_api`, `services/audio_ingest_api`).
- `infrastructure` — compose-конфиги, gateway, env-шаблоны, служебные скрипты.
- `runtime` — изменяемые локальные данные (`runtime/records`, `runtime/audio`).
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
- `application` не должен импортировать инфраструктурные библиотеки (`fastapi`, `openai`, `whisper`, `subprocess`, и т.д.).

## Структура Compose

- `docker-compose.yml` — единый audio-only стек (`whisper`, `parakeet`, `audio-ingest`, `audio-ingest-worker`, `nginx`).

## Definition of Done для изменений

1. Внешний API-контракт совместим (если не согласовано версионирование).
2. Для use case есть unit/contract-тесты.
3. Compose smoke-check проходит для затронутого контура.
4. Runtime-данные не попадают в git.

