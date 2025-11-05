"""
app.py
Versión integrada: sirve API, frontend y archivos estáticos con CORS.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from api.routes import router

# ---------------------------------------------------------------------
# Instancia de FastAPI
# ---------------------------------------------------------------------

app = FastAPI(
    title="Sistema Experto de Diagnóstico de Máquinas Big Tools",
    description="API para diagnosticar fallas en máquinas y ofrecer posibles soluciones",
    version="1.0.0",
)

# ---------------------------------------------------------------------
# Configuración CORS
# ---------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Permite cualquier origen, útil para desarrollo.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------
# Inclusión de rutas de la API
# ---------------------------------------------------------------------

app.include_router(router)

# ---------------------------------------------------------------------
# Configuración de archivos estáticos del Frontend
# ---------------------------------------------------------------------

# Ajusta estas rutas si la estructura de tu proyecto cambia
frontend_path = Path(__file__).parent.parent / "Frontend"
manuales_path = Path(__file__).parent / "data" / "manuales_pdf"

app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
app.mount("/manuales", StaticFiles(directory=str(manuales_path)), name="manuales")

# ---------------------------------------------------------------------
# Rutas para servir páginas del frontend (solo si necesitas estas URLs)
# ---------------------------------------------------------------------

@app.get("/")
def root():
    """Devuelve la página principal de tu frontend."""
    return FileResponse(str(frontend_path / "index.html"))

@app.get("/admin")
def admin():
    """Devuelve la página de administración si la tienes."""
    return FileResponse(str(frontend_path / "admin.html"))
