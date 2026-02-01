# Quick Start - Actual Budget REST API Add-on

Guía rápida de 5 minutos para tener tu API funcionando.

## Requisitos Previos

- ✅ Home Assistant instalado y funcionando
- ✅ Actual Budget server corriendo
- ✅ Conocer tu contraseña de Actual Budget

## Paso 1: Añadir el Repositorio

1. Abre Home Assistant
2. Ve a **Settings** → **Add-ons** → **Add-on Store**
3. Click en el menú **⋮** (arriba derecha) → **Repositories**
4. Añade esta URL:
   ```
   https://github.com/kerlak/actual-bank-sync
   ```
5. Click **Add**

## Paso 2: Instalar el Add-on

1. Busca **"Actual Budget REST API"** en el Add-on Store
2. Click en el add-on
3. Click **Install**
4. Espera a que termine la instalación
   - Home Assistant descargará el código y construirá la imagen localmente
   - Esto puede tardar 5-10 minutos la primera vez

## Paso 3: Configurar el Add-on

En la pestaña **Configuration**:

```yaml
api_port: 8080      # Puerto de la API (cambia si hay conflicto)
log_level: info     # Nivel de logging (info, debug, warning, error)
```

**Configuración Avanzada:**

Si el puerto 8080 está en uso, cámbialo:
```yaml
api_port: 8081      # O cualquier puerto libre
```

## Paso 4: Iniciar el Add-on

1. Ve a la pestaña **Info**
2. Activa **"Start on boot"** si quieres que inicie automáticamente
3. Click **Start**
4. Espera a que el estado sea **"Running"** (verde)

## Paso 5: Verificar que Funciona

### Opción A: Desde el navegador

Abre en tu navegador:
```
http://homeassistant.local:8080
```

Deberías ver:
```json
{
  "status": "ok",
  "service": "Actual Budget Widget API",
  "version": "2.0.0"
}
```

### Opción B: Desde la línea de comandos

```bash
curl http://homeassistant.local:8080
```

## Paso 6: Probar con Actual Budget

Haz una petición de prueba para validar la conexión:

```bash
curl -X POST http://homeassistant.local:8080/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "server_url": "http://actual.local:5006",
    "server_password": "tu_contraseña",
    "file_name": "",
    "encryption_password": null
  }'
```

Deberías recibir la lista de archivos de presupuesto:
```json
{
  "success": true,
  "files": [
    {"name": "Mi Presupuesto", "file_id": "abc123"}
  ]
}
```

## Paso 7: Usar con el Widget de iOS

Ahora que la API está funcionando, configura el widget en tu iPhone:

1. En tu iPhone, abre **Shortcuts** (Atajos)
2. Crea un nuevo atajo con:
   - URL: `http://TU_IP_HOME_ASSISTANT:8080`
   - Contraseña: Tu contraseña de Actual Budget
   - Archivo: Nombre del archivo de presupuesto
   - Clave cifrado: (opcional)

📱 **Ver documentación completa del widget:** [iOS App README](../ios-app/README.md)

## Troubleshooting Rápido

### ❌ Error: "Cannot connect to add-on"

**Solución:**
1. Verifica que el add-on esté en estado "Running"
2. Revisa los logs: Tab **Log** del add-on
3. Reinicia el add-on: Tab **Info** → **Restart**

### ❌ Error: "Connection refused"

**Causa:** El puerto está en uso por otro servicio

**Solución:**
1. Cambia el puerto en Configuration (ej: 8081)
2. Reinicia el add-on
3. Usa el nuevo puerto en tus peticiones

### ❌ Error: "Cannot connect to Actual Budget"

**Solución:**
1. Verifica que Actual Budget esté corriendo
2. Prueba con `http://` en lugar de `https://`
3. Verifica la contraseña
4. Asegúrate de que Home Assistant puede acceder a Actual Budget (misma red)

### ❌ Los logs muestran errores

**Ver logs detallados:**
1. Tab **Log** del add-on
2. O cambiar `log_level: debug` en Configuration
3. Reiniciar el add-on

## Siguiente Paso

Ahora que la API funciona, puedes:

- 📱 **Configurar el widget de iOS** - Ver [iOS App README](../ios-app/README.md)
- 🔌 **Crear integraciones custom** - Ver [README.md](README.md) para docs de API
- 📊 **Conectar con dashboards** - Usa los endpoints para crear visualizaciones

## Ayuda

¿Problemas?
- 📖 Documentación completa: [README.md](README.md)
- 🐛 Reportar bug: [GitHub Issues](https://github.com/kerlak/actual-bank-sync/issues)
- 💬 Preguntas: [GitHub Discussions](https://github.com/kerlak/actual-bank-sync/discussions)

---

**¡Listo!** Tu API de Actual Budget está funcionando 🎉
