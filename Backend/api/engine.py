"""
engine.py
Motor de inferencia del sistema experto de diagnóstico de máquinas.
Adaptado a la ESTRUCTURA SIMPLIFICADA (sin "categorias")
"""

from typing import Optional, List, Dict, Any
from Backend.api.base_conocimiento import BaseConocimiento
from Backend.api.nodo import Nodo


class MotorInferencia:
    """
    Motor que recorre el árbol de conocimiento de una máquina,
    procesando respuestas (atributos) hasta detectar la falla.
    """

    def __init__(self, base: BaseConocimiento):
        self.base = base
        self.maquina_actual: Optional[str] = None
        self.nodo_actual: Optional[Nodo] = None
        
        # self.ruta almacena los Nodos por los que se ha pasado
        self.ruta: List[Nodo] = []

    # -------------------------------------------------------------------------
    # MÉTODOS PRINCIPALES (Llamados por routes.py)
    # -------------------------------------------------------------------------

    def iniciar_diagnostico(self, nombre_maquina: str) -> dict:
        """
        Paso 1: Inicializa el diagnóstico para una máquina.
        Carga el NODO RAÍZ y devuelve la primera pregunta.
        """
        self.maquina_actual = nombre_maquina
        
        # Obtenemos el NODO RAÍZ de la máquina desde la base
        nodo_raiz = self.base.get_arbol_maquina(nombre_maquina) 

        if not nodo_raiz:
            raise ValueError(f"No se encontró la máquina '{nombre_maquina}'.")

        self.nodo_actual = nodo_raiz
        self.ruta = [nodo_raiz] # El nodo raíz es el inicio de nuestra ruta

        # Devolvemos la primera pregunta (ej: "¿Cuál es el síntoma principal?")
        return self._pregunta_actual()


    def avanzar(self, respuesta_atributo: str) -> dict:
        """
        Avanza un paso en el árbol según el 'nombre' (atributo)
        seleccionado por el usuario.
        """
        if not self.nodo_actual:
            return {"mensaje": "El diagnóstico no se ha iniciado. Use 'iniciar_diagnostico'."}

        # Buscamos en las ramas del nodo actual
        # un nodo hijo cuyo 'nombre' coincida con la 'respuesta_atributo'.
        # (Tu nodo.py se encarga de que "atributo" se vuelva "nombre")
        siguiente_nodo = self.nodo_actual.find_rama_by_nombre(respuesta_atributo)

        if not siguiente_nodo:
            # El usuario envió una respuesta que no existe en las opciones
            print(f"Error en motor: Respuesta '{respuesta_atributo}' no encontrada en nodo '{self.nodo_actual.nombre}'.")
            return self._pregunta_actual() # Devolvemos la pregunta actual

        # Avanzar al siguiente nodo
        self.nodo_actual = siguiente_nodo
        self.ruta.append(siguiente_nodo)

        # Si llegamos a un nodo hoja (falla), devolvemos el resultado final
        if self.nodo_actual.es_hoja():
            return self._resultado_final(self.nodo_actual)

        # Si no, devolvemos la siguiente pregunta
        return self._pregunta_actual()

    # -------------------------------------------------------------------------
    # MÉTODOS AUXILIARES Y DE ESTADO
    # -------------------------------------------------------------------------

    def _pregunta_actual(self) -> dict:
        """
        Devuelve la pregunta y las opciones del nodo actual.
        """
        if self.nodo_actual is None:
            return {"mensaje": "No hay un nodo activo en el diagnóstico."}

        # El texto de la pregunta está en 'nodo.pregunta'
        texto_pregunta = self.nodo_actual.pregunta
        if not texto_pregunta:
             # Fallback si el nodo no tiene pregunta (no debería pasar si el JSON está bien)
             texto_pregunta = f"¿Qué observa en '{self.nodo_actual.nombre}'?"

        # --- CORRECCIÓN CLAVE PARA BOTONES VACÍOS ---
        # Las opciones son el 'nombre' de cada nodo hijo.
        # Tu nodo.py (vía from_dict) convierte "atributo": "..." en nodo.nombre = "..."
        opciones = [r.nombre for r in self.nodo_actual.ramas if r.nombre]
        
        return {
            "pregunta": texto_pregunta,
            "opciones": opciones
        }

    def _resultado_final(self, nodo_falla: Nodo) -> dict:
        """
        Devuelve el resultado final del diagnóstico.
        """
        return {
            "falla": nodo_falla.falla,
            "soluciones": nodo_falla.soluciones,
            "referencia": nodo_falla.referencia
        }

    def get_historial_path(self) -> List[str]:
        """
        Devuelve el historial de 'atributos' (respuestas) que
        llevaron al nodo actual. No incluye el nodo raíz de la máquina.
        Esto es VITAL para saber dónde agregar nuevos nodos.
        """
        if not self.ruta or len(self.ruta) < 2:
            # Path es vacío si solo estamos en el nodo raíz
            return [] 
        
        # self.ruta[0] es el nodo raíz de la máquina.
        # self.ruta[1:] son los nodos de respuesta (atributos).
        # Devolvemos sus nombres.
        return [nodo.nombre for nodo in self.ruta[1:]]

    def reiniciar(self):
        """
        Reinicia el motor para un nuevo diagnóstico.
        """
        self.nodo_actual = None
        self.maquina_actual = None
        self.ruta = []

