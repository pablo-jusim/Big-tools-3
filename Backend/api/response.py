from enum import Enum


class Response(Enum):
    """
    Enum de respuesta binaria (Sí/No)
    """
    YES = 1
    NO = 0


class ChoiceResponse:
    """
    Respuesta de selección múltiple (una o varias opciones posibles)
    """
    def __init__(self, choice: str):
        self.choice = choice.strip().lower()

    def __str__(self):
        return self.choice

    def is_equal(self, other: str) -> bool:
        return self.choice == other.strip().lower()
