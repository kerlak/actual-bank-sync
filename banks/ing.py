"""ING bank movements downloader using Playwright browser automation."""

import getpass
import os
import re
import time
from typing import Optional

import pandas as pd
from playwright.sync_api import Playwright, Page, Browser, BrowserContext

# Constants
ING_URL = "https://ing.ingdirect.es/app-login/"
DOWNLOADS_FOLDER = "./downloads/ing"
EXCEL_HEADER_ROW = 3  # ING Excel files have header in row 4 (0-indexed: 3)


def get_credentials() -> dict:
    """Prompt user for ING bank credentials (without PIN)."""
    print("\n[ING] Enter your credentials:")
    dni = getpass.getpass("DNI: ").strip()
    dia = getpass.getpass("Birth Day (DD): ").strip()
    mes = getpass.getpass("Birth Month (MM): ").strip()
    ano = getpass.getpass("Birth Year (YYYY): ").strip()

    return {
        'dni': dni,
        'dia': dia,
        'mes': mes,
        'ano': ano
    }


def get_pin_digits(positions: list[int]) -> str:
    """Request only the specific PIN digits needed.

    Uses a special prompt format "PIN_DIGITS:pos1,pos2,pos3:" that the WebUI
    can parse to show which positions are requested.
    """
    positions_str = ','.join(str(p) for p in positions)
    prompt = f"PIN_DIGITS:{positions_str}:"
    return getpass.getpass(prompt).strip()


def get_pin_positions(text: str) -> list[int]:
    """Extract requested PIN positions from text."""
    return [int(n) for n in re.findall(r'\d+', text)][:3]


def debug_page_state(page: Page, context: str) -> None:
    """Print debug info about current page state."""
    try:
        print(f"[DEBUG:{context}] URL: {page.url}")
        print(f"[DEBUG:{context}] Title: {page.title()}")
    except Exception as e:
        print(f"[DEBUG:{context}] Error getting state: {str(e)[:30]}")


def debug_element_exists(page: Page, selector: str, description: str) -> bool:
    """Check if element exists and log result."""
    try:
        count = page.locator(selector).count()
        visible = page.locator(selector).first.is_visible() if count > 0 else False
        print(f"[DEBUG] {description}: count={count}, visible={visible}")
        return count > 0
    except Exception as e:
        print(f"[DEBUG] {description}: error={str(e)[:30]}")
        return False


def convert_excel_to_csv(excel_path: str) -> str:
    """Convert downloaded Excel file to CSV format matching Ibercaja output."""
    csv_path = excel_path.replace('.xlsx', '.csv')
    print(f"[ING] Converting {os.path.basename(excel_path)} to CSV...")

    # ING files are actually XLS format (Composite Document) despite .xlsx extension
    df = pd.read_excel(excel_path, header=EXCEL_HEADER_ROW, engine='xlrd')
    print(f"[ING] Data loaded: {len(df)} rows")

    # Create output DataFrame matching Ibercaja format
    output_df = pd.DataFrame()

    # Map columns to Ibercaja format
    output_df['Nº Orden'] = range(1, len(df) + 1)

    # Format dates as DD-MM-YYYY
    date_col = df['F. VALOR']
    output_df['Fecha Oper'] = pd.to_datetime(date_col).dt.strftime('%d-%m-%Y')
    output_df['Fecha Valor'] = output_df['Fecha Oper']

    # Map concept from category
    output_df['Concepto'] = df['CATEGORÍA']
    output_df['Descripción'] = df['DESCRIPCIÓN']
    output_df['Referencia'] = df['COMENTARIO'].fillna('')

    # Amounts and balance
    output_df['Importe'] = df['IMPORTE (€)']
    output_df['Saldo'] = df['SALDO (€)']

    output_df.to_csv(csv_path, index=False)
    print(f"[ING] CSV saved: {csv_path}")

    return csv_path


def cleanup(context: Optional[BrowserContext], browser: Optional[Browser]) -> None:
    """Close browser context and browser instance."""
    print("[ING] Closing browser...")
    if context:
        context.close()
    if browser:
        browser.close()
    print("[ING] Browser closed")


