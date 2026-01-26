"""Ibercaja bank movements downloader using Playwright browser automation."""

import getpass
import os
from typing import Optional

import pandas as pd
from playwright.sync_api import Playwright, Page, Browser, BrowserContext

# Constants
IBERCAJA_URL = "https://www.ibercaja.es/"
DOWNLOADS_FOLDER = "./downloads/ibercaja"
OUTPUT_EXCEL_FILENAME = "ibercaja_movements.xlsx"
OUTPUT_CSV_FILENAME = "ibercaja_movements.csv"
EXCEL_HEADER_ROW = 5
MAX_MODAL_REMOVAL_ATTEMPTS = 5
MODAL_CHECK_TIMEOUT_MS = 500
MODAL_WAIT_BETWEEN_ATTEMPTS_MS = 300


def get_credentials() -> tuple[str, str]:
    """Prompt user for bank credentials."""
    codigo = getpass.getpass("\nIdentification Code: ").strip()
    clave = getpass.getpass("\nAccess Key: ").strip()
    return codigo, clave


def login(page: Page, codigo: str, clave: str) -> None:
    """Perform login to Ibercaja website."""
    print("[IBERCAJA] Navigating to", IBERCAJA_URL)
    page.goto(IBERCAJA_URL)
    print("[IBERCAJA] Page loaded")

    print("[IBERCAJA] Looking for 'Client Access' link...")
    page.get_by_role("link", name="Acceso clientes").click()
    print("[IBERCAJA] Link clicked")

    print("[IBERCAJA] Filling identification code...")
    page.get_by_role("textbox", name="Código de identificación").click()
    page.get_by_role("textbox", name="Código de identificación").fill(codigo)
    print("[IBERCAJA] Identification code filled")

    print("[IBERCAJA] Filling access key...")
    page.get_by_role("textbox", name="Clave de acceso").click()
    page.get_by_role("textbox", name="Clave de acceso").fill(clave)
    print("[IBERCAJA] Access key filled")

    print("[IBERCAJA] Clicking 'Enter' button...")
    page.get_by_role("button", name=" entrar").click()
    print("[IBERCAJA] Waiting for page to load...")
    page.wait_for_load_state("networkidle")
    print("[IBERCAJA] Login completed")


def handle_blocking_elements(page: Page) -> None:
    """Remove cookies banner and modal overlays that may block interaction."""
    print("[IBERCAJA] Removing blocking elements (cookies, overlays)...")

    for attempt in range(MAX_MODAL_REMOVAL_ATTEMPTS):
        try:
            page.evaluate("""
                document.querySelector('.container-cookies')?.remove();
                document.querySelector('cookies')?.remove();
                document.querySelectorAll('.overlay, ui-modal').forEach(el => el.remove());
                document.querySelectorAll('[class*="overlay"]').forEach(el => {
                    if (el.style) {
                        el.style.display = 'none';
                        el.style.pointerEvents = 'none';
                    }
                });
            """)

            overlay = page.locator(".overlay")
            if not overlay.is_visible(timeout=MODAL_CHECK_TIMEOUT_MS):
                print(f"[IBERCAJA] Blocking elements cleared (attempt {attempt + 1})")
                break
            else:
                print(f"[IBERCAJA] Overlay still visible, retrying (attempt {attempt + 1})...")
                page.wait_for_timeout(MODAL_WAIT_BETWEEN_ATTEMPTS_MS)
        except Exception as e:
            print(f"[IBERCAJA] Blocking elements handled (attempt {attempt + 1}): {str(e)[:50]}")
            break


def download_movements(page: Page) -> str:
    """Navigate to movements and download Excel file."""
    print("[IBERCAJA] Waiting for table to load...")
    table_row = page.locator(".ui-table__row").first
    table_row.wait_for(state="visible", timeout=60000)
    print("[IBERCAJA] Table visible, clicking row to select account...")
    table_row.click()
    print("[IBERCAJA] Table row clicked")

    print("[IBERCAJA] Looking for download button...")
    page.get_by_role("button", name="\ue911").click()
    print("[IBERCAJA] Download button clicked, waiting for download...")

    with page.expect_download() as download_info:
        page.get_by_role("listitem").filter(has_text="Excel").click()

    download = download_info.value

    if not os.path.exists(DOWNLOADS_FOLDER):
        os.makedirs(DOWNLOADS_FOLDER)
        print(f"[IBERCAJA] Created downloads folder: {DOWNLOADS_FOLDER}")

    file_path = os.path.join(DOWNLOADS_FOLDER, OUTPUT_EXCEL_FILENAME)
    download.save_as(file_path)
    print(f"[IBERCAJA] File downloaded to: {file_path}")

    return file_path


