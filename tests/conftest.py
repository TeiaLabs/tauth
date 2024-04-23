import os

import dotenv
import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient
from pymongo.database import Database

from tauth.app import create_app
from tauth.settings import Settings

from .utils import validate_isostring, validate_nonempty_string, validate_token

dotenv.load_dotenv()


@pytest.fixture(scope="session")
def mongo_client() -> MongoClient:
    client = MongoClient(Settings.get().TAUTH_MONGODB_URI)
    return client


@pytest.fixture(scope="session")
def tauth_db(mongo_client: MongoClient) -> Database:
    return mongo_client[Settings.get().TAUTH_MONGODB_DBNAME]


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture(scope="session")
def test_token_value() -> str:
    return Settings().TAUTH_ROOT_API_KEY


@pytest.fixture(scope="session")
def user_email() -> str:
    return "user@org.com"


@pytest.fixture(scope="session")
def headers(test_token_value: str, user_email: str) -> dict:
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


@pytest.fixture(scope="session")
def access_token() -> str:
    return "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3Rlc3QvIiwiYXVkIjoidGVzdCIsImV4cCI6MjE0NzQ4MzY0N30.RmEUXw8i8Afo0oAJqsOQ6uIo69TnQpldRWQ_zsvinr5cPwCVwn9cPrdEKnoblhOsA1n37ZewS-7gS2DUPDBqxihLa1p8Igc_Sy5L7cIjB1jAsLHt1Anvju-vtGORN5kDez1SNDnT0JI2wioeNiBfhRdoqdF0ZJWRBgCw06Nhkbu2Kd4M40NKON99Fvh2j1hwCLSEc51P7rcpQIJM1andOMAkXDepf2BCcnnGs6SC3ORCYCGb86En8TeL6E_kPZwHzALHghaN_YgDngVD6qYgFf26_uwvTuXQBVN7ytSzjXGa7-ZFchaEkmdmywnnSGQAxh2DZ-LpNpcCmmXLIUrtDg"


@pytest.fixture(scope="session")
def id_token() -> str:
    return "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3Rlc3QvIiwiYXVkIjoidGVzdCIsImV4cCI6MjE0NzQ4MzY0N30.RmEUXw8i8Afo0oAJqsOQ6uIo69TnQpldRWQ_zsvinr5cPwCVwn9cPrdEKnoblhOsA1n37ZewS-7gS2DUPDBqxihLa1p8Igc_Sy5L7cIjB1jAsLHt1Anvju-vtGORN5kDez1SNDnT0JI2wioeNiBfhRdoqdF0ZJWRBgCw06Nhkbu2Kd4M40NKON99Fvh2j1hwCLSEc51P7rcpQIJM1andOMAkXDepf2BCcnnGs6SC3ORCYCGb86En8TeL6E_kPZwHzALHghaN_YgDngVD6qYgFf26_uwvTuXQBVN7ytSzjXGa7-ZFchaEkmdmywnnSGQAxh2DZ-LpNpcCmmXLIUrtDg"


