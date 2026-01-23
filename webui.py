"""Web UI hub for multi-bank movements downloader using PyWebIO."""

import io
import os
import sys
import traceback
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
from unittest.mock import patch

from pywebio import config, start_server
from pywebio.input import file_upload, input as pyi_input
from pywebio.output import put_buttons, put_html, put_text, clear
from playwright.sync_api import sync_playwright

from banks import ibercaja, ing
import actual_sync

# Constants
SERVER_PORT = 2077
ACTUAL_BUDGET_URL = os.environ.get("ACTUAL_BUDGET_URL", "https://localhost")
ACTUAL_BUDGET_FILE = os.environ.get("ACTUAL_BUDGET_FILE", "")
ACTUAL_CERT_PATH = os.environ.get("ACTUAL_CERT_PATH", "./certs/actual.pem")

CSS_THEME = """
    footer, .pywebio-footer, [class*='footer'] { display: none !important; }
    body { font-family: monospace; background: #191919; color: #d4d4d4; }
    .markdown-body { color: #d4d4d4; }
    .btn {
        background: transparent !important;
        border: none !important;
        color: #da7756 !important;
        font-family: monospace !important;
        font-size: inherit !important;
        padding: 0 !important;
        margin-right: 1em !important;
        box-shadow: none !important;
    }
    .btn:hover { color: #e89b7b !important; }
    .btn:focus { box-shadow: none !important; }
    .form-group, .card, .input-container, .pywebio, .container,
    .input-group, .modal-content, .card-body, [class*="input"], [class*="card"] {
        background: #191919 !important;
        background-color: #191919 !important;
        border: none !important;
    }
    .form-control {
        min-height: 44px;
        font-size: 16px !important;
        background: #2a2a2a !important;
        color: #d4d4d4 !important;
        border: 1px solid #444 !important;
    }
"""


class Bank(Enum):
    """Available banks."""
    IBERCAJA = auto()
    ING = auto()


class CredentialType(Enum):
    """Credential request types."""
    # Ibercaja
    CODIGO = auto()
    CLAVE = auto()
    # ING
    DNI = auto()
    DIA = auto()
    MES = auto()
    ANO = auto()
    PIN_DIGITS = auto()  # Interactive: only 3 specific digits requested by ING


@dataclass
class AppState:
    """Global application state."""
    current_bank: Optional[Bank] = None
    # Ibercaja credentials
    ibercaja_codigo: Optional[str] = None
    ibercaja_clave: Optional[str] = None
    # ING credentials (no PIN stored - requested interactively each time)
    ing_dni: Optional[str] = None
    ing_dia: Optional[str] = None
    ing_mes: Optional[str] = None
    ing_ano: Optional[str] = None
    # Actual Budget credentials
    actual_password: Optional[str] = None
    actual_encryption_password: Optional[str] = None
    # Account mapping for Actual Budget
    account_mapping: dict = field(default_factory=lambda: {
        'ibercaja': 'Ibercaja común',
        'ing_nomina': 'ING Nómina',
        'ing_naranja': 'ING Naranja',
    })
    # Request tracking
    _credential_queue: list = field(default_factory=list)
    _queue_index: int = 0

    def setup_ibercaja_queue(self) -> None:
        """Setup credential request queue for Ibercaja."""
        self._credential_queue = [CredentialType.CODIGO, CredentialType.CLAVE]
        self._queue_index = 0

    def setup_ing_queue(self) -> None:
        """Setup credential request queue for ING (PIN requested interactively later)."""
        self._credential_queue = [
            CredentialType.DNI, CredentialType.DIA,
            CredentialType.MES, CredentialType.ANO
        ]
        self._queue_index = 0

    def get_next_type(self) -> Optional[CredentialType]:
        """Get next credential type to request."""
        if self._queue_index < len(self._credential_queue):
            return self._credential_queue[self._queue_index]
        return None

    def advance(self) -> None:
        """Move to next credential in queue."""
        self._queue_index += 1

    def has_ibercaja_credentials(self) -> bool:
        """Check if Ibercaja credentials are stored."""
        return self.ibercaja_codigo is not None and self.ibercaja_clave is not None

    def has_ing_credentials(self) -> bool:
        """Check if ING credentials are stored (PIN not stored for security)."""
        return all([self.ing_dni, self.ing_dia, self.ing_mes, self.ing_ano])

    def has_actual_credentials(self) -> bool:
        """Check if Actual Budget credentials are stored."""
        return self.actual_password is not None

    def clear_actual(self) -> None:
        """Clear Actual Budget credentials."""
        self.actual_password = None
        self.actual_encryption_password = None

    def clear_ibercaja(self) -> None:
        """Clear Ibercaja credentials."""
        self.ibercaja_codigo = None
        self.ibercaja_clave = None

    def clear_ing(self) -> None:
        """Clear ING credentials."""
        self.ing_dni = None
        self.ing_dia = None
        self.ing_mes = None
        self.ing_ano = None

    def clear_all(self) -> None:
        """Clear all credentials."""
        self.clear_ibercaja()
        self.clear_ing()
        self.clear_actual()
        self.current_bank = None


