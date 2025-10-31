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



import json
from pathlib import Path

app = FastAPI()
DATA_PATH = Path("data/base_conocimiento.json")

@app.post("/add_conocimiento")
async def add_conocimiento(request: Request):
    data = await request.json()
    manual = data.get("manual")
    causa = data.get("causa")
    falla = data.get("falla")
    solucion = data.get("solucion")
    try:
        bd = json.loads(DATA_PATH.read_text())
        # Buscar manual existente o crear uno nuevo
        for m in bd["manuales"]:
            if m["nombre"].lower() == manual.lower():
                m["items"].append({"causa": causa, "falla": falla, "solucion": solucion})
                break
        else:
            bd["manuales"].append({
                "nombre": manual,
                "items": [{"causa": causa, "falla": falla, "solucion": solucion}]
            })
        DATA_PATH.write_text(json.dumps(bd, indent=2, ensure_ascii=False))
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

