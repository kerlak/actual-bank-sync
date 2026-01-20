import sys
from unittest.mock import patch
from pywebio.input import input as pyi_input
from pywebio.output import put_markdown, put_text, put_error, put_success
from playwright.sync_api import sync_playwright
from app import run as run_app


def dynamic_getpass(prompt=""):
    """Reemplaza getpass para solicitar entrada dinámicamente desde la UI"""
    if prompt:
        put_markdown(f"**{prompt.strip()}**")
    return pyi_input(type='password')


def main():
    from pywebio import config
    config(title="Ibercaja Movements Downloader")
    
    put_markdown("# Ibercaja Movements Downloader")
    put_markdown("La aplicación solicitará tus credenciales cuando sea necesario.")
    put_markdown("---")
    put_markdown("## Ejecutando descarga...")
    print("[WEBUI] Iniciando ejecución...")
    
    try:
        # Reemplazar getpass.getpass con nuestra función personalizada
        with patch('getpass.getpass', side_effect=dynamic_getpass):
            with sync_playwright() as playwright:
                print("[WEBUI] Llamando a run_app...")
                run_app(playwright)
                print("[WEBUI] run_app completado")
        
        print("[WEBUI] Proceso finalizado exitosamente")
        put_success("✅ Descarga completada exitosamente. Archivos disponibles en ./downloads")
    
    except Exception as e:
        print(f"[WEBUI] Error: {str(e)}")
        put_error(f"❌ Error durante la ejecución: {str(e)}")
        import traceback
        put_text(traceback.format_exc())


if __name__ == "__main__":
    from pywebio import start_server
    start_server(main, port=2077, debug=False)


