# ✅ Add-on de Home Assistant Creado Exitosamente

El servidor REST API de Actual Budget ahora está disponible como **add-on de Home Assistant**.

---

## 📦 Lo que se ha creado

### Estructura del Add-on

```
actual-budget-api/
├── config.yaml           # Configuración del add-on (puerto, logs)
├── Dockerfile            # Contenedor multi-arquitectura
├── build.yaml            # Configuración de build (amd64, aarch64, armv7)
├── run.sh                # Script de inicio con bashio
├── rest_api.py           # API completa (copiada y funcionando)
│
├── 📖 Documentación:
│   ├── README.md         # Documentación completa (endpoints, config, troubleshooting)
│   ├── QUICKSTART.md     # Guía rápida de 5 minutos
│   ├── DEPLOY.md         # Guía de deployment y releases
│   └── CHANGELOG.md      # Historial de versiones
│
└── icon.png              # Icono placeholder (reemplazar con imagen 108x108px)
```

### Automatización

```
.github/workflows/
└── build-api-addon.yml   # GitHub Actions para builds automáticos
```

### Actualizaciones al Repositorio

- ✅ `repository.yaml` - Renombrado a "Actual Budget Add-ons"
- ✅ `README.md` - Documentación de ambos add-ons
- ✅ Commits realizados y guardados

---

## 🚀 Próximos Pasos

### 1. Push al Repositorio GitHub

```bash
# Estás en: /Users/juancar/Development/banking/ibercaja

# Ver cambios
git log --oneline -3

# Push a GitHub
git push origin main
```

### 2. Crear el Primer Release

#### Opción A: GitHub CLI (recomendado)

```bash
# Crear tag y release
gh release create api-v1.0.0 \
  --title "Actual Budget REST API v1.0.0" \
  --notes-file actual-budget-api/CHANGELOG.md
```

#### Opción B: GitHub Web

1. Ve a https://github.com/kerlak/actual-bank-sync/releases/new
2. **Tag:** `api-v1.0.0`
3. **Release title:** `Actual Budget REST API v1.0.0`
4. **Description:** Copia el contenido de `actual-budget-api/CHANGELOG.md`
5. Click **"Publish release"**

**¿Qué pasará automáticamente?**
- ✅ GitHub Actions construirá imágenes Docker para amd64, aarch64, armv7
- ✅ Se publicarán en GitHub Container Registry (GHCR)
- ✅ El add-on estará disponible para instalación en Home Assistant

### 3. Configurar GitHub Container Registry (GHCR)

Para que las imágenes Docker sean públicas:

1. Ve a https://github.com/kerlak?tab=packages
2. Busca `actual-budget-api-amd64`, `actual-budget-api-aarch64`, `actual-budget-api-armv7`
3. Click en cada uno → **Package settings** → **Change visibility** → **Public**

### 4. Instalar en Home Assistant

Una vez publicado el release:

1. Home Assistant → **Settings** → **Add-ons** → **Add-on Store**
2. **⋮** (menú) → **Repositories**
3. Añadir: `https://github.com/kerlak/actual-bank-sync`
4. Buscar **"Actual Budget REST API"**
5. **Install**

📖 **Guía paso a paso:** Ver `actual-budget-api/QUICKSTART.md`

---

## ⚙️ Configuración del Add-on

### Opciones Disponibles

| Opción | Descripción | Default | Valores |
|--------|-------------|---------|---------|
| `api_port` | Puerto de la API | `8080` | Cualquier puerto libre |
| `log_level` | Nivel de logging | `info` | `debug`, `info`, `warning`, `error` |

### Ejemplo de Configuración

```yaml
api_port: 8080
log_level: info
```

### Cambiar Puerto (evitar conflictos)

Si el puerto 8080 está en uso:

```yaml
api_port: 8081  # O cualquier puerto disponible
```

---

## 📡 Endpoints de la API

### Health Check
```bash
curl http://homeassistant.local:8080/
```

### Validar Conexión
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

### Obtener Cuentas
```bash
curl -X POST http://homeassistant.local:8080/api/accounts \
  -H "Content-Type: application/json" \
  -d '{
    "server_url": "http://actual.local:5006",
    "server_password": "tu_contraseña",
    "file_name": "Mi Presupuesto",
    "encryption_password": null
  }'
```

### Obtener Presupuesto
```bash
curl -X POST "http://homeassistant.local:8080/api/budget?month=2026-01" \
  -H "Content-Type: application/json" \
  -d '{
    "server_url": "http://actual.local:5006",
    "server_password": "tu_contraseña",
    "file_name": "Mi Presupuesto",
    "encryption_password": null
  }'
```

