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
        """Check if both credentials are stored.

        Returns:
            True if both identification code and access key are stored.
        """
        return self.codigo is not None and self.clave is not None

    def clear(self) -> None:
        """Clear all stored credentials."""
        self.codigo = None
        self.clave = None

    def get_codigo(self) -> Optional[str]:
        """Get stored identification code.

        Returns:
            The stored identification code or None.
        """
        return self.codigo

    def set_codigo(self, value: str) -> None:
        """Store identification code.

        Args:
            value: The identification code to store.
        """
        self.codigo = value

    def get_clave(self) -> Optional[str]:
        """Get stored access key.

        Returns:
            The stored access key or None.
        """
        return self.clave

    def set_clave(self, value: str) -> None:
        """Store access key.

        Args:
            value: The access key to store.
        """
        self.clave = value


# Global credential store instance
credential_store = CredentialStore()


def auto_scroll() -> None:
    """Scroll to the bottom of the page for log visibility."""
    put_html("""<script>
    window.scrollTo(0, document.body.scrollHeight);
    </script>""")


def hide_footer() -> None:
    """Hide PyWebIO footer using CSS and JavaScript."""
    put_html("""<script>
    // CSS injection to hide footer
    const style = document.createElement('style');
    style.textContent = '.pywebio-footer { display: none !important; }';
    document.head.appendChild(style);
    // JavaScript removal as fallback
    const footer = document.querySelector('[id*="footer"]') || document.querySelector('.pywebio-footer');
    if (footer) footer.remove();
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
        stored = credential_store.get_codigo()
        if stored:
            put_text(f"Using stored identification code: {'*' * len(stored)}")
            return stored
        else:
            codigo = pyi_input(type='password')
            credential_store.set_codigo(codigo)
            return codigo

    elif "access" in prompt_lower or "acceso" in prompt_lower:
        stored = credential_store.get_clave()
        if stored:
            put_text(f"Using stored access key: {'*' * len(stored)}")
            return stored
        else:
            clave = pyi_input(type='password')
            credential_store.set_clave(clave)
            return clave

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
    config(title="Ibercaja Movements Downloader")

    # Hide PyWebIO footer
    hide_footer()

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
