# Changelog

Todos los cambios notables de este proyecto se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-02-01

### Corregido
- Dependencias en Dockerfile: removidas versiones específicas que no existen
- Ahora instala últimas versiones compatibles de fastapi, uvicorn, actualpy, pydantic
- Corregido error de build en Home Assistant

## [1.0.0] - 2026-02-01

### Añadido
- Lanzamiento inicial del add-on de Home Assistant
- Endpoint `/api/validate` para validar conexión y obtener archivos
- Endpoint `/api/accounts` para listar cuentas con saldos
- Endpoint `/api/budget` para obtener presupuesto mensual por categorías
- Endpoint `/api/transactions` para obtener transacciones por categoría
- Configuración de puerto personalizable (default: 8080)
- Niveles de log configurables (debug, info, warning, error)
- Soporte multi-arquitectura: amd64, aarch64, armv7
- Health check automático
- Documentación completa de API
- README con ejemplos de uso
- Integración con widget de iOS

### Seguridad
- Validación de credenciales de Actual Budget en cada petición
- Sin almacenamiento de contraseñas (solo en memoria durante la petición)
- Recomendaciones de seguridad documentadas

[1.0.0]: https://github.com/kerlak/actual-bank-sync/releases/tag/api-v1.0.0
