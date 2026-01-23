#!/bin/bash

# Read options from Home Assistant add-on config (if available)
OPTIONS_FILE="/data/options.json"
if [ -f "$OPTIONS_FILE" ]; then
    ACTUAL_HOST=$(python3 -c "import json; print(json.load(open('$OPTIONS_FILE'))['actual_budget_host'])")
    ACTUAL_IP=$(python3 -c "import json; print(json.load(open('$OPTIONS_FILE'))['actual_budget_ip'])")
    ACTUAL_FILE=$(python3 -c "import json; print(json.load(open('$OPTIONS_FILE'))['actual_budget_file_id'])")
    echo "[INIT] Running as Home Assistant add-on"
    echo "[INIT] Actual Budget: $ACTUAL_HOST -> $ACTUAL_IP"
    echo "$ACTUAL_IP $ACTUAL_HOST" >> /etc/hosts
    export ACTUAL_BUDGET_URL="https://$ACTUAL_HOST"
    export ACTUAL_BUDGET_FILE="$ACTUAL_FILE"
else
    echo "[INIT] Running standalone"
    echo "[INIT] Set ACTUAL_BUDGET_URL and ACTUAL_BUDGET_FILE env vars"
fi

export DISPLAY=:99
rm -f /tmp/.X99-lock
echo "[INIT] Starting Xvfb virtual display..."
Xvfb :99 -ac -screen 0 1920x1080x24 &
sleep 2
echo "[INIT] Launching PyWebIO application..."
exec python3 -u webui.py
