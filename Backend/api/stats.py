"""
stats.py
Gestor simple de estadísticas del sistema experto: solo máquinas y fallas (sin categorías).
"""

from collections import defaultdict, deque
from datetime import datetime

MAX_HISTORIAL = 20  # Cuántas consultas recientes guardar

class StatsManager:
    def __init__(self):
        self.total_diagnosticos = 0
        self.top_maquinas = defaultdict(int)     # maquina -> cantidad
        self.top_fallas = defaultdict(int)       # (maquina, falla) -> cantidad
        self.historial_reciente = deque(maxlen=MAX_HISTORIAL)
    
    def registrar_diagnostico_iniciado(self, maquina):
        self.total_diagnosticos += 1
        self.top_maquinas[maquina] += 1
        # El historial se completa al finalizar (diagnóstico completado)
    
    def registrar_diagnostico_completado(self, maquina, falla):
        llave = (maquina, falla)
        self.top_fallas[llave] += 1
        now = datetime.now().isoformat()
        self.historial_reciente.appendleft({
            'timestamp': now,
            'maquina': maquina,
            'falla': falla,
            'completado': True,
        })
    
    def obtener_estadisticas(self):
        # Top máquinas (orden descendente)
        maquinas = sorted(
            [{'maquina': k, 'cantidad': v} for k, v in self.top_maquinas.items()],
            key=lambda x: x['cantidad'],
            reverse=True
        )[:5]

        # Top fallas (orden descendente por cantidad)
        fallas = sorted(
            [{'maquina': k[0], 'falla': k[1], 'cantidad': v} for k, v in self.top_fallas.items()],
            key=lambda x: x['cantidad'],
            reverse=True
        )[:5]

        historial = list(self.historial_reciente)
        
        return {
            'total_diagnosticos': self.total_diagnosticos,
            'top_maquinas': maquinas,
            'top_fallas': fallas,
            'historial_reciente': historial
        }

# Singleton global listo para importar
stats_manager = StatsManager()
