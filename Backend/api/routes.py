"""
routes.py
Versión fusionada: base sin categorías, login/token admin y stats.
"""

from fastapi import APIRouter, HTTPException, Body, Depends, Header
from typing import Dict, Optional

from api.auth import validar_usuario, crear_token, validar_token, eliminar_token
from api.base_conocimiento import BaseConocimiento
from api.engine import MotorInferencia

from api.stats import stats_manager  # Debes tener este módulo

from api.schemas import (
    RespuestaBody,
    MaquinaData,
    FallaData,
    SolucionData,
    RestructuraFallaData
)

router = APIRouter(prefix="/api", tags=["Sistema Experto"])

base = BaseConocimiento()
sesiones: Dict[str, MotorInferencia] = {}

# --------- Utilidades para protección admin ---------

def get_token_from_header(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token no proporcionado")
    return authorization.replace("Bearer ", "")

def validar_token_admin(authorization: Optional[str] = Header(None)):
    token = get_token_from_header(authorization)
    user_data = validar_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    if user_data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado: Solo administradores")
    return user_data

# ---------------- Rutas de diagnóstico públicas ----------------

@router.get("/")
def home():
    return {"mensaje": "API del Sistema Experto activa"}

@router.get("/maquinas")
def listar_maquinas():
    maquinas = base.listar_maquinas()
    return {"maquinas": maquinas}

@router.post("/diagnosticar/iniciar/{nombre_maquina}")
def iniciar_diagnostico(nombre_maquina: str):
    try:
        motor = MotorInferencia(base)
        resultado = motor.iniciar_diagnostico(nombre_maquina)
        key = "default_user"
        sesiones[key] = motor
        # Registrar inicio en estadísticas
        stats_manager.registrar_diagnostico_iniciado(nombre_maquina)
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")

@router.post("/diagnosticar/avanzar/{id_sesion}")
def avanzar_diagnostico(id_sesion: str, body: RespuestaBody):
    motor = sesiones.get(id_sesion)
    if motor is None:
        raise HTTPException(status_code=404, detail="No se encontró una sesión activa. Reinicie el chat.")
    try:
        resultado = motor.avanzar(body.respuesta)
        # Si llega a una falla (resultado final), registra como diagnóstico completado
        if isinstance(resultado, dict) and "falla" in resultado:
            stats_manager.registrar_diagnostico_completado(motor.maquina_actual, resultado["falla"])
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------- Rutas de edición (protegidas admin) ----------------

@router.post("/agregar/maquina")
def agregar_maquina(
    data: MaquinaData,
    user_data: dict = Depends(validar_token_admin)
):
    try:
        base.agregar_maquina(data.nombre)
        if data.primer_rama:
            base.agregar_rama(
                data.nombre, 
                [],  
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

@router.post("/agregar/sintoma/{id_sesion}")
def agregar_sintoma(
    data: FallaData, 
    motor: MotorInferencia = Depends(get_motor_de_sesion),
    user_data: dict = Depends(validar_token_admin)
):
    try:
        path_padre = motor.get_path_a_pregunta()
        nueva_rama_dict = data.model_dump()
        base.agregar_rama(motor.maquina_actual, path_padre, nueva_rama_dict)
        return {"success": True, "message": f"Síntoma terminal '{data.atributo}' agregado con falla '{data.falla}'."}
    except ValueError as e:
        if "falla" in str(e):
            raise HTTPException(
                status_code=409,
                detail="CONFLICT: El nodo actual es una falla. Debe usar 'restructurar' para agregar una pregunta nueva."
            )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agregar/falla/{id_sesion}")
def agregar_falla(
    data: FallaData, 
    motor: MotorInferencia = Depends(get_motor_de_sesion),
    user_data: dict = Depends(validar_token_admin)
):
    try:
        path_padre = motor.get_path_a_pregunta()
        nueva_rama_dict = data.model_dump()
        nodo_padre = base.find_nodo_by_path(motor.maquina_actual, path_padre)
        if nodo_padre.es_hoja():
            raise HTTPException(
                status_code=409,
                detail=f"CONFLICT: El síntoma ya es una falla."
            )
        if (nodo_padre.ramas and len(nodo_padre.ramas) == 1 and nodo_padre.ramas[0].es_hoja()):
            falla_existente = nodo_padre.ramas[0]
            raise HTTPException(
                status_code=409,
                detail=f"CONFLICT: El síntoma conduce a la falla: '{falla_existente.falla}'. Use el formulario de reestructuración.",
            )
        base.agregar_rama(motor.maquina_actual, path_padre, nueva_rama_dict)
        return {"success": True, "message": f"Falla '{data.falla}' agregada."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/restructurar/falla/{id_sesion}")
def restructurar_falla(
    data: RestructuraFallaData, 
    motor: MotorInferencia = Depends(get_motor_de_sesion),
    user_data: dict = Depends(validar_token_admin)
):
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

@router.post("/agregar/solucion/{id_sesion}")
def agregar_solucion(
    data: SolucionData, 
    motor: MotorInferencia = Depends(get_motor_de_sesion),
    user_data: dict = Depends(validar_token_admin)
):
    try:
        path_a_falla = motor.get_historial_path_completo()
        if not motor.nodo_actual or not motor.nodo_actual.es_hoja():
            raise ValueError("No se puede agregar una solución a un nodo que no es una falla.")
        base.agregar_solucion(motor.maquina_actual, path_a_falla, data.solucion_nueva)
        return {"success": True, "message": f"Solución agregada a la falla '{motor.nodo_actual.falla}'."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------- Rutas de login/logout y stats (protegidas) ----------------

@router.post("/login_admin")
def login_admin(username: str = Body(...), password: str = Body(...)):
    usuario = validar_usuario(username, password)
    if usuario and usuario.get("role") == "admin":
        token = crear_token(usuario["username"], usuario["role"])
        return {
            "success": True,
            "token": token,
            "username": usuario["username"],
            "role": usuario["role"]
        }
    raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

@router.post("/logout_admin")
def logout_admin(authorization: Optional[str] = Header(None)):
    token = get_token_from_header(authorization)
    eliminar_token(token)
    return {"success": True, "message": "Sesión cerrada correctamente"}

@router.get("/admin/stats")
def obtener_estadisticas(user_data: dict = Depends(validar_token_admin)):
    """Retorna las estadísticas del sistema (requiere autenticación admin)."""
    return stats_manager.obtener_estadisticas()

@router.post("/admin/reset_tokens")
def reset_tokens():
    eliminar_token()
    return {"success": True, "message": "Todos los tokens han sido invalidados."}