# Actual Budget REST API - Home Assistant Add-on

REST API para Actual Budget que permite integración con aplicaciones de terceros, widgets de iOS y otras herramientas.

![Supports aarch64 Architecture][aarch64-shield]
![Supports amd64 Architecture][amd64-shield]
![Supports armv7 Architecture][armv7-shield]

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg

## Acerca de

Este add-on proporciona una REST API para Actual Budget que permite:

- 📱 **Widget de iOS**: Visualiza tu presupuesto directamente en tu iPhone
- 🔌 **Integraciones personalizadas**: Conecta Actual Budget con otras aplicaciones
- 📊 **Dashboard personalizados**: Crea visualizaciones custom de tus datos financieros
- 🤖 **Automatizaciones**: Accede a datos de presupuesto desde scripts y automatizaciones

## Endpoints disponibles

### `POST /api/validate`
Valida la conexión con el servidor de Actual Budget y obtiene la lista de archivos disponibles.

**Request:**
```json
{
  "server_url": "http://actual.local:5006",
  "server_password": "tu_contraseña",
  "file_name": "",
  "encryption_password": null
}
```

**Response:**
```json
{
  "success": true,
  "files": [
    {"name": "Mi Presupuesto", "file_id": "abc123"}
  ]
}
```

### `POST /api/accounts`
Obtiene la lista de cuentas con sus saldos.

**Request:**
```json
{
  "server_url": "http://actual.local:5006",
  "server_password": "tu_contraseña",
  "file_name": "Mi Presupuesto",
  "encryption_password": "clave_opcional"
}
```

**Response:**
```json
{
  "accounts": [
    {
      "id": "acc-1",
      "name": "Cuenta Corriente",
      "balance": 1234.56,
      "off_budget": false,
      "closed": false
    }
  ],
  "total_balance": 1234.56,
  "count": 1
}
```

### `POST /api/budget`
Obtiene el presupuesto de un mes específico con categorías y gastos.

**Query Parameters:**
- `month` (opcional): Mes en formato YYYY-MM (ej: 2026-01). Por defecto: mes actual.

**Request:**
```json
{
  "server_url": "http://actual.local:5006",
  "server_password": "tu_contraseña",
  "file_name": "Mi Presupuesto",
  "encryption_password": "clave_opcional"
}
```

**Response:**
```json
{
  "month": "2026-01",
  "groups": [
    {
      "id": "group-1",
      "name": "Gastos Fijos",
      "is_income": false,
      "budgeted": 1500.0,
      "spent": -1234.56,
      "available": 265.44,
      "categories": [...]
    }
  ],
  "total_budgeted": 2000.0,
  "total_spent": -1800.0,
  "total_available": 200.0
}
```

### `POST /api/transactions`
Obtiene las transacciones de una categoría específica.

**Query Parameters:**
- `category_id` (requerido): ID de la categoría
- `month` (opcional): Mes en formato YYYY-MM
- `limit` (opcional): Número máximo de transacciones (default: 20)

**Request:**
```json
{
  "server_url": "http://actual.local:5006",
  "server_password": "tu_contraseña",
  "file_name": "Mi Presupuesto",
  "encryption_password": "clave_opcional"
}
```

**Response:**
```json
{
  "category_id": "cat-123",
  "category_name": "Supermercado",
  "month": "2026-01",
  "transactions": [
    {
      "id": "trans-1",
      "date": "2026-01-15",
      "payee": "Mercadona",
      "notes": "Compra semanal",
      "amount": -45.67,
      "account": "Cuenta Corriente"
    }
  ],
  "count": 1
}
```

## Instalación

1. **Añade este repositorio** a Home Assistant:
   - Settings → Add-ons → Add-on Store → ⋮ → Repositories
   - Añade: `https://github.com/kerlak/actual-bank-sync`

2. **Instala** "Actual Budget REST API"

3. **Configura** el add-on:
   - `api_port`: Puerto en el que escuchará la API (default: 8080)
   - `log_level`: Nivel de log (debug, info, warning, error)

4. **Inicia** el add-on

5. **Accede** a la API en `http://homeassistant.local:8080`

## Configuración

### Opciones

| Opción | Descripción | Default |
|--------|-------------|---------|
| `api_port` | Puerto de la API | `8080` |
| `log_level` | Nivel de logging | `info` |

### Ejemplo de configuración

```yaml
api_port: 8080
log_level: info
```

## Uso con Widget de iOS

Este add-on está diseñado para funcionar con la app de iOS de Actual Budget. Consulta la documentación del widget para más detalles:

- **[iOS App README](../ios-app/README.md)**: Documentación completa de la app iOS
- **[Tutorial TabView](../ios-app/TUTORIAL_TABVIEW.md)**: Guía de desarrollo

## Seguridad

⚠️ **IMPORTANTE**: Esta API **NO** implementa autenticación propia. Confía en:

1. **Seguridad de red**: Úsala solo en redes privadas/locales
2. **Autenticación de Actual Budget**: Todas las peticiones requieren la contraseña de Actual Budget
3. **HTTPS recomendado**: Si expones la API públicamente, usa un reverse proxy con HTTPS

**Recomendaciones:**
- No expongas este puerto a internet directamente
- Usa VPN o Tailscale para acceso remoto
- Considera usar un reverse proxy con autenticación (Nginx, Traefik, etc.)

## Solución de problemas

### Error: "Cannot connect to Actual Budget server"

**Causa:** El add-on no puede conectarse al servidor de Actual Budget.

**Solución:**
1. Verifica que Actual Budget esté ejecutándose
2. Verifica que la URL sea accesible desde el add-on
3. Prueba con `http://` en lugar de `https://` si usas certificados autofirmados

### Error: "Invalid credentials"

**Causa:** La contraseña de Actual Budget es incorrecta.

**Solución:**
1. Verifica la contraseña en tu cliente de Actual Budget
2. Asegúrate de no tener espacios al inicio/final de la contraseña

### Error: "File not found"

**Causa:** El nombre del archivo de presupuesto no existe.

**Solución:**
1. Usa el endpoint `/api/validate` para obtener la lista de archivos disponibles
2. Verifica que el nombre sea exactamente igual (case-sensitive)

### El widget de iOS no se conecta

**Causa:** Problemas de red o configuración incorrecta.

**Solución:**
1. Verifica que el iPhone esté en la misma red que Home Assistant
2. Usa la IP local de Home Assistant (ej: `http://192.168.1.100:8080`)
3. Verifica que el puerto no esté bloqueado por firewall
4. Comprueba los logs del add-on para ver errores

## Soporte

¿Problemas? Abre un issue en [GitHub](https://github.com/kerlak/actual-bank-sync/issues).

## Changelog

### v1.0.0 (2026-02-01)
- Lanzamiento inicial
- Soporte para endpoints: validate, accounts, budget, transactions
- Configuración de puerto
- Soporte multi-arquitectura (amd64, aarch64, armv7)

## Licencia

MIT License - Ver [LICENSE](../LICENSE) para más detalles.

## Créditos

- Construido con [actualpy](https://github.com/bvanelli/actualpy)
- API con [FastAPI](https://fastapi.tiangolo.com/)
- Desarrollado por [kerlak](https://github.com/kerlak)
