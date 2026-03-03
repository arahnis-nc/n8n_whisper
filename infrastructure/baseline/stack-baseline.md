# Stack Baseline

Этот документ фиксирует runtime baseline audio-only стека.

## Service Group

- Audio context: `nginx`, `whisper`, `parakeet`, `audio-ingest`, `audio-ingest-worker`

## Public Ports

- `8080` -> `nginx`

## Primary Health Checks

- `http://localhost:8080/audio-upload` (UI)
- `http://localhost:8080/audio-ingest/health`
- `http://localhost:8080/whisper/health`
- `http://localhost:8080/parakeet/health`

## Persistent Runtime Data

- `./runtime/records`
- `./runtime/audio`

