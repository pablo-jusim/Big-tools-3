"""
base_conocimiento.py
Clase para gestionar la base de conocimientos de máquinas (en formato árbol de objetos Nodo o JSON)
"""

from typing import Dict, Any, List, Optional
import json
from nodo import Nodo


JSON_LATEST = 1


class BaseConocimiento:
    """
    Clase principal de la base de conocimientos para el sistema experto.
    Gestiona la carga, almacenamiento y expansión de la base desde archivos JSON.
    """

    def __init__(self):
        self.description = "Base de conocimientos de máquinas"
        # Diccionario principal que contiene todas las máquinas (como árboles de Nodos)
        self.maquinas: Dict[str, Nodo] = {}

    # -------------------------------------------------------------------------
    # MÉTODOS DE CARGA Y GUARDADO
    # -------------------------------------------------------------------------

    def from_json(self, filename: str):
        """
        Carga una base de conocimientos desde un archivo JSON.
        Convierte cada máquina en una estructura de objetos Nodo.
        """
        with open(filename, 'r', encoding='utf8') as f:
            data = json.load(f)

        if "__v" in data and data["__v"] != JSON_LATEST:
            raise ValueError("Actualizar JSON a nueva versión")

        self.description = data.get("description", self.description)

        # Cargar los árboles de máquinas como Nodos
        self.maquinas = {}
        for entry in data.get("entries", []):
            nombre = entry["name"]
            estructura = entry["tree"]
            self.maquinas[nombre] = Nodo.from_dict(estructura)

        return self

    def to_json(self, filename: str):
        """
        Guarda la base de conocimientos en un archivo JSON.
        Convierte cada árbol de Nodo a diccionario.
        """
        obj = {
            "__v": JSON_LATEST,
            "description": self.description,
            "entries": []
        }

        for nombre, nodo_raiz in self.maquinas.items():
            obj["entries"].append({
                "name": nombre,
                "tree": nodo_raiz.to_dict()
            })

        data = json.dumps(obj, indent=2, ensure_ascii=False)
        with open(filename, 'w', encoding='utf8') as f:
            f.write(data)
        return data

    # -------------------------------------------------------------------------
    # MÉTODOS DE CONSULTA Y EXPANSIÓN
    # -------------------------------------------------------------------------

    def listar_maquinas(self) -> List[str]:
        """Devuelve una lista de todas las máquinas registradas en la base."""
        return list(self.maquinas.keys())

    def get_arbol(self, nombre_maquina: str) -> Optional[Nodo]:
        """Devuelve el nodo raíz (árbol) de una máquina específica, o None si no existe."""
        return self.maquinas.get(nombre_maquina)

    def agregar_maquina(self, nombre_maquina: str, nodo_raiz: Nodo):
        """
        Agrega una nueva máquina completa a la base.
        :param nombre_maquina: Nombre único de la máquina
        :param nodo_raiz: Nodo raíz del árbol de conocimiento
        """
        if nombre_maquina in self.maquinas:
            raise ValueError(f"La máquina '{nombre_maquina}' ya existe en la base.")
        self.maquinas[nombre_maquina] = nodo_raiz

    def agregar_rama(self, nombre_maquina: str, ruta: List[str], nueva_rama: Nodo):
        """
        Agrega una nueva rama (Nodo) dentro del árbol existente.
        :param nombre_maquina: Nombre de la máquina
        :param ruta: Lista de nombres de nodos hasta el punto de inserción
        :param nueva_rama: Nodo a insertar
        """
        arbol = self.get_arbol(nombre_maquina)
        if not arbol:
            raise ValueError(f"No se encontró la máquina '{nombre_maquina}' en la base.")

        nodo_actual = arbol
        for nivel in ruta:
            nodo_hijo = next((r for r in nodo_actual.ramas if r.nombre == nivel), None)
            if not nodo_hijo:
                raise ValueError(f"No se encontró el nodo '{nivel}' en la ruta especificada.")
            nodo_actual = nodo_hijo

        nodo_actual.ramas.append(nueva_rama)

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
