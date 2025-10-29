"""
app.py
Entrada principal de la API del sistema experto.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Backend.api.routes import router

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

origins = [
    "*",  # Permite cualquier origen, útil para desarrollo. Ajustar en producción.
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------
# Inclusión de rutas
# ---------------------------------------------------------------------

app.include_router(router)

# ---------------------------------------------------------------------
# Ruta raíz opcional
# ---------------------------------------------------------------------

@app.get("/")
def root():
    return {"mensaje": "API del Sistema Experto activa"}
