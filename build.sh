#!/usr/bin/env bash
set -euo pipefail

# Build script used by Vercel to build frontend and collect static files
ROOT_DIR=$(dirname "$0")
echo "Building frontend with bun..."
if [ -d "$ROOT_DIR/frontend" ]; then
  (cd "$ROOT_DIR/frontend" && if command -v bun >/dev/null 2>&1; then bun install --prefer-offline; bun run build; else echo "bun not found, skipping frontend build"; fi)
else
  echo "No frontend directory found, skipping frontend build"
fi

echo "Installing Python dependencies..."
if [ -f "$ROOT_DIR/uv.lock" ] && command -v uv >/dev/null 2>&1; then
  echo "uv.lock detected and uv available: installing dependencies with uv"
  # Try sync first (preferred), fall back to install
  if ! uv sync; then
    uv install
  fi

  echo "Running collectstatic via uv"
  uv run python manage.py collectstatic --noinput
else
  echo "uv not available or uv.lock missing: falling back to pip"
  if [ -f "$ROOT_DIR/requirements.txt" ]; then
    pip install -r "$ROOT_DIR/requirements.txt"
  fi

  echo "Collecting static files"
  python manage.py collectstatic --noinput
fi
