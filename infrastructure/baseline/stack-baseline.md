# Stack Baseline

This document captures the pre-refactor runtime baseline and rollback checkpoints.

## Service Groups

- Automation context: `n8n`, `nginx`, `whisper`, `parakeet`
- Supabase context: `studio`, `kong`, `auth`, `rest`, `realtime`, `storage`, `imgproxy`, `meta`, `functions`, `analytics`, `vector`, `db`

## Public Ports

- `5678` -> `n8n`
- `8080` -> `nginx`
- `3000` -> `studio`
- `8000` -> `kong`

## Primary Health Checks

- `http://localhost:5678/healthz` (n8n)
- `http://localhost:8080/` (nginx reverse proxy)
- `http://localhost:8000/auth/v1/health` (supabase auth via kong)
- `http://localhost:3000/` (studio)
- `http://localhost:8000/rest/v1/` (postgrest via kong; requires auth config in real calls)

## Persistent Runtime Data (Rollback-Critical)

- `./runtime/n8n_data`
- `./runtime/records`
- `./runtime/audio`
- `./infrastructure/supabase/volumes/db/data`
- `./infrastructure/supabase/volumes/storage`

## Rollback Policy

1. Keep compose service names and volume mount paths stable during structural refactors.
2. Before switching runtime commands, create a backup archive of rollback-critical directories.
3. Keep legacy `docker-compose.yml` runnable until all split compose flows are validated.
4. If migration introduces instability, restore the backup archive and use legacy compose command.
