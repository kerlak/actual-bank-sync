#!/bin/bash
# Launch Playwright codegen from the container
# This ensures you're using the exact same environment as the production container

set -e

echo "[*] Building container image..."
podman build -t banking-hub .

echo ""
echo "[*] Checking X11 setup..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS with XQuartz
    if [ ! -d "/Applications/Utilities/XQuartz.app" ]; then
        echo "[!] XQuartz not installed."
        echo "[!] Run: ./setup-xquartz.sh"
        exit 1
    fi

    # Start XQuartz if not running
    if ! pgrep -q XQuartz; then
        echo "[*] Starting XQuartz..."
        open -a XQuartz
        sleep 3
    fi

    # Setup DISPLAY
    if [ -z "$DISPLAY" ]; then
        export DISPLAY=:0
        echo "[*] Set DISPLAY=$DISPLAY"
    fi

    # Try to configure xhost
    xhost +localhost > /dev/null 2>&1 || {
        echo "[!] Could not configure xhost automatically"
        echo "[!] Run in another terminal:"
        echo "    export DISPLAY=:0"
        echo "    xhost +localhost"
        echo ""
        read -p "Press Enter after running those commands..."
    }

    # Get host IP for macOS
    # Podman on macOS needs the actual host IP, not host.docker.internal
    HOST_IP=$(ipconfig getifaddr en0 || ipconfig getifaddr en1 || echo "192.168.1.1")
    echo "[*] Host IP: $HOST_IP"

    # Allow connections from that IP
    xhost + "$HOST_IP" > /dev/null 2>&1 || true

    DISPLAY_VAR="$HOST_IP:0"
else
    # Linux
    DISPLAY_VAR="${DISPLAY:-:0}"
    xhost +local:root > /dev/null 2>&1 || true
fi

echo "[*] Display: $DISPLAY_VAR"
echo ""
echo "[*] Launching Playwright codegen..."
echo "[*] Browser will open - interact with the site to record actions"
echo "[*] Press Ctrl+C when done to generate the code"
echo ""

# Launch codegen with network host mode for macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS: use slirp4netns for networking
    podman run -it --rm \
      --network slirp4netns:allow_host_loopback=true \
      -e DISPLAY="$DISPLAY_VAR" \
      -v "$PWD:/app" \
      --workdir /app \
      banking-hub \
      playwright codegen https://www.ibercaja.es/
else
    # Linux: use host network
    podman run -it --rm \
      --network host \
      -e DISPLAY="$DISPLAY_VAR" \
      -v "$PWD:/app" \
      --workdir /app \
      banking-hub \
      playwright codegen https://www.ibercaja.es/
fi

echo ""
echo "[*] Done! Copy the generated code to banks/ibercaja.py"
