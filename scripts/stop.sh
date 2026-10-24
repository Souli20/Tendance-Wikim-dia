#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
command -v docker >/dev/null 2>&1 || { echo 'Docker CLI introuvable.' >&2; exit 1; }
docker compose stop
echo 'Conteneurs arrêtés. Les volumes et les données persistantes sont conservés.'
echo 'Redémarrer : bash scripts/start.sh'
