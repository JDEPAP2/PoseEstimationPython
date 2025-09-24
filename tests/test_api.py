"""Pruebas unitarias para el módulo de rutas web (src.presentation.web.routes)."""

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


def test_api_metrics(client):
    """El endpoint /api/metrics responde con una lista JSON (puede estar vacía).

    Args:
        client (flask.testing.FlaskClient): Cliente de pruebas inyectado
            automáticamente por pytest.
    """
    response = client.get("/api/metrics?n=5")
    assert response.status_code == 200

    data = response.get_json()
    assert isinstance(data, list)

    # Si hay métricas, validamos la forma de los elementos
    if data:
        item = data[-1]
        assert isinstance(item, dict)
        assert "t" in item
        assert "inference_ms" in item
        assert "server_fps" in item
        # Esta puede no estar si aún no corriste inferencias
        assert "mean_kp_conf" in item or "persons" in item


@pytest.mark.parametrize("n", [1, 3, 10])
def test_api_metrics_with_args(client, n):
    """El endpoint /api/metrics responde correctamente con distintos args de 'n'.

    Args:
        client (flask.testing.FlaskClient): Cliente de pruebas inyectado.
        n (int): Número de métricas a solicitar.
    """
    response = client.get(f"/api/metrics?n={n}")
    assert response.status_code == 200

    data = response.get_json()
    assert isinstance(data, list)
    # No garantizamos que siempre devuelva exactamente 'n', pero sí que no falle
    assert len(data) <= n


def test_root_redirects(client):
    """El endpoint raíz (/) redirige correctamente al frontend o dashboard.

    Args:
        client (flask.testing.FlaskClient): Cliente de pruebas inyectado.
    """
    response = client.get("/", follow_redirects=False)
    # Puede ser 302 si redirige, o 200 si devuelve algo simple
    assert response.status_code in (200, 302)
