# Guía de Deployment - Actual Budget REST API Add-on

Esta guía explica cómo hacer deployment del add-on de Home Assistant para Actual Budget REST API.

## Estructura del Repositorio

Este repositorio contiene dos add-ons:

```
actual-bank-sync/
├── repository.yaml           # Configuración del repositorio
├── config.yaml              # Banking Hub add-on (raíz)
├── Dockerfile               # Banking Hub Dockerfile
├── run.sh                   # Banking Hub run script
├── ...                      # Resto de archivos Banking Hub
└── actual-budget-api/       # Nuevo add-on REST API
    ├── config.yaml
    ├── Dockerfile
    ├── run.sh
    ├── rest_api.py
    ├── build.yaml
    ├── README.md
    ├── CHANGELOG.md
    └── DEPLOY.md (este archivo)
```

## Proceso de Release

### 1. Preparar la versión

Actualiza la versión en estos archivos:

**`actual-budget-api/config.yaml`:**
```yaml
version: "1.0.0"  # ← Actualizar aquí
```

**`actual-budget-api/CHANGELOG.md`:**
```markdown
## [1.0.0] - 2026-02-01
### Añadido
- Nuevas características...
```

### 2. Commit y push

```bash
git add actual-budget-api/
git commit -m "chore(api): release v1.0.0"
git push origin main
```

### 3. Crear release en GitHub

#### Opción A: Usando GitHub CLI

```bash
gh release create api-v1.0.0 \
  --title "Actual Budget REST API v1.0.0" \
  --notes-file actual-budget-api/CHANGELOG.md
```

#### Opción B: Usando la interfaz web

1. Ve a https://github.com/kerlak/actual-bank-sync/releases/new
2. Tag: `api-v1.0.0`
3. Release title: `Actual Budget REST API v1.0.0`
4. Description: Copia el contenido del CHANGELOG
5. Click "Publish release"

### 4. Build automático (GitHub Actions)

El workflow de GitHub Actions se ejecutará automáticamente cuando crees el tag y:

1. Construirá imágenes Docker para todas las arquitecturas (amd64, aarch64, armv7)
2. Publicará las imágenes en GitHub Container Registry
3. Hará disponible el add-on para instalación en Home Assistant

## Build Manual (Desarrollo Local)

### Requisitos

- Docker instalado
- Home Assistant Builder: `docker pull homeassistant/amd64-builder`

### Build para una arquitectura

```bash
# Navegar al directorio del add-on
cd actual-budget-api

# Build para amd64
docker run --rm --privileged \
  -v ~/.docker:/root/.docker \
  -v "$(pwd)":/data \
  homeassistant/amd64-builder \
  --amd64 \
  --target actual-budget-api \
  --docker-hub ghcr.io/kerlak
```

### Build para todas las arquitecturas

```bash
# Desde el directorio raíz del repositorio
docker run --rm --privileged \
  -v ~/.docker:/root/.docker \
  -v "$(pwd)":/data \
  homeassistant/amd64-builder \
  --all \
  --target actual-budget-api \
  --docker-hub ghcr.io/kerlak
```

### Test local

```bash
# Build local
docker build -t actual-budget-api:test \
  --build-arg BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.11-alpine3.19 \
  actual-budget-api/

# Run local
docker run --rm -p 8080:8080 \
  -e API_PORT=8080 \
  -e LOG_LEVEL=info \
  actual-budget-api:test
```

## Instalación en Home Assistant

### Método 1: Desde el Add-on Store

1. Settings → Add-ons → Add-on Store → ⋮ → Repositories
2. Añadir: `https://github.com/kerlak/actual-bank-sync`
3. Buscar "Actual Budget REST API"
4. Click Install

### Método 2: Manual (para desarrollo)

```bash
# Copiar add-on al directorio de Home Assistant
cp -r actual-budget-api /usr/share/hassio/addons/local/

# Recargar add-ons
ha addons reload
```

## Configuración de GitHub Actions

### Secrets requeridos

En Settings → Secrets → Actions, configurar:

- `GITHUB_TOKEN`: Automático, no hace falta configurar
- `DOCKER_USERNAME`: Tu usuario de GitHub (para GHCR)
- `DOCKER_PASSWORD`: Personal Access Token con permisos `write:packages`

### Workflow file

El archivo `.github/workflows/build-addon.yml` debe contener:

```yaml
name: Build Add-on

on:
  push:
    tags:
      - 'api-v*'

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        arch: [amd64, aarch64, armv7]
    steps:
      - uses: actions/checkout@v3

      - name: Build add-on
        uses: home-assistant/builder@master
        with:
          args: |
            --${{ matrix.arch }} \
            --target actual-budget-api \
            --docker-hub ghcr.io/${{ github.repository_owner }}
```

## Versionado

Este add-on sigue [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.x.x): Cambios incompatibles en la API
- **MINOR** (x.1.x): Nuevas funcionalidades compatibles hacia atrás
- **PATCH** (x.x.1): Corrección de bugs

**Tags de Git:**
- Banking Hub: `v1.0.0`, `v1.1.0`, etc.
- REST API: `api-v1.0.0`, `api-v1.1.0`, etc.

## Troubleshooting

### Build falla con error de arquitectura

**Problema:** `exec format error` al ejecutar en arquitectura diferente

**Solución:**
```bash
# Instalar buildx
docker buildx create --use

# Build con buildx
docker buildx build --platform linux/amd64,linux/arm64,linux/arm/v7 \
  -t ghcr.io/kerlak/actual-budget-api:latest \
  --push \
  actual-budget-api/
```

### Home Assistant no detecta el add-on

**Problema:** El add-on no aparece en el Add-on Store

**Soluciones:**
1. Verificar que `repository.yaml` esté en la raíz
2. Verificar que `config.yaml` exista en `actual-budget-api/`
3. Recargar repositorio en Home Assistant
4. Ver logs: Settings → System → Logs

### Imagen Docker no se descarga

**Problema:** Error al instalar: "Image not found"

**Soluciones:**
1. Verificar que el tag en `config.yaml` sea correcto
2. Verificar que la imagen exista en GHCR
3. Hacer el repositorio de GHCR público (Settings → Packages)

## Recursos

- [Home Assistant Add-on Development](https://developers.home-assistant.io/docs/add-ons)
- [Add-on Configuration](https://developers.home-assistant.io/docs/add-ons/configuration)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

## Soporte

¿Problemas con el deployment? Abre un issue: https://github.com/kerlak/actual-bank-sync/issues
