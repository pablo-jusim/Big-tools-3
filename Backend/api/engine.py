"""
engine.py
Motor de inferencia del sistema experto de diagnóstico de máquinas.
Adaptado a la ESTRUCTURA SIMPLIFICADA (sin "categorias").
"""

from typing import Optional, List, Dict, Any
from api.base_conocimiento import BaseConocimiento
from api.nodo import Nodo

class MotorInferencia:
    """
    Motor que recorre el árbol de conocimiento de una máquina,
    procesando respuestas (atributos) hasta detectar la falla.
    """

    def __init__(self, base: BaseConocimiento):
        self.base = base
        self.maquina_actual: Optional[str] = None
        self.nodo_actual: Optional[Nodo] = None
        self.ruta: List[Nodo] = []
        # Path de atributos hasta la última pregunta
        self.path_pregunta_actual: List[str] = []

    # ------------------- FLUJO PRINCIPAL ---------------------

    def iniciar_diagnostico(self, nombre_maquina: str) -> dict:
        """
        Inicia el diagnóstico cargando el nodo raíz y devolviendo la primera pregunta.
        """
        self.maquina_actual = nombre_maquina

        nodo_raiz = self.base.get_arbol_maquina(nombre_maquina) 
        if not nodo_raiz:
            raise ValueError(f"No se encontró la máquina '{nombre_maquina}'.")

        self.nodo_actual = nodo_raiz
        self.ruta = [nodo_raiz]
        self.path_pregunta_actual = []  # El nodo raíz es la primera pregunta

        return self._pregunta_actual()

    def avanzar(self, respuesta_atributo: str) -> dict:
        """
        Avanza un paso en el árbol según la opción seleccionada.
        """
        if not self.nodo_actual:
            return {"mensaje": "El diagnóstico no se ha iniciado. Use 'iniciar_diagnostico'."}

        # Buscar el hijo según el atributo seleccionado
        siguiente_nodo = self.nodo_actual.find_rama_by_nombre(respuesta_atributo)
        if not siguiente_nodo:
            print(f"Error en motor: Respuesta '{respuesta_atributo}' no encontrada en nodo '{self.nodo_actual.nombre}'.")
            return self._pregunta_actual()

        self.nodo_actual = siguiente_nodo
        self.ruta.append(siguiente_nodo)

        # Avance automático sobre contenedores mudos (nodo sin pregunta y con una sola rama)
        while (
            not self.nodo_actual.pregunta
            and self.nodo_actual.ramas 
            and len(self.nodo_actual.ramas) == 1
        ):
            hijo_unico = self.nodo_actual.ramas[0]
            self.nodo_actual = hijo_unico
            self.ruta.append(hijo_unico)
            if self.nodo_actual.es_hoja():
                # No actualizamos path_pregunta_actual: queda atascado en el padre
                return self._resultado_final(self.nodo_actual)

        # Si es hoja (tiene una falla), devolver resultado final
        if self.nodo_actual.es_hoja():
            # path_pregunta_actual no cambia (queda detenido en el nodo de pregunta padre)
            return self._resultado_final(self.nodo_actual)

        # Si es una pregunta, actualizar path hasta este punto
        self.path_pregunta_actual = self.get_historial_path_completo()
        return self._pregunta_actual()

    # ------------------- FUNCIONES AUXILIARES ----------------

    def _pregunta_actual(self) -> dict:
        """
        Devuelve la pregunta y las opciones del nodo actual.
        """
        if self.nodo_actual is None:
            return {"mensaje": "No hay un nodo activo en el diagnóstico."}
        
        texto_pregunta = self.nodo_actual.pregunta
        if not texto_pregunta:
            texto_pregunta = f"¿Qué observa en '{self.nodo_actual.nombre}'?"

        opciones = [r.nombre for r in self.nodo_actual.ramas if r.nombre]
        return {"pregunta": texto_pregunta, "opciones": opciones}

    def _resultado_final(self, nodo_falla: Nodo) -> dict:
        """
        Devuelve el resultado final del diagnóstico (una hoja).
        """
        return {
            "falla": nodo_falla.falla,
            "soluciones": nodo_falla.soluciones,
            "referencia": nodo_falla.referencia
        }

    def get_historial_path_completo(self) -> List[str]:
        """
        Devuelve los atributos seleccionados hasta el nodo actual (sin incluir el raíz).
        """
        if not self.ruta or len(self.ruta) < 2:
            return []
        return [nodo.nombre for nodo in self.ruta[1:]]

    def get_path_a_pregunta(self) -> List[str]:
        """
        Devuelve el path de atributos hasta el último nodo de pregunta alcanzado.
        """
        return self.path_pregunta_actual

    def reiniciar(self):
        """
        Reinicia el motor para un nuevo diagnóstico.
        """
        self.nodo_actual = None
        self.maquina_actual = None
        self.ruta = []
        self.path_pregunta_actual = []
