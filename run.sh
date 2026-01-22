#!/bin/bash

# Add local DNS entry for Actual Budget server
echo "192.168.1.147 money.home" >> /etc/hosts

export DISPLAY=:99
rm -f /tmp/.X99-lock
echo "[INIT] Starting Xvfb virtual display..."
Xvfb :99 -ac -screen 0 1920x1080x24 &
sleep 2
echo "[INIT] Launching PyWebIO application..."
exec python3 -u webui.py
