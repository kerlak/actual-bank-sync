#!/bin/bash
# Launch Playwright codegen from the container
# This ensures you're using the exact same environment as the production container

set -e

echo "[*] Building container image..."
podman build -t banking-hub .

echo ""
echo "[*] Checking X11 setup..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v xquartz &> /dev/null; then
        echo "[!] XQuartz not found. Install with: brew install --cask xquartz"
        echo "[!] After installing, open XQuartz and enable 'Allow connections from network clients'"
        echo "[!] Then run: xhost +localhost"
        exit 1
    fi

    if ! pgrep -q XQuartz; then
        echo "[!] XQuartz is not running. Starting..."
        open -a XQuartz
        sleep 2
    fi

    # Allow localhost connections
    xhost +localhost > /dev/null 2>&1 || true
    DISPLAY_VAR="host.docker.internal:0"
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

# Launch codegen
podman run -it --rm \
  -e DISPLAY="$DISPLAY_VAR" \
  -v "$PWD:/app" \
  --workdir /app \
  banking-hub \
  playwright codegen https://www.ibercaja.es/

echo ""
echo "[*] Done! Copy the generated code to banks/ibercaja.py"
