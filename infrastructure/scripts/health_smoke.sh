#!/usr/bin/env bash
set -euo pipefail

check() {
  local url="$1"
  local label="$2"
  if curl -fsS "$url" >/dev/null; then
    echo "[OK] ${label}: ${url}"
  else
    echo "[FAIL] ${label}: ${url}" >&2
    return 1
  fi
}

check "http://localhost:5678/healthz" "n8n"
check "http://localhost:8080/" "nginx"
check "http://localhost:3000/" "studio"
check "http://localhost:8000/auth/v1/health" "kong->auth"

echo "Smoke checks passed."
