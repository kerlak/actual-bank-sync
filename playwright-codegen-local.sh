#!/bin/bash
# Run Playwright codegen locally (not in container)
# Simpler alternative for macOS

set -e

echo "[*] Installing Playwright locally if needed..."

# Check if playwright is installed
if ! python3 -c "import playwright" 2>/dev/null; then
    echo "[*] Installing playwright..."
    pip3 install playwright==1.56.0 playwright-stealth==2.0.0
fi

# Install browsers if needed
if [ ! -d "$HOME/Library/Caches/ms-playwright" ]; then
    echo "[*] Installing Chromium..."
    python3 -m playwright install chromium
fi

echo ""
echo "[*] Launching Playwright codegen (local)..."
echo "[*] Browser will open - interact with the site to record actions"
echo "[*] Press Ctrl+C when done to generate the code"
echo ""

# Run codegen locally
python3 -m playwright codegen https://www.ibercaja.es/

echo ""
echo "[*] Done! Copy the generated code to banks/ibercaja.py"
