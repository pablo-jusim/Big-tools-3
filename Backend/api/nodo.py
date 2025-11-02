"""
nodo.py
Define la clase Nodo, que es la estructura de datos
fundamental del árbol de conocimiento.
"""

from typing import List, Optional, Dict, Any

class Nodo:
    """
    Representa un nodo en el árbol de conocimiento de una máquina.
    Un nodo puede ser una pregunta (con ramas) o una falla (hoja).
    
    El 'nombre' de un nodo es el texto de la opción (el "atributo" en el JSON)
    que el usuario selecciona para llegar a él.
    """

    def __init__(self, 
                 nombre: Optional[str] = None,
                 pregunta: Optional[str] = None,
                 falla: Optional[str] = None,
                 soluciones: Optional[List[str]] = None,
                 referencia: Optional[str] = None):
        """
        Constructor del Nodo.
        - nombre: El texto de la opción que lleva a este nodo (viene de "atributo" en el JSON).
        - pregunta: El texto que el bot muestra si este nodo es una pregunta.
        - falla: El diagnóstico final si este nodo es una hoja.
        """
        self.nombre = nombre or ""
        self.pregunta = pregunta
        self.falla = falla
        self.soluciones = soluciones or []
        self.referencia = referencia
        self.ramas: List['Nodo'] = []

    def agregar_rama(self, nodo_hijo: 'Nodo'):
        """Agrega una rama (subnodo) al nodo actual."""
        self.ramas.append(nodo_hijo)

    def es_hoja(self) -> bool:
        """Determina si el nodo es una hoja (tiene una falla)."""
        # Un nodo es una hoja si tiene un diagnóstico de "falla".
        return self.falla is not None

    def find_rama_by_nombre(self, nombre_buscado: str) -> Optional['Nodo']:
        """
        Busca en las ramas hijas un nodo cuyo 'nombre' coincida.
        Este es el método que engine.py necesita.
        """
        for rama in self.ramas:
            if rama.nombre == nombre_buscado:
                return rama
        return None # No se encontró

    def to_dict(self) -> dict:
        """
        Convierte el objeto Nodo y sus ramas de nuevo a un
        diccionario listo para ser guardado como JSON.
        """
        obj: Dict[str, Any] = {}

        # --- LÓGICA INVERSA A from_dict ---
        # Guardamos self.nombre (que es el texto de la opción)
        # de vuelta en la clave "atributo".
        if self.nombre:
            obj["atributo"] = self.nombre
            
        if self.pregunta:
            obj["pregunta"] = self.pregunta
        if self.falla:
            obj["falla"] = self.falla
        if self.soluciones:
            obj["soluciones"] = self.soluciones
        if self.referencia:
            obj["referencia"] = self.referencia
        
        # Agregamos las ramas recursivamente
        if self.ramas:
            obj["ramas"] = [rama.to_dict() for rama in self.ramas]
        
        return obj

    @staticmethod
    def from_dict(data: dict) -> 'Nodo':
        """
        Método estático para crear un árbol de Nodos
        a partir de un diccionario (leído del JSON).
        
        --- ESTA ES LA CORRECCIÓN CLAVE ---
        """
        
        # El "nombre" del Nodo (la opción que el usuario ve)
        # se toma de la clave "atributo" en el JSON.
        # Si no hay "atributo" (ej. en el nodo raíz de la máquina),
        # usamos "nombre" (que base_conocimiento.py agrega).
        nombre_nodo = data.get("atributo") or data.get("nombre")

        nodo = Nodo(
            nombre=nombre_nodo,
            pregunta=data.get("pregunta"),
            falla=data.get("falla"),
            soluciones=data.get("soluciones", []),
            referencia=data.get("referencia")
        )
        
        for rama_data in data.get("ramas", []):
            nodo.agregar_rama(Nodo.from_dict(rama_data))
            
        return nodo

    def __repr__(self):
        """Representación de texto para depuración."""
        if self.falla:
            return f"Nodo(FALLA: {self.falla})"
        if self.pregunta:
             return f"Nodo(PREGUNTA: {self.pregunta}, RAMAS: {len(self.ramas)})"
        return f"Nodo({self.nombre}, RAMAS: {len(self.ramas)})"

