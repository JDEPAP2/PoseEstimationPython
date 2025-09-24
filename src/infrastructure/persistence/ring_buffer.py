"""
Implementación de un buffer circular para almacenar métricas.

Se utiliza un deque con tamaño máximo para conservar las métricas más recientes.
"""

from collections import deque
from ...domain.entities import Metrics


class RingBufferMetrics:
    """
    Buffer circular de métricas basado en deque.
    """

    def __init__(self, capacity: int = 600) -> None:
        """
        Inicializa el buffer con una capacidad máxima.

        Args:
            capacity (int, opcional): Número máximo de métricas a almacenar.
                Por defecto 600.
        """
        self._buf: deque[dict[str, float]] = deque(maxlen=capacity)

    def push(self, m: Metrics) -> None:
        """
        Inserta una métrica en el buffer.

        Args:
            m (Metrics): Métrica a insertar.
        """
        self._buf.append(m.__dict__)

    def snapshot(self, n: int = 120) -> list[dict[str, float]]:
        """
        Recupera las últimas métricas almacenadas.

        Args:
            n (int, opcional): Número máximo de métricas a devolver.
                Si n <= 0, devuelve todo el buffer.
                Por defecto 120.

        Returns:
            list[dict[str, float]]: Lista de métricas en formato diccionario.
        """
        if n <= 0:
            return list(self._buf)
        return list(self._buf)[-n:]
