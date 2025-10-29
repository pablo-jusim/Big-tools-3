from typing import List, Optional

class Nodo:
    """
    Representa un nodo en el árbol de conocimiento de una máquina.
    """

    def __init__(self, nombre: Optional[str] = None, categoria: Optional[str] = None,
                 atributo: Optional[str] = None, pregunta: Optional[str] = None,
                 falla: Optional[str] = None, soluciones: Optional[List[str]] = None,
                 referencia: Optional[str] = None):
        self.nombre = nombre or categoria or ""
        self.categoria = categoria  # Para nodos raíz de categorías
        self.atributo = atributo or ""
        self.pregunta = pregunta
        self.falla = falla
        self.soluciones = soluciones or []
        self.referencia = referencia
        self.ramas: List['Nodo'] = []

    def agregar_rama(self, nodo_hijo: 'Nodo'):
        """Agrega una rama (subnodo) al nodo actual."""
        self.ramas.append(nodo_hijo)

    def es_hoja(self) -> bool:
        """Determina si el nodo es una hoja (sin ramas o con falla)."""
        return len(self.ramas) == 0 and self.falla is not None

    def to_dict(self) -> dict:
        """Convierte el nodo y sus ramas a un diccionario para JSON."""
        return {
            "nombre": self.nombre,
            "categoria": self.categoria,
            "atributo": self.atributo,
            "pregunta": self.pregunta,
            "falla": self.falla,
            "soluciones": self.soluciones,
            "referencia": self.referencia,
            "ramas": [rama.to_dict() for rama in self.ramas]
        }

    @staticmethod
    def from_dict(data: dict) -> 'Nodo':
        """
        Crea un nodo a partir de un diccionario.
        Detecta 'categoria' si no hay 'nombre'.
        """
        nodo = Nodo(
            nombre=data.get("nombre") or data.get("categoria"),
            categoria=data.get("categoria"),
            atributo=data.get("atributo"),
            pregunta=data.get("pregunta"),
            falla=data.get("falla"),
            soluciones=data.get("soluciones", []),
            referencia=data.get("referencia")
        )
        for rama_data in data.get("ramas", []):
            nodo.agregar_rama(Nodo.from_dict(rama_data))
        return nodo

    def __repr__(self):
        return f"Nodo({self.nombre or self.categoria}, ramas={len(self.ramas)})"
