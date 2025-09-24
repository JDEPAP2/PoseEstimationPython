"""
Módulo principal para ejecutar el servidor Flask de la aplicación.

La configuración del puerto sigue esta prioridad:
1. Argumento de línea de comandos (--port).
2. Variable de entorno PORT.
3. Valor por defecto: 5000.
"""

import argparse
import os

from src.presentation.web.routes import create_app


def main() -> None:
    """
    Punto de entrada de la aplicación.

    Se encarga de:
    - Parsear los argumentos de entrada (--port).
    - Determinar el puerto según prioridad (arg > env > default).
    - Crear y ejecutar la aplicación Flask.

    Args:
        --port (int, opcional): Puerto para el servidor Flask.  
            Si no se especifica, se usará la variable de entorno
            PORT o el valor por defecto 5000.
    """
    parser = argparse.ArgumentParser(
        description="Inicia el servidor Flask de la aplicación."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Puerto para el servidor Flask (por defecto: $PORT o 5000).",
    )
    args = parser.parse_args()

    port: int = args.port or int(os.environ.get("PORT", 5000))

    app = create_app()
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        threaded=True,  # Permite concurrencia en /api/infer y /api/metrics
    )


if __name__ == "__main__":
    main()
