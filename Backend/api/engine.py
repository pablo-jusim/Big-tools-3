"""
engine.py
Motor de inferencia del sistema experto de diagnóstico de máquinas.
Adaptado a flujo de categorías y opciones fijas.
Compatible con BaseConocimiento y Nodo actuales.
"""

from typing import Optional, List
from Backend.api.base_conocimiento import BaseConocimiento
from Backend.api.nodo import Nodo


class MotorInferencia:
    """
    Motor que recorre el árbol de conocimiento de una máquina,
    procesando respuestas de selección múltiple,
    hasta detectar la falla y ofrecer posibles soluciones.
    """

    def __init__(self, base: BaseConocimiento):
        self.base = base
        self.resultado: Optional[Nodo] = None
        self.maquina_actual: Optional[str] = None
        self.categorias: List[Nodo] = []
        self.nodo_actual: Optional[Nodo] = None
        self.ruta: List[Nodo] = []

    # -------------------------------------------------------------------------
    # MÉTODOS PRINCIPALES
    # -------------------------------------------------------------------------

    def iniciar_diagnostico(self, nombre_maquina: str) -> dict:
        """
        Inicializa el diagnóstico para una máquina.
        Devuelve la lista de categorías disponibles.
        """
        self.maquina_actual = nombre_maquina
        self.categorias = self.base.maquinas.get(nombre_maquina, [])

        if not self.categorias:
            raise ValueError(f"No hay categorías disponibles para la máquina '{nombre_maquina}'.")

        self.resultado = None
        self.nodo_actual = None
        self.ruta = []

        # Retornamos las categorías para que el frontend las muestre
        return {"categorias": [cat.nombre for cat in self.categorias]}

    def seleccionar_categoria(self, categoria: str) -> dict:
        """
        Selecciona una categoría dentro de la máquina y devuelve la primera pregunta.
        Añade lógica para "avanzar" si la categoría es solo un contenedor.
        """
        nodo = next((c for c in self.categorias if c.nombre == categoria), None)
        if not nodo:
            raise ValueError(f"No se encontró la categoría '{categoria}' en la máquina '{self.maquina_actual}'.")

        self.nodo_actual = nodo
        self.ruta = [nodo]

        # Si la categoría es un nodo hoja directo (ej: "El aparato no funciona")
        if nodo.es_hoja():
            self.resultado = nodo
            return self._resultado_final(nodo)
        
        # Si el nodo de categoría NO tiene pregunta, pero SÍ tiene ramas,
        # es un contenedor. Debemos avanzar automáticamente.
        if not nodo.pregunta and nodo.ramas:
            
            # Caso 1: La categoría apunta a una falla directa 
            # (Ej: "El aparato no funciona / no se pone en marcha")
            if len(nodo.ramas) == 1 and nodo.ramas[0].es_hoja():
                self.nodo_actual = nodo.ramas[0]
                self.ruta.append(self.nodo_actual)
                self.resultado = self.nodo_actual
                return self._resultado_final(self.nodo_actual)

            # Caso 2: La categoría apunta a un nodo de pregunta 
            # (Ej: "Una luz parpadea")
            if len(nodo.ramas) == 1 and nodo.ramas[0].pregunta:
                self.nodo_actual = nodo.ramas[0] # Avanzamos al nodo de la pregunta
                self.ruta.append(self.nodo_actual)
                # Ahora self.nodo_actual SÍ tiene la pregunta y las opciones correctas.

        # Retornamos la pregunta y opciones del nodo actual
        # (que ahora es el nodo de pregunta correcto, no el de categoría)
        return self._pregunta_actual()

    def avanzar(self, respuesta: str) -> dict:
        """
        Avanza un paso en el árbol según la opción seleccionada por el usuario.
        """
        if not self.nodo_actual:
            return {"error": "No se ha seleccionado una categoría. Use 'seleccionar_categoria'."}

        nodo = self.nodo_actual

        # Buscar la rama correspondiente a la respuesta (nombre, atributo o categoria)
        siguiente = next(
            (r for r in nodo.ramas
             if r.nombre == respuesta
             or getattr(r, "atributo", None) == respuesta
             or getattr(r, "categoria", None) == respuesta),
            None
        )

        if not siguiente:
            # Opciones disponibles si no se encuentra la respuesta
            opciones = [r.nombre or getattr(r, "atributo", "") or getattr(r, "categoria", "")
                        for r in nodo.ramas]
            return {
                "mensaje": f"No se encontró la opción '{respuesta}'.",
                "opciones": opciones
            }

        # Avanzar al siguiente nodo
        self.nodo_actual = siguiente
        self.ruta.append(siguiente)

        # Si llegamos a un nodo hoja, devolvemos el resultado final
        if siguiente.es_hoja():
            self.resultado = siguiente
            return self._resultado_final(siguiente)

        # Si el nodo actual tiene pregunta y opciones
        return self._pregunta_actual()

    # -------------------------------------------------------------------------
    # MÉTODOS AUXILIARES
    # -------------------------------------------------------------------------

    def _pregunta_actual(self) -> dict:
        """
        Devuelve la pregunta y las opciones del nodo actual.
        """
        nodo = self.nodo_actual
        if nodo is None:
            return {"mensaje": "No hay un nodo activo en el diagnóstico."}

        # Determinar el texto de la pregunta
        if nodo.pregunta:
            texto_pregunta = nodo.pregunta
        elif getattr(nodo, "categoria", None):
            texto_pregunta = f"Elige una opción dentro de la categoría '{nodo.categoria}':"
        elif nodo.nombre:
            texto_pregunta = f"Selecciona una opción relacionada con '{nodo.nombre}':"
        else:
            texto_pregunta = "Selecciona una opción:"

        # Generar lista de opciones (usa nombre, atributo o categoría)
        opciones = []
        if nodo.ramas:
            for r in nodo.ramas:
                if r.nombre:
                    opciones.append(r.nombre)
                elif getattr(r, "atributo", None):
                    opciones.append(r.atributo)
                elif getattr(r, "categoria", None):
                    opciones.append(r.categoria)

        return {
            "pregunta": texto_pregunta,
            "opciones": opciones
        }

    def _resultado_final(self, nodo: Nodo) -> dict:
        """
        Devuelve el resultado final del diagnóstico.
        """
        return {
            "maquina": self.maquina_actual,
            "falla": nodo.falla,
            "referencia": getattr(nodo, "referencia", None),
            "soluciones": nodo.soluciones
        }

    def reiniciar(self):
        """
        Reinicia el motor para un nuevo diagnóstico.
        """
        self.resultado = None
        self.nodo_actual = None
        self.maquina_actual = None
        self.categorias = []
        self.ruta = []


# Ejemplo conceptual dentro de engine.py
# (Se asume que tienes acceso a la Entry_Final)

def finalizar_diagnostico(entry_final):
    # 1. Obtener el mensaje final
    mensaje = entry_final.get_prop('MENSAJE_FINAL') 
    
    # 2. Obtener la referencia del PDF (la propiedad que añadimos)
    referencia = entry_final.get_prop('REFERENCIA_FINAL')
    
    # 3. Retornar la respuesta usando la función actualizada
    return response.create_final_response(
        mensaje_final=mensaje,
        referencia_pdf=referencia  # Pasa el link completo aquí
    )
