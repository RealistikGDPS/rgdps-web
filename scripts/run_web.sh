#!/bin/bash
set -euo pipefail

echo "Starting the RealistikGDPS website..."

UVICORN_ARGS=(
    "--host" "${APP_HTTP_HOST:=0.0.0.0}"
    "--port" "${APP_HTTP_PORT:=80}"
    "--no-server-header"
)

if [ "${APP_TRUST_PROXY_HEADERS:-false}" = "true" ]; then
    UVICORN_ARGS+=("--proxy-headers" "--forwarded-allow-ips" "*")
fi

# Worker processes, each with its own event loop, connection pools and icon
# cache. Reload implies one process, so development mode ignores the setting.
if [ "${APP_DEV_MODE:-false}" = "true" ]; then
    echo "Development mode enabled."
    UVICORN_ARGS+=("--reload")
else
    UVICORN_ARGS+=("--workers" "${APP_WORKERS:=1}")
fi

exec uv run --no-sync uvicorn web.main:asgi_app "${UVICORN_ARGS[@]}"
