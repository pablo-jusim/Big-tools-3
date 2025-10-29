"""
engine.py
Motor de inferencia del sistema experto de diagnóstico de máquinas.
"""

from typing import Optional, List
from api.base_conocimiento import BaseConocimiento
from api.nodo import Nodo
from api.response import Response, ChoiceResponse


class MotorInferencia:
    """
    Motor que recorre el árbol de conocimiento de una máquina,
    procesando respuestas binarias o de selección múltiple,
    hasta detectar la falla y ofrecer posibles soluciones.
    """

    def __init__(self, base: BaseConocimiento):
        self.base = base
        self.resultado: Optional[Nodo] = None
        self.maquina_actual: Optional[str] = None
        self.nodo_actual: Optional[Nodo] = None
        self.ruta: List[Nodo] = []

    # -------------------------------------------------------------------------
    # MÉTODOS PRINCIPALES
    # -------------------------------------------------------------------------

    def iniciar_diagnostico(self, nombre_maquina: str) -> Nodo:
        """
        Inicializa el diagnóstico para una máquina.
        :param nombre_maquina: Nombre de la máquina a diagnosticar
        :return: Nodo inicial para comenzar el recorrido
        """
        self.maquina_actual = nombre_maquina
        nodo_raiz = self.base.get_arbol(nombre_maquina)

        if not nodo_raiz:
            raise ValueError(f"No se encontró la máquina '{nombre_maquina}' en la base de conocimiento.")

        self.nodo_actual = nodo_raiz
        self.ruta = [nodo_raiz]
        return nodo_raiz

    def avanzar(self, respuesta: Optional[str] = None) -> dict:
        """
        Avanza en el árbol según la respuesta recibida.
        :param respuesta: respuesta del usuario ('sí'/'no' o texto de selección)
        :return: diccionario con la siguiente pregunta, opciones o resultado final
        """
        if not self.nodo_actual:
            return {"error": "No se ha iniciado el diagnóstico. Use 'iniciar_diagnostico'."}

        nodo = self.nodo_actual

        # Caso hoja: fin del recorrido
        if nodo.es_hoja():
            self.resultado = nodo
            return self._resultado_final(nodo)

        # Nodo con pregunta
        if nodo.pregunta and nodo.ramas:
            # Si es binario
            if len(nodo.ramas) == 2 and all(r.nombre.lower() in ("sí", "si", "no") for r in nodo.ramas):
                if respuesta is None:
                    return {"pregunta": nodo.pregunta, "tipo": "binaria", "opciones": ["sí", "no"]}

                resp_enum = Response.YES if respuesta.lower() in ("sí", "si", "s") else Response.NO
                siguiente = next(
                    r for r in nodo.ramas
                    if (r.nombre.lower() in ("sí", "si") and resp_enum == Response.YES)
                    or (r.nombre.lower() == "no" and resp_enum == Response.NO)
                )

            # Selección múltiple
            else:
                if respuesta is None:
                    return {
                        "pregunta": nodo.pregunta,
                        "tipo": "multiple",
                        "opciones": [r.nombre for r in nodo.ramas]
                    }

                opcion = ChoiceResponse(respuesta)
                siguiente = next((r for r in nodo.ramas if opcion.is_equal(r.nombre)), None)
                if not siguiente:
                    return {"error": f"Opción inválida. Las opciones válidas son {[r.nombre for r in nodo.ramas]}"}

            # Avanzar
            self.nodo_actual = siguiente
            self.ruta.append(siguiente)
            return self.avanzar()  # Llamada recursiva para procesar siguiente paso

        # Nodo sin pregunta pero con ramas (flujo automático)
        elif nodo.ramas:
            self.nodo_actual = nodo.ramas[0]
            self.ruta.append(nodo.ramas[0])
            return self.avanzar()

        # Nodo sin ramas ni pregunta
        self.resultado = nodo
        return self._resultado_final(nodo)

    def _resultado_final(self, nodo: Nodo) -> dict:
        """
        Devuelve el resultado final del diagnóstico.
        """
        if nodo.falla:
            return {
                "maquina": self.maquina_actual,
                "falla": nodo.falla,
                "soluciones": nodo.soluciones
            }
        else:
            return {
                "maquina": self.maquina_actual,
                "mensaje": "No se pudo determinar una falla con la información proporcionada."
            }

    def reiniciar(self):
        """
        Reinicia el motor para un nuevo diagnóstico.
        """
        self.resultado = None
        self.nodo_actual = None
        self.maquina_actual = None
        self.ruta = []

