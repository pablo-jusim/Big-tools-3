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
        
        # self.ruta almacena TODOS los nodos por los que se ha pasado
        self.ruta: List[Nodo] = []
        
        # Almacena el path (lista de atributos) al ÚLTIMO NODO DE PREGUNTA
        self.path_pregunta_actual: List[str] = []

    # -------------------------------------------------------------------------
    # MÉTODOS PRINCIPALES (Llamados por routes.py)
    # -------------------------------------------------------------------------

    def iniciar_diagnostico(self, nombre_maquina: str) -> dict:
        """
        Paso 1: Inicializa el diagnóstico para una máquina.
        Carga el NODO RAÍZ y devuelve la primera pregunta.
        """
        self.maquina_actual = nombre_maquina
        
        nodo_raiz = self.base.get_arbol_maquina(nombre_maquina) 
        if not nodo_raiz:
            raise ValueError(f"No se encontró la máquina '{nombre_maquina}'.")

        self.nodo_actual = nodo_raiz
        self.ruta = [nodo_raiz] # El nodo raíz es el inicio de nuestra ruta
        
        # El nodo raíz es la primera pregunta, su path es vacío []
        self.path_pregunta_actual = [] 

        return self._pregunta_actual()


    def avanzar(self, respuesta_atributo: str) -> dict:
        """
        Avanza un paso en el árbol según el 'nombre' (atributo)
        seleccionado por el usuario.
        """
        if not self.nodo_actual:
            return {"mensaje": "El diagnóstico no se ha iniciado. Use 'iniciar_diagnostico'."}

        # 1. Encontrar el siguiente nodo basado en la respuesta
        siguiente_nodo = self.nodo_actual.find_rama_by_nombre(respuesta_atributo)

        if not siguiente_nodo:
            print(f"Error en motor: Respuesta '{respuesta_atributo}' no encontrada en nodo '{self.nodo_actual.nombre}'.")
            return self._pregunta_actual() # Devolvemos la pregunta actual

        # 2. Avanzar al siguiente nodo
        self.nodo_actual = siguiente_nodo
        self.ruta.append(siguiente_nodo)

        # 3. --- LÓGICA DE AUTO-AVANCE (LA CORRECCIÓN) ---
        # Si el nodo al que llegamos (ej: "El aparato no funciona...")
        # NO tiene pregunta, pero SÍ tiene una única rama,
        # significa que es un "contenedor" y debemos avanzar automáticamente.
        while (not self.nodo_actual.pregunta and 
               self.nodo_actual.ramas and 
               len(self.nodo_actual.ramas) == 1):
            
            # Obtenemos el único hijo
            hijo_unico = self.nodo_actual.ramas[0]

            # Avanzamos al nodo hijo
            self.nodo_actual = hijo_unico 
            self.ruta.append(self.nodo_actual)

            # Si este hijo es una FALLA (Tu bug), paramos y devolvemos el resultado.
            if self.nodo_actual.es_hoja():
                # self.path_pregunta_actual se queda "atascado" en el padre (¡correcto!)
                return self._resultado_final(self.nodo_actual)
            
            # Si el hijo es otra pregunta, el bucle 'while' continuará
            # (aunque en tu JSON actual, el hijo es o una falla o un nodo de pregunta final)

        # 4. Comprobar si hemos llegado a una falla (si no era un contenedor)
        if self.nodo_actual.es_hoja():
            # self.path_pregunta_actual se queda "atascado" en el padre (¡correcto!)
            return self._resultado_final(self.nodo_actual)

        # 5. Si no es una falla, es una pregunta. Actualizamos el path de la pregunta.
        #    get_historial_path_completo() ahora devuelve el path a ESTE nodo de pregunta.
        self.path_pregunta_actual = self.get_historial_path_completo()
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

        texto_pregunta = self.nodo_actual.pregunta
        if not texto_pregunta:
             texto_pregunta = f"¿Qué observa en '{self.nodo_actual.nombre}'?"

        # Las opciones son el 'nombre' de cada nodo hijo.
        # (Tu nodo.py convierte "atributo": "..." en nodo.nombre = "...")
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

    def get_historial_path_completo(self) -> List[str]:
        """
        Devuelve el historial COMPLETO de atributos
        hasta el nodo actual (incluyendo si es una falla).
        Usado por 'agregar_solucion'.
        """
        if not self.ruta or len(self.ruta) < 2:
            return [] 
        # Devuelve todos los nombres (atributos) MENOS el raíz
        return [nodo.nombre for nodo in self.ruta[1:]]

    def get_path_a_pregunta(self) -> List[str]:
        """
        Devuelve el historial de atributos hasta el
        ÚLTIMO NODO DE PREGUNTA.
        Usado por 'agregar_sintoma' y 'agregar_falla'.
        """
        # Esta variable la hemos estado manteniendo actualizada
        return self.path_pregunta_actual

    def reiniciar(self):
        """
        Reinicia el motor para un nuevo diagnóstico.
        """
        self.nodo_actual = None
        self.maquina_actual = None
        self.ruta = []
        self.path_pregunta_actual = []

