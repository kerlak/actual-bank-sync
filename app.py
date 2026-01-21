"""Ibercaja bank movements downloader using Playwright browser automation."""

import getpass
import os
from typing import Optional

import pandas as pd
from playwright.sync_api import Playwright, sync_playwright, Page, BrowserContext

# Constants
IBERCAJA_URL = "https://www.ibercaja.es/"
DOWNLOADS_FOLDER = "./downloads"
OUTPUT_EXCEL_FILENAME = "ibercaja_movements.xlsx"
OUTPUT_CSV_FILENAME = "ibercaja_movements.csv"
EXCEL_HEADER_ROW = 5  # 0-indexed, so row 6 in Excel (1-indexed)
MAX_MODAL_REMOVAL_ATTEMPTS = 5
MODAL_CHECK_TIMEOUT_MS = 500
MODAL_WAIT_BETWEEN_ATTEMPTS_MS = 300


def get_credentials() -> tuple[str, str]:
    """Prompt user for bank credentials.

    Returns:
        Tuple of (identification_code, access_key).
    """
    codigo = getpass.getpass("\nIdentification Code: ").strip()
    clave = getpass.getpass("\nAccess Key: ").strip()
    return codigo, clave


def login(page: Page, codigo: str, clave: str) -> None:
    """Perform login to Ibercaja website.

    Args:
        page: Playwright page instance.
        codigo: User identification code.
        clave: User access key.

    Raises:
        Exception: If login elements are not found or login fails.
    """
    print("[APP] Navigating to", IBERCAJA_URL)
    page.goto(IBERCAJA_URL)
    print("[APP] Page loaded")

    print("[APP] Looking for 'Client Access' link...")
    page.get_by_role("link", name="Acceso clientes").click()
    print("[APP] Link clicked")

    print("[APP] Filling identification code...")
    page.get_by_role("textbox", name="Código de identificación").click()
    page.get_by_role("textbox", name="Código de identificación").fill(codigo)
    print("[APP] Identification code filled")

    print("[APP] Filling access key...")
    page.get_by_role("textbox", name="Clave de acceso").click()
    page.get_by_role("textbox", name="Clave de acceso").fill(clave)
    print("[APP] Access key filled")

    print("[APP] Clicking 'Enter' button...")
    page.get_by_role("button", name=" entrar").click()
    print("[APP] Waiting for page to load...")
    page.wait_for_load_state("networkidle")
    print("[APP] Login completed")


def handle_modal_overlay(page: Page) -> None:
    """Remove modal overlays that may block interaction.

    Attempts to hide or remove overlay elements using JavaScript injection.
    Retries multiple times if the overlay persists.

    Args:
        page: Playwright page instance.
    """
    print("[APP] Handling modal overlay...")

    for attempt in range(MAX_MODAL_REMOVAL_ATTEMPTS):
        try:
            # Attempt to hide all overlays and modals via JavaScript
            page.evaluate("""
                const overlays = document.querySelectorAll('.overlay, ui-modal');
                overlays.forEach(el => {
                    if (el.style) el.style.display = 'none';
                    el.style.pointerEvents = 'none';
                });
            """)

            overlay = page.locator(".overlay")
            if not overlay.is_visible(timeout=MODAL_CHECK_TIMEOUT_MS):
                print(f"[APP] Overlay is hidden (attempt {attempt + 1})")
                break
            else:
                print(f"[APP] Overlay still visible, removing via JavaScript (attempt {attempt + 1})...")
                page.evaluate("document.querySelector('ui-modal')?.remove()")
                page.wait_for_timeout(MODAL_WAIT_BETWEEN_ATTEMPTS_MS)
        except Exception as e:
            print(f"[APP] Overlay handling done (attempt {attempt + 1}): {str(e)[:50]}")
            break


def download_movements(page: Page) -> str:
    """Navigate to movements and download Excel file.

    Args:
        page: Playwright page instance.

    Returns:
        Path to the downloaded Excel file.

    Raises:
        Exception: If download fails or elements are not found.
    """
    print("[APP] Clicking table row to select account...")
    page.locator(".ui-table__row").click()
    print("[APP] Table row clicked")

    print("[APP] Looking for download button...")
    page.get_by_role("button", name="\ue911").click()
    print("[APP] Download button clicked, waiting for download...")

    with page.expect_download() as download_info:
        page.get_by_role("listitem").filter(has_text="Excel").click()

    download = download_info.value

    # Ensure downloads folder exists
    if not os.path.exists(DOWNLOADS_FOLDER):
        os.makedirs(DOWNLOADS_FOLDER)
        print(f"[APP] Created downloads folder: {DOWNLOADS_FOLDER}")

    file_path = os.path.join(DOWNLOADS_FOLDER, OUTPUT_EXCEL_FILENAME)
    download.save_as(file_path)
    print(f"[APP] File downloaded to: {file_path}")

    return file_path


def convert_excel_to_csv(excel_path: str) -> str:
    """Convert downloaded Excel file to CSV format.

    Args:
        excel_path: Path to the Excel file.

    Returns:
        Path to the generated CSV file.

    Raises:
        Exception: If file reading or conversion fails.
    """
    print(f"[APP] Processing Excel to CSV (header at row {EXCEL_HEADER_ROW + 1})...")
    csv_path = os.path.join(DOWNLOADS_FOLDER, OUTPUT_CSV_FILENAME)

    df = pd.read_excel(excel_path, header=EXCEL_HEADER_ROW, engine='openpyxl')
    print(f"[APP] Data loaded: {len(df)} rows")

    df.to_csv(csv_path, index=False)
    print(f"[APP] CSV file saved to: {csv_path}")

    return csv_path


def cleanup(context: Optional[BrowserContext], browser: Optional[object]) -> None:
    """Close browser context and browser instance.

    Args:
        context: Browser context to close.
        browser: Browser instance to close.
    """
    print("[APP] Closing browser...")
    if context:
        context.close()
    if browser:
        browser.close()
    print("[APP] Browser closed")


def run(playwright: Playwright) -> None:
    """Main entry point for the Ibercaja movements downloader.

    Orchestrates the full download process: login, handle modals,
    download movements, and convert to CSV.

    Args:
        playwright: Playwright instance.

    Raises:
        Exception: If any step of the process fails.
    """
    print("[APP] Starting application...")

    browser = None
    context = None

    try:
        browser = playwright.chromium.launch(headless=False)
        print("[APP] Browser launched")

        context = browser.new_context()
        page = context.new_page()

        # Get credentials (may be mocked by webui)
        print("[APP] Requesting credentials...")
        codigo, clave = get_credentials()
        print("[APP] Credentials received")

        # Perform login
        login(page, codigo, clave)

        # Handle any modal overlays
        handle_modal_overlay(page)

        # Download movements Excel
        excel_path = download_movements(page)

        # Convert to CSV
        convert_excel_to_csv(excel_path)

        print("[APP] Application completed successfully")

    except Exception as e:
        print(f"[APP] Error during execution: {str(e)}")
        raise

    finally:
        cleanup(context, browser)


if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)
