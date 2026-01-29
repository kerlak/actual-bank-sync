#!/bin/bash
# Launch Playwright codegen from the container
# For Linux - macOS users should use playwright-codegen-local.sh instead

set -e

# Check if running on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "=========================================="
    echo "  macOS Detected"
    echo "=========================================="
    echo ""
    echo "Podman on macOS runs in a VM which makes X11 forwarding complex."
    echo ""
    echo "Recommended: Use the local script instead:"
    echo "  ./playwright-codegen-local.sh"
    echo ""
    echo "This will run Playwright directly on your Mac (no container)."
    echo ""
    read -p "Continue with container anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting. Run: ./playwright-codegen-local.sh"
        exit 0
    fi
fi

echo "[*] Building container image..."
podman build -t banking-hub .

echo ""
echo "[*] Checking X11 setup..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo ""
    echo "[!] macOS X11 setup is complex with Podman."
    echo "[!] This may not work. Consider using playwright-codegen-local.sh"
    echo ""

    # Try to setup anyway
    if [ ! -d "/Applications/Utilities/XQuartz.app" ]; then
        echo "[!] XQuartz not installed. Install with:"
        echo "    brew install --cask xquartz"
        exit 1
    fi

    if ! pgrep -q XQuartz; then
        echo "[*] Starting XQuartz..."
        open -a XQuartz
        sleep 3
    fi

    export DISPLAY=:0
    xhost +localhost > /dev/null 2>&1 || true

    HOST_IP=$(ipconfig getifaddr en0 || ipconfig getifaddr en1 || echo "localhost")
    xhost + "$HOST_IP" > /dev/null 2>&1 || true

    DISPLAY_VAR="$HOST_IP:0"

    echo "[*] Display: $DISPLAY_VAR"
    echo "[*] Trying with Podman VM..."

    # Use podman machine ssh to run inside the VM
    podman machine ssh -- -X bash -c "
        cd /Users/$(whoami)/Development/banking/ibercaja
        podman run -it --rm \
          -e DISPLAY=\$DISPLAY \
          -v \"\$PWD:/app\" \
          --workdir /app \
          banking-hub \
          playwright codegen https://www.ibercaja.es/
    " || {
        echo ""
        echo "[!] Container codegen failed."
        echo "[!] Use instead: ./playwright-codegen-local.sh"
        exit 1
    }
else
    # Linux - straightforward
    DISPLAY_VAR="${DISPLAY:-:0}"
    xhost +local:root > /dev/null 2>&1 || true

    echo "[*] Display: $DISPLAY_VAR"
    echo ""
    echo "[*] Launching Playwright codegen..."
    echo "[*] Browser will open - interact with the site to record actions"
    echo "[*] Press Ctrl+C when done to generate the code"
    echo ""

    podman run -it --rm \
      --network host \
      -e DISPLAY="$DISPLAY_VAR" \
      -v /tmp/.X11-unix:/tmp/.X11-unix \
      -v "$PWD:/app" \
      --workdir /app \
      banking-hub \
      playwright codegen https://www.ibercaja.es/
fi

echo ""
echo "[*] Done! Copy the generated code to banks/ibercaja.py"
