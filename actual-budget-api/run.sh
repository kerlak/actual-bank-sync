#!/bin/sh

# Read options from Home Assistant add-on config (if available)
OPTIONS_FILE="/data/options.json"
if [ -f "$OPTIONS_FILE" ]; then
    API_PORT=$(python3 -c "import json; print(json.load(open('$OPTIONS_FILE')).get('api_port', 2078))")
    LOG_LEVEL=$(python3 -c "import json; print(json.load(open('$OPTIONS_FILE')).get('log_level', 'info'))")
    ACTUAL_HOST=$(python3 -c "import json; print(json.load(open('$OPTIONS_FILE')).get('actual_budget_host', ''))")
    ACTUAL_IP=$(python3 -c "import json; print(json.load(open('$OPTIONS_FILE')).get('actual_budget_ip', ''))")
    IGNORE_SSL=$(python3 -c "import json; print(json.load(open('$OPTIONS_FILE')).get('ignore_ssl', True))")
    echo "[INIT] Running as Home Assistant add-on"

    # Configure /etc/hosts if host and IP are provided
    if [ -n "$ACTUAL_HOST" ] && [ -n "$ACTUAL_IP" ]; then
        echo "$ACTUAL_IP $ACTUAL_HOST" >> /etc/hosts
        echo "[INIT] Added hosts entry: $ACTUAL_IP $ACTUAL_HOST"
    fi

    # Disable SSL verification if configured
    if [ "$IGNORE_SSL" = "True" ]; then
        export PYTHONHTTPSVERIFY=0
        export CURL_CA_BUNDLE=""
        export REQUESTS_CA_BUNDLE=""
        echo "[INIT] SSL verification disabled"
    fi
else
    API_PORT=2078
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
