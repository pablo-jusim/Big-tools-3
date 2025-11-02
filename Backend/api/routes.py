"""
routes.py
Define las rutas de la API del sistema experto.
"""
from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict

# --- Importaciones de lógica de negocio ---
from Backend.api.auth import validar_usuario
from Backend.api.base_conocimiento import BaseConocimiento
from Backend.api.engine import MotorInferencia
# Importamos Nodo, aunque no se use aquí, es bueno tenerlo de referencia
from Backend.api.nodo import Nodo 

# --- Importación de los Schemas Pydantic ---
from Backend.api.schemas import (
    RespuestaBody,
    MaquinaData,
    SintomaData,
    FallaData,
    SolucionData
)

# ---------------------------------------------------------------------
# Inicialización
# ---------------------------------------------------------------------

router = APIRouter(prefix="/api", tags=["Sistema Experto"])

# --- Instancia ÚNICA de la Base de Conocimiento ---
# Esto asegura que la base se carga UNA SOLA VEZ al iniciar el servidor
# y se comparte entre todas las peticiones.
base = BaseConocimiento()

# Diccionario para almacenar motores de sesión activos
# Clave: id_sesion (ej: "default_user") -> MotorInferencia
sesiones: Dict[str, MotorInferencia] = {}

# ---------------------------------------------------------------------
# RUTAS DE DIAGNÓSTICO (Simplificadas)
# ---------------------------------------------------------------------

@router.get("/")
def home():
    """Ruta base de la API."""
    return {"mensaje": "API del Sistema Experto activa"}

@router.get("/maquinas")
def listar_maquinas():
    """Lista todas las máquinas disponibles en la base de conocimiento."""
    return {"maquinas": base.listar_maquinas()}

@router.post("/diagnosticar/iniciar/{nombre_maquina}")
def iniciar_diagnostico(nombre_maquina: str):
    """
    Inicia el diagnóstico para una máquina y crea una sesión.
    Devuelve la PRIMERA PREGUNTA.
    """
    try:
        motor = MotorInferencia(base)
        # 'iniciar_diagnostico' ahora carga el nodo raíz y devuelve la 1ra pregunta
        resultado = motor.iniciar_diagnostico(nombre_maquina) 

        # Guardamos la sesión (usando el ID que main.js conoce)
        key = "default_user" # ID_SESION
        sesiones[key] = motor

        return resultado
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")

@router.post("/diagnosticar/avanzar/{id_sesion}")
def avanzar_diagnostico(id_sesion: str, body: RespuestaBody):
    """
    Avanza un paso en el árbol de diagnóstico de una sesión activa.
    """
    motor = sesiones.get(id_sesion) # Obtiene el motor de la sesión
    if motor is None:
        raise HTTPException(status_code=404, detail="No se encontró una sesión activa. Por favor, reinicie el chat.")
    
    try:
        resultado = motor.avanzar(body.respuesta)
        print('el resultado es:', resultado)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------------------
# RUTAS DE EDICIÓN DE CONOCIMIENTO (NUEVAS Y CORREGIDAS)
# ---------------------------------------------------------------------

@router.post("/agregar/maquina", summary="Agrega una nueva máquina")
def agregar_maquina(data: MaquinaData):
    """
    Agrega una nueva máquina a la base de conocimientos.
    El frontend solo necesita enviar: {"nombre": "Nueva Máquina"}
    """
    try:
        base.agregar_maquina(data.nombre)
        return {"success": True, "message": f"Máquina '{data.nombre}' agregada."}
    except ValueError as e: # Si la máquina ya existe
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_motor_de_sesion(id_sesion: str) -> MotorInferencia:
    """
    Dependencia de FastAPI para obtener el motor de la sesión actual.
    Se usa en las rutas de "agregar".
    """
    motor = sesiones.get(id_sesion)
    if motor is None:
        raise HTTPException(status_code=404, detail="Sesión de diagnóstico no encontrada. No se puede agregar el nodo.")
    return motor

@router.post("/agregar/sintoma/{id_sesion}", summary="Agrega un nuevo síntoma (pregunta)")
def agregar_sintoma(data: SintomaData, motor: MotorInferencia = Depends(get_motor_de_sesion)):
    """
    Agrega un nuevo síntoma (una rama con pregunta) al nodo actual de la sesión.
    El frontend envía: {"atributo": "...", "pregunta": "..."}
    """
    try:
        path_padre = motor.get_historial_path()
        
        # model_dump() crea el dict {"atributo": "...", "pregunta": "..."}
        # que Nodo.from_dict() espera.
        nueva_rama_dict = data.model_dump()

        base.agregar_nodo(motor.maquina_actual, path_padre, nueva_rama_dict)
        return {"success": True, "message": f"Síntoma '{data.atributo}' agregado."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agregar/falla/{id_sesion}", summary="Agrega una nueva falla (hoja)")
def agregar_falla(data: FallaData, motor: MotorInferencia = Depends(get_motor_de_sesion)):
    """
    Agrega una nueva falla (una rama hoja) al nodo actual de la sesión.
    El frontend envía: {"atributo": "...", "falla": "...", "soluciones": [...]}
    """
    try:
        path_padre = motor.get_historial_path()
        
        # model_dump() crea el dict {"atributo": "...", "falla": "...", ...}
        # que Nodo.from_dict() espera.
        nueva_rama_dict = data.model_dump()

        base.agregar_nodo(motor.maquina_actual, path_padre, nueva_rama_dict)
        return {"success": True, "message": f"Falla '{data.falla}' agregada."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agregar/solucion/{id_sesion}", summary="Agrega una solución a una falla existente")
def agregar_solucion(data: SolucionData, motor: MotorInferencia = Depends(get_motor_de_sesion)):
    """
    Agrega una nueva solución al nodo de falla actual de la sesión.
    El frontend envía: {"solucion_nueva": "..."}
    """
    try:
        # El path al nodo de falla es el historial completo de respuestas
        path_a_falla = motor.get_historial_path()
        
        if not motor.nodo_actual or not motor.nodo_actual.es_hoja():
            raise ValueError("No se puede agregar una solución a un nodo que no es una falla (el nodo actual es una pregunta).")

        base.agregar_solucion(motor.maquina_actual, path_a_falla, data.solucion_nueva)
        return {"success": True, "message": f"Solución agregada a la falla '{motor.nodo_actual.falla}'."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------------------
# RUTAS DE LOGIN (Ejemplo)
# ---------------------------------------------------------------------

@router.post("/login_admin")
def login_admin(username: str = Body(...), password: str = Body(...)):
    """
    Valida a un usuario administrador.
    (La lógica de 'validar_usuario' está en auth.py)
    """
    if validar_usuario(username, password):
        return {"success": True, "message": "Login correcto"}
    raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

