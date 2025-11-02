"""
nodo.py
Define la clase Nodo, adaptada a la nueva estructura simplificada.
"""

from typing import List, Optional, Dict, Any

class Nodo:
    """
    Representa un nodo en el árbol de conocimiento de una máquina.
    Un nodo puede ser:
      - la raíz ("pregunta" + "ramas"),
      - un nodo intermedio ("atributo" + "pregunta" + "ramas"),
      - o una hoja ("atributo" + "falla" + "soluciones" + "referencia").
    """
    def __init__(
        self,
        nombre: Optional[str] = None,
        pregunta: Optional[str] = None,
        falla: Optional[str] = None,
        soluciones: Optional[List[str]] = None,
        referencia: Optional[str] = None
    ):
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
        return self.falla is not None

    def find_rama_by_nombre(self, nombre_buscado: str) -> Optional['Nodo']:
        """
        Busca en las ramas hijas un nodo cuyo 'nombre' coincida.
        """
        for rama in self.ramas:
            if rama.nombre == nombre_buscado:
                return rama
        return None

    def to_dict(self) -> dict:
        """
        Convierte el Nodo y sus ramas a un dict para guardar como JSON.
        """
        obj: Dict[str, Any] = {}

        # Siempre mantener la clave "atributo" para opciones del usuario
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
        if self.ramas:
            obj["ramas"] = [rama.to_dict() for rama in self.ramas]

        return obj

    @staticmethod
    def from_dict(data: dict) -> 'Nodo':
        """
        Crea un árbol de Nodos a partir de un dict (base_conocimiento.json).
        """
        # "atributo" es el texto de la opción seleccionable.
        nombre_nodo = data.get("atributo") or data.get("nombre")  # raíz puede no tener atributo

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
        """Dev-friendly representation for debugging."""
        if self.falla:
            return f"Nodo(FALLA: {self.falla})"
        if self.pregunta:
            return f"Nodo(PREGUNTA: {self.pregunta}, RAMAS: {len(self.ramas)})"
        return f"Nodo({self.nombre}, RAMAS: {len(self.ramas)})"
