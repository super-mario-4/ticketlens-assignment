from fastapi.testclient import TestClient

from app.api.deps import get_health_repository
from app.main import create_app


class FakeHealthRepository:
    def __init__(self, postgres: bool, elasticsearch: bool) -> None:
        self._postgres = postgres
        self._elasticsearch = elasticsearch

    def postgres_is_available(self) -> bool:
        return self._postgres

    def elasticsearch_is_available(self) -> bool:
        return self._elasticsearch


def client_with(repository: FakeHealthRepository) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_health_repository] = lambda: repository
    return TestClient(app)


def test_live_returns_ok() -> None:
    response = TestClient(create_app()).get("/api/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_live_does_not_depend_on_the_database() -> None:
    client = client_with(FakeHealthRepository(postgres=False, elasticsearch=False))

    assert client.get("/api/health/live").status_code == 200


def test_ready_with_real_services(client: TestClient) -> None:
    response = client.get("/api/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "components": {"postgres": "ok", "elasticsearch": "ok"},
    }


def test_ready_returns_503_when_postgres_is_down() -> None:
    client = client_with(FakeHealthRepository(postgres=False, elasticsearch=True))

    response = client.get("/api/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "components": {"postgres": "unavailable", "elasticsearch": "ok"},
    }


def test_ready_stays_up_when_elasticsearch_is_down() -> None:
    client = client_with(FakeHealthRepository(postgres=True, elasticsearch=False))

    response = client.get("/api/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "components": {"postgres": "ok", "elasticsearch": "unavailable"},
    }