def run(playwright: Playwright) -> None:
    """Main entry point for the ING movements downloader."""
    print("[ING] Starting application...")

    browser = None
    context = None

    try:
        browser = playwright.chromium.launch(
            headless=False,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled", "--start-maximized"]
        )
        print("[ING] Browser launched (headless=False)")

        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        print("[ING] Context created (1920x1080)")

        page = context.new_page()
        print("[ING] New page created")

        print("[ING] Requesting credentials...")
        credentials = get_credentials()
        print("[ING] Credentials received")

        # Navigate to login page
        print(f"[ING] Navigating to {ING_URL}")
        page.goto(ING_URL)
        debug_page_state(page, "after_goto")

        # Try to reject cookies
        print("[ING] Checking for cookie banner...")
        try:
            reject_btn = page.get_by_role("button", name="Rechazar")
            if reject_btn.is_visible(timeout=3000):
                print("[ING] Cookie banner found, clicking Rechazar...")
                reject_btn.click()
                print("[ING] Cookies rejected")
                time.sleep(0.5)
                debug_page_state(page, "after_cookies")
            else:
                print("[ING] Rechazar button not visible")
        except Exception as e:
            print(f"[ING] Cookie handling: {str(e)[:40]}")

        # Check for Didomi overlay
        debug_element_exists(page, "#didomi-host", "Didomi host")
        debug_element_exists(page, ".ing-popup-banner-body", "ING popup banner")

        # Remove Didomi overlay if present (it intercepts clicks)
        print("[ING] Removing Didomi overlay via JavaScript...")
        page.evaluate("""
            const didomi = document.querySelector('#didomi-host');
            if (didomi) {
                didomi.remove();
                console.log('Didomi removed');
            }
        """)
        time.sleep(0.5)
        debug_element_exists(page, "#didomi-host", "Didomi host after removal")

        # Fill credentials
        print("[ING] Filling credentials...")

        print("[ING] Filling DNI...")
        dni_field = page.get_by_role("textbox", name="Número de documento DNI o")
        print(f"[DEBUG] DNI field visible: {dni_field.is_visible()}")
        dni_field.fill(credentials['dni'])

        print("[ING] Filling birth day...")
        page.get_by_role("textbox", name="Fecha de nacimiento").fill(credentials['dia'])

        print("[ING] Filling birth month...")
        page.get_by_role("textbox", name="Mes, formato MM").fill(credentials['mes'])

        print("[ING] Filling birth year...")
        page.get_by_role("textbox", name="Año, formato AAAA").fill(credentials['ano'])

        print("[ING] Credentials filled")
        debug_page_state(page, "after_fill")

        # Check continue button state
        continue_btn = page.get_by_role("button", name="Continuas al siguiente paso")
        print(f"[DEBUG] Continue button visible: {continue_btn.is_visible()}")
        print(f"[DEBUG] Continue button enabled: {continue_btn.is_enabled()}")

        # Remove any Didomi overlay that appeared after filling credentials
        print("[ING] Checking for Didomi overlay before click...")
        debug_element_exists(page, "#didomi-host", "Didomi host before click")
        page.evaluate("""
            const didomi = document.querySelector('#didomi-host');
            if (didomi) {
                didomi.remove();
                console.log('Didomi removed before click');
            }
            // Also remove any overlays
            document.querySelectorAll('.ing-popup-banner-body, .ing-popup-banner, [class*="popup"]').forEach(el => el.remove());
        """)
        time.sleep(0.5)
        debug_element_exists(page, "#didomi-host", "Didomi host after JS removal")

        # Click continue
        print("[ING] Clicking continue button...")
        continue_btn.click()
        print("[ING] Continue button clicked")

        # Wait a moment and check state
        time.sleep(2)
        debug_page_state(page, "after_continue_click")

        # Wait for PIN challenge
        print("[ING] Waiting for PIN challenge...")
        debug_element_exists(page, "div.c-pinpad__secret-positions", "PIN positions div")

        try:
            page.wait_for_selector("div.c-pinpad__secret-positions", timeout=15000)
            print("[ING] PIN challenge selector found")
        except Exception as e:
            print(f"[ING] PIN wait failed: {str(e)[:60]}")
            debug_page_state(page, "pin_wait_failed")

            # Try to see what's on the page
            debug_element_exists(page, "div.c-pinpad", "PIN pad container")
            debug_element_exists(page, ".c-pinpad__secret-positions", "PIN positions (class)")
            debug_element_exists(page, "[class*='pinpad']", "Any pinpad element")
            debug_element_exists(page, "[class*='error']", "Any error element")
            debug_element_exists(page, "[class*='alert']", "Any alert element")

            # List visible buttons
            buttons = page.get_by_role("button").all()
            print(f"[DEBUG] Found {len(buttons)} buttons on page")
            for i, btn in enumerate(buttons[:5]):
                try:
                    text = btn.text_content()[:30] if btn.text_content() else "N/A"
                    print(f"[DEBUG]   Button {i}: {text}")
                except:
                    pass

            raise Exception("Timeout waiting for PIN challenge")

        # Get PIN positions
        sec_text = page.locator("div.c-pinpad__secret-positions").text_content()
        print(f"[DEBUG] PIN positions text: {sec_text}")
        positions = get_pin_positions(sec_text) if sec_text else []
        if not positions:
            raise Exception("Failed to read PIN positions")

        print(f"[ING] PIN positions requested: {positions}")

        # Request only the specific PIN digits needed (more secure - no full PIN stored)
        pin_digits = get_pin_digits(positions)
        print(f"[ING] Entering {len(pin_digits)} PIN digits...")

        # Click numpad buttons
        for i, digit in enumerate(pin_digits):
            print(f"[ING] Clicking digit {i+1}/{len(pin_digits)}...")
            page.get_by_role("button", name=digit).click()
            time.sleep(0.2)
        print("[ING] PIN digits entered")
        debug_page_state(page, "after_pin_entry")

        # Verify access
        print("[ING] Verifying access...")
        try:
            page.wait_for_url("**/pfm/#overall-position**", timeout=15000)
            print("[ING] Access granted")
            debug_page_state(page, "access_granted")
        except:
            debug_page_state(page, "access_check_failed")
            if page.get_by_role("heading", name="Acceso seguro").is_visible():
                print("[ING] MOBILE VALIDATION REQUIRED - Check your phone")
                page.get_by_role("heading", name="Acceso seguro").click()
                try:
                    page.wait_for_url("**/pfm/#overall-position**", timeout=60000)
                    print("[ING] Access confirmed via mobile")
                except:
                    raise Exception("Mobile validation timeout")
            else:
                raise Exception("Could not access home page")

        # Download accounts
        print("[ING] Looking for accounts...")
        debug_page_state(page, "before_accounts")

        if not os.path.exists(DOWNLOADS_FOLDER):
            os.makedirs(DOWNLOADS_FOLDER)
            print(f"[ING] Created downloads folder: {DOWNLOADS_FOLDER}")

        accounts = ["NARANJA", "NÓMINA"]
        downloaded_files = []

        for acc in accounts:
            print(f"[ING] ========== Processing account: {acc} ==========")
            try:
                print(f"[ING] Navigating to overall-position...")
                page.goto("https://ing.ingdirect.es/pfm/#overall-position")
                page.wait_for_load_state("networkidle")
                debug_page_state(page, f"acc_{acc}_loaded")

                # Wait for page content to render
                print("[ING] Waiting for page content...")
                time.sleep(3)

                # Debug: Check what's on the page BEFORE any removal
                links_before = page.get_by_role("link").all()
                print(f"[DEBUG] Links BEFORE Didomi removal: {len(links_before)}")
                for i, link in enumerate(links_before[:5]):
                    try:
                        text = link.text_content()[:40] if link.text_content() else "N/A"
                        print(f"[DEBUG]   Link {i}: {text}")
                    except:
                        pass

                # Check if Didomi is actually present
                didomi_present = page.locator("#didomi-host").count() > 0
                print(f"[DEBUG] Didomi host present: {didomi_present}")

                if didomi_present:
                    # Only remove specific blocking overlay elements
                    print("[ING] Removing Didomi overlay (conservative)...")
                    page.evaluate("""
                        const didomi = document.querySelector('#didomi-host');
                        if (didomi) didomi.remove();
                    """)
                    time.sleep(0.5)

                # Debug: Check what's on the page AFTER removal
                links_after = page.get_by_role("link").all()
                print(f"[DEBUG] Links AFTER Didomi removal: {len(links_after)}")

                # Find account link
                print(f"[ING] Looking for {acc} account link...")
                acc_locator = page.get_by_role("link", name=re.compile(acc, re.IGNORECASE))
                count = acc_locator.count()
                print(f"[DEBUG] Found {count} matches for '{acc}'")

                if count > 0:
                    print(f"[ING] Clicking on {acc} account...")
                    acc_locator.first.click()
                    time.sleep(1)
                    debug_page_state(page, f"acc_{acc}_clicked")

                    print("[ING] Clicking 'Buscar movimientos'...")
                    page.get_by_role("link", name="Buscar movimientos").click()
                    time.sleep(1)
                    debug_page_state(page, f"acc_{acc}_search")

                    print("[ING] Clicking 'Más opciones de búsqueda'...")
                    page.get_by_role("button", name="Más opciones de búsqueda").click()
                    time.sleep(0.5)

                    print("[ING] Selecting 'Últimos 2 meses'...")
                    page.get_by_text("Últimos 2 meses").click()
                    time.sleep(0.5)

                    print("[ING] Clicking 'Buscar'...")
                    page.get_by_role("button", name="Buscar").last.click()
                    time.sleep(3)
                    debug_page_state(page, f"acc_{acc}_searched")

                    print(f"[ING] Downloading Excel for {acc}...")
                    page.get_by_role("button", name="Descargar movimientos").click()
                    time.sleep(0.5)

                    with page.expect_download() as download_info:
                        page.get_by_text("Descargar Excel").click()

                    download = download_info.value
                    filename = f"ing_{acc}_{int(time.time())}.xlsx"
                    file_path = os.path.join(DOWNLOADS_FOLDER, filename)
                    download.save_as(file_path)
                    downloaded_files.append(file_path)
                    print(f"[ING] Downloaded: {file_path}")

                    # Convert to CSV
                    convert_excel_to_csv(file_path)
                else:
                    print(f"[ING] Account {acc} not found, skipping")
                    # Debug: list all links (more verbose)
                    links = page.get_by_role("link").all()
                    print(f"[DEBUG] Found {len(links)} total links")
                    for i, link in enumerate(links[:15]):
                        try:
                            text = link.text_content()[:50] if link.text_content() else "N/A"
                            href = link.get_attribute("href") or "no-href"
                            print(f"[DEBUG]   Link {i}: '{text}' -> {href[:40]}")
                        except:
                            pass

                    # Also check for elements with account-related text
                    print("[DEBUG] Checking for any text containing account names...")
                    page_text = page.content()
                    if "NARANJA" in page_text.upper():
                        print("[DEBUG]   Page contains 'NARANJA' text")
                    if "NOMINA" in page_text.upper() or "NÓMINA" in page_text.upper():
                        print("[DEBUG]   Page contains 'NOMINA' text")

                    # Check for common ING page elements
                    debug_element_exists(page, "[class*='account']", "Account elements")
                    debug_element_exists(page, "[class*='position']", "Position elements")
                    debug_element_exists(page, "[class*='product']", "Product elements")

            except Exception as e:
                print(f"[ING] Error processing {acc}: {str(e)}")
                debug_page_state(page, f"acc_{acc}_error")
                continue

        # Logout
        print("[ING] Logging out...")
        try:
            page.get_by_role("button", name="Cerrar sesión").click()
            print("[ING] Session closed")
        except Exception as e:
            print(f"[ING] Could not close session: {str(e)[:30]}")

        print(f"[ING] Downloaded {len(downloaded_files)} files")
        print("[ING] Application completed successfully")

    except Exception as e:
        print(f"[ING] Error during execution: {str(e)}")
        raise

    finally:
        cleanup(context, browser)
