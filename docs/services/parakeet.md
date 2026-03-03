# Parakeet API

Сервис: `services/parakeet_api`  
Внутренний URL в docker-сети: `http://parakeet:8000`

## Эндпоинты

- `GET /health`
- `POST /transcribe`

## Health-check

```bash
curl -sS http://parakeet:8000/health
```

## JSON-режим (файл уже в records)

```bash
curl -sS http://parakeet:8000/transcribe \
  -H 'Content-Type: application/json' \
  -d '{
    "path": "calls/call-001.wav",
    "model": "nvidia/parakeet-tdt-0.6b-v3",
    "delete_source": false
  }'
```

## Multipart-режим (загрузка файла)

```bash
curl -sS http://parakeet:8000/transcribe \
  -F "file=@/absolute/path/to/file.wav" \
  -F "model=nvidia/parakeet-tdt-0.6b-v3"
```

## Важно

- `path` в JSON — относительный путь внутри `runtime/records`
- при multipart сервис кладет файл во временный upload и удаляет после обработки
