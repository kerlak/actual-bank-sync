#!/bin/bash
#
# Script para iniciar la REST API del widget de Actual Budget
#

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Iniciando REST API de Actual Budget ===${NC}\n"

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 no está instalado${NC}"
    exit 1
fi

echo -e "${YELLOW}Python version:${NC}"
python3 --version

# Verificar si las dependencias están instaladas
echo -e "\n${YELLOW}Verificando dependencias...${NC}"
if ! python3 -c "import fastapi" &> /dev/null; then
    echo -e "${YELLOW}Instalando dependencias...${NC}"
    pip3 install -r requirements.txt
else
    echo -e "${GREEN}✓ Dependencias instaladas${NC}"
fi

# Obtener IP local
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null)
    if [ -z "$LOCAL_IP" ]; then
        LOCAL_IP=$(ipconfig getifaddr en1 2>/dev/null)
    fi
else
    # Linux
    LOCAL_IP=$(hostname -I | awk '{print $1}')
fi

echo -e "\n${GREEN}=== Servidor REST API ===${NC}"
echo -e "URL local:    ${GREEN}http://localhost:8080${NC}"
if [ -n "$LOCAL_IP" ]; then
    echo -e "URL red local: ${GREEN}http://${LOCAL_IP}:8080${NC}"
    echo -e "\n${YELLOW}Usa esta URL en tu iPhone:${NC} http://${LOCAL_IP}:8080"
fi

echo -e "\n${YELLOW}Endpoints disponibles:${NC}"
echo -e "  GET  /                      - Health check"
echo -e "  POST /api/validate-connection - Validar conexión"
echo -e "  POST /api/monthly-balance    - Balance mensual"
echo -e "  POST /api/accounts           - Listar cuentas"

echo -e "\n${YELLOW}Presiona Ctrl+C para detener el servidor${NC}"
echo -e "${GREEN}===========================================${NC}\n"

# Iniciar el servidor
python3 rest_api.py
