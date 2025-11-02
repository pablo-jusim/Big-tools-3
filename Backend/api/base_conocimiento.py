"""
base_conocimiento.py
Clase para gestionar la base de conocimientos de máquinas.
Adaptado a la ESTRUCTURA SIMPLIFICADA (sin "categorias")
"""

from typing import Dict, Any, List, Optional
import json
from pathlib import Path
from Backend.api.nodo import Nodo # Asumimos que nodo.py existe y está correcto

JSON_LATEST = 1
DEFAULT_JSON = "Backend/data/base_conocimiento.json" 


class BaseConocimiento:
    """
    Clase principal de la base de conocimientos para el sistema experto.
    Gestiona la carga, almacenamiento y consulta de la base desde archivos JSON.
    """

    def __init__(self, archivo_json: str = DEFAULT_JSON):
        self.archivo_path = Path(archivo_json)
        self.description = "Base de conocimientos de máquinas"
        
        # CAMBIO CLAVE:
        # self.maquinas ya no es Dict[str, List[Nodo]]
        # Ahora es un diccionario que mapea el nombre de la máquina a su ÚNICO Nodo raíz.
        self.maquinas: Dict[str, Nodo] = {} 
        
        self.from_json(self.archivo_path) # carga automática al instanciar

    # -------------------------------------------------------------------------
    # MÉTODOS DE CARGA Y GUARDADO
    # -------------------------------------------------------------------------

    def from_json(self, filename: Path):
        """
        Carga una base de conocimientos desde un archivo JSON.
        Convierte cada máquina en un objeto Nodo raíz.
        """
        if not filename.exists():
            print(f"Archivo {filename} no encontrado. Se creará uno nuevo al guardar.")
            self.maquinas = {}
            return self

        with open(filename, 'r', encoding='utf8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"Error al decodificar {filename}. La base de conocimientos está vacía.")
                self.maquinas = {}
                return self

        if "__v" in data and data["__v"] != JSON_LATEST:
            raise ValueError("Actualizar JSON a nueva versión")

        self.description = data.get("description", self.description)
        self.maquinas = {}

        # --- LÓGICA DE CARGA MODIFICADA ---
        # Ahora data.items() son (nombre_maquina, arbol_dict)
        for nombre_maquina, arbol_dict in data.items():
            if nombre_maquina.startswith("__"): # Ignorar __v y description
                continue
            
            # Asignamos el nombre de la máquina al nodo raíz para coherencia
            arbol_dict['nombre'] = nombre_maquina 
            
            # Convertimos el diccionario del árbol de la máquina en un objeto Nodo
            self.maquinas[nombre_maquina] = Nodo.from_dict(arbol_dict)

        return self

    def to_json(self, filename: Optional[Path] = None):
        """
        Guarda la base de conocimientos (en memoria) en un archivo JSON.
        Convierte cada árbol de Nodo a diccionario.
        """
        path = filename or self.archivo_path
        
        obj = {
            "__v": JSON_LATEST,
            "description": self.description
        }

        for nombre_maquina, nodo_raiz in self.maquinas.items():
            # Convertimos el Nodo raíz de nuevo a un diccionario
            obj[nombre_maquina] = nodo_raiz.to_dict()
            # Opcional: limpiar el 'nombre' que agregamos al cargar
            if 'nombre' in obj[nombre_maquina]:
                 del obj[nombre_maquina]['nombre'] 


        data = json.dumps(obj, indent=2, ensure_ascii=False)
        with open(path, 'w', encoding='utf8') as f:
            f.write(data)
        return data

    # -------------------------------------------------------------------------
    # MÉTODOS DE CONSULTA
    # -------------------------------------------------------------------------

    def listar_maquinas(self) -> List[str]:
        """Devuelve una lista de todas las máquinas registradas en la base."""
        return list(self.maquinas.keys())

    def get_arbol_maquina(self, nombre_maquina: str) -> Optional[Nodo]:
        """Devuelve el NODO RAÍZ de una máquina específica."""
        return self.maquinas.get(nombre_maquina)

    # --- MÉTODOS DE EDICIÓN (para las nuevas funciones) ---

    def agregar_maquina(self, nombre_maquina: str) -> bool:
        """Agrega una nueva máquina (vacía) a la base."""
        if nombre_maquina in self.maquinas:
            return False # Ya existe

        # Creamos un nodo raíz vacío para la nueva máquina
        self.maquinas[nombre_maquina] = Nodo(
            nombre=nombre_maquina,
            pregunta=f"¿Cuál es el síntoma principal de {nombre_maquina}?",
            ramas=[]
        )
        self.to_json() # Guardar cambios
        return True

    def find_nodo_by_path(self, nombre_maquina: str, path: List[str]) -> Optional[Nodo]:
        """
        Encuentra un nodo específico siguiendo un 'path' de atributos (respuestas).
        Un path vacío [] devuelve el nodo raíz de la máquina.
        """
        nodo_actual = self.get_arbol_maquina(nombre_maquina)
        if nodo_actual is None:
            return None

        for nombre_atributo in path:
            siguiente_nodo = nodo_actual.find_rama_by_nombre(nombre_atributo)
            if siguiente_nodo is None:
                # El path está roto o no existe
                return None 
            nodo_actual = siguiente_nodo
            
        return nodo_actual

    def agregar_nodo(self, nombre_maquina: str, path_padre: List[str], nuevo_nodo_data: dict) -> bool:
        """
        Agrega un nuevo nodo (síntoma, falla o pregunta) en una ubicación
        específica del árbol.
        """
        # 1. Encontrar el nodo padre donde queremos agregar la rama
        nodo_padre = self.find_nodo_by_path(nombre_maquina, path_padre)
        if nodo_padre is None:
            raise ValueError("El path (ruta) al nodo padre no existe.")

        # 2. Convertir los datos del nuevo nodo en un objeto Nodo
        nuevo_nodo = Nodo.from_dict(nuevo_nodo_data)
        
        # 3. Validar que no sea un duplicado
        if nodo_padre.find_rama_by_nombre(nuevo_nodo.nombre):
             raise ValueError(f"El síntoma/atributo '{nuevo_nodo.nombre}' ya existe en este nivel.")

        # 4. Agregar la nueva rama
        nodo_padre.ramas.append(nuevo_nodo)
        
        # 5. Guardar toda la base de conocimientos en el archivo
        self.to_json() 
        return True

    def agregar_solucion(self, nombre_maquina: str, path_a_falla: List[str], nueva_solucion: str) -> bool:
        """
        Agrega una nueva solución a un nodo de falla existente.
        """
        # 1. Encontrar el nodo de la falla
        nodo_falla = self.find_nodo_by_path(nombre_maquina, path_a_falla)
        
        if nodo_falla is None:
            raise ValueError("El path (ruta) al nodo de falla no existe.")
        
        if not nodo_falla.es_hoja():
             raise ValueError("El nodo seleccionado no es un nodo de falla (aún tiene ramas).")
             
        # 2. Agregar la solución
        if nueva_solucion not in nodo_falla.soluciones:
            nodo_falla.soluciones.append(nueva_solucion)
            
            # 3. Guardar cambios
            self.to_json()
            return True
        return False # La solución ya existía

    def __str__(self):
        resumen = f"{self.description}\nMáquinas registradas: {', '.join(self.listar_maquinas())}"
        return resumen

