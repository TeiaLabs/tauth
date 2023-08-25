import os

import dotenv
import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient
from pymongo.database import Database

from tauth.app import create_app

from .utils import (
    validate_isostring,
    validate_nonempty_string,
    validate_token,
)

dotenv.load_dotenv()


@pytest.fixture(scope="session")
def mongo_client() -> MongoClient:
    client = MongoClient(os.environ["MELTING_API_MONGODB_URI"])
    return client


@pytest.fixture(scope="session")
def db(mongo_client: MongoClient) -> Database:
    return mongo_client[os.environ["MELTING_API_MONGODB_DBNAME"]]


@pytest.fixture(scope="session")
def tauth_db(mongo_client: MongoClient) -> Database:
    return mongo_client[os.environ["TAUTH_MONGODB_DBNAME"]]


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture(scope="session")
def test_token_value() -> str:
    return "MELT_/--default--abcdef123456789"


@pytest.fixture(scope="session")
def user_email() -> str:
    return "user@org.com"


@pytest.fixture(scope="session")
def headers(test_token_value, user_email) -> dict:
    obj = {
        "Authorization": f"Bearer {test_token_value}",
        "X-User-Email": user_email,
    }
    return obj


@pytest.fixture(scope="session")
def client_obj() -> dict:
    obj = {"name": "/example_app"}
    return obj


@pytest.fixture(scope="session")
def expectations_creator():
    exp = {
        "client_name": validate_nonempty_string,
        "user_email": validate_nonempty_string,
        "token_name": validate_nonempty_string,
    }
    return exp


@pytest.fixture(scope="session")
def expectations_token_creation_obj(expectations_creator):
    validations = {
        "created_at": validate_isostring,
        "created_by": expectations_creator,
        "name": "default",
        "value": validate_token,
    }
    return validations