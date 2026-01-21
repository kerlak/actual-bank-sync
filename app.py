import re
from playwright.sync_api import Playwright, sync_playwright, expect
import getpass
import os
import pandas as pd

def run(playwright: Playwright) -> None:
    print("[APP] Starting application...")
    browser = playwright.chromium.launch(headless=False)
    print("[APP] Browser launched")
    context = browser.new_context()
    page = context.new_page()
    print("[APP] Navigating to https://www.ibercaja.es/")
    page.goto("https://www.ibercaja.es/")
    print("[APP] Page loaded")
    print("[APP] Looking for 'Client Access' link...")
    page.get_by_role("link", name="Acceso clientes").click()
    print("[APP] Link clicked")
    print("[APP] Looking for 'Identification Code' field...")
    page.get_by_role("textbox", name="Código de identificación").click()
    codigo = getpass.getpass("\nIdentification Code: ").strip()
    print("[APP] Identification code received, filling form...")
    page.get_by_role("textbox", name="Código de identificación").fill(codigo)
    print("[APP] Field filled")
    print("[APP] Looking for 'Access Key' field...")
    page.get_by_role("textbox", name="Clave de acceso").click()
    clave = getpass.getpass("\nAccess Key: ").strip()
    print("[APP] Access key received, filling form...")
    page.get_by_role("textbox", name="Clave de acceso").fill(clave)
    print("[APP] Field filled")
    print("[APP] Clicking 'Enter' button...")
    page.get_by_role("button", name=" entrar").click()
    print("[APP] Waiting for page to load...")
    page.wait_for_load_state("networkidle")
    print("[APP] Waiting for modal overlay to disappear...")
    
    # Esperar a que el overlay sea invisible o removerlo con JavaScript
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            # Intentar remover todos los overlays y modales con JavaScript
            page.evaluate("""
                const overlays = document.querySelectorAll('.overlay, ui-modal');
                overlays.forEach(el => {
                    if (el.style) el.style.display = 'none';
                    el.style.pointerEvents = 'none';
                });
            """)
            
            overlay = page.locator(".overlay")
            if not overlay.is_visible(timeout=500):
                print(f"[APP] Overlay is hidden (attempt {attempt + 1})")
                break
            else:
                print(f"[APP] Overlay still visible, removing via JavaScript (attempt {attempt + 1})...")
                page.evaluate("document.querySelector('ui-modal')?.remove()")
                page.wait_for_timeout(300)
        except Exception as e:
            print(f"[APP] Overlay handling done (attempt {attempt + 1}): {str(e)[:50]}")
            break
    
    print("[APP] Attempting to click table row...")
    page.locator(".ui-table__row").click()
    print("[APP] Table row clicked")
    print("[APP] Looking for download button...")
    page.get_by_role("button", name="\ue911").click()
    print("[APP] Download button clicked, waiting for download...")
    with page.expect_download() as download_info:
        page.get_by_role("listitem").filter(has_text="Excel").click()
    download = download_info.value
    downloads_folder = "./downloads"
    print("[APP] Creating downloads folder if it doesn't exist...")
    if not os.path.exists(downloads_folder):
      os.makedirs(downloads_folder)
      print(f"[APP] Folder created: {downloads_folder}")
      
    file_path = os.path.join(downloads_folder, "ibercaja_movements.xlsx")
    download.save_as(file_path)
    print(f"[APP] ✓ File downloaded to: {file_path}")

    print("[APP] Processing Excel to CSV (reading 7th row as header, skipping first 6 rows)...")
    csv_path = os.path.join(downloads_folder, "ibercaja_movements.csv")
    df = pd.read_excel(file_path, header=5, engine='openpyxl')
    print(f"[APP] Data loaded: {len(df)} rows")
    df.to_csv(csv_path, index=False)
    print(f"[APP] ✓ CSV file saved to: {csv_path}")
    
    print("[APP] Closing browser...")
    context.close()
    browser.close()
    print("[APP] ✓ Application completed successfully")

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)

