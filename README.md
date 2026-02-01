# Actual Budget Add-ons Repository

Home Assistant add-ons para Actual Budget: automatización bancaria y REST API.

## Add-ons Disponibles

### 1. Banking Hub - Actual Budget Sync

Multi-bank movements downloader with Actual Budget synchronization for Spanish banks (Ibercaja & ING).

## IMPORTANT DISCLAIMERS

**LEGAL NOTICE**: This software automates access to banking websites. Be aware:
- May violate your bank's Terms of Service
- You are responsible for compliance with local laws
- Use only with your own accounts
- No warranty or liability - use at your own risk

**See [SECURITY.md](SECURITY.md) for complete security policy and legal considerations.**

**RECOMMENDED**: Use the manual upload feature instead of automated scraping to avoid potential ToS violations.

#### Features

- **Automated bank scraping**: Download movements from Ibercaja and ING automatically
- **Manual upload support**: Upload Excel files manually if needed
- **Actual Budget integration**: Sync transactions directly to your Actual Budget accounts
- **Interactive file & account selection**: Choose which budget file and account to sync to
- **Smart credential management**: Saves your selections for future syncs
- **Multi-file support**: Different encryption keys for different budget files
- **Web UI**: Clean, terminal-style interface on port 2077
- **Home Assistant add-on**: Easy integration with Home Assistant

#### Supported Banks

- **Ibercaja**: Automatic Excel download via Playwright
- **ING**: Both Nómina and Naranja accounts with anti-bot protection

---

### 2. Actual Budget REST API

REST API para Actual Budget que permite integración con aplicaciones de terceros, widgets de iOS y otras herramientas.

📱 **[Ver documentación completa →](actual-budget-api/README.md)**

#### Features

- **REST API completa**: Endpoints para validación, cuentas, presupuesto y transacciones
- **Widget de iOS**: Visualiza tu presupuesto en tu iPhone
- **Integraciones personalizadas**: Conecta Actual Budget con otras apps
- **Puerto configurable**: Evita conflictos con otros servicios (default: 8080)
- **Multi-arquitectura**: Soporte para amd64, aarch64, armv7
- **Sin autenticación adicional**: Usa las credenciales de Actual Budget

#### Endpoints Disponibles

- `POST /api/validate` - Validar conexión y listar archivos
- `POST /api/accounts` - Obtener cuentas con saldos
- `POST /api/budget` - Presupuesto mensual por categorías
- `POST /api/transactions` - Transacciones por categoría

---

## Installation

### Home Assistant Add-ons

1. **Add this repository** to your Home Assistant:
   - Settings → Add-ons → Add-on Store → ⋮ → Repositories
   - Add repository: `https://github.com/kerlak/actual-bank-sync`

2. **Install the add-on you need**:
   - **Banking Hub**: For automated bank syncing
   - **Actual Budget REST API**: For iOS widget and integrations

3. **Configure and start** the add-on

#### Banking Hub Configuration

- `actual_budget_host`: Hostname of your Actual Budget server (e.g., `actual.local`)
- `actual_budget_ip`: IP address of your Actual Budget server
- `actual_budget_file_id`: (Optional) Default budget file name or ID
- Access the web UI on port **2077**

#### REST API Configuration

- `api_port`: Puerto de la API (default: 8080)
- `log_level`: Nivel de logging (info, debug, warning, error)
- Access the API on port **8080** (or configured port)

### Standalone (Docker)

#### Banking Hub
```bash
docker build -t banking-hub .
docker run -p 2077:2077 banking-hub
```

#### REST API
```bash
docker build -t actual-budget-api \
  --build-arg BUILD_FROM=python:3.11-alpine \
  actual-budget-api/
docker run -p 8080:8080 actual-budget-api
```

## Usage

### First Time Sync

1. Navigate to `http://your-host:2077`
2. Select your bank (Ibercaja or ING)
3. Download or upload movements
4. Click `[sync to actual]`
5. Enter Actual Budget server password
6. Select budget file from the list
7. Enter encryption key for the file (if encrypted)
8. Select target account
9. **Done!** Your selections are saved for next time

### Subsequent Syncs

1. Select your bank
2. Download or upload movements
3. Click `[sync to actual]`
4. Choose to use saved mapping or select different file/account
5. Sync completes automatically

### Managing Credentials

