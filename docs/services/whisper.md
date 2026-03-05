# Whisper Chunk API

Сервис: `services/whisper_chunk_api`  
Внутренний URL в docker-сети: `http://whisper:8000`

Отдельный polling-воркер: `python -m whisper_chunk_api.worker`

## Эндпоинты

- `GET /health` — проверка состояния
- `POST /transcribe-chunks` — разбиение аудио на чанки и распознавание
- `POST /tasks` — поставить mp3 задачу в SQLite очередь `whisper_tasks` для воркера

## Базовый health-check

```bash
curl -sS http://whisper:8000/health
```

## Входные параметры `POST /transcribe-chunks`

- `path` — путь к файлу **относительно** `runtime/records`
- `backend` — `local` или `cloud`
- `model` — локальная модель (используется при `backend=local`)
- `cloud_model` — облачная модель (используется при `backend=cloud`)
- `task` — `transcribe` или `translate`
- `language` — необязательно (например, `ru`, `en`)
- `chunk_seconds` — длина чанка, от `30` до `3600`
- `prompt` — дополнительная подсказка для распознавания
- `temperature` — `0.0..1.0`

## Локальная модель (backend=local)

Локальный режим использует `openai-whisper` внутри контейнера (`whisper.load_model(...)`).

Пример:

```bash
curl -sS http://whisper:8000/transcribe-chunks \
  -H 'Content-Type: application/json' \
  -d '{
    "path": "calls/call-001.wav",
    "backend": "local",
    "model": "tiny",
    "task": "transcribe",
    "language": "ru",
    "chunk_seconds": 300,
    "temperature": 0.0
  }'
```

Типичные значения `model` для local:
- `tiny`
- `base`
- `small`
- `medium`
- `large`

## Облачный режим (backend=cloud)

Облачный режим использует OpenAI Audio API (`transcriptions`/`translations`).

### Обязательные переменные окружения

- `OPENAI_API_KEY` — обязателен
- `OPENAI_BASE_URL` — опционально (если нужен совместимый провайдер)
- `OPENAI_WHISPER_MODEL` — модель по умолчанию (если не передан `cloud_model`)

Если ключ не задан, сервис вернет `400` с ошибкой:
- `OPENAI_API_KEY is not set for backend=cloud`

Пример для облака:

```bash
curl -sS http://whisper:8000/transcribe-chunks \
  -H 'Content-Type: application/json' \
  -d '{
    "path": "calls/call-001.wav",
    "backend": "cloud",
    "cloud_model": "whisper-1",
    "task": "transcribe",
    "language": "ru",
    "chunk_seconds": 300,
    "temperature": 0.0
  }'
```

Пример для перевода в английский (`task=translate`):

```bash
curl -sS http://whisper:8000/transcribe-chunks \
  -H 'Content-Type: application/json' \
  -d '{
    "path": "calls/call-001.wav",
    "backend": "cloud",
    "cloud_model": "whisper-1",
    "task": "translate",
    "chunk_seconds": 300
  }'
```

## Формат ответа

Сервис возвращает:
- `input_path`
- `backend`
- `model`
- `task`
- `language`
- `chunk_seconds`
- `chunks_count`
- `text` (склеенный итоговый текст)
- `chunks` (массив по каждому чанку)

## Частые проблемы

- `File not found: ...` — неверный `path` или файла нет в `runtime/records`
- `Path must stay inside records directory` — попытка выйти за пределы records
- `ffmpeg failed: ...` — ошибка декодирования/чтения аудио
- пустой/плохой результат — попробуйте:
  - уменьшить `chunk_seconds`
  - задать `language`
  - для local сменить `model` на более точную

## Whisper worker (SQLite queue)

Воркер читает готовые mp3-задачи из SQLite (`status=ready`), отправляет файл в обработку и записывает результат разбора обратно в SQLite.

### Переменные окружения

- `WHISPER_TASKS_DB_PATH` — путь к БД задач (по умолчанию `/data/whisper/whisper.db`)
- `WHISPER_OUTBOX_POLL_SECONDS` — пауза между polling-циклами
- `WHISPER_OUTBOX_BATCH_SIZE` — сколько задач забрать за один claim
- `WHISPER_WORKER_COUNT` — количество параллельных worker-потоков
- `WHISPER_WORKER_LOG_LEVEL` — уровень логирования
- `WHISPER_ALLOWED_INPUT_DIRS` — список разрешенных директорий для входных файлов (через запятую)
- `WHISPER_TEXT_POSTPROCESS_ENABLED` — включить постобработку транскрипта через ChatGPT
- `WHISPER_TEXT_POSTPROCESS_MODEL` — модель ChatGPT для вычитки/разбивки по спикерам
- `WHISPER_TEXT_POSTPROCESS_TEMPERATURE` — температура для постобработки
- `WHISPER_SUMMARY_ENABLED` — включить генерацию summary встречи через ChatGPT
- `WHISPER_SUMMARY_MODEL` — модель ChatGPT для summary
- `WHISPER_SUMMARY_TEMPERATURE` — температура для summary
- `WHISPER_SUMMARY_EMAIL_ENABLED` — отправлять summary на почту запросившего

### Схема очереди

Таблица `whisper_tasks`:
- вход: `audio_path`, `status=ready`, параметры транскрибации (`backend`, `model`, `cloud_model`, `task`, `chunk_seconds`, `language`, `prompt`, `temperature`)
- выход: `status=done|failed`, `transcript_text`, `transcript_json`, `summary`, `error`

Если включен `WHISPER_TEXT_POSTPROCESS_ENABLED=true`, воркер после ASR отправляет текст в ChatGPT:
- добавляет пунктуацию;
- раскладывает текст по репликам (`Спикер 1:`, `Спикер 2:`).

Если включен `WHISPER_SUMMARY_ENABLED=true`, воркер формирует `summary` по фиксированному аналитическому промпту со структурой:
- `## Решения`
- `## Открытые вопросы`
- `## Action items`
- `## Риски`

Если `WHISPER_SUMMARY_EMAIL_ENABLED=true` и в задаче известен email запросившего, summary отправляется на почту.
Текст письма содержит обязательную фразу:
`Письмо отправлено автоматически, отвечать на него не нужно.`

### Постановка задачи в очередь

Пример:

```bash
curl -sS http://whisper:8000/tasks \
  -H 'Content-Type: application/json' \
  -d '{
    "audio_path": "calls/call-001.mp3",
    "backend": "local",
    "model": "tiny",
    "task": "transcribe",
    "chunk_seconds": 300,
    "temperature": 0.0
  }'
```

Ответ:
- `task_id` — идентификатор задачи в `whisper_tasks`
- `status` — `ready`

Обычно этот endpoint вызывается автоматически из `audio-ingest-worker` после того, как mp3
был выделен/подготовлен в `runtime/audio/processed`.
