# Despliegue de Actual Budget PWA

Guia completa para desplegar la PWA de Actual Budget con barras de progreso estilo YNAB.

## Prerrequisitos

- Docker o Podman instalado
- Servidor Actual Budget funcionando
- iPhone con iOS 17+ en la misma red local

## Paso 1: Generar Iconos (Opcional)

La PWA necesita iconos PNG. Puedes generarlos desde el SVG incluido:

### Opcion A: Con ImageMagick

```bash
cd pwa
convert icon.svg -resize 192x192 icon-192.png
convert icon.svg -resize 512x512 icon-512.png
```

### Opcion B: Online

1. Abre `pwa/icon.svg` en un navegador
2. Haz captura de pantalla
3. Recorta y redimensiona a 192x192 y 512x512

### Opcion C: Sin iconos

La PWA funcionara sin iconos, pero mostrara un icono generico.

## Paso 2: Construir la Imagen Docker

```bash
cd /Users/juancar/Development/banking/ibercaja

# Con Docker
docker build -f Dockerfile.widget-api -t actual-budget-pwa .

# Con Podman
podman build -f Dockerfile.widget-api -t actual-budget-pwa .
```

## Paso 3: Ejecutar el Servidor

```bash
# Con Docker
docker run -d \
  --name actual-budget-pwa \
  -p 8080:8080 \
  --restart unless-stopped \
  actual-budget-pwa

# Con Podman
podman run -d \
  --name actual-budget-pwa \
  -p 8080:8080 \
  --restart unless-stopped \
  actual-budget-pwa
```

### Verificar que funciona

```bash
curl http://localhost:8080/
# Deberia devolver: {"status":"ok","service":"Actual Budget Widget API","version":"2.0.0"}
```

## Paso 4: Obtener la IP del Servidor

```bash
# En macOS
ipconfig getifaddr en0

# En Linux
hostname -I | awk '{print $1}'
```

Anota la IP (ejemplo: `192.168.1.100`)

## Paso 5: Instalar la PWA en iPhone

1. **Abre Safari** en tu iPhone
2. **Navega a**: `http://192.168.1.100:8080/app`
   (usa tu IP real)
3. **Configura la conexion**:
   - Toca el icono de engranaje
   - URL del Servidor API: `http://192.168.1.100:8080`
   - URL de Actual Budget: `https://actual.tudominio.com`
   - Contrasena: (tu contrasena de Actual Budget)
   - Nombre del Archivo: (nombre de tu presupuesto)
   - Clave de Cifrado: (solo si esta cifrado)
4. **Prueba la conexion**:
   - Toca "Probar Conexion"
   - Deberia mostrar "Conexion exitosa!"
5. **Guarda la configuracion**:
   - Toca "Guardar"
6. **Instala como app**:
   - Toca el boton de compartir (cuadrado con flecha)
   - Selecciona "Anadir a pantalla de inicio"
   - Pon un nombre (ej: "Budget")
   - Toca "Anadir"

## Uso de la PWA

### Navegacion

- **Swipe izquierda**: Mes siguiente
- **Swipe derecha**: Mes anterior
- **Botones < >**: Cambiar mes

### Visualizacion

- **Verde**: Categoria dentro del presupuesto
- **Amarillo**: Categoria al 90%+ del presupuesto
- **Rojo**: Categoria sobrepasada

### Offline

La PWA funciona offline mostrando los ultimos datos cacheados.

## Docker Compose (Alternativa)

Si prefieres Docker Compose, crea `docker-compose.pwa.yml`:

```yaml
version: '3.8'

services:
  actual-budget-pwa:
    build:
      context: .
      dockerfile: Dockerfile.widget-api
    container_name: actual-budget-pwa
    ports:
      - "8080:8080"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

```bash
docker-compose -f docker-compose.pwa.yml up -d
```

## Solucion de Problemas

### Error: "Failed to connect"

1. Verifica que Actual Budget este corriendo
2. Verifica la URL de Actual Budget (debe ser accesible desde el servidor Docker)
3. Si usas SSL con certificado autofirmado, el servidor lo permite

### Error: "Network error"

1. Verifica que el contenedor Docker este corriendo:
   ```bash
   docker ps | grep actual-budget-pwa
   ```
2. Verifica que el puerto 8080 este accesible
3. Asegurate de que el iPhone este en la misma red

### La PWA no se actualiza

1. Cierra completamente la app (swipe up)
2. Reabrela
3. Si persiste, elimina y reinstala la PWA

### Los datos no son correctos

1. Verifica el mes seleccionado
2. Verifica que las categorias tengan presupuesto asignado en Actual Budget
3. Las categorias sin presupuesto ni gastos no aparecen

## Detener el Servidor

```bash
# Con Docker
docker stop actual-budget-pwa
docker rm actual-budget-pwa

# Con Podman
podman stop actual-budget-pwa
podman rm actual-budget-pwa
```

## Siguiente Paso: Widget Nativo iOS

Si la PWA funciona bien y quieres un widget nativo de iOS:

1. La PWA demuestra que la arquitectura funciona
2. Podemos crear un widget nativo usando el mismo servidor REST API
3. Requerira Xcode y que sigas una guia de instalacion

Confirma cuando estes listo para el widget nativo.
