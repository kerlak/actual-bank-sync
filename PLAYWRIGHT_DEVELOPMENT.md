# Playwright Development Guide

Scripts para desarrollar y probar scrapers de Playwright en el mismo entorno que producción.

## Requisitos previos

### macOS
```bash
# Instalar XQuartz (necesario para mostrar el navegador)
brew install --cask xquartz

# Abrir XQuartz
open -a XQuartz

# En XQuartz > Preferences > Security:
# ✓ Marcar "Allow connections from network clients"

# Permitir conexiones desde localhost
xhost +localhost
```

### Linux
```bash
# Permitir conexiones X11 desde root
xhost +local:root
```

## Scripts disponibles

### 1. Codegen - Grabar nueva integración

```bash
./playwright-codegen.sh
```

Esto:
- Construye la imagen del contenedor
- Configura X11/XQuartz
- Abre el navegador de Playwright
- Graba tus acciones y genera código

**Uso:**
1. El navegador se abrirá en https://www.ibercaja.es/
2. Interactúa con la web (login, navegación, clicks, etc.)
3. Playwright genera el código automáticamente
4. Copia el código generado a `banks/ibercaja.py`
5. Presiona Ctrl+C cuando termines

### 2. Shell interactivo

```bash
./playwright-shell.sh
```

Lanza un shell interactivo dentro del contenedor.

**Comandos útiles:**
```bash
# Codegen desde shell
playwright codegen https://www.ibercaja.es/

# Probar el scraper actual
python -c "from banks import ibercaja; from playwright.sync_api import sync_playwright; sync_playwright().start()"

# Instalar navegadores (si es necesario)
playwright install chromium

# Debug de un script
python -m playwright codegen --save-trace=trace.zip https://www.ibercaja.es/
```

## Tips de desarrollo

### Selectores robustos

Preferir en orden:
1. **Roles ARIA**: `page.get_by_role("button", name="Entrar")`
2. **Texto visible**: `page.get_by_text("Acceso clientes")`
3. **Labels**: `page.get_by_label("Usuario")`
4. **Placeholders**: `page.get_by_placeholder("DNI")`
5. **Data attributes**: `page.locator('[data-testid="login"]')`
6. **CSS clases**: `page.locator('.ui-table__row')` (último recurso)

### Ejemplo: Reescribir selector CSS a role-based

❌ **Malo (frágil):**
```python
page.locator(".login-button").click()
```

✅ **Bueno (robusto):**
```python
page.get_by_role("button", name="Entrar").click()
```

### Debug cuando falla

```python
# Añadir screenshots
page.screenshot(path='debug.png')

# Ver qué hay en la página
print(f"URL: {page.url}")
print(f"Title: {page.title()}")

# Listar todos los botones
buttons = page.get_by_role("button").all()
for btn in buttons:
    print(f"Button: {btn.text_content()}")
```

### Probar con headless=False

En `banks/ibercaja.py`, temporalmente:
```python
browser = playwright.chromium.launch(headless=False)  # Ver el navegador
```

## Estructura del scraper

```python
def login(page, codigo, clave):
    """Realizar login"""
    page.goto("https://www.ibercaja.es/")
    page.get_by_role("link", name="Acceso clientes").click()
    page.get_by_role("textbox", name="Código de identificación").fill(codigo)
    page.get_by_role("textbox", name="Clave de acceso").fill(clave)
    page.get_by_role("button", name="entrar").click()
    page.wait_for_load_state("networkidle")

def download_movements(page):
    """Navegar y descargar movimientos"""
    # Esperar tabla de cuentas
    table_row = page.locator(".ui-table__row").first
    table_row.wait_for(state="visible", timeout=60000)
    table_row.click()

    # Descargar Excel
    page.get_by_role("button", name="descargar").click()
    with page.expect_download() as download_info:
        page.get_by_text("Excel").click()

    return download_info.value
```

## Troubleshooting

### El navegador no se abre

**macOS:**
```bash
# Verificar XQuartz
pgrep XQuartz

# Reiniciar XQuartz
killall XQuartz
open -a XQuartz
xhost +localhost
```

**Linux:**
```bash
# Verificar DISPLAY
echo $DISPLAY

# Permitir root
xhost +local:root
```

### Error "playwright: command not found"

```bash
# Dentro del contenedor
playwright install chromium
```

### Timeout al buscar elementos

1. Aumentar timeout: `wait_for(timeout=120000)`
2. Añadir `page.wait_for_load_state("networkidle")`
3. Verificar que no hay modals/popups bloqueando
4. Usar selectores más específicos

## Recursos

- [Playwright Python Docs](https://playwright.dev/python/)
- [Codegen Guide](https://playwright.dev/python/docs/codegen)
- [Locators Best Practices](https://playwright.dev/python/docs/locators)
- [Debugging Guide](https://playwright.dev/python/docs/debug)