# Global state
state = AppState()


def blur_active_element() -> None:
    """Remove focus from active element to fix iOS keyboard issues."""
    put_html('''<script>
        setTimeout(() => {
            document.querySelectorAll('input').forEach(i => i.blur());
        }, 100);
    </script>''')


def auto_scroll() -> None:
    """Scroll to the bottom of the page and hide footer."""
    put_html("""<script>
        window.scrollTo(0, document.body.scrollHeight);
        document.querySelectorAll('footer, .pywebio-footer, [class*="footer"]')
            .forEach(el => el.style.display = 'none');
    </script>""")


class LogCapture(io.StringIO):
    """Captures stdout and displays it in real-time in PyWebIO."""

    def write(self, message: str) -> int:
        if message and message.strip():
            put_text(message.rstrip())
            auto_scroll()
        return len(message)

    def flush(self) -> None:
        pass


def dynamic_getpass_ibercaja(prompt: str = "") -> str:
    """Dynamic getpass for Ibercaja credentials."""
    if prompt:
        put_text(f"> {prompt.strip()}")

    blur_active_element()
    cred_type = state.get_next_type()

    if cred_type == CredentialType.CODIGO:
        if state.ibercaja_codigo:
            put_text(f"Using stored identification code: {'*' * len(state.ibercaja_codigo)}")
            state.advance()
            return state.ibercaja_codigo
        state.ibercaja_codigo = pyi_input(type='password')
        state.advance()
        return state.ibercaja_codigo

    elif cred_type == CredentialType.CLAVE:
        if state.ibercaja_clave:
            put_text(f"Using stored access key: {'*' * len(state.ibercaja_clave)}")
            state.advance()
            return state.ibercaja_clave
        state.ibercaja_clave = pyi_input(type='password')
        state.advance()
        return state.ibercaja_clave

    return ""


