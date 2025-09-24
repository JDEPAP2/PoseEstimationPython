"""Pruebas unitarias básicas para el frontend web de la aplicación."""

import pytest
from src.presentation.web.routes import create_app


@pytest.fixture
def client():
    """Fixture que inicializa la aplicación en modo de pruebas.

    Returns:
        flask.testing.FlaskClient: Cliente de pruebas para la API.
    """
    app = create_app()
    app.config.update({"TESTING": True})
    return app.test_client()


def test_index_ok(client):
    """La página raíz carga correctamente y contiene el título esperado.

    Args:
        client (flask.testing.FlaskClient): Cliente de pruebas inyectado por
            pytest.
    """
    rv = client.get("/")
    assert rv.status_code == 200
    assert b"Pose Estimation" in rv.data


def test_favicon(client):
    """El favicon responde con 204 si no existe, o 200 si está disponible.

    Args:
        client (flask.testing.FlaskClient): Cliente de pruebas inyectado por
            pytest.
    """
    rv = client.get("/favicon.ico")
    assert rv.status_code in (200, 204)
