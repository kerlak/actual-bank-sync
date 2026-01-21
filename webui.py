import sys
import io
from unittest.mock import patch
from pywebio.input import input as pyi_input
from pywebio.output import put_markdown, put_text, put_button
from playwright.sync_api import sync_playwright
from app import run as run_app


# Variables globales para almacenar credenciales en memoria
stored_credentials = {
    "codigo": None,
    "clave": None
}


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
    
    # Determinar qué credencial se está pidiendo
    if "Identification" in prompt or "identificación" in prompt.lower():
        if stored_credentials["codigo"]:
            put_text(f"Using stored identification code: {'*' * len(stored_credentials['codigo'])}")
            return stored_credentials["codigo"]
        else:
            codigo = pyi_input(type='password')
            stored_credentials["codigo"] = codigo
            return codigo
    elif "Access" in prompt or "acceso" in prompt.lower():
        if stored_credentials["clave"]:
            put_text(f"Using stored access key: {'*' * len(stored_credentials['clave'])}")
            return stored_credentials["clave"]
        else:
            clave = pyi_input(type='password')
            stored_credentials["clave"] = clave
            return clave
    else:
        return pyi_input(type='password')


def clear_credentials():
    """Limpia las credenciales almacenadas"""
    global stored_credentials
    stored_credentials["codigo"] = None
    stored_credentials["clave"] = None
    put_text("[SYSTEM] Credentials cleared. Next execution will prompt for new credentials.")


def execute_download():
    """Ejecuta la descarga cuando el usuario hace click en el botón"""
    put_markdown("---")
    put_markdown("## Execution log...")
    
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
        put_text("[PROCESS] ✓ Download completed successfully. Files available in ./downloads")
    
    except Exception as e:
        sys.stdout = old_stdout
        print(f"[WEBUI] Error: {str(e)}")
        put_text(f"[ERROR] ✗ Error during execution: {str(e)}")
        import traceback
        put_text(traceback.format_exc())


def main():
    from pywebio import config
    config(title="Ibercaja Movements Downloader")
    
    put_markdown("# Ibercaja Movements Downloader")
    put_markdown("Click the button below to start the download process.")
    put_markdown("The application will request your credentials when needed.")
    put_markdown("")
    
    # Mostrar estado de credenciales
    if stored_credentials["codigo"] and stored_credentials["clave"]:
        put_text("✓ Credentials stored in memory")
    else:
        put_text("⚠ No credentials stored yet")
    
    put_markdown("")
    
    put_button("▶ START DOWNLOAD", onclick=execute_download)
    put_button("✗ CLEAR CREDENTIALS", onclick=clear_credentials)


if __name__ == "__main__":
    from pywebio import start_server
    start_server(main, port=2077, debug=False)



