#!/bin/bash
# Run Playwright codegen locally (not in container)
# Simpler alternative for macOS

set -e

VENV_DIR=".venv-playwright"

echo "[*] Setting up Python virtual environment..."

# Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "[*] Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Check if playwright is installed in venv
if ! python -c "import playwright" 2>/dev/null; then
    echo "[*] Installing playwright in virtual environment..."
    pip install --quiet playwright==1.56.0 playwright-stealth==2.0.0
fi

# Install browsers if needed
PLAYWRIGHT_CACHE="$HOME/Library/Caches/ms-playwright"
if [ ! -d "$PLAYWRIGHT_CACHE" ] || [ -z "$(ls -A $PLAYWRIGHT_CACHE 2>/dev/null)" ]; then
    echo "[*] Installing Chromium browser..."
    playwright install chromium
fi

echo ""
echo "[*] Launching Playwright codegen..."
echo "[*] Browser will open - interact with the site to record actions"
echo "[*] Press Ctrl+C when done to generate the code"
echo ""

# Run codegen
playwright codegen https://www.ibercaja.es/

# Deactivate venv
deactivate

echo ""
echo "[*] Done! Copy the generated code to banks/ibercaja.py"
