"""
Aplicación Flask para servir la UI web, modelos GLB/GLTF y la API de inferencia.

Rutas:
- GET  /           : Renderiza la página principal. Query arg opcional: `model`.
- GET  /models     : Lista los modelos .glb/.gltf disponibles.
- GET  /models/<f> : Sirve un archivo de modelo desde el directorio de modelos.
- GET  /favicon.ico: Sirve el favicon si existe, 204 en caso contrario.

Notas:
- El directorio de modelos se resuelve automáticamente con prioridad:
  1) Variable de entorno MODELS_DIR
  2) assets/models en el CWD
  3) assets/models en la raíz del proyecto
  Si no existe, se crea.
"""

from __future__ import annotations

import os
from typing import Iterable, Optional

from flask import Flask, Response, jsonify, render_template, request, send_from_directory
from flask_cors import CORS

from .api import api_bp, build_containers

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


# ---------- Helpers para ubicar assets/models ----------


def _candidate_model_dirs(app_root: str) -> Iterable[str]:
    """
    Genera directorios candidatos donde buscar modelos .glb/.gltf.

    Args:
        app_root (str): Ruta raíz de la app Flask (app.root_path).

    Yields:
        str: Rutas candidatas en orden de prioridad decreciente.
    """
    # 1) Variable de entorno, si está definida
    env_dir = os.environ.get("MODELS_DIR")
    if env_dir:
        yield env_dir

    # 2) assets/models en el CWD
    yield os.path.abspath(os.path.join(os.getcwd(), "assets", "models"))

    # 3) assets/models en la raíz del proyecto (sube 4 niveles desde este paquete)
    here = os.path.dirname(__file__)
    root_dir = os.path.abspath(os.path.join(here, "..", "..", "..", ".."))
    yield os.path.join(root_dir, "assets", "models")


def _resolve_models_dir(app_root: str) -> str:
    """
    Resuelve el directorio de modelos existente o crea el primero candidato.

    Args:
        app_root (str): Ruta raíz de la app Flask (app.root_path).

    Returns:
        str: Directorio final para modelos .glb/.gltf.
    """
    for p in _candidate_model_dirs(app_root):
        if os.path.isdir(p):
            return p

    target = next(_candidate_model_dirs(app_root))
    os.makedirs(target, exist_ok=True)
    return target


def _list_glb(models_dir: str) -> list[str]:
    """
    Lista los archivos .glb/.gltf disponibles en `models_dir`.

    Args:
        models_dir (str): Directorio de modelos.

    Returns:
        list[str]: Nombres de archivo ordenados alfabéticamente.
    """
    try:
        return sorted(
            f for f in os.listdir(models_dir) if f.lower().endswith((".glb", ".gltf"))
        )
    except Exception:
        return []


def _pick_first_glb(models_dir: str) -> Optional[str]:
    """
    Selecciona el primer .glb/.gltf disponible en `models_dir`.

    Args:
        models_dir (str): Directorio de modelos.

    Returns:
        Optional[str]: Nombre del primer archivo o None si no hay.
    """
    files = _list_glb(models_dir)
    return files[0] if files else None


# ---------- App factory ----------


def create_app() -> Flask:
    """
    Crea y configura la aplicación Flask.

    Args de entrada (configuración externa):
        - ENV VAR `MODELS_DIR` (opcional): Directorio donde buscar modelos .glb/.gltf.
        - Query arg `model` en GET / (opcional): Nombre de archivo .glb/.gltf
          para forzar el modelo a cargar en la UI.

    Returns:
        Flask: Instancia de la aplicación lista para ejecutar.
    """
    app = Flask(__name__, static_folder=STATIC_DIR, template_folder=TEMPLATES_DIR)
    CORS(app)

    # API
    app.register_blueprint(api_bp, url_prefix="/api")

    # Dependencias (wiring) dentro de la app factory para evitar efectos al importar
    pose_service, metrics_service = build_containers()
    app.config["POSE_SERVICE"] = pose_service
    app.config["METRICS_SERVICE"] = metrics_service

    # Directorio de modelos
    models_dir = _resolve_models_dir(app.root_path)

    # ---------- Rutas Web ----------

    @app.get("/")
    def index() -> Response:
        """
        Renderiza la página principal.

        Query Args:
            model (str, opcional): Nombre de archivo .glb/.gltf a forzar en la UI.

        Returns:
            Response: HTML renderizado (template index.html).
        """
        forced = request.args.get("model")
        glb_name = forced if forced else _pick_first_glb(models_dir)
        glb_path = f"/models/{glb_name}" if glb_name else None
        items = _list_glb(models_dir)
        glb_files = [f"/models/{f}" for f in items]

        # Pasar SIEMPRE glb_files para evitar 'Undefined' en Jinja
        return render_template("index.html", glb_path=glb_path, glb_files=glb_files)

    @app.get("/models/<path:filename>")
    def serve_models(filename: str) -> Response:
        """
        Sirve un archivo de modelo desde el directorio de modelos.

        Args (Path Param):
            filename (str): Ruta relativa dentro de `models_dir`.

        Returns:
            Response: Archivo estático.
        """
        return send_from_directory(models_dir, filename)

    @app.get("/models")
    def list_models() -> Response:
        """
        Devuelve la lista de modelos disponibles.

        Returns:
            Response (application/json): { "dir": "<ruta>", "items": ["a.glb", ...] }
        """
        items = _list_glb(models_dir)
        return jsonify({"dir": models_dir, "items": items})

    @app.get("/favicon.ico")
    def favicon() -> Response:
        """
        Sirve el favicon si existe; devuelve 204 si no.

        Returns:
            Response: favicon.ico o 204 No Content.
        """
        ico_path = os.path.join(STATIC_DIR, "favicon.ico")
        if os.path.exists(ico_path):
            return send_from_directory(STATIC_DIR, "favicon.ico")
        return Response(status=204)

    return app
