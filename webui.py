"""Web UI for Ibercaja movements downloader using PyWebIO."""

import io
import sys
import traceback
from dataclasses import dataclass, field
from typing import Optional
from unittest.mock import patch

from pywebio import config, start_server
from pywebio.input import input as pyi_input
from pywebio.output import put_buttons, put_html, put_text
from playwright.sync_api import sync_playwright

from app import run as run_app

# Constants
SERVER_PORT = 2077


@dataclass
class CredentialStore:
    """Encapsulates credential storage and management."""

    codigo: Optional[str] = field(default=None)
    clave: Optional[str] = field(default=None)

    def has_credentials(self) -> bool:
        """Check if both credentials are stored."""
        return self.codigo is not None and self.clave is not None

    def clear(self) -> None:
        """Clear all stored credentials."""
        self.codigo = None
        self.clave = None


# Global credential store instance
credential_store = CredentialStore()


def auto_scroll() -> None:
    """Scroll to the bottom of the page and hide footer."""
    put_html("""<script>
    window.scrollTo(0, document.body.scrollHeight);
    document.querySelectorAll('footer, .pywebio-footer, [class*="footer"]').forEach(el => el.style.display = 'none');
    </script>""")


class LogCapture(io.StringIO):
    """Captures stdout and displays it in real-time in PyWebIO."""

    def write(self, message: str) -> int:
        """Write message to the UI.

        Args:
            message: The message to display.

        Returns:
            Length of the message.
        """
        if message and message.strip():
            put_text(message.rstrip())
            auto_scroll()
        return len(message)

    def flush(self) -> None:
        """Flush the buffer (no-op for this implementation)."""
        pass


def dynamic_getpass(prompt: str = "") -> str:
    """Replace getpass to request input dynamically from the UI.

    Args:
        prompt: The prompt message to display.

    Returns:
        The user-entered password or stored credential.
    """
    if prompt:
        put_text(f"> {prompt.strip()}")

    # Determine which credential is being requested
    prompt_lower = prompt.lower()

    # Remove autofocus from inputs on iOS - user must tap to get keyboard
    put_html('''<script>
        setTimeout(() => {
            document.querySelectorAll('input').forEach(i => i.blur());
        }, 100);
    </script>''')

    if "identification" in prompt_lower or "identificacion" in prompt_lower:
        if credential_store.codigo:
            put_text(f"Using stored identification code: {'*' * len(credential_store.codigo)}")
            return credential_store.codigo
        else:
            credential_store.codigo = pyi_input(type='password')
            return credential_store.codigo

    elif "access" in prompt_lower or "acceso" in prompt_lower:
        if credential_store.clave:
            put_text(f"Using stored access key: {'*' * len(credential_store.clave)}")
            return credential_store.clave
        else:
            credential_store.clave = pyi_input(type='password')
            return credential_store.clave

    else:
        return pyi_input(type='password')


def clear_credentials() -> None:
    """Clear stored credentials and notify user."""
    credential_store.clear()
    put_text("[SYSTEM] Credentials cleared. Next execution will prompt for new credentials.")


def execute_download() -> None:
    """Execute the download process when user clicks the link."""
    put_text("---")
    put_text("execution log:")

    old_stdout = sys.stdout

    try:
        # Redirect stdout to capture logs
        sys.stdout = LogCapture()

        # Replace getpass.getpass with our custom function
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


def main() -> None:
    """Main entry point for the PyWebIO application."""
    config(
        title="ibercaja",
        css_style="""
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
    )

    # Remove autofocus on mobile to prevent keyboard issues
    put_html('<script>setTimeout(() => document.activeElement?.blur(), 100);</script>')

    put_text("ibercaja movements downloader")
    put_text("----------------------------")
    put_text("")

    # Show credential status
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
        onclick=lambda val: execute_download() if val == 'download' else clear_credentials()
    )


if __name__ == "__main__":
    start_server(main, port=SERVER_PORT, debug=False)
