"""
preprocesamiento.py
Funciones para limpiar y comparar texto de forma flexible.
"""

import re
from difflib import SequenceMatcher
import unicodedata


def limpiar_texto(texto: str) -> str:
    """
    Limpia el texto eliminando acentos, signos de puntuación, espacios extra y lo pasa a minúsculas.
    """
    if not texto:
        return ""

    # Normalizar caracteres acentuados (á -> a, ñ -> n)
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf8")

    # Convertir a minúsculas
    texto = texto.lower()

    # Eliminar caracteres no alfabéticos ni numéricos
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)

    # Quitar espacios extra
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


def similitud_rapida(texto_usuario: str, opciones: list, umbral: float = 0.7) -> str | None:
    """
    Busca la opción más parecida al texto del usuario usando fuzzy matching básico.
    Retorna la mejor coincidencia o None si no hay ninguna por encima del umbral.
    """
    if not opciones:
        return None

    texto_usuario = limpiar_texto(texto_usuario)

    mejor_opcion = None
    mejor_puntaje = 0

    for opcion in opciones:
        opcion_limpia = limpiar_texto(opcion)
        puntaje = SequenceMatcher(None, texto_usuario, opcion_limpia).ratio()
        if puntaje > mejor_puntaje:
            mejor_puntaje = puntaje
            mejor_opcion = opcion

    return mejor_opcion if mejor_puntaje >= umbral else None
