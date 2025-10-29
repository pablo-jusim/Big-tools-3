"""
routes.py
Define las rutas de la API del sistema experto.
"""

from fastapi import APIRouter, HTTPException, Body
from Backend.api.auth import validar_usuario
from Backend.api.base_conocimiento import BaseConocimiento
from Backend.api.engine import MotorInferencia

# ---------------------------------------------------------------------
# Inicialización
# ---------------------------------------------------------------------

router = APIRouter(prefix="/api", tags=["Sistema Experto"])

# Instancias globales
base = BaseConocimiento()
motor_global = MotorInferencia(base)

# Diccionario para almacenar sesiones activas por máquina+categoria
# Clave: "nombre_maquina|categoria"
sesiones = {}

# ---------------------------------------------------------------------
# RUTAS
# ---------------------------------------------------------------------

@router.get("/")
def home():
    """Ruta base de la API."""
    return {"mensaje": "API del Sistema Experto activa"}


@router.post("/login")
def login(username: str = Body(...), password: str = Body(...)):
    if validar_usuario(username, password):
        return {"success": True, "message": "Login correcto"}
    raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")


@router.get("/maquinas")
def listar_maquinas():
    """Lista todas las máquinas disponibles en la base de conocimiento."""
    maquinas = base.listar_maquinas()
    return {"maquinas": maquinas}


@router.get("/categorias/{nombre_maquina}")
def listar_categorias(nombre_maquina: str):
    """Devuelve las categorías disponibles para una máquina específica."""
    categorias = base.listar_categorias(nombre_maquina)
    return {"categorias": categorias}


@router.post("/diagnosticar/iniciar/{nombre_maquina}/{categoria}")
def iniciar_diagnostico(nombre_maquina: str, categoria: str):
    """
    Inicia el diagnóstico de una máquina específica para la categoría seleccionada.
    Devuelve la primera pregunta u opciones para el frontend.
    """
    try:
        motor = MotorInferencia(base)
        
        # Paso 1: Iniciar el motor (carga categorías de la máquina)
        motor.iniciar_diagnostico(nombre_maquina) 
        
        # Paso 2: Seleccionar la categoría (obtiene la 1ra pregunta o resultado)
        # !! ESTE ES EL PASO CRÍTICO QUE FALTABA !!
        resultado = motor.seleccionar_categoria(categoria) 

        # Guardamos la sesión por máquina + categoría
        key = f"{nombre_maquina}|{categoria}"
        sesiones[key] = motor

        # Retornamos el resultado del Paso 2
        return resultado

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/diagnosticar/avanzar/{nombre_maquina}/{categoria}")
def avanzar_diagnostico(nombre_maquina: str, categoria: str, respuesta: str = Body(..., embed=True)):
    """
    Avanza un paso en el árbol de diagnóstico según la respuesta del usuario.
    Devuelve la siguiente pregunta u opciones, o la falla y soluciones si se llegó a un nodo hoja.
    """
    key = f"{nombre_maquina}|{categoria}"
    motor = sesiones.get(key)

    if motor is None:
        raise HTTPException(status_code=404, detail="No se encontró una sesión activa para esta máquina y categoría.")

    resultado = motor.avanzar(respuesta)
    return resultado
