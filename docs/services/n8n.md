# n8n

Сервис: `n8n`  
UI с хоста: `http://localhost:5678`  
Через nginx: `http://localhost:8080`

## Проверка доступности

```bash
curl -sS http://localhost:5678/healthz
```

## Рекомендации по вызову внутренних API из workflow

В `HTTP Request` node лучше использовать внутренние адреса docker-сети:

- `http://whisper:8000/transcribe-chunks`
- `http://parakeet:8000/transcribe`

Это уменьшает задержки и не зависит от публикации портов на хосте.

## Где лежат данные

- рабочие данные n8n: `runtime/n8n_data`
- общие аудио-данные: `runtime/records` и `runtime/audio`
