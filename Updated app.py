import re
from playwright.sync_api import Playwright, sync_playwright, expect
import getpass
import os
import pandas as pd

def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.ibercaja.es/")
    page.get_by_role("link", name="Acceso clientes").click()
    page.get_by_role("textbox", name="Código de identificación").click()
    codigo = getpass.getpass("\nCódigo de identificación: ").strip()
    page.get_by_role("textbox", name="Código de identificación").fill(codigo)
    page.get_by_role("textbox", name="Clave de acceso").click()
    clave = getpass.getpass("\nClave de acceso: ").strip()
    page.get_by_role("textbox", name="Clave de acceso").fill(clave)
    page.get_by_role("button", name=" entrar").click()
    page.locator(".ui-table__row").click()
    page.get_by_role("button", name="").click()
    with page.expect_download() as download_info:
        page.get_by_role("listitem").filter(has_text="Excel").click()
    download = download_info.value
    downloads_folder = download_directory
    # Crear carpeta si no existe
    if not os.path.exists(downloads_folder):
      os.makedirs(downloads_folder)
      
    file_path = os.path.join(downloads_folder, "ibercaja_movements.xlsx")
    download.save_as(file_path)
    print(f"Archivo descargado en: {file_path}")

    # Leer la séptima fila como cabecera y omitir las primeras 6 filas
    csv_path = os.path.join(downloads_folder, "ibercaja_movements.csv")
    df = pd.read_excel(file_path, header=5, engine='openpyxl')
    df.to_csv(csv_path, index=False)
    print(f"Archivo CSV guardado en: {csv_path}")
    
    # ---------------------
    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)

