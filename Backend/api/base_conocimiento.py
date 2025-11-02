"""
base_conocimiento.py
Clase para gestionar la base de conocimientos de máquinas.
AHORA con lógica de restructuración de nodos.
"""

from typing import Dict, Any, List, Optional
import json
from pathlib import Path
from Backend.api.nodo import Nodo 

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
        self.maquinas: Dict[str, Nodo] = {} 
        self.from_json(self.archivo_path)

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

        for nombre_maquina, arbol_dict in data.items():
            if nombre_maquina.startswith("__") or not isinstance(arbol_dict, dict):
                continue 

            arbol_dict['nombre'] = nombre_maquina 
            self.maquinas[nombre_maquina] = Nodo.from_dict(arbol_dict)

        return self

    def to_json(self, filename: Optional[Path] = None):
        """
        Guarda la base de conocimientos (en memoria) en un archivo JSON.
        """
        path = filename or self.archivo_path
        
        obj = {
            "__v": JSON_LATEST,
            "description": self.description
        }

        for nombre_maquina, nodo_raiz in self.maquinas.items():
            dict_para_guardar = nodo_raiz.to_dict()
            
            # Limpiamos el 'nombre' (atributo) del nodo raíz, 
            # ya que el nombre de la máquina es la clave.
            if 'atributo' in dict_para_guardar:
                 del dict_para_guardar['atributo']

            obj[nombre_maquina] = dict_para_guardar

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
        nodo = self.maquinas.get(nombre_maquina)
        if not nodo:
             raise ValueError(f"No se encontró la máquina: {nombre_maquina}")
        return nodo

    def find_nodo_by_path(self, nombre_maquina: str, path: List[str]) -> Optional[Nodo]:
        """
        Encuentra un nodo específico siguiendo un 'path' de atributos (respuestas).
        Un path vacío [] devuelve el nodo raíz de la máquina.
        """
        nodo_actual = self.get_arbol_maquina(nombre_maquina)
        if nodo_actual is None:
            return None # La máquina no existe

        # Recorremos el path para encontrar el nodo
        for nombre_atributo in path:
            siguiente_nodo = nodo_actual.find_rama_by_nombre(nombre_atributo)
            if siguiente_nodo is None:
                raise ValueError(f"No se pudo encontrar el síntoma '{nombre_atributo}' en la ruta.")
            nodo_actual = siguiente_nodo
            
        return nodo_actual

    # -------------------------------------------------------------------------
    # MÉTODOS DE EDICIÓN (para las nuevas funciones)
    # -------------------------------------------------------------------------

    def agregar_maquina(self, nombre_maquina: str) -> bool:
        """Agrega una nueva máquina (vacía) a la base."""
        if nombre_maquina in self.maquinas:
            raise ValueError(f"La máquina '{nombre_maquina}' ya existe.")

        self.maquinas[nombre_maquina] = Nodo(
            nombre=nombre_maquina,
            pregunta=f"¿Cuál es el síntoma principal de {nombre_maquina}?",
            ramas=[]
        )
        self.to_json() # Guardar cambios
        return True

    def agregar_rama(self, nombre_maquina: str, path_padre: List[str], nuevo_nodo_dict: dict) -> bool:
        """
        Agrega un nuevo nodo (síntoma o falla) a un nodo de PREGUNTA existente.
        """
        nodo_padre = self.find_nodo_by_path(nombre_maquina, path_padre)
        if nodo_padre is None:
            raise ValueError("El path (ruta) al nodo padre no existe.")
            
        if nodo_padre.es_hoja():
            # ¡Este es el error que tenías!
            # Si el padre es una falla, no podemos agregarle ramas.
            raise ValueError("No se puede agregar una rama a un nodo que ya es una falla.")

        nuevo_nodo = Nodo.from_dict(nuevo_nodo_dict)
        
        if not nuevo_nodo.nombre:
             raise ValueError("El nuevo síntoma o falla debe tener un 'atributo' (nombre).")

        if nodo_padre.find_rama_by_nombre(nuevo_nodo.nombre):
             raise ValueError(f"El síntoma/atributo '{nuevo_nodo.nombre}' ya existe en este nivel.")

        nodo_padre.agregar_rama(nuevo_nodo)
        self.to_json() 
        return True

    def agregar_solucion(self, nombre_maquina: str, path_a_falla: List[str], nueva_solucion: str) -> bool:
        """
        Agrega una nueva solución a un nodo de falla existente.
        """
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

    # --- MÉTODO NUEVO Y CLAVE ---
    def restructurar_falla_a_pregunta(
        self, 
        nombre_maquina: str, 
        path_al_contenedor: List[str],
        pregunta_nueva: str,
        
        # Datos de la falla que YA EXISTÍA
        atributo_existente: str, 
        
        # Datos de la falla NUEVA
        atributo_nuevo: str,
        falla_nueva_dict: dict
    ) -> bool:
        """
        Transforma un nodo contenedor de falla única (como "El aparato no funciona")
        en un nodo de pregunta para diferenciar entre la falla antigua y la nueva.
        """
        
        # 1. Encontrar el nodo contenedor (ej: "El aparato no funciona...")
        nodo_contenedor = self.find_nodo_by_path(nombre_maquina, path_al_contenedor)
        if not nodo_contenedor:
            raise ValueError("No se encontró el nodo contenedor a restructurar.")
            
        # 2. Verificar que estemos en la situación correcta
        if not (len(nodo_contenedor.ramas) == 1 and nodo_contenedor.ramas[0].es_hoja()):
            raise ValueError("El nodo no es un contenedor de falla única. No se puede restructurar.")
            
        # 3. Guardar el nodo de la falla existente y eliminarlo de las ramas
        nodo_falla_existente = nodo_contenedor.ramas.pop()
        
        # 4. Modificar el nodo contenedor: ahora es un nodo de PREGUNTA
        nodo_contenedor.pregunta = pregunta_nueva
        
        # 5. Modificar el nodo de falla existente:
        #    Ahora SÍ necesita un atributo (nombre) que el usuario le dio
        nodo_falla_existente.nombre = atributo_existente
        
        # 6. Crear el nuevo nodo de falla
        falla_nueva_dict["atributo"] = atributo_nuevo # Asegurarnos que tenga el atributo
        nodo_falla_nueva = Nodo.from_dict(falla_nueva_dict)

        # 7. Agregar ambas fallas como ramas del nodo (ahora de pregunta)
        nodo_contenedor.agregar_rama(nodo_falla_existente)
        nodo_contenedor.agregar_rama(nodo_falla_nueva)
        
        # 8. Guardar todo en el JSON
        self.to_json()
        return True