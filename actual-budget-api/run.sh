#!/bin/bash
set -e

CONFIG_PATH="/data/options.json"

# Get configuration from Home Assistant options
API_PORT=$(jq --raw-output '.api_port // 8080' $CONFIG_PATH)
LOG_LEVEL=$(jq --raw-output '.log_level // "info"' $CONFIG_PATH)

echo "[INFO] Starting Actual Budget REST API..."
echo "[INFO] API Port: ${API_PORT}"
echo "[INFO] Log Level: ${LOG_LEVEL}"

# Start the REST API server
cd /app
exec python3 -m uvicorn rest_api:app \
    --host 0.0.0.0 \
    --port "${API_PORT}" \
    --log-level "${LOG_LEVEL}"
