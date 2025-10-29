"""
engine.py
Motor de inferencia del sistema experto de diagnóstico de máquinas.
"""

from typing import Optional
from api.base_conocimiento import BaseConocimiento
from api.nodo import Nodo


class MotorInferencia:
    """
    Motor que recorre el árbol de conocimiento de una máquina,
    haciendo preguntas al usuario y guiándolo hasta detectar la falla
    y ofrecer posibles soluciones.
    """

    def __init__(self, base: BaseConocimiento):
        self.base = base
        self.resultado: Optional[Nodo] = None
        self.maquina_actual: Optional[str] = None

    # -------------------------------------------------------------------------
    # MÉTODOS PRINCIPALES
    # -------------------------------------------------------------------------

    def diagnosticar(self, nombre_maquina: str):
        """
        Inicia el proceso de diagnóstico para una máquina específica.
        :param nombre_maquina: Nombre de la máquina a diagnosticar
        """
        self.maquina_actual = nombre_maquina
        nodo_actual = self.base.get_arbol(nombre_maquina)

        if not nodo_actual:
            raise ValueError(f"No se encontró la máquina '{nombre_maquina}' en la base de conocimiento.")

        print(f"\n🔧 Iniciando diagnóstico para: {nombre_maquina}")
        self.resultado = self._recorrer_arbol(nodo_actual)

        if self.resultado and self.resultado.falla:
            print(f"\n❗ Falla detectada: {self.resultado.falla}")
            if self.resultado.soluciones:
                print("Posibles soluciones:")
                for i, s in enumerate(self.resultado.soluciones, 1):
                    print(f"  {i}. {s}")
        else:
            print("\n⚠️ No se pudo determinar una falla con la información proporcionada.")

    # -------------------------------------------------------------------------
    # MÉTODOS AUXILIARES
    # -------------------------------------------------------------------------

    def _recorrer_arbol(self, nodo: Nodo) -> Optional[Nodo]:
        """
        Recorre el árbol de conocimiento de forma interactiva.
        Si el nodo es hoja, devuelve el nodo final.
        Si tiene ramas, pregunta según el tipo de respuesta esperada.
        """
        # Caso base: si el nodo es hoja, se encontró una falla o punto final
        if nodo.es_hoja():
            return nodo

        # Mostrar la pregunta asociada al nodo
        if nodo.pregunta:
            print(f"\n{nodo.pregunta}")

            # Si las ramas son binarias (sí/no)
            if len(nodo.ramas) == 2 and all(r.nombre.lower() in ("sí", "no", "si", "no") for r in nodo.ramas):
                respuesta = input("(s/n): ").strip().lower()
                while respuesta not in ("s", "n", "sí", "si", "no"):
                    respuesta = input("Respuesta inválida. Ingrese 's' o 'n': ").strip().lower()

                if respuesta in ("s", "sí", "si"):
                    siguiente = next(r for r in nodo.ramas if r.nombre.lower() in ("sí", "si"))
                else:
                    siguiente = next(r for r in nodo.ramas if r.nombre.lower() == "no")

                return self._recorrer_arbol(siguiente)

            # Si tiene múltiples opciones (más de dos ramas)
            else:
                print("Opciones:")
                for i, rama in enumerate(nodo.ramas, 1):
                    print(f"  {i}. {rama.nombre}")

                opcion = input("Seleccione una opción (número): ").strip()
                while not opcion.isdigit() or int(opcion) not in range(1, len(nodo.ramas) + 1):
                    opcion = input("Opción inválida. Ingrese un número válido: ").strip()

                siguiente = nodo.ramas[int(opcion) - 1]
                return self._recorrer_arbol(siguiente)

        # Si el nodo no tiene pregunta, pero tiene ramas (caso irregular)
        elif nodo.ramas:
            print(f"\nEl nodo '{nodo.nombre}' no tiene pregunta, pero posee ramas. Continuando automáticamente...")
            return self._recorrer_arbol(nodo.ramas[0])

        # Si no hay más ramas ni falla, fin del recorrido
        return nodo
