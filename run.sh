#!/bin/bash

# Read options from Home Assistant add-on config (if available)
OPTIONS_FILE="/data/options.json"
if [ -f "$OPTIONS_FILE" ]; then
    ACTUAL_HOST=$(python3 -c "import json; print(json.load(open('$OPTIONS_FILE'))['actual_budget_host'])")
    ACTUAL_IP=$(python3 -c "import json; print(json.load(open('$OPTIONS_FILE'))['actual_budget_ip'])")
    echo "[INIT] Running as Home Assistant add-on"
    echo "[INIT] Actual Budget: $ACTUAL_HOST -> $ACTUAL_IP"

    # Use /share for persistent downloads
    DOWNLOADS_DIR="/share/banking-hub/downloads"
    mkdir -p "$DOWNLOADS_DIR"
    ln -sfn "$DOWNLOADS_DIR" /app/downloads
else
    ACTUAL_HOST="money.home"
    ACTUAL_IP="192.168.1.147"
    echo "[INIT] Running standalone"
fi

# Add local DNS entry for Actual Budget server
echo "$ACTUAL_IP $ACTUAL_HOST" >> /etc/hosts

export DISPLAY=:99
rm -f /tmp/.X99-lock
echo "[INIT] Starting Xvfb virtual display..."
Xvfb :99 -ac -screen 0 1920x1080x24 &
sleep 2
echo "[INIT] Launching PyWebIO application..."
exec python3 -u webui.py