### Obtener Transacciones
```bash
curl -X POST "http://homeassistant.local:8080/api/transactions?category_id=abc123&month=2026-01" \
  -H "Content-Type: application/json" \
  -d '{
    "server_url": "http://actual.local:5006",
    "server_password": "tu_contraseña",
    "file_name": "Mi Presupuesto",
    "encryption_password": null
  }'
```

📖 **Documentación completa:** Ver `actual-budget-api/README.md`

---

## 📱 Integración con iOS

Una vez que el add-on esté corriendo, podrás usarlo con tu app de iOS:

1. Configurar la app con la URL del add-on:
   ```
   http://homeassistant.local:8080
   ```

2. Usar los endpoints para obtener datos

3. El add-on maneja todas las peticiones de forma segura

---

## 🔒 Seguridad

### Recomendaciones

- ✅ **Red privada:** Usa el add-on solo en tu red local
- ✅ **VPN/Tailscale:** Para acceso remoto seguro
- ✅ **No exponer públicamente:** No abras el puerto al internet directamente
- ✅ **HTTPS opcional:** Usa un reverse proxy si necesitas HTTPS

### Autenticación

El add-on **NO** implementa autenticación propia. Confía en:
- Seguridad de la red (firewall, VPN)
- Autenticación de Actual Budget (contraseña requerida en cada petición)

---

## 📋 Troubleshooting

### Add-on no aparece en la Store

**Solución:**
1. Verifica que hiciste push a GitHub
2. Verifica que `repository.yaml` esté en la raíz
3. Recarga repositorios en Home Assistant
4. Espera 1-2 minutos y recarga

### Error al instalar: "Image not found"

**Causa:** Las imágenes Docker no están publicadas

**Solución:**
1. Verifica que el release exista en GitHub
2. Verifica que GitHub Actions terminó correctamente
3. Haz los paquetes públicos en GHCR (ver paso 3 arriba)

### Add-on instalado pero no inicia

**Solución:**
1. Ver logs: Tab **Log** del add-on
2. Verificar configuración en tab **Configuration**
3. Verificar que el puerto no esté en uso
4. Reiniciar el add-on

### API responde 500/Error

**Solución:**
1. Verificar que Actual Budget esté accesible
2. Verificar contraseña de Actual Budget
3. Ver logs del add-on (nivel `debug`)
4. Verificar red: ¿Home Assistant puede acceder a Actual Budget?

---

## 📚 Documentación

- **Quick Start (5 min):** `actual-budget-api/QUICKSTART.md`
- **README Completo:** `actual-budget-api/README.md`
- **Deployment:** `actual-budget-api/DEPLOY.md`
- **Changelog:** `actual-budget-api/CHANGELOG.md`

---

## 🎯 Resumen de Configuración del Puerto

El puerto configurable (feature que pediste) está implementado en:

1. **`config.yaml`:**
   ```yaml
   options:
     api_port: 8080  # Default
   schema:
     api_port: port  # Valida que sea un puerto válido
   ```

2. **`run.sh`:**
   ```bash
   API_PORT=$(bashio::config 'api_port')
   uvicorn rest_api:app --port "${API_PORT}"
   ```

3. **Usuarios pueden cambiarlo:**
   - En la interfaz de Home Assistant: Tab **Configuration**
   - Sin conflictos con otros servicios
   - Reiniciar add-on para aplicar cambios

---

## ✨ Características Implementadas

- ✅ Add-on completo de Home Assistant
- ✅ Puerto configurable (evitar conflictos)
- ✅ Multi-arquitectura (amd64, aarch64, armv7)
- ✅ GitHub Actions para releases automáticos
- ✅ Documentación completa
- ✅ Logs configurables
- ✅ Health check automático
- ✅ Compatible con iOS widget
- ✅ Siguiendo filosofía de releases del repo actual

---

## 🚦 Estado Actual

| Componente | Estado |
|------------|--------|
| Add-on creado | ✅ Completo |
| Documentación | ✅ Completa |
| GitHub Actions | ✅ Configurado |
| Commits guardados | ✅ Realizados |
| **Pendiente** | 🔄 Push a GitHub + Release |

---

## 🎉 ¡Todo listo!

Solo falta:
1. **Push** a GitHub: `git push origin main`
2. **Crear release**: Tag `api-v1.0.0`
3. **Esperar build** (automático via GitHub Actions)
4. **Instalar** en Home Assistant

**¿Necesitas ayuda con algún paso?** Pregúntame lo que necesites. 😊
