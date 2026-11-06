import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_app


def test_application_starts_and_stops() -> None:
    with TestClient(create_app()) as client:
        assert client.get("/api/health/live").status_code == 200


def test_health_routes_are_registered() -> None:
    paths = create_app().openapi()["paths"]

    assert {"/api/health/live", "/api/health/ready", "/api/imports"} <= paths.keys()
    assert "/api/tickets/{ticket_id}/reclassify" in paths


def test_settings_require_a_database_password(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)

    with pytest.raises(ValidationError):
        Settings()