@pytest.fixture(scope="session")
def jwk() -> dict:
    return {
        "keys": [
            {
                "kty": "RSA",
                "n": "rD7HTTojtL3nuvhi_TvIg0inRr_d98aFU18dBJWb5PuXYj2ujkDDC4HGdXIEWDrwYx3M-dKFO2qB_EJu63XI9hc1wL7TsLpJf6Ek2HRJAiCDYBt4hBdpnwDjZ86_Xs6e9HgpVBW8e7NX90Ho4-IY5Y-1qTL-amRRWPrIJ_a5aNwgvyctVVHyhsYGbDB7mncdgKQnZfpY9XGtlZI9IMdlPcr50lSxgII1jRxKYJ4C6MTPixke4uWxmmeNf6ajXddXWhR_Xe_TuESRjCbZMig5ORgITr7pnEjX3GEdZOpdVvQDxmE70XcLLlvZNX3NDmHn0kqFwk0w_WyInHVLhAKl-Q",
                "e": "AQAB",
                "d": "AgdJy78BdAg1ga1EV53YUPrR6_CvH9MiqTZjLi5V3rF0YF0cw_R_PN7e6XvH9O22UfedEn__VGbUWADhD86KfluorCYfnO2As-s4xQBdzhO_HMbxmV4xxf0vGxRjUdh7syItBqVlOBsqc62ijvhBp7-Nbv3t4u7Qrai42-NnetvHLKKW0WZltQSc2SAFgIrC7N4UQdNOOMOYolDcB9l0aqBugTfx9yrYq2rXzWHKyWZfW6bj83CZN2bhClzWqYk_qZzpqISC_ESCWH82AXLv2MZLmzBwmYdIUd4Z5ghl5wXQRhZ20QFah9FkQzbML1ZAeSlKFIjXmAOeY4F31LdGIQ",
                "p": "4Ch5iiyMENWbGPZUZcUJA3ngLLaaQe3bykov05IOo1HyIQJ4QMcUS79w-ZCCyzjpC4GnRbPUtj8wW8RSvFDaj_t1qP_gWuY1BxJDfrMGHoVavIs9UaqKfEjdWBg9CIOpr-ghsV2CzcWa-uzQR4CeWHdgwsjrEzk_-svX-ekv1tE",
                "q": "xLZ9BgQA-EQOMqia_F-2a77E2_iOgG25MPwvuVL3lGzVJUDkSzTAWKEZTKEHxFVbDu0arAdsFuVJYfMEntR7duXXjJ4Ac-jBb7x5de_cv18HSwgfgtGeMoHqUm0JyKE5xhXIWTwb-bl0GfsK3t80m_9TYUa2DkLraxpTJe0x9qk",
                "dp": "UNUnpvUTeUqeCG1j1-Mqse80MMuUauvsU1FXV9MWpjx5tP-f_7QKlJovkj9TexdFqpmRiWgk76dvt9ffAfuiJUPHlS7YZ88WFju2zSyfq0fphY4siZOXJuRbtVXgRH6-JSnvZHdVIQD-NzhIj1BJSZua8ALmCmOdt8HkW0GEt9E",
                "dq": "dM-8_EaCYOrg13pB1p3rkJ3O_qTh0ifV8d2_ZTh8ZnoeNCoNpw8jLT407Mku-IqLMRjhXshlik8LvYt28e5RhrBDyG_G6w2LWJO-OKeAGXAPv6GKPL_HRkzZXar8RVRgH12uBDdqkWdsJ0VpFiHLdtsuozQ_Rca9T3NpbrskkUk",
                "qi": "MhiaF5tZsMLlze4cvaPkaZCrBjsmePbc40-U9U4o7FfSHHsXLD3hNCQ6jc_otPksf9xdKGhYiL7AHc8kV4cHVWF2k9oaYiBkiRhZPUA4v67wwm-07Q-yKragUCJIFsE5dtzQ8cKWLwHQnJ7YuYRX4VsJ1Q546GR34IMxRLu_gbo",
                "kid": "HhFOdjqWJC6AodX7nRWCiYu_kIhB8QGvlmAFBg1f16g",
            },
            {
                "kty": "RSA",
                "n": "rD7HTTojtL3nuvhi_TvIg0inRr_d98aFU18dBJWb5PuXYj2ujkDDC4HGdXIEWDrwYx3M-dKFO2qB_EJu63XI9hc1wL7TsLpJf6Ek2HRJAiCDYBt4hBdpnwDjZ86_Xs6e9HgpVBW8e7NX90Ho4-IY5Y-1qTL-amRRWPrIJ_a5aNwgvyctVVHyhsYGbDB7mncdgKQnZfpY9XGtlZI9IMdlPcr50lSxgII1jRxKYJ4C6MTPixke4uWxmmeNf6ajXddXWhR_Xe_TuESRjCbZMig5ORgITr7pnEjX3GEdZOpdVvQDxmE70XcLLlvZNX3NDmHn0kqFwk0w_WyInHVLhAKl-Q",
                "e": "AQAB",
                "kid": "HhFOdjqWJC6AodX7nRWCiYu_kIhB8QGvlmAFBg1f16g",
            },
        ]
    }