def dynamic_getpass_ing(prompt: str = "") -> str:
    """Dynamic getpass for ING credentials.

    Handles both initial credentials and interactive PIN digits request.
    PIN digits are requested with format "PIN_DIGITS:pos1,pos2,pos3:"
    """
    # Check for interactive PIN digits request (format: "PIN_DIGITS:1,3,6:")
    if prompt.startswith("PIN_DIGITS:"):
        positions_str = prompt.replace("PIN_DIGITS:", "").rstrip(":")
        positions = [int(p) for p in positions_str.split(",")]

        # Visual representation: _ for requested positions, · for others
        pin_visual = ''.join('_' if i in positions else '·' for i in range(1, 7))
        pos_labels = ''.join(str(i) if i in positions else ' ' for i in range(1, 7))

        put_text("> Enter PIN digits:")
        put_text(f"  PIN:  [ {' '.join(pin_visual)} ]")
        put_text(f"          {' '.join(pos_labels)}")

        blur_active_element()
        pin_digits = pyi_input(type='password')
        return pin_digits

    # Regular credential flow
    if prompt:
        put_text(f"> {prompt.strip()}")

    blur_active_element()
    cred_type = state.get_next_type()

    if cred_type == CredentialType.DNI:
        if state.ing_dni:
            put_text(f"Using stored DNI: {'*' * len(state.ing_dni)}")
            state.advance()
            return state.ing_dni
        state.ing_dni = pyi_input(type='password')
        state.advance()
        return state.ing_dni

    elif cred_type == CredentialType.DIA:
        if state.ing_dia:
            put_text(f"Using stored day: {state.ing_dia}")
            state.advance()
            return state.ing_dia
        state.ing_dia = pyi_input(type='password')
        state.advance()
        return state.ing_dia

    elif cred_type == CredentialType.MES:
        if state.ing_mes:
            put_text(f"Using stored month: {state.ing_mes}")
            state.advance()
            return state.ing_mes
        state.ing_mes = pyi_input(type='password')
        state.advance()
        return state.ing_mes

    elif cred_type == CredentialType.ANO:
        if state.ing_ano:
            put_text(f"Using stored year: {state.ing_ano}")
            state.advance()
            return state.ing_ano
        state.ing_ano = pyi_input(type='password')
        state.advance()
        return state.ing_ano

    return ""


def execute_ibercaja() -> None:
    """Execute Ibercaja download."""
    put_text("---")
    put_text("execution log:")

    state.setup_ibercaja_queue()
    old_stdout = sys.stdout

    try:
        sys.stdout = LogCapture()

        with patch('getpass.getpass', side_effect=dynamic_getpass_ibercaja):
            with sync_playwright() as playwright:
                print("[WEBUI] Starting Ibercaja download...")
                ibercaja.run(playwright)
                print("[WEBUI] Ibercaja completed")

        sys.stdout = old_stdout
        put_text("[PROCESS] Download completed. Files in ./downloads/ibercaja")

    except Exception as e:
        sys.stdout = old_stdout
        put_text(f"[ERROR] {str(e)}")
        put_text(traceback.format_exc())


def execute_ing() -> None:
    """Execute ING download."""
    put_text("---")
    put_text("execution log:")

    state.setup_ing_queue()
    old_stdout = sys.stdout

    try:
        sys.stdout = LogCapture()

        with patch('getpass.getpass', side_effect=dynamic_getpass_ing):
            with sync_playwright() as playwright:
                print("[WEBUI] Starting ING download...")
                ing.run(playwright)
                print("[WEBUI] ING completed")

        sys.stdout = old_stdout
        put_text("[PROCESS] Download completed. Files in ./downloads/ing")

    except Exception as e:
        sys.stdout = old_stdout
        put_text(f"[ERROR] {str(e)}")
        put_text(traceback.format_exc())


def request_actual_credentials() -> bool:
    """Request Actual Budget credentials if not stored."""
    if not state.has_actual_credentials():
        put_text("> Actual Budget server password:")
        state.actual_password = pyi_input(type='password')
        if not state.actual_password:
            put_text("[ERROR] Password is required")
            return False

        put_text("> Actual Budget file encryption key (leave empty if none):")
        encryption = pyi_input(type='password')
        state.actual_encryption_password = encryption if encryption else None

    return True


