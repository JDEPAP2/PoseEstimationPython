"""
Caso de uso: enviar métricas a un sink de almacenamiento o monitoreo.
"""

from ..entities import Metrics
from ..repositories import MetricsSink


class PushMetrics:
    """
    Encapsula la lógica para insertar métricas en un sink de métricas.
    """

    def __init__(self, sink: MetricsSink) -> None:
        """
        Inicializa el caso de uso con un sink de métricas.

        Args:
            sink (MetricsSink): Instancia concreta que recibe y almacena métricas.
        """
        self._sink: MetricsSink = sink

    def __call__(self, m: Metrics) -> None:
        """
        Envía una métrica al sink.

        Args:
            m (Metrics): Métrica a insertar en el sink.
        """
        self._sink.push(m)
