"""
routes.py
Define las rutas de la API del sistema experto.
"""

from fastapi import APIRouter, HTTPException, Query
from Backend.api.base_conocimiento import BaseConocimiento
from Backend.api.engine import MotorInferencia

# ---------------------------------------------------------------------
# Inicialización
# ---------------------------------------------------------------------

router = APIRouter(prefix="/api", tags=["Sistema Experto"])

# Instancias globales
base = BaseConocimiento()
motor = MotorInferencia(base)

# Diccionario para almacenar sesiones activas por máquina (puede adaptarse según usuario si se quiere)
sesiones = {}

# ---------------------------------------------------------------------
# RUTAS
# ---------------------------------------------------------------------

@router.get("/")
def home():
    """
    Ruta base de la API.
    """
    return {"mensaje": "API del Sistema Experto activa"}


@router.get("/maquinas")
def listar_maquinas():
    """
    Lista todas las máquinas disponibles en la base de conocimiento.
    """
    maquinas = base.listar_maquinas()
    return {"maquinas": maquinas}


@router.post("/diagnosticar/iniciar/{nombre_maquina}")
def iniciar_diagnostico(nombre_maquina: str):
    """
    Inicia el diagnóstico de una máquina específica.
    Devuelve la primera pregunta u opciones para que el frontend la muestre.
    """
    try:
        motor.iniciar_diagnostico(nombre_maquina)
        nodo_actual = motor.nodo_actual
        if nodo_actual is None:
            return {"mensaje": "No se encontró una falla inicial."}

        # Guardamos la sesión
        sesiones[nombre_maquina] = motor

        # Retornamos pregunta y opciones si las hay
        if nodo_actual.pregunta:
            return {
                "pregunta": nodo_actual.pregunta,
                "opciones": [r.nombre for r in nodo_actual.ramas] if nodo_actual.ramas else []
            }
        else:
            return {"mensaje": "Nodo sin pregunta, continuar automáticamente."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/diagnosticar/avanzar/{nombre_maquina}")
def avanzar_diagnostico(nombre_maquina: str, respuesta: str = Query(..., description="Respuesta del usuario")):
    """
    Avanza un paso en el árbol de diagnóstico según la respuesta del usuario.
    Devuelve la siguiente pregunta u opciones, o la falla y soluciones si se llegó a un nodo hoja.
    """
    try:
        motor = sesiones.get(nombre_maquina)
        if motor is None:
            raise HTTPException(status_code=404, detail="No se encontró una sesión activa para esta máquina.")

        nodo_siguiente = motor.avanzar(respuesta)
        if nodo_siguiente is None:
            return {"mensaje": "No se pudo avanzar en el diagnóstico."}

        if nodo_siguiente.es_hoja():
            # Nodo hoja: devolvemos falla y soluciones
            return {
                "falla": nodo_siguiente.falla,
                "soluciones": nodo_siguiente.soluciones
            }

        # Nodo intermedio: devolvemos pregunta y opciones
        return {
            "pregunta": nodo_siguiente.pregunta,
            "opciones": [r.nombre for r in nodo_siguiente.ramas] if nodo_siguiente.ramas else []
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
