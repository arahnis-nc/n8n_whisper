#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="${ROOT_DIR}/runtime/backups"
STAMP="$(date +%Y%m%d-%H%M%S)"
TARGET="${OUT_DIR}/baseline-${STAMP}.tar.gz"

mkdir -p "${OUT_DIR}"

echo "Creating baseline backup archive at: ${TARGET}"
tar -czf "${TARGET}" \
  -C "${ROOT_DIR}" \
  runtime/n8n_data \
  runtime/records \
  runtime/audio \
  infrastructure/supabase/volumes/db/data \
  infrastructure/supabase/volumes/storage

echo "Done."
