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

check "http://localhost:8080/audio-upload" "nginx static ui"
check "http://localhost:8080/audio-ingest/health" "audio-ingest health"
check "http://localhost:8080/whisper/health" "whisper health"
check "http://localhost:8080/parakeet/health" "parakeet health"

echo "Smoke checks passed."
