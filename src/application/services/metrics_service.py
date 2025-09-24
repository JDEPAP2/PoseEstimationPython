"""
Servicio de aplicación para manejar métricas:
- Enviar métricas a un sink.
- Recuperar snapshots de métricas almacenadas.
"""

from ...domain.entities import Metrics
from ...domain.repositories import MetricsSink
from ...domain.usecases.push_metrics import PushMetrics


class MetricsService:
    """
    Servicio que orquesta el flujo de métricas entre los casos de uso
    y el sink de almacenamiento.
    """

    def __init__(self, push_metrics: PushMetrics, sink: MetricsSink) -> None:
        """
        Inicializa el servicio de métricas.

        Args:
            push_metrics (PushMetrics): Caso de uso para enviar métricas.
            sink (MetricsSink): Repositorio/sink para almacenar y consultar métricas.
        """
        self._push: PushMetrics = push_metrics
        self._sink: MetricsSink = sink

    def push(self, m: Metrics) -> None:
        """
        Envía una métrica al sink a través del caso de uso.

        Args:
            m (Metrics): Métrica a insertar.
        """
        self._push(m)

    def snapshot(self, n: int = 120) -> list[dict[str, float]]:
        """
        Devuelve un snapshot de las últimas métricas.

        Args:
            n (int, opcional): Número máximo de métricas a recuperar.
                Por defecto 120.

        Returns:
            list[dict[str, float]]: Lista de métricas en formato diccionario.
        """
        return self._sink.snapshot(n)
