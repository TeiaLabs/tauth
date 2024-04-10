import pytest
from fastapi.testclient import TestClient
from pymongo.database import Database

from .utils import run_validations, validate_id, validate_isostring


@pytest.fixture(autouse=True)
def teardown(tauth_db: Database):
    try:
        yield None
    finally:
        tauth_db["organizations"].delete_many({"name": "/teia"})


@pytest.fixture(scope="module")
def organization_obj() -> dict:
    return {
        "name": "/teia",
        "external_ids": [
            {
                "name": "oauth_org_id",
                "value": "org_123",
            },
        ]
    }


def test_create_one(
    client: TestClient,
    headers: dict,
    organization_obj: dict,
) -> None:
    response = client.post("/api/tauth/organizations", json=organization_obj, headers=headers)
    assert response.status_code == 201
    print(response.json())
    response_body = response.json()
    response_body["created_at"] = validate_isostring("created_at", response_body)