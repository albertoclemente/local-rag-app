#!/usr/bin/env bash
set -euo pipefail

# Docker-only (backend + qdrant). Requires backend Dockerfile.
# Starts qdrant and backend with docker compose --profile full

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

docker compose -f docker/docker-compose.yml --profile full up -d

echo "Services running:"
docker compose -f docker/docker-compose.yml ps

echo "- Qdrant:  http://localhost:6333"
echo "- Backend:  http://localhost:8000"
echo "(Frontend still runs locally: cd frontend && npm run build && npm run start, or use dev server npm run dev)"