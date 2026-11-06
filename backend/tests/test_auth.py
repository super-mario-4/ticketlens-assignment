import uuid
from collections.abc import Iterator

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.core.config import Settings, get_settings
from app.core.security import create_token, hash_password, read_token, verify_password
from app.db.session import get_session_factory
from app.main import create_app
from app.models import ImportJob, Ticket, User


@pytest.fixture
def api(migrated_database: None) -> Iterator[TestClient]:
    with TestClient(create_app()) as client:  # Startup creates the configured accounts.
        yield client

    with get_session_factory()() as cleanup:
        for model in (Ticket, ImportJob, User):
            cleanup.execute(delete(model))
        cleanup.commit()


def login(api: TestClient, username: str, password: str):
    return api.post("/api/auth/login", json={"username": username, "password": password})


def headers(api: TestClient, username: str) -> dict[str, str]:
    token = login(api, username, username).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_password_hash_verifies_only_the_right_password() -> None:
    stored = hash_password("secret")

    assert stored != "secret"
    assert verify_password("secret", stored)
    assert not verify_password("wrong", stored)


@pytest.mark.parametrize("stored", ["!", "", "plain", "scrypt$only-two"])
def test_values_that_are_not_hashes_never_verify(stored: str) -> None:
    assert not verify_password("!", stored)


def test_login_returns_a_token_and_role(api: TestClient) -> None:
    response = login(api, "operator", "operator")

    assert response.status_code == 200
    assert response.json()["role"] == "operator"
    assert response.json()["username"] == "operator"
    assert read_token(response.json()["access_token"], get_settings()) is not None


@pytest.mark.parametrize(
    ("username", "password"), [("operator", "wrong"), ("nobody", "operator"), ("lead", "operator")]
)
def test_bad_credentials_are_rejected_the_same_way(
    api: TestClient, username: str, password: str
) -> None:
    response = login(api, username, password)

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "invalid_credentials"


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/tickets"),
        ("get", f"/api/tickets/{uuid.uuid4()}"),
        ("patch", f"/api/tickets/{uuid.uuid4()}/classification"),
        ("post", f"/api/tickets/{uuid.uuid4()}/reclassify"),
        ("get", f"/api/imports/{uuid.uuid4()}"),
        ("post", "/api/imports"),
        ("get", "/api/stats"),
        ("get", "/api/meta"),
    ],
)
def test_routes_require_a_token(api: TestClient, method: str, path: str) -> None:
    response = getattr(api, method)(path, **({"json": {}} if method == "patch" else {}))

    # Request validation may run first for a body or file, and it reveals nothing.
    assert response.status_code in (401, 422)
    if response.status_code == 401:
        assert response.json()["detail"]["code"] == "not_authenticated"


def test_health_needs_no_token(api: TestClient) -> None:
    assert api.get("/api/health/live").status_code == 200


def test_import_without_a_token_is_refused(api: TestClient) -> None:
    files = {"file": ("t.csv", b"id,channel,created_at,text,customer_id\n", "text/csv")}

    assert api.post("/api/imports", files=files).status_code == 401


@pytest.mark.parametrize(
    "token",
    [
        "not-a-token",
        jwt.encode({"sub": str(uuid.uuid4())}, "x" * 40, algorithm="HS256"),
    ],
)
def test_forged_tokens_are_refused(api: TestClient, token: str) -> None:
    response = api.get("/api/tickets", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_expired_token_is_refused(api: TestClient) -> None:
    settings = Settings(jwt_expire_minutes=-1)

    token = create_token(uuid.uuid4(), settings)

    assert read_token(token, settings) is None


def test_token_of_a_deleted_user_is_refused(api: TestClient) -> None:
    token = create_token(uuid.uuid4(), get_settings())

    response = api.get("/api/tickets", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_both_roles_can_read_the_queue(api: TestClient) -> None:
    for username in ("operator", "lead"):
        response = api.get("/api/tickets?status=classified", headers=headers(api, username))
        assert response.status_code == 200


def test_statistics_are_for_the_lead_only(api: TestClient) -> None:
    assert api.get("/api/stats", headers=headers(api, "lead")).status_code == 200
    assert api.get("/api/stats", headers=headers(api, "operator")).status_code == 403


def test_lead_cannot_import_or_correct(api: TestClient) -> None:
    lead = headers(api, "lead")
    files = {"file": ("t.csv", b"id,channel,created_at,text,customer_id\n", "text/csv")}
    body = {"category": "other", "priority": "Low"}

    assert api.post("/api/imports", files=files, headers=lead).status_code == 403
    response = api.patch(f"/api/tickets/{uuid.uuid4()}/classification", json=body, headers=lead)
    assert response.status_code == 403
    assert api.post(f"/api/tickets/{uuid.uuid4()}/reclassify", headers=lead).status_code == 403


def test_starting_again_keeps_accounts(api: TestClient) -> None:
    with TestClient(create_app()):
        pass

    assert login(api, "operator", "operator").status_code == 200
