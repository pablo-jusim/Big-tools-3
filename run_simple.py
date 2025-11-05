"""
run_simple.py
Script Python para iniciar el backend y abrir el frontend automáticamente.
Funciona en Windows, Linux y Mac.
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

try:
    import requests
except ImportError:
    print("Instala requests para logout global: pip install requests")
    requests = None

def print_banner():
    print("=" * 50)
    print("    Big Tools - Sistema Experto")
    print("=" * 50)
    print()

def check_python():
    print("[1/4] Verificando Python...")
    print(f"✓ Python {sys.version.split()[0]} detectado")
    print()

def install_dependencies():
    print("[2/4] Verificando dependencias...")
    try:
        import fastapi
        import uvicorn
        print("✓ Dependencias verificadas correctamente")
    except ImportError:
        print("⚠ Instalando dependencias...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencias instaladas")
    print()

def start_backend():
    print("[3/4] Iniciando Backend (FastAPI)...")
    print("Backend ejecutándose en: http://127.0.0.1:8000")
    print()
    backend_path = Path(__file__).parent / "Backend"
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app", "--reload", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(backend_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    return process

def open_frontend():
    print("[4/4] Abriendo Frontend en el navegador...")
    print()
    time.sleep(3)  # Esperar a que backend levante
    webbrowser.open("http://127.0.0.1:8000/")
    print("=" * 50)
    print("  Sistema iniciado correctamente!")
    print("=" * 50)
    print()
    print("  - Backend (API): http://127.0.0.1:8000")
    print("  - Frontend (Chatbot): Frontend/index.html")
    print("  - Dashboard Admin: Frontend/admin.html")
    print()
    print("  Credenciales de Admin:")
    print("    Usuario: admin")
    print("    Contraseña: 1234")
    print()
    print("=" * 50)
    print()
    print("Presiona Ctrl+C para detener el sistema...")
    print()

def reset_tokens_backend():
    if requests is None:
        print("No se puede limpiar tokens: requests no disponible.")
        return
    try:
        print("[*] Invalidando las sesiones (tokens) del backend...")
        r = requests.post("http://127.0.0.1:8000/api/admin/reset_tokens")
        if r.ok:
            print("[*] Tokens limpiados correctamente.")
        else:
            print("[!] El endpoint respondió error.")
    except Exception as e:
        print("[!] Error al intentar limpiar tokens:", e)

def main():
    try:
        print_banner()
        check_python()
        install_dependencies()
        backend_process = start_backend()
        open_frontend()
        try:
            backend_process.wait()
        except KeyboardInterrupt:
            print("\n\n⚠ Deteniendo el sistema...")
            reset_tokens_backend()
            backend_process.terminate()
            backend_process.wait()
            print("✓ Sistema detenido correctamente.")
            print()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPor favor, verifica que todas las dependencias estén instaladas:")
        print("  pip install -r requirements.txt")
        print()
        sys.exit(1)

if __name__ == "__main__":
    main()
