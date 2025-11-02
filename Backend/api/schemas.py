"""
schemas.py
Define los modelos de datos Pydantic (schemas)
usados para la validación de datos de entrada en la API.
"""

from pydantic import BaseModel, Field
from typing import List, Optional

# --- MODELOS DE ENTRADA Y VALIDACIÓN ---

class RespuestaBody(BaseModel):
    """Esquema para el body de la ruta /avanzar."""
    respuesta: str

class MaquinaData(BaseModel):
    """Esquema para agregar una nueva máquina."""
    nombre: str = Field(..., min_length=3)
    primer_rama: Optional[dict] = None

class SintomaData(BaseModel):
    """
    Esquema para agregar un nuevo síntoma (nodo de pregunta).
    El frontend envía 'atributo' y 'pregunta'.
    Para el árbol actualizado: se inserta como
    {'atributo': ..., 'pregunta': ...}
    """
    atributo: str = Field(..., min_length=2)
    pregunta: str = Field(..., min_length=5)

class FallaData(BaseModel):
    """
    Esquema para agregar una nueva falla (nodo hoja).
    El frontend envía: 'atributo', 'falla', etc.
    """
    atributo: str = Field(..., min_length=2)
    falla: str = Field(..., min_length=5)
    soluciones: List[str] = []
    referencia: Optional[str] = None

class SolucionData(BaseModel):
    """Esquema para agregar una nueva solución a una falla existente."""
    solucion_nueva: str = Field(..., min_length=5)

class RestructuraFallaData(BaseModel):
    """
    Esquema para restructurar un nodo de falla única en un nodo de pregunta con dos fallas.
    Incluye todos los datos necesarios de ambas fallas.
    Usado en /restructurar/falla.
    """
    pregunta_nueva: str = Field(..., min_length=5)
    # Datos de la falla EXISTENTE
    atributo_existente: str = Field(..., min_length=2)
    falla_existente: str = Field(..., min_length=5)
    soluciones_existente: List[str] = []
    referencia_existente: Optional[str] = None
    # Datos de la nueva falla
    atributo_nuevo: str = Field(..., min_length=2)
    falla_nueva: str = Field(..., min_length=5)
    soluciones_nuevas: List[str] = []
    referencia_nueva: Optional[str] = None
