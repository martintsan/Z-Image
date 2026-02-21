#!/usr/bin/env bash
# Start the Z-Image FastAPI service.
# Usage: ./server/run.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Activate venv if it exists
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
fi

# Install dependencies if needed
python3 -c "import fastapi, uvicorn, httpx" 2>/dev/null || {
    echo "Installing Python dependencies..."
    pip install fastapi uvicorn python-multipart httpx
}

echo "Starting Z-Image API server..."
exec python3 -m uvicorn server.app:app \
    --host "${FASTAPI_HOST:-0.0.0.0}" \
    --port "${FASTAPI_PORT:-8000}" \
    --log-level info
