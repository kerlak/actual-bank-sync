import re
from playwright.sync_api import Playwright, sync_playwright, expect
import getpass
import os
import pandas as pd

def run(playwright: Playwright) -> None:
    print("[APP] Iniciando aplicación...")
    browser = playwright.chromium.launch(headless=False)
    print("[APP] Navegador abierto")
    context = browser.new_context()
    page = context.new_page()
    print("[APP] Navegando a https://www.ibercaja.es/")
    page.goto("https://www.ibercaja.es/")
    print("[APP] Página cargada")
    print("[APP] Buscando enlace 'Acceso clientes'...")
    page.get_by_role("link", name="Acceso clientes").click()
    print("[APP] Enlace clickeado")
    print("[APP] Buscando campo 'Código de identificación'...")
    page.get_by_role("textbox", name="Código de identificación").click()
    codigo = getpass.getpass("\nCódigo de identificación: ").strip()
    print("[APP] Código de identificación recibido, rellenando formulario...")
    page.get_by_role("textbox", name="Código de identificación").fill(codigo)
    print("[APP] Campo rellenado")
    print("[APP] Buscando campo 'Clave de acceso'...")
    page.get_by_role("textbox", name="Clave de acceso").click()
    clave = getpass.getpass("\nClave de acceso: ").strip()
    print("[APP] Clave de acceso recibida, rellenando formulario...")
    page.get_by_role("textbox", name="Clave de acceso").fill(clave)
    print("[APP] Campo rellenado")
    print("[APP] Clickeando botón 'entrar'...")
    page.get_by_role("button", name=" entrar").click()
    print("[APP] Esperando a que cargue la página...")
    page.locator(".ui-table__row").click()
    print("[APP] Fila de tabla clickeada")
    print("[APP] Buscando botón de descarga...")
    page.get_by_role("button", name="").click()
    print("[APP] Botón clickeado, esperando descarga...")
    with page.expect_download() as download_info:
        page.get_by_role("listitem").filter(has_text="Excel").click()
    download = download_info.value
    downloads_folder = "./downloads"
    # Crear carpeta si no existe
    if not os.path.exists(downloads_folder):
      os.makedirs(downloads_folder)
      print(f"[APP] Carpeta creada: {downloads_folder}")
      
    file_path = os.path.join(downloads_folder, "ibercaja_movements.xlsx")
    download.save_as(file_path)
    print(f"[APP] ✓ Archivo descargado en: {file_path}")

    # Leer la séptima fila como cabecera y omitir las primeras 6 filas
    print("[APP] Procesando Excel a CSV...")
    csv_path = os.path.join(downloads_folder, "ibercaja_movements.csv")
    df = pd.read_excel(file_path, header=5, engine='openpyxl')
    print(f"[APP] Datos cargados: {len(df)} filas")
    df.to_csv(csv_path, index=False)
    print(f"[APP] ✓ Archivo CSV guardado en: {csv_path}")
    
    # ---------------------
    print("[APP] Cerrando navegador...")
    context.close()
    browser.close()
    print("[APP] ✓ Aplicación finalizada correctamente")

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)

