import pytest
from fastapi.testclient import TestClient
from pymongo.database import Database

from ..utils import run_validations


def non_leading_slash_client_name_error_message(value):
    return isinstance(value, str) and "absolute" in value and "slash" in value


def has_standard_error_fields(obj: dict):
    assert "detail" in obj
    inner_obj = obj["detail"]
    keys = ["loc", "msg", "type"]
    for k in keys:
        assert k in inner_obj


def begins_with_body_and_name(obj):
    assert obj["detail"]["loc"][0] == "body"
    assert obj["detail"]["loc"][1] == "name"


def is_non_empty_string(obj):
    assert isinstance(obj, str) and len(obj) > 0


def test_non_leading_slash_client_name(client: TestClient, headers: dict):
    response = client.post("/api/tauth/clients/", json={"name": "example_app"}, headers=headers)
    assert response.status_code == 422
    response_body = response.json()
    has_standard_error_fields(response_body)
    details_obj = response_body["detail"]
    begins_with_body_and_name(response_body)
    assert non_leading_slash_client_name_error_message(details_obj["msg"])
    assert details_obj["type"] == "InvalidClientName"


def test_invalid_client_names(client: TestClient, headers: dict):
    invalid_client_names = ["/example--app", "//example_app", "/example app", "/example\napp", "/example\tapp"]
    for name in invalid_client_names:
        response = client.post("/api/tauth/clients/", json={"name": name}, headers=headers)
        assert response.status_code == 422
        response_body = response.json()
        has_standard_error_fields(response_body)
        begins_with_body_and_name(response_body)
        is_non_empty_string(response_body["detail"]["msg"])
        assert response_body["detail"]["type"] == "InvalidClientName"
