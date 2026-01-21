"""Web UI for Ibercaja movements downloader using PyWebIO."""

import io
import sys
import traceback
from dataclasses import dataclass, field
from typing import Optional
from unittest.mock import patch

from pywebio import config, start_server
from pywebio.input import input as pyi_input
from pywebio.output import put_button, put_html, put_markdown, put_text
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
        put_markdown(f"**{prompt.strip()}**")

    # Determine which credential is being requested
    prompt_lower = prompt.lower()

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
    """Execute the download process when user clicks the button."""
    put_markdown("---")
    put_markdown("## Execution log")

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
        title="Ibercaja Movements Downloader",
        css_style="footer, .pywebio-footer, [class*='footer'] { display: none !important; }"
    )

    put_markdown("# Ibercaja Movements Downloader")
    put_markdown("Click the button below to start the download process.")
    put_markdown("The application will request your credentials when needed.")
    put_markdown("")

    # Show credential status
    if credential_store.has_credentials():
        put_text("[OK] Credentials stored in memory")
    else:
        put_text("[INFO] No credentials stored yet")

    put_markdown("")

    put_button("START DOWNLOAD", onclick=execute_download)
    put_button("CLEAR CREDENTIALS", onclick=clear_credentials)


if __name__ == "__main__":
    start_server(main, port=SERVER_PORT, debug=False)
