#!/bin/bash
# Setup XQuartz for Playwright on macOS

set -e

echo "=== XQuartz Setup para Playwright ==="
echo ""

# 1. Verificar instalación
echo "[1/5] Verificando XQuartz..."
if [ ! -d "/Applications/Utilities/XQuartz.app" ]; then
    echo "XQuartz no está instalado."
    echo "Instalando con Homebrew..."
    brew install --cask xquartz
    echo ""
    echo "⚠️  IMPORTANTE: Después de instalar XQuartz:"
    echo "   1. Cierra sesión y vuelve a iniciarla (o reinicia el Mac)"
    echo "   2. Vuelve a ejecutar este script"
    exit 0
fi
echo "✓ XQuartz instalado"

# 2. Verificar que no esté corriendo (para poder configurarlo)
echo ""
echo "[2/5] Verificando estado de XQuartz..."
if pgrep -q XQuartz; then
    echo "XQuartz ya está corriendo. Cerrando para reconfigurar..."
    killall XQuartz 2>/dev/null || true
    sleep 2
fi

# 3. Configurar preferencias de XQuartz
echo ""
echo "[3/5] Configurando preferencias..."
defaults write org.xquartz.X11 nolisten_tcp -bool false
defaults write org.xquartz.X11 no_auth -bool false
defaults write org.xquartz.X11 enable_iglx -bool true

# 4. Iniciar XQuartz
echo ""
echo "[4/5] Iniciando XQuartz..."
open -a XQuartz

# Esperar a que se inicie
echo "Esperando a que XQuartz se inicie..."
for i in {1..10}; do
    if pgrep -q XQuartz; then
        break
    fi
    sleep 1
done

if ! pgrep -q XQuartz; then
    echo "✗ XQuartz no se inició correctamente"
    echo ""
    echo "Por favor:"
    echo "1. Abre XQuartz manualmente desde Applications/Utilities/XQuartz.app"
    echo "2. Ve a XQuartz > Preferences > Security"
    echo "3. Marca: 'Allow connections from network clients'"
    echo "4. Reinicia XQuartz y ejecuta este script de nuevo"
    exit 1
fi

echo "✓ XQuartz corriendo"

# 5. Configurar DISPLAY y permisos
echo ""
echo "[5/5] Configurando DISPLAY y permisos..."
export DISPLAY=:0

# Esperar un poco más para que XQuartz esté completamente listo
sleep 2

# Permitir conexiones desde localhost
xhost +localhost 2>/dev/null || {
    echo "⚠️  No se pudo ejecutar xhost automáticamente"
    echo ""
    echo "Ejecuta manualmente en otra terminal:"
    echo "  export DISPLAY=:0"
    echo "  xhost +localhost"
}

echo ""
echo "========================================="
echo "✓ XQuartz configurado correctamente"
echo "========================================="
echo ""
echo "Para usar Playwright, ejecuta en TU TERMINAL ACTUAL:"
echo ""
echo "  export DISPLAY=:0"
echo "  ./playwright-codegen.sh"
echo ""
echo "O simplemente ejecuta:"
echo "  ./playwright-codegen.sh"
echo ""
