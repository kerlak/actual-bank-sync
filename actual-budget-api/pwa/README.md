# Actual Budget PWA

Progressive Web App para visualizar tu presupuesto de Actual Budget con barras de progreso estilo YNAB.

## Características

- Visualizacion de presupuesto por categorias con barras de progreso
- Navegacion entre meses con swipe gestures
- Modo offline con Service Worker
- Instalable como app en iOS (Add to Home Screen)
- Datos cacheados localmente

## Arquitectura

```
iPhone/Navegador  -->  REST API (Python)  -->  Actual Budget Server
    [PWA]               [FastAPI]              [SQLite + Sync]
```

## Requisitos

1. **Servidor Actual Budget** funcionando
2. **Servidor REST API** (incluido en este proyecto)
3. **Navegador moderno** (Safari iOS 17+, Chrome, Firefox)

## Despliegue Rapido con Docker

### 1. Generar iconos PNG (opcional)

Los iconos deben ser PNG de 192x192 y 512x512 pixeles. Puedes generarlos desde el SVG incluido:

```bash
# Con ImageMagick
convert pwa/icon.svg -resize 192x192 pwa/icon-192.png
convert pwa/icon.svg -resize 512x512 pwa/icon-512.png

# O usa cualquier editor de imagenes para exportar icon.svg a PNG
```

Si no tienes los iconos, la PWA funcionara pero no mostrara icono personalizado.

### 2. Construir y ejecutar con Docker

```bash
# Desde el directorio raiz del proyecto
docker build -f Dockerfile.widget-api -t actual-budget-pwa .

docker run -d \
  --name actual-budget-pwa \
  -p 8080:8080 \
  --restart unless-stopped \
  actual-budget-pwa
```

### 3. Acceder a la PWA

1. Abre Safari en tu iPhone
2. Navega a `http://<IP_DEL_SERVIDOR>:8080/app`
3. Toca el boton de compartir
4. Selecciona "Anadir a pantalla de inicio"
5. Ahora tienes la app instalada

## Configuracion en la PWA

Al abrir la app por primera vez:

1. Toca el boton de configuracion (engranaje)
2. Introduce:
   - **URL del Servidor API**: `http://<IP_DEL_SERVIDOR>:8080`
   - **URL de Actual Budget**: `https://actual.tudominio.com` (tu servidor Actual)
   - **Contrasena del Servidor**: Tu contrasena de Actual Budget
   - **Nombre del Archivo**: Nombre de tu archivo de presupuesto
   - **Clave de Cifrado**: Solo si el archivo esta cifrado
3. Toca "Probar Conexion" para verificar
4. Toca "Guardar"

## Desarrollo Local

### Sin Docker

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
python rest_api.py

# Acceder a http://localhost:8080/app
```

### Con Docker Compose

Crea un archivo `docker-compose.widget.yml`:

```yaml
version: '3.8'
services:
  actual-budget-pwa:
    build:
      context: .
      dockerfile: Dockerfile.widget-api
    ports:
      - "8080:8080"
    restart: unless-stopped
```

```bash
docker-compose -f docker-compose.widget.yml up -d
```

## Estructura de Archivos

```
pwa/
├── index.html      # HTML principal
├── styles.css      # Estilos (dark theme YNAB-style)
├── app.js          # Logica de la aplicacion
├── manifest.json   # Manifest para PWA
├── sw.js           # Service Worker
├── icon.svg        # Icono fuente (SVG)
├── icon-192.png    # Icono 192x192 (generar)
└── icon-512.png    # Icono 512x512 (generar)
```

## API Endpoints Utilizados

| Metodo | Endpoint | Descripcion |
|--------|----------|-------------|
| POST | `/api/validate` | Valida conexion y lista archivos |
| POST | `/api/budget?month=YYYY-MM` | Obtiene presupuesto del mes |
| POST | `/api/accounts` | Lista cuentas |

## Seguridad

- Las credenciales se guardan en localStorage del navegador
- Solo accesibles desde el mismo dispositivo
- Se recomienda usar HTTPS en produccion
- No exponer el servidor a Internet sin autenticacion adicional

## Solucion de Problemas

### "No se puede conectar al servidor"

1. Verifica que el servidor API este corriendo
2. Verifica que el iPhone este en la misma red
3. Usa la IP local, no `localhost`

### La PWA no se instala

1. Safari: Asegurate de acceder via HTTP (no file://)
2. Usa el boton "Compartir" > "Anadir a pantalla de inicio"

### Los iconos no aparecen

1. Genera los PNG desde el SVG incluido
2. Reinicia el navegador despues de instalar

### Datos no se actualizan

1. Fuerza el refresh (pull down en iOS)
2. Cierra y reabre la app
3. Verifica la conexion con el servidor

## Proximos Pasos

Una vez que la PWA funcione, podemos evolucionar a:
1. Widget nativo de iOS (requiere Xcode)
2. App nativa completa
3. Notificaciones de presupuesto
