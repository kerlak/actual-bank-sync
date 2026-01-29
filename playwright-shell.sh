#!/bin/bash
# Launch interactive shell in the container
# Useful for testing Playwright commands manually

set -e

echo "[*] Building container image..."
podman build -t banking-hub .

echo ""
echo "[*] Checking X11 setup..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v xquartz &> /dev/null; then
        echo "[!] XQuartz not found. Install with: brew install --cask xquartz"
        exit 1
    fi

    if ! pgrep -q XQuartz; then
        echo "[!] XQuartz is not running. Starting..."
        open -a XQuartz
        sleep 2
    fi

    xhost +localhost > /dev/null 2>&1 || true
    DISPLAY_VAR="host.docker.internal:0"
else
    DISPLAY_VAR="${DISPLAY:-:0}"
    xhost +local:root > /dev/null 2>&1 || true
fi

echo "[*] Display: $DISPLAY_VAR"
echo ""
echo "[*] Launching interactive shell..."
echo ""
echo "Available commands:"
echo "  playwright codegen https://www.ibercaja.es/"
echo "  python banks/ibercaja.py"
echo "  python -m playwright install  # if needed"
echo ""

podman run -it --rm \
  -e DISPLAY="$DISPLAY_VAR" \
  -v "$PWD:/app" \
  --workdir /app \
  banking-hub \
  /bin/bash
