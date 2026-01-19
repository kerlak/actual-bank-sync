#!/bin/bash
export DISPLAY=:99
rm -f /tmp/.X99-lock
echo "[INIT] Starting Xvfb virtual display..."
Xvfb :99 -ac -screen 0 1920x1080x24 &
sleep 2
echo "[INIT] Launching Python application..."
exec python3 -u app.py
