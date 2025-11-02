"""
routes.py
Define las rutas de la API del sistema experto.
"""
from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from Backend.api.auth import validar_usuario
from Backend.api.base_conocimiento import BaseConocimiento
from Backend.api.engine import MotorInferencia

# ---------------------------------------------------------------------
# Modelos Pydantic (para validar datos de entrada)
# ---------------------------------------------------------------------

class RespuestaBody(BaseModel):
    respuesta: str

class MaquinaData(BaseModel):
    nombre: str = Field(..., min_length=3)

class CategoriaData(BaseModel):
    maquina_padre: str
    nombre_categoria: str = Field(..., min_length=3)

class SintomaData(BaseModel):
    # 'atributo' es la respuesta del usuario, 'nombre' en el Nodo
    atributo_nuevo: str = Field(..., alias="atributo", min_length=2)
    pregunta_nueva: str = Field(..., alias="pregunta", min_length=5)

class FallaData(BaseModel):
    atributo_nuevo: str = Field(..., alias="atributo", min_length=2)
    falla_nueva: str = Field(..., alias="falla", min_length=5)
    soluciones: List[str] = []
    referencia: Optional[str] = None

class SolucionData(BaseModel):
    solucion_nueva: str = Field(..., min_length=5)

# ---------------------------------------------------------------------
# Inicialización
# ---------------------------------------------------------------------

router = APIRouter(prefix="/api", tags=["Sistema Experto"])

# --- Instancia ÚNICA de la Base de Conocimiento ---
# Esto asegura que la base se carga UNA SOLA VEZ al iniciar el servidor.
# La variable 'base' se compartirá entre todas las peticiones.
base = BaseConocimiento()

# Diccionario para almacenar sesiones (motores) activas
# Clave: "maquina|categoria" -> motor
sesiones: Dict[str, MotorInferencia] = {}

# ---------------------------------------------------------------------
# RUTAS DE DIAGNÓSTICO
# ---------------------------------------------------------------------

@router.get("/")
def home():
    """Ruta base de la API."""
    return {"mensaje": "API del Sistema Experto activa"}

@router.get("/maquinas")
def listar_maquinas():
    """Lista todas las máquinas disponibles en la base de conocimiento."""
    return {"maquinas": base.listar_maquinas()}

@router.get("/categorias/{nombre_maquina}")
def listar_categorias(nombre_maquina: str):
    """Devuelve las categorías disponibles para una máquina específica."""
    try:
        categorias = base.listar_categorias(nombre_maquina)
        return {"categorias": categorias}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/diagnosticar/iniciar/{nombre_maquina}/{categoria}")
def iniciar_diagnostico(nombre_maquina: str, categoria: str):
    """
    Inicia el diagnóstico y crea una sesión para el usuario.
    """
    try:
        motor = MotorInferencia(base)
        motor.iniciar_diagnostico(nombre_maquina) 
        resultado = motor.seleccionar_categoria(categoria) 

        # Guardamos la sesión
        key = f"{nombre_maquina}|{categoria}"
        sesiones[key] = motor

        return resultado
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")

@router.post("/diagnosticar/avanzar/{nombre_maquina}/{categoria}")
def avanzar_diagnostico(nombre_maquina: str, categoria: str, body: RespuestaBody):
    """
    Avanza un paso en el árbol de diagnóstico según la respuesta.
    """
    key = f"{nombre_maquina}|{categoria}"
    motor = sesiones.get(key)

    if motor is None:
        raise HTTPException(status_code=404, detail="No se encontró una sesión activa. Por favor, reinicie el chat.")
    
    try:
        resultado = motor.avanzar(body.respuesta)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------------------
# RUTAS DE EDICIÓN DE CONOCIMIENTO (NUEVAS)
# ---------------------------------------------------------------------

@router.post("/agregar/maquina", summary="Agrega una nueva máquina")
def agregar_maquina(data: MaquinaData):
    try:
        base.agregar_maquina(data.nombre)
        return {"success": True, "message": f"Máquina '{data.nombre}' agregada."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agregar/categoria", summary="Agrega una nueva categoría a una máquina")
def agregar_categoria(data: CategoriaData):
    try:
        base.agregar_categoria(data.maquina_padre, data.nombre_categoria)
        return {"success": True, "message": f"Categoría '{data.nombre_categoria}' agregada a '{data.maquina_padre}'."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_motor_de_sesion(maquina: str, categoria: str) -> MotorInferencia:
    """Dependencia para obtener el motor de la sesión actual."""
    key = f"{maquina}|{categoria}"
    motor = sesiones.get(key)
    if motor is None:
        raise HTTPException(status_code=404, detail="Sesión de diagnóstico no encontrada. No se puede agregar el nodo.")
    return motor

@router.post("/agregar/sintoma/{maquina}/{categoria}", summary="Agrega un nuevo síntoma (pregunta)")
def agregar_sintoma(data: SintomaData, motor: MotorInferencia = Depends(get_motor_de_sesion)):
    """
    Agrega un nuevo síntoma (una rama con pregunta) al nodo actual de la sesión.
    """
    try:
        # El path al nodo padre es el historial de respuestas del motor
        path_padre = motor.get_historial_path()
        
        # El diccionario para el nuevo Nodo
        nueva_rama_dict = data.model_dump(by_alias=True) # Usa 'atributo' y 'pregunta'

        base.agregar_rama(motor.maquina_actual, motor.categoria_actual, path_padre, nueva_rama_dict)
        return {"success": True, "message": f"Síntoma '{data.atributo_nuevo}' agregado."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agregar/falla/{maquina}/{categoria}", summary="Agrega una nueva falla (hoja)")
def agregar_falla(data: FallaData, motor: MotorInferencia = Depends(get_motor_de_sesion)):
    """
    Agrega una nueva falla (una rama hoja) al nodo actual de la sesión.
    """
    try:
        path_padre = motor.get_historial_path()
        nueva_rama_dict = data.model_dump(by_alias=True) # Usa 'atributo', 'falla', etc.

        base.agregar_rama(motor.maquina_actual, motor.categoria_actual, path_padre, nueva_rama_dict)
        return {"success": True, "message": f"Falla '{data.falla_nueva}' agregada."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agregar/solucion/{maquina}/{categoria}", summary="Agrega una solución a una falla existente")
def agregar_solucion(data: SolucionData, motor: MotorInferencia = Depends(get_motor_de_sesion)):
    """
    Agrega una nueva solución al nodo de falla actual de la sesión.
    """
    try:
        # El path al nodo de falla es el historial completo de respuestas
        path_a_falla = motor.get_historial_path()
        
        if not motor.nodo_actual.es_hoja():
            raise ValueError("No se puede agregar una solución a un nodo que no es una falla.")

        base.agregar_solucion(motor.maquina_actual, motor.categoria_actual, path_a_falla, data.solucion_nueva)
        return {"success": True, "message": f"Solución agregada a la falla '{motor.nodo_actual.falla}'."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------------------
# RUTAS DE LOGIN (Ejemplo)
# ---------------------------------------------------------------------

@router.post("/login_admin") # Renombrada para evitar colisión con la tuya
def login_admin(username: str = Body(...), password: str = Body(...)):
    if validar_usuario(username, password):
        return {"success": True, "message": "Login correcto"}
    raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
