import sys
import io
from unittest.mock import patch
from pywebio.input import input as pyi_input
from pywebio.output import put_markdown, put_text, put_error, put_success
from playwright.sync_api import sync_playwright
from app import run as run_app


class LogCapture(io.StringIO):
    """Captura stdout y lo muestra en tiempo real en PyWebIO"""
    def write(self, message):
        if message and message.strip():
            put_text(message.rstrip())
        return len(message)
    
    def flush(self):
        pass


def dynamic_getpass(prompt=""):
    """Reemplaza getpass para solicitar entrada dinámicamente desde la UI"""
    if prompt:
        put_markdown(f"**{prompt.strip()}**")
    return pyi_input(type='password')


def main():
    from pywebio import config
    config(
        title="Ibercaja Movements Downloader",
        theme='dark',
        css_style="""
        body {
            background-color: #1e1e1e;
            color: #e0e0e0;
        }
        .container {
            background-color: #2d2d2d;
            border-radius: 8px;
            padding: 20px;
        }
        a {
            color: #4a9eff;
        }
        .btn {
            background-color: #0d47a1;
            border-color: #0d47a1;
            color: white;
        }
        .btn:hover {
            background-color: #1565c0;
            border-color: #1565c0;
        }
        input, textarea, select {
            background-color: #3d3d3d;
            color: #e0e0e0;
            border-color: #555;
        }
        .footer {
            display: none !important;
        }
        """
    )
    
    put_markdown("# Ibercaja Movements Downloader")
    put_markdown("The application will request your credentials when needed.")
    put_markdown("---")
    put_markdown("## Starting download...")
    put_markdown("```")
    
    try:
        # Capturar stdout
        old_stdout = sys.stdout
        sys.stdout = LogCapture()
        
        # Reemplazar getpass.getpass con nuestra función personalizada
        with patch('getpass.getpass', side_effect=dynamic_getpass):
            with sync_playwright() as playwright:
                print("[WEBUI] Calling run_app...")
                run_app(playwright)
                print("[WEBUI] run_app completed")
        
        sys.stdout = old_stdout
        print("[WEBUI] Process completed successfully")
        put_markdown("```")
        put_success("✅ Download completed successfully. Files available in ./downloads")
    
    except Exception as e:
        sys.stdout = old_stdout
        put_markdown("```")
        print(f"[WEBUI] Error: {str(e)}")
        put_error(f"❌ Error during execution: {str(e)}")
        import traceback
        put_text(traceback.format_exc())


if __name__ == "__main__":
    from pywebio import start_server
    start_server(main, port=2077, debug=False)



