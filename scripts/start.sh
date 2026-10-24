#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
BUILD=0
OPEN=0
for arg in "$@"; do
  case "$arg" in
    --build) BUILD=1 ;;
    --open) OPEN=1 ;;
    -h|--help) echo 'Usage: bash scripts/start.sh [--build] [--open]'; exit 0 ;;
    *) echo "Option inconnue : $arg" >&2; exit 2 ;;
  esac
done
command -v docker >/dev/null 2>&1 || { echo 'Docker CLI introuvable. Démarre Docker Desktop.' >&2; exit 1; }
echo 'Attente du moteur Docker (maximum 3 minutes)...'
ready=0
for _ in $(seq 1 36); do
  if docker info >/dev/null 2>&1; then ready=1; break; fi
  sleep 5
done
[[ "$ready" -eq 1 ]] || { echo 'Docker ne répond pas. Démarre Docker Desktop puis réessaie.' >&2; exit 1; }
docker compose config -q
if [[ "$BUILD" -eq 1 ]]; then docker compose up -d --build; else docker compose up -d; fi
echo
docker compose ps
echo
echo 'Dashboard : http://localhost:8502'
echo 'UI Spark (si active) : http://localhost:4041'
if [[ "$OPEN" -eq 1 ]]; then
  if command -v explorer.exe >/dev/null 2>&1; then explorer.exe http://localhost:8502 >/dev/null 2>&1 || true
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open http://localhost:8502 >/dev/null 2>&1 || true
  fi
fi