def execute_sync_ibercaja() -> None:
    """Sync Ibercaja CSV to Actual Budget."""
    put_text("---")
    put_text("sync to actual budget:")

    if not request_actual_credentials():
        return

    csv_path = actual_sync.get_latest_csv('ibercaja')
    if not csv_path:
        put_text("[ERROR] No CSV found. Download movements first.")
        return

    put_text(f"[SYNC] CSV: {csv_path}")
    put_text(f"[SYNC] Target account: {state.account_mapping['ibercaja']}")

    result = actual_sync.sync_csv_to_actual(
        csv_path=csv_path,
        source='ibercaja',
        base_url=ACTUAL_BUDGET_URL,
        password=state.actual_password,
        encryption_password=state.actual_encryption_password,
        file_name=ACTUAL_BUDGET_FILE,
        account_mapping=state.account_mapping,
        cert_path=ACTUAL_CERT_PATH
    )

    if result.success:
        put_text(f"[OK] {result.message}")
        if result.errors:
            for err in result.errors[:5]:
                put_text(f"[WARN] {err}")
    else:
        put_text(f"[ERROR] {result.message}")


def execute_sync_ing(account_type: str) -> None:
    """Sync ING CSV to Actual Budget."""
    put_text("---")
    put_text(f"sync to actual budget ({account_type}):")

    if not request_actual_credentials():
        return

    source = f'ing_{account_type}'
    csv_path = actual_sync.get_latest_csv(source)
    if not csv_path:
        put_text(f"[ERROR] No CSV found for {account_type}. Download movements first.")
        return

    put_text(f"[SYNC] CSV: {csv_path}")
    put_text(f"[SYNC] Target account: {state.account_mapping[source]}")

    result = actual_sync.sync_csv_to_actual(
        csv_path=csv_path,
        source=source,
        base_url=ACTUAL_BUDGET_URL,
        password=state.actual_password,
        encryption_password=state.actual_encryption_password,
        file_name=ACTUAL_BUDGET_FILE,
        account_mapping=state.account_mapping,
        cert_path=ACTUAL_CERT_PATH
    )

    if result.success:
        put_text(f"[OK] {result.message}")
        if result.errors:
            for err in result.errors[:5]:
                put_text(f"[WARN] {err}")
    else:
        put_text(f"[ERROR] {result.message}")


def execute_upload_ibercaja() -> None:
    """Upload an Ibercaja Excel file and convert to CSV."""
    put_text("---")
    put_text("upload excel (ibercaja):")

    content = file_upload(
        label="Select Ibercaja Excel file (.xlsx)",
        accept=".xlsx"
    )

    if not content:
        put_text("[ERROR] No file selected")
        return

    downloads_dir = './downloads/ibercaja'
    os.makedirs(downloads_dir, exist_ok=True)

    # Save uploaded file
    xlsx_path = os.path.join(downloads_dir, 'ibercaja_movements.xlsx')
    with open(xlsx_path, 'wb') as f:
        f.write(content['content'])
    put_text(f"[UPLOAD] Saved: {xlsx_path}")

    # Convert to CSV
    try:
        csv_path = ibercaja.convert_excel_to_csv(xlsx_path)
        os.remove(xlsx_path)
        put_text(f"[OK] Converted to: {csv_path}")
        put_text(f"[OK] Ready to sync to Actual Budget")
    except Exception as e:
        put_text(f"[ERROR] Conversion failed: {e}")


def show_ibercaja() -> None:
    """Show Ibercaja interface."""
    state.current_bank = Bank.IBERCAJA
    clear()

    inject_styles()
    put_text("ibercaja")
    put_text("--------")
    put_text("")

    if state.has_ibercaja_credentials():
        put_text("[ok] credentials stored")
    else:
        put_text("[--] no credentials stored")

    put_text("")
    put_buttons(
        [
            {'label': '[start download]', 'value': 'download'},
            {'label': '[upload xlsx]', 'value': 'upload'},
            {'label': '[sync to actual]', 'value': 'sync'},
            {'label': '[clear credentials]', 'value': 'clear'},
            {'label': '[back]', 'value': 'back'}
        ],
        onclick=handle_ibercaja_action
    )


