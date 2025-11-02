"""
schemas.py
Define los modelos de datos Pydantic (schemas)
usados para la validación de datos de entrada en la API.
"""

from pydantic import BaseModel, Field
from typing import List, Optional

# ---------------------------------------------------------------------
# Modelos Pydantic (para validar datos de entrada)
# ---------------------------------------------------------------------

class RespuestaBody(BaseModel):
    """Schema para el body de la ruta /avanzar."""
    respuesta: str

class MaquinaData(BaseModel):
    """Schema para agregar una nueva máquina."""
    nombre: str = Field(..., min_length=3)

class SintomaData(BaseModel):
    """Schema para agregar un nuevo síntoma (nodo de pregunta)."""
    # El frontend envía 'atributo' y 'pregunta'
    atributo: str = Field(..., min_length=2)
    pregunta: str = Field(..., min_length=5)

class FallaData(BaseModel):
    """Schema para agregar una nueva falla (nodo hoja)."""
    # El frontend envía 'atributo', 'falla', etc.
    atributo: str = Field(..., min_length=2)
    falla: str = Field(..., min_length=5)
    soluciones: List[str] = []
    referencia: Optional[str] = None

class SolucionData(BaseModel):
    """Schema para agregar una nueva solución a una falla existente."""
    solucion_nueva: str = Field(..., min_length=5)
