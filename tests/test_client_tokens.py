import pytest
from fastapi.testclient import TestClient
from pymongo.database import Database

from .utils import run_validations


@pytest.fixture(autouse=True)
def teardown(tauth_db: Database):
    try:
        yield None
    finally:
        tauth_db["entities"].delete_many({"name": "/example_app"})
        tauth_db["melt_keys"].delete_many({"name": {"$in": ["default", "second"]}})


@pytest.fixture(scope="module")
def token_creation_request_obj() -> dict:
    obj = {"name": "second"}
    return obj


@pytest.mark.order(after="test_clients.py::test_create_one")
def test_create_one(
    client: TestClient, headers: dict, client_obj: dict, token_creation_request_obj: dict, expectations_token_creation_obj: dict
) -> None:
    _ = client.post("/api/tauth/clients/", json=client_obj, headers=headers)
    response = client.post(f"/api/tauth/clients/{client_obj['name']}/tokens", json=token_creation_request_obj, headers=headers)
    assert response.status_code == 201
    response_body = response.json()
    expectations = dict(**expectations_token_creation_obj)
    expectations["name"] = token_creation_request_obj["name"]
    run_validations(response_body, expectations)
    response2 = client.post(f"/api/tauth/clients/{client_obj['name']}/tokens", json=token_creation_request_obj, headers=headers)
    assert response2.status_code == 409
    # TODO: check error body
