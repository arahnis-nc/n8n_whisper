#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-all}" == "automation" ]]; then
  docker compose -f docker-compose.base.yml -f docker-compose.automation.yml up -d
elif [[ "${1:-all}" == "supabase" ]]; then
  docker compose -f docker-compose.base.yml -f docker-compose.supabase.yml up -d
else
  docker compose -f docker-compose.base.yml -f docker-compose.automation.yml -f docker-compose.supabase.yml up -d
fi
