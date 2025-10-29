"""
base_conocimiento.py
Clase para gestionar la base de conocimientos de máquinas (en formato árbol de objetos Nodo o JSON)
Adaptado al flujo de categorías dentro de cada máquina.
"""

from typing import Dict, Any, List, Optional
import json
from pathlib import Path
from Backend.api.nodo import Nodo

JSON_LATEST = 1
DEFAULT_JSON = "Backend/data/base_conocimiento.json"  # ruta por defecto al JSON


class BaseConocimiento:
    """
    Clase principal de la base de conocimientos para el sistema experto.
    Gestiona la carga, almacenamiento y consulta de la base desde archivos JSON.
    Ahora con soporte de categorías por máquina.
    """

    def __init__(self, archivo_json: str = DEFAULT_JSON):
        self.description = "Base de conocimientos de máquinas"
        # Diccionario principal: nombre de la máquina → lista de categorías (cada una con un Nodo raíz)
        self.maquinas: Dict[str, List[Nodo]] = {}
        self.from_json(archivo_json)  # carga automática al instanciar

    # -------------------------------------------------------------------------
    # MÉTODOS DE CARGA Y GUARDADO
    # -------------------------------------------------------------------------

    def from_json(self, filename: str):
        """
        Carga una base de conocimientos desde un archivo JSON.
        Convierte cada máquina y sus categorías en estructuras de objetos Nodo.
        """
        path = Path(filename)
        if not path.exists():
            print(f"Archivo {filename} no encontrado")
            return self

        with open(filename, 'r', encoding='utf8') as f:
            data = json.load(f)

        if "__v" in data and data["__v"] != JSON_LATEST:
            raise ValueError("Actualizar JSON a nueva versión")

        self.description = data.get("description", self.description)
        self.maquinas = {}

        for nombre_maquina, info_maquina in data.items():
            if nombre_maquina == "__v" or nombre_maquina == "description":
                continue
            categorias = info_maquina.get("categorias", [])
            lista_nodos = []
            for cat in categorias:
                nodo_categoria = Nodo.from_dict(cat)
                lista_nodos.append(nodo_categoria)
            self.maquinas[nombre_maquina] = lista_nodos

        return self

    def to_json(self, filename: str):
        """
        Guarda la base de conocimientos en un archivo JSON.
        Convierte cada árbol de Nodo a diccionario.
        """
        obj = {
            "__v": JSON_LATEST,
            "description": self.description
        }

        for nombre_maquina, lista_categorias in self.maquinas.items():
            obj[nombre_maquina] = {
                "categorias": [n.to_dict() for n in lista_categorias]
            }

        data = json.dumps(obj, indent=2, ensure_ascii=False)
        with open(filename, 'w', encoding='utf8') as f:
            f.write(data)
        return data

    # -------------------------------------------------------------------------
    # MÉTODOS DE CONSULTA
    # -------------------------------------------------------------------------

    def listar_maquinas(self) -> List[str]:
        """Devuelve una lista de todas las máquinas registradas en la base."""
        return list(self.maquinas.keys())

    def listar_categorias(self, nombre_maquina: str) -> List[str]:
        """Devuelve la lista de categorías de una máquina específica."""
        categorias = self.maquinas.get(nombre_maquina)
        if not categorias:
            return []
        return [cat.nombre for cat in categorias]

    def get_arbol_categoria(self, nombre_maquina: str, categoria: str) -> Optional[Nodo]:
        """Devuelve el nodo raíz de una categoría específica dentro de una máquina."""
        categorias = self.maquinas.get(nombre_maquina)
        if not categorias:
            return None
        nodo_categoria = next((c for c in categorias if c.nombre == categoria), None)
        return nodo_categoria

    def agregar_maquina(self, nombre_maquina: str, lista_categorias: List[Nodo]):
        """
        Agrega una nueva máquina completa a la base con sus categorías.
        """
        if nombre_maquina in self.maquinas:
            raise ValueError(f"La máquina '{nombre_maquina}' ya existe en la base.")
        self.maquinas[nombre_maquina] = lista_categorias

    def agregar_categoria(self, nombre_maquina: str, nodo_categoria: Nodo):
        """
        Agrega una nueva categoría a una máquina existente.
        """
        if nombre_maquina not in self.maquinas:
            raise ValueError(f"No se encontró la máquina '{nombre_maquina}'.")
        self.maquinas[nombre_maquina].append(nodo_categoria)

    # -------------------------------------------------------------------------
    # FUTURAS AMPLIACIONES (IA / EDICIÓN DE USUARIO)
    # -------------------------------------------------------------------------

    def integrar_manual_ia(self, texto_manual: str):
        """[Futuro] Analiza un texto de manual usando IA y genera un árbol de conocimiento JSON."""
        raise NotImplementedError("Integración IA pendiente.")

    def editar_nodo(self, nombre_maquina: str, nodo_id: str, cambios: Dict[str, Any]):
        """[Futuro] Permite editar atributos de un nodo específico dentro de una máquina."""
        raise NotImplementedError("Edición de nodo pendiente.")

    def __str__(self):
        resumen = f"{self.description}\nMáquinas registradas: {', '.join(self.listar_maquinas())}"
        return resumen