def execute_upload_ing(account_type: str) -> None:
    """Upload an ING Excel file and convert to CSV."""
    put_text("---")
    put_text(f"upload excel ({account_type}):")

    content = file_upload(
        label=f"Select ING {account_type} Excel file (.xls/.xlsx)",
        accept=".xls,.xlsx"
    )

    if not content:
        put_text("[ERROR] No file selected")
        return

    downloads_dir = './downloads/ing'
    os.makedirs(downloads_dir, exist_ok=True)

    # Save uploaded file temporarily
    xlsx_path = os.path.join(downloads_dir, f"ing_{account_type}.xlsx")
    with open(xlsx_path, 'wb') as f:
        f.write(content['content'])
    put_text(f"[UPLOAD] Saved: {xlsx_path}")

    # Convert to CSV
    try:
        csv_path = ing.convert_excel_to_csv(xlsx_path)
        os.remove(xlsx_path)
        put_text(f"[OK] Converted to: {csv_path}")
        put_text(f"[OK] Ready to sync to Actual Budget")
    except Exception as e:
        put_text(f"[ERROR] Conversion failed: {e}")


def show_ing() -> None:
    """Show ING interface."""
    state.current_bank = Bank.ING
    clear()

    inject_styles()
    put_text("ing")
    put_text("---")
    put_text("")

    if state.has_ing_credentials():
        put_text("[ok] credentials stored")
    else:
        put_text("[--] no credentials stored")

    put_text("")
    put_buttons(
        [
            {'label': '[start download]', 'value': 'download'},
            {'label': '[upload nómina xlsx]', 'value': 'upload_nomina'},
            {'label': '[upload naranja xlsx]', 'value': 'upload_naranja'},
            {'label': '[sync nómina]', 'value': 'sync_nomina'},
            {'label': '[sync naranja]', 'value': 'sync_naranja'},
            {'label': '[clear credentials]', 'value': 'clear'},
            {'label': '[back]', 'value': 'back'}
        ],
        onclick=handle_ing_action
    )


def handle_ibercaja_action(action: str) -> None:
    """Handle Ibercaja actions."""
    if action == 'download':
        execute_ibercaja()
    elif action == 'upload':
        execute_upload_ibercaja()
    elif action == 'sync':
        execute_sync_ibercaja()
    elif action == 'clear':
        state.clear_ibercaja()
        state.clear_actual()
        put_text("[SYSTEM] Ibercaja and Actual Budget credentials cleared")
    elif action == 'back':
        show_menu()


def handle_ing_action(action: str) -> None:
    """Handle ING actions."""
    if action == 'download':
        execute_ing()
    elif action == 'upload_nomina':
        execute_upload_ing('nomina')
    elif action == 'upload_naranja':
        execute_upload_ing('naranja')
    elif action == 'sync_nomina':
        execute_sync_ing('nomina')
    elif action == 'sync_naranja':
        execute_sync_ing('naranja')
    elif action == 'clear':
        state.clear_ing()
        state.clear_actual()
        put_text("[SYSTEM] ING and Actual Budget credentials cleared")
    elif action == 'back':
        show_menu()


def handle_menu_selection(bank: str) -> None:
    """Handle bank selection from main menu."""
    if bank == 'ibercaja':
        show_ibercaja()
    elif bank == 'ing':
        show_ing()


def inject_styles() -> None:
    """Inject CSS styles immediately to prevent FOUC (Flash of Unstyled Content)."""
    put_html(f'<style>{CSS_THEME}</style>')


def show_menu() -> None:
    """Show main menu."""
    state.current_bank = None
    clear()

    inject_styles()
    blur_active_element()

    put_text("banking hub")
    put_text("-----------")
    put_text("")
    put_text("select bank:")
    put_text("")
    put_buttons(
        [
            {'label': '[ibercaja]', 'value': 'ibercaja'},
            {'label': '[ing]', 'value': 'ing'}
        ],
        onclick=handle_menu_selection
    )


def main() -> None:
    """Main entry point for the PyWebIO application."""
    config(title="banking hub", css_style=CSS_THEME)
    show_menu()


if __name__ == "__main__":
    start_server(main, port=SERVER_PORT, debug=False)
