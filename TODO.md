# TODO - Banking Hub

Roadmap de mejoras planificadas para el proyecto.

## Prioridad Alta (Seguridad)

### 1. Rehabilitar verificación SSL
- **Ubicación**: `actual_sync.py:123, 138, 254, 282`
- **Problema**: `cert=False` deshabilita verificación SSL en todas las conexiones
- **Riesgo**: Vulnerable a ataques Man-in-the-Middle en redes no confiables
- **Solución**: Añadir soporte para especificar certificado auto-firmado válido
```python
# Ejemplo de implementación
cert_path = os.environ.get('ACTUAL_CERT_PATH', None)
cert = cert_path if cert_path and os.path.exists(cert_path) else False
```

### 2. Validar archivos subidos
- **Ubicación**: `webui.py:760, 827`
- **Problema**: Sin validación de MIME type, tamaño ni estructura
- **Solución**:
  - Validar MIME type (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)
  - Limitar tamaño máximo (~10MB)
  - Validar estructura antes de procesar

## Prioridad Media (Mantenimiento)

### 3. Refactorizar conversión Excel
- **Ubicación**: `banks/ibercaja.py:132`, `banks/ing.py:88`
- **Problema**: Código duplicado para conversión Excel->CSV
- **Solución**: Extraer a módulo común `utils/excel.py`

### 4. Actualizar dependencias
- **Ubicación**: `requirements.txt`, `Dockerfile`
- **Problemas**:
  - `xlrd>=2.0.1` no soporta archivos .xls (solo .xlsx)
  - Versiones muy permisivas pueden causar incompatibilidades
  - Divergencia entre `requirements.txt` y `Dockerfile`
- **Solución**: Fijar versiones exactas y sincronizar

### 5. Validar keys en generación de transaction ID
- **Ubicación**: `actual_sync.py:37-41`
- **Nota**: El `Saldo` ES necesario en el hash para distinguir transacciones idénticas el mismo día (ej: dos compras de -4.90€ en la misma gasolinera)
- **Problema pendiente**: Sin validación de existencia de keys antes de acceder
- **Solución**: Añadir validación con valores por defecto para keys opcionales

## Prioridad Baja (Mejoras)

### 6. Tests unitarios
- Parseo de CSV/Excel
- Generación de IDs de transacción
- Lógica de sincronización
- Mocks para conexión a Actual Budget

### 7. Documentación
- Diagrama de flujo de datos
- Guía de contribución
- Documentar estructura de Excel por banco

### 8. Funcionalidades futuras
- [ ] Soporte para más bancos españoles (Santander, BBVA, CaixaBank)
- [ ] Sincronización programada (cron/scheduler)
- [ ] Notificaciones tras sync (Telegram, email)
- [ ] Modo headless para ejecución automática sin UI
- [ ] API REST para integración con otros sistemas

## Notas técnicas

### Estructura de Excel por banco

**Ibercaja**:
- Header row: Variable (auto-detectado)
- Columnas: `Nº Orden`, `Fecha Oper`, `Fecha Valor`, `Concepto`, `Descripción`, `Referencia`, `Importe`, `Saldo`

**ING**:
- Header row: 4 (índice 3)
- Columnas originales: `F. VALOR`, `CATEGORÍA`, `DESCRIPCIÓN`, `COMENTARIO`, `IMPORTE (€)`, `SALDO (€)`
- Se mapean a formato Ibercaja para compatibilidad

### Consideraciones de seguridad
- Las credenciales NUNCA se persisten a disco
- El PIN de ING solo se solicita parcialmente (3 dígitos)
- Sesión en memoria se limpia al reiniciar
