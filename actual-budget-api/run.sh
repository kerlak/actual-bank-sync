#!/bin/bash

# Read options from Home Assistant add-on config (if available)
OPTIONS_FILE="/data/options.json"
if [ -f "$OPTIONS_FILE" ]; then
    API_PORT=$(python3 -c "import json; print(json.load(open('$OPTIONS_FILE')).get('api_port', 8080))")
    LOG_LEVEL=$(python3 -c "import json; print(json.load(open('$OPTIONS_FILE')).get('log_level', 'info'))")
    echo "[INIT] Running as Home Assistant add-on"
else
    API_PORT=8080
    LOG_LEVEL=info
    echo "[INIT] Running standalone"
fi

echo "[INIT] API Port: $API_PORT"
echo "[INIT] Log Level: $LOG_LEVEL"
echo "[INIT] Starting Actual Budget REST API..."

exec python3 -m uvicorn rest_api:app \
    --host 0.0.0.0 \
    --port "$API_PORT" \
    --log-level "$LOG_LEVEL"
