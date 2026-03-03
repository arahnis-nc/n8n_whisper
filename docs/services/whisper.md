# Whisper Chunk API

Сервис: `services/whisper_chunk_api`  
Внутренний URL в docker-сети: `http://whisper:8000`

## Эндпоинты

- `GET /health` — проверка состояния
- `POST /transcribe-chunks` — разбиение аудио на чанки и распознавание

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
