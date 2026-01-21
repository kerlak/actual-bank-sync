"""Web UI for Ibercaja movements downloader using PyWebIO."""

import io
import sys
import traceback
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
from unittest.mock import patch

from pywebio import config, start_server
from pywebio.input import input as pyi_input
from pywebio.output import put_buttons, put_html, put_text
from playwright.sync_api import sync_playwright

from app import run as run_app

# Constants
SERVER_PORT = 2077

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


class CredentialType(Enum):
    """Identifies which credential is being requested."""
    CODIGO = auto()
    CLAVE = auto()


@dataclass
class CredentialStore:
    """Encapsulates credential storage and request tracking."""

    codigo: Optional[str] = field(default=None)
    clave: Optional[str] = field(default=None)
    _next_request: CredentialType = field(default=CredentialType.CODIGO)

    def has_credentials(self) -> bool:
        """Check if both credentials are stored."""
        return self.codigo is not None and self.clave is not None

    def clear(self) -> None:
        """Clear all stored credentials and reset request order."""
        self.codigo = None
        self.clave = None
        self._next_request = CredentialType.CODIGO

    def get_next_type(self) -> CredentialType:
        """Get the type of the next credential to be requested."""
        return self._next_request

    def advance_request(self) -> None:
        """Move to the next credential in the request sequence."""
        if self._next_request == CredentialType.CODIGO:
            self._next_request = CredentialType.CLAVE
        else:
            self._next_request = CredentialType.CODIGO


# Global credential store instance
credential_store = CredentialStore()


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
        """Write message to the UI."""
        if message and message.strip():
            put_text(message.rstrip())
            auto_scroll()
        return len(message)

    def flush(self) -> None:
        """Flush the buffer (no-op for this implementation)."""
        pass


def dynamic_getpass(prompt: str = "") -> str:
    """Replace getpass to request input dynamically from the UI.

    Uses request order tracking instead of parsing prompt text.
    """
    if prompt:
        put_text(f"> {prompt.strip()}")

    blur_active_element()

    credential_type = credential_store.get_next_type()

    if credential_type == CredentialType.CODIGO:
        if credential_store.codigo:
            put_text(f"Using stored identification code: {'*' * len(credential_store.codigo)}")
            credential_store.advance_request()
            return credential_store.codigo
        else:
            credential_store.codigo = pyi_input(type='password')
            credential_store.advance_request()
            return credential_store.codigo

    else:  # CredentialType.CLAVE
        if credential_store.clave:
            put_text(f"Using stored access key: {'*' * len(credential_store.clave)}")
            credential_store.advance_request()
            return credential_store.clave
        else:
            credential_store.clave = pyi_input(type='password')
            credential_store.advance_request()
            return credential_store.clave


def clear_credentials() -> None:
    """Clear stored credentials and notify user."""
    credential_store.clear()
    put_text("[SYSTEM] Credentials cleared. Next execution will prompt for new credentials.")


def execute_download() -> None:
    """Execute the download process when user clicks the link."""
    put_text("---")
    put_text("execution log:")

    # Reset request order for new download
    credential_store._next_request = CredentialType.CODIGO

    old_stdout = sys.stdout

    try:
        sys.stdout = LogCapture()

        with patch('getpass.getpass', side_effect=dynamic_getpass):
            with sync_playwright() as playwright:
                print("[WEBUI] Calling run_app...")
                run_app(playwright)
                print("[WEBUI] run_app completed")

        sys.stdout = old_stdout
        print("[WEBUI] Process completed successfully")
        put_text("[PROCESS] Download completed successfully. Files available in ./downloads")

    except Exception as e:
        sys.stdout = old_stdout
        print(f"[WEBUI] Error: {str(e)}")
        put_text(f"[ERROR] Error during execution: {str(e)}")
        put_text(traceback.format_exc())


def handle_button_click(action: str) -> None:
    """Handle button clicks for main actions."""
    if action == 'download':
        execute_download()
    elif action == 'clear':
        clear_credentials()


def main() -> None:
    """Main entry point for the PyWebIO application."""
    config(title="ibercaja", css_style=CSS_THEME)

    blur_active_element()

    put_text("ibercaja movements downloader")
    put_text("----------------------------")
    put_text("")

    if credential_store.has_credentials():
        put_text("[ok] credentials stored")
    else:
        put_text("[--] no credentials stored")

    put_text("")
    put_buttons(
        [
            {'label': '[start download]', 'value': 'download'},
            {'label': '[clear credentials]', 'value': 'clear'}
        ],
        onclick=handle_button_click
    )


if __name__ == "__main__":
    start_server(main, port=SERVER_PORT, debug=False)
