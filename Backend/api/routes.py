"""
routes.py
Define las rutas de la API del sistema experto.
Adaptado a la estructura simplificada (sin "categorias").
"""

from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict

from Backend.api.auth import validar_usuario
from Backend.api.base_conocimiento import BaseConocimiento
from Backend.api.engine import MotorInferencia
from Backend.api.nodo import Nodo

from Backend.api.schemas import (
    RespuestaBody,
    MaquinaData,
    SintomaData,
    FallaData,
    SolucionData,
    RestructuraFallaData
)

router = APIRouter(prefix="/api", tags=["Sistema Experto"])

base = BaseConocimiento()
sesiones: Dict[str, MotorInferencia] = {}

# ---------------- Rutas de diagnóstico ----------------

@router.get("/")
def home():
    return {"mensaje": "API del Sistema Experto activa"}

@router.get("/maquinas")
def listar_maquinas():
    return {"maquinas": base.listar_maquinas()}

@router.post("/diagnosticar/iniciar/{nombre_maquina}")
def iniciar_diagnostico(nombre_maquina: str):
    try:
        motor = MotorInferencia(base)
        resultado = motor.iniciar_diagnostico(nombre_maquina)
        key = "default_user"
        sesiones[key] = motor
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")

@router.post("/diagnosticar/avanzar/{id_sesion}")
def avanzar_diagnostico(id_sesion: str, body: RespuestaBody):
    motor = sesiones.get(id_sesion)
    if motor is None:
        raise HTTPException(status_code=404, detail="No se encontró una sesión activa. Por favor, reinicie el chat.")
    try:
        resultado = motor.avanzar(body.respuesta)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------- Rutas de edición ----------------

@router.post("/agregar/maquina", summary="Agrega una nueva máquina")
def agregar_maquina(data: MaquinaData):
    try:
        base.agregar_maquina(data.nombre)
        # Agrega rama terminal inicial bajo la pregunta principal
        if data.primer_rama:
            base.agregar_rama(
                data.nombre, 
                [],  # primer nivel de la máquina
                data.primer_rama
            )
        return {"success": True, "message": f"Máquina '{data.nombre}' agregada."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_motor_de_sesion(id_sesion: str) -> MotorInferencia:
    motor = sesiones.get(id_sesion)
    if motor is None:
        raise HTTPException(status_code=404, detail="Sesión de diagnóstico no encontrada. No se puede agregar el nodo.")
    return motor

@router.post("/agregar/sintoma/{id_sesion}", summary="Agrega un nuevo síntoma HOJA")
def agregar_sintoma(data: FallaData, motor: MotorInferencia = Depends(get_motor_de_sesion)):
    try:
        path_padre = motor.get_path_a_pregunta()
        nueva_rama_dict = data.model_dump()
        base.agregar_rama(motor.maquina_actual, path_padre, nueva_rama_dict)
        return {"success": True, "message": f"Síntoma terminal '{data.atributo}' agregado con falla '{data.falla}'."}
    except ValueError as e:
        if "falla" in str(e):
            raise HTTPException(
                status_code=409,
                detail="CONFLICT: El nodo actual es una falla. Debe usar la opción 'restructurar' para agregar una nueva pregunta."
            )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agregar/falla/{id_sesion}", summary="Agrega una nueva falla (hoja)")
def agregar_falla(data: FallaData, motor: MotorInferencia = Depends(get_motor_de_sesion)):
    try:
        path_padre = motor.get_path_a_pregunta()
        nueva_rama_dict = data.model_dump()
        nodo_padre = base.find_nodo_by_path(motor.maquina_actual, path_padre)
        if nodo_padre.es_hoja():
            raise HTTPException(
                status_code=409,
                detail=f"CONFLICT: El síntoma al que intenta agregar una falla ('{nodo_padre.nombre}') ya es una falla: '{nodo_padre.falla}'. Use el formulario de reestructuración."
            )
        if (nodo_padre.ramas and len(nodo_padre.ramas) == 1 and nodo_padre.ramas[0].es_hoja()):
            falla_existente = nodo_padre.ramas[0]
            raise HTTPException(
                status_code=409,
                detail=f"CONFLICT: El síntoma al que intenta agregar una falla ya conduce a la falla: '{falla_existente.falla}'. Use el formulario de reestructuración.",
            )
        base.agregar_rama(motor.maquina_actual, path_padre, nueva_rama_dict)
        return {"success": True, "message": f"Falla '{data.falla}' agregada."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/restructurar/falla/{id_sesion}", summary="Restructura una falla en una pregunta")
def restructurar_falla(data: RestructuraFallaData, motor: MotorInferencia = Depends(get_motor_de_sesion)):
    try:
        path_a_restructurar = motor.get_historial_path_completo()
        # Preparar ambos dicts de falla, viejo y nuevo
        falla_existente_dict = {
            "falla": data.falla_existente,
            "soluciones": data.soluciones_existente,
            "referencia": data.referencia_existente
        }
        falla_nueva_dict = {
            "falla": data.falla_nueva,
            "soluciones": data.soluciones_nuevas,
            "referencia": data.referencia_nueva
        }
        base.restructurar_falla_a_pregunta(
            nombre_maquina=motor.maquina_actual,
            path_a_hoja=path_a_restructurar,
            pregunta_nueva=data.pregunta_nueva,
            atributo_existente=data.atributo_existente,
            falla_existente_dict=falla_existente_dict,
            atributo_nuevo=data.atributo_nuevo,
            falla_nueva_dict=falla_nueva_dict
        )
        return {"success": True, "message": f"Nodo restructurado con la pregunta: '{data.pregunta_nueva}'."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agregar/solucion/{id_sesion}", summary="Agrega una solución a una falla existente")
def agregar_solucion(data: SolucionData, motor: MotorInferencia = Depends(get_motor_de_sesion)):
    try:
        path_a_falla = motor.get_historial_path_completo()
        if not motor.nodo_actual or not motor.nodo_actual.es_hoja():
            raise ValueError("No se puede agregar una solución a un nodo que no es una falla (el nodo actual es una pregunta).")
        base.agregar_solucion(motor.maquina_actual, path_a_falla, data.solucion_nueva)
        return {"success": True, "message": f"Solución agregada a la falla '{motor.nodo_actual.falla}'."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------- Rutas de login ----------------
@router.post("/login_admin")
def login_admin(username: str = Body(...), password: str = Body(...)):
    if validar_usuario(username, password):
        return {"success": True, "message": "Login correcto"}
    raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
