# Modular Compose Layout

This repository now supports modular compose files in addition to the legacy monolith file.

## Files

- `docker-compose.base.yml` - shared networks and volumes
- `docker-compose.automation.yml` - n8n + ASR services
- `docker-compose.supabase.yml` - Supabase services
- `docker-compose.yml` - legacy compatibility entrypoint

## Run Full Stack (Modular)

```bash
docker compose \
  -f docker-compose.base.yml \
  -f docker-compose.automation.yml \
  -f docker-compose.supabase.yml \
  up -d
```

## Run Only Automation Context

```bash
docker compose \
  -f docker-compose.base.yml \
  -f docker-compose.automation.yml \
  up -d
```

## Run Only Supabase Context

```bash
docker compose \
  -f docker-compose.base.yml \
  -f docker-compose.supabase.yml \
  up -d
```
