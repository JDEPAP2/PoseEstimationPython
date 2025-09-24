"""Pruebas unitarias para el manejo de modelos en la aplicación web."""

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


def test_models_list(client):
    """El endpoint /models devuelve JSON con directorio e items.

    Args:
        client (flask.testing.FlaskClient): Cliente de pruebas inyectado por
            pytest.
    """
    rv = client.get("/models")
    assert rv.status_code == 200

    data = rv.get_json()
    assert "dir" in data
    assert "items" in data
    assert isinstance(data["items"], list)


def test_models_serve_not_found(client):
    """Si pedimos un modelo inexistente, el servidor responde 404.

    Args:
        client (flask.testing.FlaskClient): Cliente de pruebas inyectado por
            pytest.
    """
    rv = client.get("/models/no_existe.glb")
    assert rv.status_code == 404