def find_header_row(excel_path: str, expected_columns: list[str]) -> int:
    """Find the row containing the header by searching for expected column names."""
    # Read first 20 rows without header to search for the header row
    df_preview = pd.read_excel(excel_path, header=None, nrows=20, engine='openpyxl')

    for idx, row in df_preview.iterrows():
        row_values = [str(v).strip() for v in row.values if pd.notna(v)]
        # Check if any expected column is in this row
        matches = sum(1 for col in expected_columns if any(col.lower() in v.lower() for v in row_values))
        if matches >= 2:  # At least 2 matches indicates header row
            print(f"[IBERCAJA] Found header at row {idx + 1}")
            return idx

    # Fallback to default if not found
    print(f"[IBERCAJA] Header not auto-detected, using default row {EXCEL_HEADER_ROW + 1}")
    return EXCEL_HEADER_ROW


def convert_excel_to_csv(excel_path: str) -> str:
    """Convert downloaded Excel file to CSV format."""
    print(f"[IBERCAJA] Processing Excel to CSV...")
    csv_path = os.path.join(DOWNLOADS_FOLDER, OUTPUT_CSV_FILENAME)

    # Auto-detect header row
    expected_cols = ['Fecha', 'Concepto', 'Descripción', 'Importe', 'Saldo']
    header_row = find_header_row(excel_path, expected_cols)

    df = pd.read_excel(excel_path, header=header_row, engine='openpyxl')
    print(f"[IBERCAJA] Data loaded: {len(df)} rows, columns: {list(df.columns)}")

    # Validate required columns exist
    required = ['Fecha Oper', 'Concepto', 'Importe']
    missing = [col for col in required if col not in df.columns]
    if missing:
        # Try to map common column variations
        col_mapping = {}
        for col in df.columns:
            col_lower = str(col).lower()
            if 'fecha' in col_lower and 'oper' in col_lower:
                col_mapping[col] = 'Fecha Oper'
            elif 'fecha' in col_lower and 'valor' in col_lower:
                col_mapping[col] = 'Fecha Valor'
            elif col_lower == 'concepto':
                col_mapping[col] = 'Concepto'
            elif 'descrip' in col_lower:
                col_mapping[col] = 'Descripción'
            elif 'importe' in col_lower:
                col_mapping[col] = 'Importe'
            elif 'saldo' in col_lower:
                col_mapping[col] = 'Saldo'

        if col_mapping:
            df = df.rename(columns=col_mapping)
            print(f"[IBERCAJA] Renamed columns: {col_mapping}")

    df.to_csv(csv_path, index=False)
    print(f"[IBERCAJA] CSV file saved to: {csv_path}")

    return csv_path


def cleanup(context: Optional[BrowserContext], browser: Optional[Browser]) -> None:
    """Close browser context and browser instance."""
    print("[IBERCAJA] Closing browser...")
    if context:
        context.close()
    if browser:
        browser.close()
    print("[IBERCAJA] Browser closed")


def run(playwright: Playwright) -> None:
    """Main entry point for the Ibercaja movements downloader."""
    print("[IBERCAJA] Starting application...")

    browser = None
    context = None

    try:
        browser = playwright.chromium.launch(headless=False)
        print("[IBERCAJA] Browser launched")

        context = browser.new_context()
        page = context.new_page()

        print("[IBERCAJA] Requesting credentials...")
        codigo, clave = get_credentials()
        print("[IBERCAJA] Credentials received")

        login(page, codigo, clave)
        handle_blocking_elements(page)
        excel_path = download_movements(page)
        convert_excel_to_csv(excel_path)

        print("[IBERCAJA] Application completed successfully")

    except Exception as e:
        print(f"[IBERCAJA] Error during execution: {str(e)}")
        raise

    finally:
        cleanup(context, browser)