Access `[manage credentials]` from the main menu to:
- View all stored credentials
- View all saved file/account mappings
- Clear specific bank credentials
- Clear Actual Budget password
- Clear all saved mappings
- Clear everything

## Configuration

### Environment Variables

- `ACTUAL_BUDGET_URL`: URL of your Actual Budget server (default: `https://localhost`)
- `ACTUAL_BUDGET_FILE`: Default budget file name (used as pre-selection in HA)
- `ACTUAL_CERT_PATH`: Path to custom SSL certificate (default: `./certs/actual.pem`)

### Home Assistant Compatibility

Version 1.1.0 is **100% backward compatible** with version 1.0.0:

- Existing `actual_budget_file_id` configuration is automatically detected and pre-selected
- Legacy account mappings are pre-selected if they match existing accounts
- No configuration changes required

## Upgrading from 1.0.0 to 1.1.0

### For Standalone Users

No action required. The first sync will prompt you to select file and account, then save your preferences.

### For Home Assistant Users

No action required. Your existing configuration will be automatically detected:
- `actual_budget_file_id` from your add-on config will be pre-selected
- Default account names (Ibercaja común, ING Nómina, ING Naranja) will be pre-selected if they exist

To change these defaults, simply select different options during sync or use the `[manage credentials]` menu.

## Architecture

- **webui.py**: PyWebIO-based web interface
- **actual_sync.py**: Actual Budget synchronization logic using `actualpy`
- **banks/ibercaja.py**: Ibercaja scraper
- **banks/ing.py**: ING scraper with playwright-stealth
- **run.sh**: Docker entrypoint with Xvfb setup

## Security

- Bank credentials are stored in memory only (not persisted to disk)
- Actual Budget password is stored in memory only
- Encryption passwords are stored in memory only
- All credentials are cleared on app restart
- SSL verification is disabled for self-signed certificates (Actual Budget servers often use self-signed certs)

## iOS Widget

**NEW**: Widget de iOS para visualizar tu balance mensual por categorías directamente en tu iPhone.

### Características del Widget

- Muestra el balance del mes actual por categorías
- Tres tamaños: Pequeño (balance total), Mediano (top 5 categorías), Grande (todas las categorías)
- Actualización automática cada 15 minutos
- Almacenamiento seguro de credenciales en Keychain
- Compatible con iOS 17.0+ (iPhone 15 y posteriores)

### Inicio Rápido

1. Inicia el servidor REST API:
   ```bash
   ./start_rest_api.sh
   ```

2. Sigue la guía de instalación en `ios-widget/QUICKSTART.md`

3. Configura el widget con:
   - URL del servidor (ej: `http://192.168.1.100:8080`)
   - Contraseña de Actual Budget
   - Nombre del archivo de presupuesto
   - Clave de cifrado (opcional)

### Documentación del Widget

- **[QUICKSTART.md](ios-widget/QUICKSTART.md)**: Inicio rápido en 5 minutos
- **[INSTALLATION.md](ios-widget/INSTALLATION.md)**: Guía completa de instalación
- **[README.md](ios-widget/README.md)**: Documentación detallada

### Requisitos

- macOS con Xcode 15.0+
- iPhone con iOS 17.0+ (iPhone 15 y posteriores)
- Cuenta de desarrollador de Apple
- Python 3.8+ con FastAPI

## Troubleshooting

### "No budget files found"
- Verify Actual Budget server URL is correct
- Ensure server password is correct
- Check that Actual Budget server is accessible from the container

### "No accounts found"
- Verify the budget file is not corrupted
- Check that the encryption password is correct (if file is encrypted)
- Ensure at least one account exists and is not closed

### Home Assistant: File not pre-selected
- Ensure `actual_budget_file_id` in add-on config matches the exact file name in Actual Budget
- File names are case-sensitive

### iOS Widget: "No se puede conectar al servidor"
- Ensure the REST API is running (`./start_rest_api.sh`)
- Verify your iPhone is on the same WiFi network as your Mac
- Use your Mac's local IP address (not localhost)
- Check firewall settings on your Mac

## License

[Your License Here]

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## Credits

- Built with [actualpy](https://github.com/bvanelli/actualpy)
- Web UI powered by [PyWebIO](https://github.com/pywebio/PyWebIO)
- Browser automation via [Playwright](https://playwright.dev/)
