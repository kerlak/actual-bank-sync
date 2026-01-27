"""Web UI hub for multi-bank movements downloader using PyWebIO."""

import io
import os
import sys
import threading
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Optional, Callable
from unittest.mock import patch

from pywebio import config, start_server
from pywebio.input import file_upload, input as pyi_input, select
from pywebio.output import put_buttons, put_html, put_text, clear, use_scope
from playwright.sync_api import sync_playwright

from banks import ibercaja, ing
import actual_sync


# =============================================================================
# SCHEDULER FOR IBERCAJA AUTO-SYNC
# =============================================================================

class IbercajaScheduler:
    """Scheduler for automatic Ibercaja download and sync."""

    INTERVALS = {
        '1h': 3600,
        '3h': 10800,
        '6h': 21600,
        '12h': 43200,
        '24h': 86400,
    }

    def __init__(self):
        self.enabled = False
        self.interval_key = None
        self.timer: Optional[threading.Timer] = None
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.last_result: Optional[str] = None
        self._lock = threading.Lock()

    def start(self, interval_key: str, run_now: bool = False) -> bool:
        """Start the scheduler with given interval."""
        if interval_key not in self.INTERVALS:
            return False

        with self._lock:
            self.stop()  # Stop any existing timer
            self.enabled = True
            self.interval_key = interval_key

            if run_now:
                # Run immediately in a thread, then schedule next
                threading.Thread(target=self._run_and_schedule, daemon=True).start()
            else:
                self._schedule_next()

            return True

    def stop(self) -> None:
        """Stop the scheduler."""
        with self._lock:
            self.enabled = False
            self.interval_key = None
            self.next_run = None
            if self.timer:
                self.timer.cancel()
                self.timer = None

    def _schedule_next(self) -> None:
        """Schedule the next execution."""
        if not self.enabled or not self.interval_key:
            return

        interval_seconds = self.INTERVALS[self.interval_key]
        self.next_run = datetime.now() + timedelta(seconds=interval_seconds)

        self.timer = threading.Timer(interval_seconds, self._run_and_schedule)
        self.timer.daemon = True
        self.timer.start()

    def _run_and_schedule(self) -> None:
        """Execute the sync and schedule next run."""
        if not self.enabled:
            return

        self.last_run = datetime.now()
        self.last_result = self._execute_sync()

        # Schedule next run
        with self._lock:
            if self.enabled:
                self._schedule_next()

    def _execute_sync(self) -> str:
        """Execute Ibercaja download and sync (background, no UI)."""
        try:
            print(f"[SCHEDULER] Starting Ibercaja auto-sync at {datetime.now()}")

            # Check prerequisites
            if not state.has_ibercaja_credentials():
                return "ERROR: No Ibercaja credentials stored"

            if not state.has_actual_credentials():
                return "ERROR: No Actual Budget credentials stored"

            if not state.has_saved_mapping('ibercaja'):
                return "ERROR: No sync mapping configured"

            # 1. Download movements
            print("[SCHEDULER] Downloading movements...")

            def auto_getpass(prompt: str = "") -> str:
                """Auto-provide credentials from state."""
                if 'Identification' in prompt or 'Code' in prompt or not prompt:
                    if state.ibercaja_codigo:
                        return state.ibercaja_codigo
                if 'Key' in prompt or 'Clave' in prompt or 'clave' in prompt:
                    if state.ibercaja_clave:
                        return state.ibercaja_clave
                # Fallback based on queue position
                if hasattr(state, '_auto_queue_idx'):
                    state._auto_queue_idx += 1
                    if state._auto_queue_idx == 1:
                        return state.ibercaja_codigo or ""
                    else:
                        return state.ibercaja_clave or ""
                state._auto_queue_idx = 0
                return state.ibercaja_codigo or ""

            state._auto_queue_idx = 0

            with patch('getpass.getpass', side_effect=auto_getpass):
                with sync_playwright() as playwright:
                    ibercaja.run(playwright)

            print("[SCHEDULER] Download completed")

            # 2. Sync to Actual Budget
            print("[SCHEDULER] Syncing to Actual Budget...")

            csv_path = actual_sync.get_latest_csv('ibercaja')
            if not csv_path:
                return "ERROR: No CSV found after download"

            saved_file = state.get_saved_file('ibercaja')
            saved_account = state.get_saved_account('ibercaja')
            saved_encryption = state.get_saved_encryption(saved_file) if saved_file else None

            result = actual_sync.sync_csv_to_actual(
                csv_path=csv_path,
                source='ibercaja',
                base_url=ACTUAL_BUDGET_URL,
                password=state.actual_password,
                encryption_password=saved_encryption,
                file_name=saved_file,
                account_name=saved_account,
                cert_path=ACTUAL_CERT_PATH
            )

            if result.success:
                msg = f"OK: {result.imported} imported, {result.skipped} skipped"
                print(f"[SCHEDULER] {msg}")
                return msg
            else:
                print(f"[SCHEDULER] Sync failed: {result.message}")
                return f"ERROR: {result.message}"

        except Exception as e:
            error_msg = f"ERROR: {str(e)}"
            print(f"[SCHEDULER] {error_msg}")
            return error_msg

    def get_status(self) -> dict:
        """Get current scheduler status."""
        return {
            'enabled': self.enabled,
            'interval': self.interval_key,
            'last_run': self.last_run.strftime('%Y-%m-%d %H:%M') if self.last_run else None,
            'next_run': self.next_run.strftime('%Y-%m-%d %H:%M') if self.next_run else None,
            'last_result': self.last_result,
        }


