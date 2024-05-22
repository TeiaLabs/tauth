import pytest
from fastapi.testclient import TestClient
from pymongo.database import Database

from .utils import run_validations, validate_id, validate_isostring


@pytest.fixture(autouse=True)
def teardown(tauth_db: Database):
    try:
        yield None
    finally:
        tauth_db["entites"].delete_many({"name": "/example_app"})
        tauth_db["melt_keys"].delete_many({"name": {"$in": ["default", "second"]}})


@pytest.fixture(scope="module")
def expectations_token_metadata_obj(expectations_creator) -> dict:
    validations = {
        "created_at": validate_isostring,
        "created_by": expectations_creator,
        "name": lambda k, obj: isinstance(obj[k], str) and len(obj[k]) > 0,
    }
    return validations


@pytest.fixture(scope="module")
def expectations_client_creation_obj(expectations_token_creation_obj) -> dict:
    obj = {
        "created_at": validate_isostring,
        "_id": validate_id,
        "name": "/example_app",
        "tokens": [expectations_token_creation_obj],
        "users": lambda k, obj: isinstance(obj[k], list) and len(obj[k]) == 0,
    }
    return obj


@pytest.fixture(scope="module")
def expectations_client_view_obj(expectations_token_metadata_obj) -> dict:
    obj = {
        "created_at": validate_isostring,
        "_id": validate_id,
        "name": "/example_app",
        "tokens": [expectations_token_metadata_obj],
    }
    return obj


def test_create_one(
    client: TestClient,
    headers: dict,
    client_obj: dict,
    expectations_client_creation_obj: dict,
) -> None:
    response = client.post("/api/tauth/clients", json=client_obj, headers=headers)
    assert response.status_code == 201
    response_body = response.json()
    run_validations(response_body, expectations_client_creation_obj)


@pytest.mark.order(after="test_create_one")
def test_read_one(
    client: TestClient,
    headers: dict,
    client_obj: dict,
    expectations_client_view_obj: dict,
) -> None:
    _ = client.post("/api/tauth/clients", json=client_obj, headers=headers)
    response = client.get(f"/api/tauth/clients/{client_obj['name']}", headers=headers)
    assert response.status_code == 200
    response_body = response.json()
    run_validations(response_body, expectations_client_view_obj)
