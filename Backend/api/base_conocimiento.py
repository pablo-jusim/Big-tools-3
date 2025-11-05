"""
base_conocimiento.py
Clase para gestionar la base de conocimientos de máquinas.
Compatible con la nueva estructura simplificada de JSON.
"""

from typing import Dict, Any, List, Optional
import json
from pathlib import Path
from api.nodo import Nodo

JSON_LATEST = 1
DEFAULT_JSON = "data/base_conocimiento.json"

class BaseConocimiento:
    def __init__(self, archivo_json: str = DEFAULT_JSON):
        self.archivo_path = Path(archivo_json)
        self.description = "Base de conocimientos de máquinas"
        self.maquinas: Dict[str, Nodo] = {}
        self.from_json(self.archivo_path)

    # ------------ CARGA Y GUARDADO ----------------
    def from_json(self, filename: Path):
        if not filename.exists():
            self.maquinas = {}
            return self
        with open(filename, 'r', encoding='utf8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"Error al decodificar {filename}.")
                self.maquinas = {}
                return self
        if "__v" in data and data["__v"] != JSON_LATEST:
            raise ValueError("Actualizar JSON a nueva versión")
        self.description = data.get("description", self.description)
        self.maquinas = {}
        for nombre_maquina, arbol_dict in data.items():
            if nombre_maquina.startswith("__") or not isinstance(arbol_dict, dict):
                continue
            arbol_dict['nombre'] = nombre_maquina
            self.maquinas[nombre_maquina] = Nodo.from_dict(arbol_dict)
            print('maquinas', self.maquinas)
        return self

    def to_json(self, filename: Optional[Path] = None):
        path = filename or self.archivo_path
        obj = {
            "__v": JSON_LATEST,
            "description": self.description
        }
        for nombre_maquina, nodo_raiz in self.maquinas.items():
            dict_para_guardar = nodo_raiz.to_dict()
            if 'atributo' in dict_para_guardar:
                del dict_para_guardar['atributo']
            obj[nombre_maquina] = dict_para_guardar
        data = json.dumps(obj, indent=2, ensure_ascii=False)
        with open(path, 'w', encoding='utf8') as f:
            f.write(data)
        return data

    # ------------- CONSULTA ----------------------------
    def listar_maquinas(self) -> List[str]:
        return list(self.maquinas.keys())

    def get_arbol_maquina(self, nombre_maquina: str) -> Optional[Nodo]:
        nodo = self.maquinas.get(nombre_maquina)
        if not nodo:
            raise ValueError(f"No se encontró la máquina: {nombre_maquina}")
        return nodo

    def find_nodo_by_path(self, nombre_maquina: str, path: List[str]) -> Optional[Nodo]:
        nodo_actual = self.get_arbol_maquina(nombre_maquina)
        if nodo_actual is None:
            return None
        for nombre_atributo in path:
            siguiente_nodo = nodo_actual.find_rama_by_nombre(nombre_atributo)
            if siguiente_nodo is None:
                raise ValueError(f"No se pudo encontrar el síntoma '{nombre_atributo}' en la ruta.")
            nodo_actual = siguiente_nodo
        return nodo_actual

    # ------------- EDICIÓN (con restructuración explícita) ----------------------------

    def agregar_maquina(self, nombre_maquina: str) -> bool:
        if nombre_maquina in self.maquinas:
            raise ValueError(f"La máquina '{nombre_maquina}' ya existe.")
        self.maquinas[nombre_maquina] = Nodo(
            nombre=nombre_maquina,
            pregunta=f"¿Cuál es el síntoma principal de {nombre_maquina}?"
        )
        self.to_json()
        return True

    def agregar_rama(self, nombre_maquina: str, path_padre: List[str], nuevo_nodo_dict: dict) -> bool:
        nodo_padre = self.find_nodo_by_path(nombre_maquina, path_padre)
        if nodo_padre is None:
            raise ValueError("El path (ruta) al nodo padre no existe.")
        # Permite agregar ramas únicamente a nodos de pregunta ("ramas" debe existir)
        if nodo_padre.es_hoja():
            raise ValueError("No se puede agregar una rama a un nodo que es una falla. Use restructuración para dividir el nodo.")
        nuevo_nodo = Nodo.from_dict(nuevo_nodo_dict)
        if not nuevo_nodo.nombre:
            raise ValueError("El nuevo síntoma o falla debe tener un 'atributo' (nombre).")
        if nodo_padre.find_rama_by_nombre(nuevo_nodo.nombre):
            raise ValueError(f"El síntoma/atributo '{nuevo_nodo.nombre}' ya existe en este nivel.")
        nodo_padre.agregar_rama(nuevo_nodo)
        self.to_json()
        return True

    def agregar_solucion(self, nombre_maquina: str, path_a_falla: List[str], nueva_solucion: str) -> bool:
        nodo_falla = self.find_nodo_by_path(nombre_maquina, path_a_falla)
        if nodo_falla is None:
            raise ValueError("El path (ruta) al nodo de falla no existe.")
        if not nodo_falla.es_hoja():
            raise ValueError("El nodo seleccionado no es un nodo de falla.")
        if nueva_solucion not in nodo_falla.soluciones:
            nodo_falla.soluciones.append(nueva_solucion)
            self.to_json()
            return True
        raise ValueError("La solución ya existe para esta falla.")

    def restructurar_falla_a_pregunta(
        self,
        nombre_maquina: str,
        path_a_hoja: List[str],
        pregunta_nueva: str,
        atributo_existente: str,
        falla_existente_dict: dict,
        atributo_nuevo: str,
        falla_nueva_dict: dict
        ) -> bool:
        """
        Convierte un nodo hoja (la falla actual) en un nodo intermedio con:
        - Su mismo atributo
        - La pregunta redactada por el usuario
        - Dos hijos/ramas hoja: una con los datos de la falla anterior, otra con la falla nueva.
        """

        # 1. Buscar el nodo hoja a restructurar
        nodo = self.find_nodo_by_path(nombre_maquina, path_a_hoja)
        if not nodo:
            raise ValueError("No se encontró el nodo hoja a restructurar.")

        atributo_anterior = nodo.nombre  # Guardar por claridad, aunque no se vuelve a usar

        # 2. Extraer info de la falla vieja antes de sobreescribir
        # (falla_existente_dict debería venir directo del frontend, pero igual validamos...)
        # -- Esta parte depende si usas el modelo que lo recibe desde frontend, si no:
        # falla_existente_dict = {
        #     "falla": nodo.falla,
        #     "soluciones": nodo.soluciones,
        #     "referencia": nodo.referencia,
        # }
        # El frontend puede enviar los datos actualizados para asegurar integridad.

        # 3. Limpiar el nodo y convertir a nodo de pregunta
        nodo.falla = None
        nodo.soluciones = []
        nodo.referencia = None
        nodo.pregunta = pregunta_nueva
        nodo.ramas = []

        # 4. Agregar ramas con nuevas opciones/atributos (ambas hojas)
        falla_existente_dict["atributo"] = atributo_existente
        rama_vieja = Nodo.from_dict(falla_existente_dict)
        falla_nueva_dict["atributo"] = atributo_nuevo
        rama_nueva = Nodo.from_dict(falla_nueva_dict)

        nodo.agregar_rama(rama_vieja)
        nodo.agregar_rama(rama_nueva)

        self.to_json()
        return True