# Global scheduler instance
ibercaja_scheduler = IbercajaScheduler()

# Constants
SERVER_PORT = 2077
ACTUAL_BUDGET_URL = os.environ.get("ACTUAL_BUDGET_URL", "https://localhost")
ACTUAL_BUDGET_FILE = os.environ.get("ACTUAL_BUDGET_FILE", "")
ACTUAL_CERT_PATH = os.environ.get("ACTUAL_CERT_PATH", "./certs/actual.pem")
APP_TITLE = "Banking Hub"

# SVG favicon: sync arrows with euro symbol (base64 encoded)
FAVICON_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="12" fill="#191919"/>
  <g fill="none" stroke="#da7756" stroke-width="3" stroke-linecap="round">
    <path d="M20 32a12 12 0 0 1 12-12"/>
    <path d="M32 16l5 4-5 4"/>
    <path d="M44 32a12 12 0 0 1-12 12"/>
    <path d="M32 48l-5-4 5-4"/>
  </g>
  <text x="32" y="38" text-anchor="middle" fill="#da7756" font-family="monospace" font-size="16" font-weight="bold">$</text>
</svg>'''

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
    .input-group, .modal-content, .card-body, [class*="input"], [class*="card"],
    [id*="input-container"] {
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


class ActivityIndicator:
    """Simple activity indicator using put_text (WebSocket-friendly)."""

    def __init__(self):
        self.active = False

    def start(self):
        """Show activity indicator."""
        if self.active:
            return
        self.active = True
        put_text("[...] processing")

    def stop(self):
        """Mark activity as stopped."""
        self.active = False


# Global activity indicator instance
activity_indicator = ActivityIndicator()


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
    # Account mapping for Actual Budget (legacy, kept for backward compatibility)
    account_mapping: dict = field(default_factory=lambda: {
        'ibercaja': 'Ibercaja común',
        'ing_nomina': 'ING Nómina',
        'ing_naranja': 'ING Naranja',
    })
    # Saved mappings from source to Actual Budget file and account
    file_mappings: dict = field(default_factory=dict)  # source -> file_name
    account_mappings_saved: dict = field(default_factory=dict)  # source -> account_name
    encryption_passwords: dict = field(default_factory=dict)  # file_name -> encryption_password
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

    def has_saved_mapping(self, source: str) -> bool:
        """Check if a source has saved file and account mapping."""
        return source in self.file_mappings and source in self.account_mappings_saved

    def get_saved_file(self, source: str) -> Optional[str]:
        """Get saved file name for a source."""
        return self.file_mappings.get(source)

    def get_saved_account(self, source: str) -> Optional[str]:
        """Get saved account name for a source."""
        return self.account_mappings_saved.get(source)

    def get_saved_encryption(self, file_name: str) -> Optional[str]:
        """Get saved encryption password for a file."""
        return self.encryption_passwords.get(file_name)

    def save_mapping(self, source: str, file_name: str, account_name: str, encryption_password: Optional[str] = None) -> None:
        """Save mapping from source to file and account."""
        self.file_mappings[source] = file_name
        self.account_mappings_saved[source] = account_name
        if encryption_password:
            self.encryption_passwords[file_name] = encryption_password

    def clear_saved_mappings(self) -> None:
        """Clear all saved mappings."""
        self.file_mappings.clear()
        self.account_mappings_saved.clear()
        self.encryption_passwords.clear()


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

    # App URL schemes and fallbacks
    APP_LINKS = {
        'ing': {
            'fallback': 'https://ing.es',  # ING website (opens app if installed)
            'label': 'Abrir app ING'
        }
    }

    def write(self, message: str) -> int:
        if message and message.strip():
            stripped = message.strip()

            # Check for app open marker: OPEN_APP:appname:
            if stripped.startswith("OPEN_APP:") and stripped.endswith(":"):
                app_name = stripped.replace("OPEN_APP:", "").rstrip(":")
                if app_name in self.APP_LINKS:
                    app_info = self.APP_LINKS[app_name]
                    # Create clickable link styled like app buttons
                    put_html(f'''
                        <div style="margin: 10px 0;">
                            <a href="{app_info['fallback']}"
                               target="_blank"
                               style="display: inline-block; background: transparent; color: #da7756;
                                      text-decoration: none; font-family: monospace; padding: 0; margin-right: 1em;">
                                [{app_info['label']}]
                            </a>
                            <span style="color: #888; font-size: 12px;">
                                Vuelve aquí tras aprobar
                            </span>
                        </div>
                    ''')
                    auto_scroll()
                    return len(message)

            put_text(stripped)
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
        pin_digits = pyi_input(
            type='password',
            other_html_attrs={'inputmode': 'numeric', 'pattern': '[0-9]*'}
        )
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
        state.ing_dni = pyi_input(
            type='password',
            other_html_attrs={'inputmode': 'numeric', 'pattern': '[0-9]*'}
        )
        state.advance()
        return state.ing_dni

    elif cred_type == CredentialType.DIA:
        if state.ing_dia:
            put_text(f"Using stored day: {state.ing_dia}")
            state.advance()
            return state.ing_dia
        state.ing_dia = pyi_input(
            type='password',
            other_html_attrs={'inputmode': 'numeric', 'pattern': '[0-9]*'}
        )
        state.advance()
        return state.ing_dia

    elif cred_type == CredentialType.MES:
        if state.ing_mes:
            put_text(f"Using stored month: {state.ing_mes}")
            state.advance()
            return state.ing_mes
        state.ing_mes = pyi_input(
            type='password',
            other_html_attrs={'inputmode': 'numeric', 'pattern': '[0-9]*'}
        )
        state.advance()
        return state.ing_mes

    elif cred_type == CredentialType.ANO:
        if state.ing_ano:
            put_text(f"Using stored year: {state.ing_ano}")
            state.advance()
            return state.ing_ano
        state.ing_ano = pyi_input(
            type='password',
            other_html_attrs={'inputmode': 'numeric', 'pattern': '[0-9]*'}
        )
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
        activity_indicator.start()  # Start activity indicator
        sys.stdout = LogCapture()

        with patch('getpass.getpass', side_effect=dynamic_getpass_ibercaja):
            with sync_playwright() as playwright:
                print("[WEBUI] Starting Ibercaja download...")
                ibercaja.run(playwright)
                print("[WEBUI] Ibercaja completed")

        sys.stdout = old_stdout
        activity_indicator.stop()  # Stop activity indicator
        put_text("[PROCESS] Download completed. Files in ./downloads/ibercaja")

    except Exception as e:
        sys.stdout = old_stdout
        activity_indicator.stop()  # Stop activity indicator on error
        put_text(f"[ERROR] {str(e)}")
        put_text(traceback.format_exc())


def execute_ing() -> None:
    """Execute ING download."""
    put_text("---")
    put_text("execution log:")
    
    state.setup_ing_queue()
    old_stdout = sys.stdout

    try:
        activity_indicator.start()  # Start activity indicator
        sys.stdout = LogCapture()

        with patch('getpass.getpass', side_effect=dynamic_getpass_ing):
            with sync_playwright() as playwright:
                print("[WEBUI] Starting ING download...")
                ing.run(playwright)
                print("[WEBUI] ING completed")

        sys.stdout = old_stdout
        activity_indicator.stop()  # Stop activity indicator
        put_text("[PROCESS] Download completed. Files in ./downloads/ing")

    except Exception as e:
        sys.stdout = old_stdout
        activity_indicator.stop()  # Stop activity indicator on error
        put_text(f"[ERROR] {str(e)}")
        put_text(traceback.format_exc())


def request_actual_server_password() -> bool:
    """Request Actual Budget server password if not stored."""
    if not state.has_actual_credentials():
        put_text("> Actual Budget server password:")
        state.actual_password = pyi_input(type='password')
        if not state.actual_password:
            put_text("[ERROR] Password is required")
            return False

    return True


def request_file_encryption_password(file_name: str) -> Optional[str]:
    """Request encryption password for a specific budget file."""
    # Check if we have a saved encryption password for this file
    saved_encryption = state.get_saved_encryption(file_name)
    if saved_encryption:
        put_text(f"> Using saved encryption key for '{file_name}'")
        return saved_encryption

    put_text(f"> Encryption key for '{file_name}' (leave empty if none):")
    blur_active_element()
    encryption = pyi_input(type='password')
    return encryption if encryption else None


def select_file_and_account(source: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Select budget file and account for a source, using saved mappings if available.

    Returns:
        Tuple of (selected_file, selected_account, encryption_password) or (None, None, None) if cancelled
    """
    # Check if we have saved mappings
    if state.has_saved_mapping(source):
        saved_file = state.get_saved_file(source)
        saved_account = state.get_saved_account(source)
        put_text(f"[SAVED] File: {saved_file}")
        put_text(f"[SAVED] Account: {saved_account}")
        put_text("> Use saved mapping?")
        blur_active_element()
        use_saved = select(
            label="",
            options=[
                ('Yes, use saved mapping', True),
                ('No, select different file/account', False)
            ]
        )

        if use_saved:
            # Get encryption password for saved file
            saved_encryption = state.get_saved_encryption(saved_file)
            if saved_encryption:
                put_text(f"[SYNC] Using saved encryption for '{saved_file}'")
            return saved_file, saved_account, saved_encryption

    # List available budget files
    put_text("[SYNC] Fetching available budget files...")
    budget_files = actual_sync.list_budget_files(
        base_url=ACTUAL_BUDGET_URL,
        password=state.actual_password
    )

    if not budget_files:
        put_text("[ERROR] No budget files found or connection failed")
        return None, None, None

    # Check if ACTUAL_BUDGET_FILE env var is set (Home Assistant compatibility)
    default_file = None
    if ACTUAL_BUDGET_FILE:
        # Try to find a matching file
        for f in budget_files:
            if f['name'] == ACTUAL_BUDGET_FILE or f['file_id'] == ACTUAL_BUDGET_FILE:
                default_file = f['name']
                put_text(f"[HA CONFIG] Found configured file: {default_file}")
                break

    # Let user select budget file
    if default_file and len(budget_files) > 1:
        put_text("> Select budget file (Home Assistant default pre-selected):")
    else:
        put_text("> Select budget file:")

    blur_active_element()

    # Set default option if found
    file_options = [(f['name'], f['name']) for f in budget_files]
    if default_file:
        # Move default to the top of the list
        file_options = [(default_file, default_file)] + [(f['name'], f['name']) for f in budget_files if f['name'] != default_file]

    selected_file = select(
        label="",
        options=file_options
    )

    if not selected_file:
        put_text("[ERROR] No file selected")
        return None, None, None

    put_text(f"[SYNC] Selected file: {selected_file}")

    # Request encryption password for this specific file
    file_encryption_password = request_file_encryption_password(selected_file)

    # List available accounts in the selected file
    put_text("[SYNC] Fetching available accounts...")
    accounts = actual_sync.list_accounts(
        base_url=ACTUAL_BUDGET_URL,
        password=state.actual_password,
        file_name=selected_file,
        encryption_password=file_encryption_password
    )

    if not accounts:
        put_text("[ERROR] No accounts found or connection failed")
        return None, None, None

    # Check if there's a legacy account mapping for this source (Home Assistant compatibility)
    default_account = state.account_mapping.get(source)
    matching_account = None
    if default_account:
        for acc in accounts:
            if acc['name'] == default_account:
                matching_account = default_account
                put_text(f"[HA CONFIG] Found configured account: {matching_account}")
                break

    # Let user select account
    if matching_account and len(accounts) > 1:
        put_text("> Select target account (Home Assistant default pre-selected):")
    else:
        put_text("> Select target account:")

    blur_active_element()

    # Set default option if found
    account_options = [(a['name'], a['name']) for a in accounts]
    if matching_account:
        # Move default to the top of the list
        account_options = [(matching_account, matching_account)] + [(a['name'], a['name']) for a in accounts if a['name'] != matching_account]

    selected_account = select(
        label="",
        options=account_options
    )

    if not selected_account:
        put_text("[ERROR] No account selected")
        return None, None, None

    put_text(f"[SYNC] Target account: {selected_account}")

    return selected_file, selected_account, file_encryption_password


def execute_sync_ibercaja() -> None:
    """Sync Ibercaja CSV to Actual Budget."""
    put_text("---")
    put_text("sync to actual budget:")

    # Request server password only
    if not request_actual_server_password():
        return

    csv_path = actual_sync.get_latest_csv('ibercaja')
    if not csv_path:
        put_text("[ERROR] No CSV found. Download movements first.")
        return

    put_text(f"[SYNC] CSV: {csv_path}")

    # Select file and account (using saved mappings if available)
    selected_file, selected_account, file_encryption_password = select_file_and_account('ibercaja')

    if not selected_file or not selected_account:
        return

        activity_indicator.start()  # Start activity indicator

    result = actual_sync.sync_csv_to_actual(
        csv_path=csv_path,
        source='ibercaja',
        base_url=ACTUAL_BUDGET_URL,
        password=state.actual_password,
        encryption_password=file_encryption_password,
        file_name=selected_file,
        account_name=selected_account,
        cert_path=ACTUAL_CERT_PATH
    )

    activity_indicator.stop()  # Stop activity indicator

    if result.success:
        put_text(f"[OK] {result.message}")
        if result.errors:
            for err in result.errors[:5]:
                put_text(f"[WARN] {err}")

        # Save mapping for future use
        state.save_mapping('ibercaja', selected_file, selected_account, file_encryption_password)
        put_text("[SAVED] File and account mapping saved for future syncs")
    else:
        put_text(f"[ERROR] {result.message}")


def execute_sync_ing(account_type: str) -> None:
    """Sync ING CSV to Actual Budget."""
    put_text("---")
    put_text(f"sync to actual budget ({account_type}):")

    # Request server password only
    if not request_actual_server_password():
        return

    source = f'ing_{account_type}'
    csv_path = actual_sync.get_latest_csv(source)
    if not csv_path:
        put_text(f"[ERROR] No CSV found for {account_type}. Download movements first.")
        return

    put_text(f"[SYNC] CSV: {csv_path}")

    # Select file and account (using saved mappings if available)
    selected_file, selected_account, file_encryption_password = select_file_and_account(source)

    if not selected_file or not selected_account:
        return

        activity_indicator.start()  # Start activity indicator

    result = actual_sync.sync_csv_to_actual(
        csv_path=csv_path,
        source=source,
        base_url=ACTUAL_BUDGET_URL,
        password=state.actual_password,
        encryption_password=file_encryption_password,
        file_name=selected_file,
        account_name=selected_account,
        cert_path=ACTUAL_CERT_PATH
    )

    activity_indicator.stop()  # Stop activity indicator

    if result.success:
        put_text(f"[OK] {result.message}")
        if result.errors:
            for err in result.errors[:5]:
                put_text(f"[WARN] {err}")

        # Save mapping for future use
        state.save_mapping(source, selected_file, selected_account, file_encryption_password)
        put_text("[SAVED] File and account mapping saved for future syncs")
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

    if state.has_saved_mapping('ibercaja'):
        saved_file = state.get_saved_file('ibercaja')
        saved_account = state.get_saved_account('ibercaja')
        put_text(f"[ok] sync mapping: {saved_file} -> {saved_account}")
    else:
        put_text("[--] no sync mapping saved")

    # Scheduler status
    put_text("")
    sched_status = ibercaja_scheduler.get_status()
    if sched_status['enabled']:
        put_text(f"[ok] auto-sync: every {sched_status['interval']}")
        if sched_status['next_run']:
            put_text(f"     next run: {sched_status['next_run']}")
        if sched_status['last_run']:
            put_text(f"     last run: {sched_status['last_run']}")
        if sched_status['last_result']:
            put_text(f"     result: {sched_status['last_result']}")
    else:
        put_text("[--] auto-sync: disabled")

    put_text("")
    put_buttons(
        [
            {'label': '[start download]', 'value': 'download'},
            {'label': '[upload xlsx]', 'value': 'upload'},
            {'label': '[sync to actual]', 'value': 'sync'},
        ],
        onclick=handle_ibercaja_action
    )
    put_text("")

    # Scheduler buttons
    if sched_status['enabled']:
        put_buttons(
            [
                {'label': '[stop auto-sync]', 'value': 'sched_stop'},
                {'label': '[run now]', 'value': 'sched_run_now'},
            ],
            onclick=handle_ibercaja_action
        )
    else:
        put_buttons(
            [
                {'label': '[auto-sync 1h]', 'value': 'sched_1h'},
                {'label': '[auto-sync 3h]', 'value': 'sched_3h'},
                {'label': '[auto-sync 6h]', 'value': 'sched_6h'},
                {'label': '[auto-sync 12h]', 'value': 'sched_12h'},
                {'label': '[auto-sync 24h]', 'value': 'sched_24h'},
            ],
            onclick=handle_ibercaja_action
        )

    put_text("")
    put_buttons(
        [{'label': '[back]', 'value': 'back'}],
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

    # Show saved mappings
    if state.has_saved_mapping('ing_nomina'):
        saved_file = state.get_saved_file('ing_nomina')
        saved_account = state.get_saved_account('ing_nomina')
        put_text(f"[ok] nómina mapping: {saved_file} -> {saved_account}")
    else:
        put_text("[--] no nómina mapping saved")

    if state.has_saved_mapping('ing_naranja'):
        saved_file = state.get_saved_file('ing_naranja')
        saved_account = state.get_saved_account('ing_naranja')
        put_text(f"[ok] naranja mapping: {saved_file} -> {saved_account}")
    else:
        put_text("[--] no naranja mapping saved")

    put_text("")
    put_buttons(
        [
            {'label': '[start download]', 'value': 'download'},
            {'label': '[upload nómina xlsx]', 'value': 'upload_nomina'},
            {'label': '[upload naranja xlsx]', 'value': 'upload_naranja'},
            {'label': '[sync nómina]', 'value': 'sync_nomina'},
            {'label': '[sync naranja]', 'value': 'sync_naranja'},
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
    elif action == 'back':
        show_menu()
    # Scheduler actions
    elif action == 'sched_stop':
        ibercaja_scheduler.stop()
        put_text("[SCHEDULER] Auto-sync stopped")
        show_ibercaja()
    elif action == 'sched_run_now':
        put_text("[SCHEDULER] Running sync now...")
        threading.Thread(target=ibercaja_scheduler._run_and_schedule, daemon=True).start()
        put_text("[SCHEDULER] Sync started in background")
    elif action.startswith('sched_'):
        interval = action.replace('sched_', '')
        # Check prerequisites before starting
        if not state.has_ibercaja_credentials():
            put_text("[ERROR] Store Ibercaja credentials first (run download once)")
            return
        if not state.has_actual_credentials():
            put_text("[ERROR] Store Actual Budget password first (run sync once)")
            return
        if not state.has_saved_mapping('ibercaja'):
            put_text("[ERROR] Configure sync mapping first (run sync once)")
            return

        if ibercaja_scheduler.start(interval, run_now=True):
            put_text(f"[SCHEDULER] Auto-sync enabled: every {interval}")
            put_text("[SCHEDULER] First sync running now...")
            show_ibercaja()
        else:
            put_text(f"[ERROR] Invalid interval: {interval}")


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
    elif action == 'back':
        show_menu()


def handle_menu_selection(bank: str) -> None:
    """Handle bank selection from main menu."""
    if bank == 'ibercaja':
        show_ibercaja()
    elif bank == 'ing':
        show_ing()
    elif bank == 'credentials':
        show_credentials_management()


def inject_styles() -> None:
    """Inject CSS styles and favicon to prevent FOUC (Flash of Unstyled Content)."""
    import base64
    favicon_b64 = base64.b64encode(FAVICON_SVG.encode()).decode()

    # JavaScript to handle WebSocket reconnection on mobile Safari
    # When user switches apps (e.g., to bank app for 2FA), the WebSocket may drop
    reconnect_script = '''
    <script>
    (function() {
        let hiddenTime = null;
        let reconnectBanner = null;
        let checkInterval = null;

        function createReconnectBanner() {
            if (reconnectBanner) return;
            reconnectBanner = document.createElement('div');
            reconnectBanner.id = 'reconnect-banner';
            reconnectBanner.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                background: #da7756;
                color: #191919;
                text-align: center;
                padding: 10px;
                font-family: monospace;
                z-index: 9999;
                cursor: pointer;
            `;
            reconnectBanner.innerHTML = 'Connection interrupted. <strong>Tap to dismiss</strong> or wait for auto-reconnect...';
            reconnectBanner.onclick = function() { removeReconnectBanner(); };
            document.body.insertBefore(reconnectBanner, document.body.firstChild);

            // Monitor WebSocket state and remove banner when connection is restored
            if (checkInterval) clearInterval(checkInterval);
            checkInterval = setInterval(function() {
                // Check multiple ways to detect reconnection
                const wsReady = window.WebIO && window.WebIO.session &&
                               window.WebIO.session._ws &&
                               window.WebIO.session._ws.readyState === WebSocket.OPEN;
                if (wsReady) {
                    removeReconnectBanner();
                }
            }, 1000);

            // Clear interval after 60 seconds
            setTimeout(function() {
                if (checkInterval) clearInterval(checkInterval);
                checkInterval = null;
            }, 60000);
        }

        function removeReconnectBanner() {
            if (checkInterval) {
                clearInterval(checkInterval);
                checkInterval = null;
            }
            const banner = document.getElementById('reconnect-banner');
            if (banner) banner.remove();
            reconnectBanner = null;
        }

        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                hiddenTime = Date.now();
            } else {
                if (hiddenTime && (Date.now() - hiddenTime) > 5000) {
                    setTimeout(function() {
                        const wsReady = window.WebIO && window.WebIO.session &&
                                       window.WebIO.session._ws &&
                                       window.WebIO.session._ws.readyState === WebSocket.OPEN;
                        if (!wsReady) {
                            createReconnectBanner();
                        }
                    }, 500);
                }
                hiddenTime = null;
            }
        });
    })();
    </script>
    '''

    put_html(f'''
        <style>{CSS_THEME}</style>
        <link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,{favicon_b64}">
        {reconnect_script}
    ''')


def show_credentials_management() -> None:
    """Show credentials and mappings management interface."""
    clear()
    inject_styles()
    put_text("credentials & mappings")
    put_text("----------------------")
    put_text("")

    # Show Ibercaja credentials status
    put_text("ibercaja:")
    if state.has_ibercaja_credentials():
        put_text("  [ok] credentials stored")
    else:
        put_text("  [--] no credentials stored")

    if state.has_saved_mapping('ibercaja'):
        saved_file = state.get_saved_file('ibercaja')
        saved_account = state.get_saved_account('ibercaja')
        put_text(f"  [ok] sync mapping: {saved_file} -> {saved_account}")
    else:
        put_text("  [--] no sync mapping saved")

    put_text("")

    # Show ING credentials status
    put_text("ing:")
    if state.has_ing_credentials():
        put_text("  [ok] credentials stored")
    else:
        put_text("  [--] no credentials stored")

    if state.has_saved_mapping('ing_nomina'):
        saved_file = state.get_saved_file('ing_nomina')
        saved_account = state.get_saved_account('ing_nomina')
        put_text(f"  [ok] nómina mapping: {saved_file} -> {saved_account}")
    else:
        put_text("  [--] no nómina mapping saved")

    if state.has_saved_mapping('ing_naranja'):
        saved_file = state.get_saved_file('ing_naranja')
        saved_account = state.get_saved_account('ing_naranja')
        put_text(f"  [ok] naranja mapping: {saved_file} -> {saved_account}")
    else:
        put_text("  [--] no naranja mapping saved")

    put_text("")

    # Show Actual Budget credentials status
    put_text("actual budget:")
    if state.has_actual_credentials():
        put_text("  [ok] server password stored")
    else:
        put_text("  [--] no server password stored")

    put_text("")
    put_buttons(
        [
            {'label': '[clear ibercaja]', 'value': 'clear_ibercaja'},
            {'label': '[clear ing]', 'value': 'clear_ing'},
            {'label': '[clear actual]', 'value': 'clear_actual'},
            {'label': '[clear all mappings]', 'value': 'clear_mappings'},
            {'label': '[clear everything]', 'value': 'clear_all'},
            {'label': '[back]', 'value': 'back'}
        ],
        onclick=handle_credentials_action
    )


def handle_credentials_action(action: str) -> None:
    """Handle credentials management actions."""
    if action == 'clear_ibercaja':
        state.clear_ibercaja()
        put_text("[SYSTEM] Ibercaja credentials cleared")
        show_credentials_management()
    elif action == 'clear_ing':
        state.clear_ing()
        put_text("[SYSTEM] ING credentials cleared")
        show_credentials_management()
    elif action == 'clear_actual':
        state.clear_actual()
        put_text("[SYSTEM] Actual Budget credentials cleared")
        show_credentials_management()
    elif action == 'clear_mappings':
        state.clear_saved_mappings()
        put_text("[SYSTEM] All saved file and account mappings cleared")
        show_credentials_management()
    elif action == 'clear_all':
        state.clear_all()
        state.clear_saved_mappings()
        put_text("[SYSTEM] All credentials and mappings cleared")
        show_credentials_management()
    elif action == 'back':
        show_menu()


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
            {'label': '[ing]', 'value': 'ing'},
            {'label': '[manage credentials]', 'value': 'credentials'}
        ],
        onclick=handle_menu_selection
    )


def main() -> None:
    """Main entry point for the PyWebIO application."""
    config(title=APP_TITLE, css_style=CSS_THEME)
    show_menu()


if __name__ == "__main__":
    start_server(main, port=SERVER_PORT, debug=False, reconnect_timeout=60)
