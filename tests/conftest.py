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
    client = MongoClient(Settings.get().MONGODB_URI)
    return client


@pytest.fixture(scope="session")
def tauth_db(mongo_client: MongoClient) -> Database:
    return mongo_client[Settings.get().MONGODB_DBNAME]


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture(scope="session")
def test_token_value() -> str:
    return Settings().ROOT_API_KEY


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
    return "eyJhbGciOiJSUzI1NiIsImtpZCI6IlFodUdSLWZ5aWttVGVOaEVCYzRDYnozUVhrOHdNWm10R0NPQjNPcHlMVm8iLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3Rlc3QvIiwiYXVkIjoiaHR0cHM6Ly90ZXN0LyIsImV4cCI6MjE0NzQ4MzY0Nywib3JnX2lkIjoidGVzdCIsInN1YiI6InRlc3QiLCJlbWFpbCI6InRlc3RAZ21haWwuY29tIn0.SkhvwwVibrFktqeISs0soMI0gFzJWnN2RqtLiNSYxEydGacwNimKZ9GTiz01m0gVzKbcTt4hV567ohCCvVU969FFRD-9UmtoTvG9gSE6WnJORryKq5UrNKAjU6TP07Y3zy2FOVOCrO-4y7c04rCAPA6oeL2JxLpf0n9t2D1rzsX7YpdIGWxyFTNcaxUwzx3x4f0NXtQuu-HN07OumA5dPa68Xq8zAheOFYx91O_RTRYXr236KKy7oytoGdl7yFz-p4nICycuG-RllYcOCwxHUxN3m77DAgjeiIdHLulpL6FkSmMFTdXr-cwkddBIlCwy3nMdQDbBv3NBlu6V-kcwbw"


@pytest.fixture(scope="session")
def jwk() -> dict:
    return {
        "keys": [
            {
                "kty": "RSA",
                "n": "5J0I_Gidm_l6s4gxjSHLMsc9dJGnvOgLaE3CrmP-iftv8JWvgG9SBCB1pPtJgyOyh4ZQHIjG2wbePQZCgynRmEPFTlT_LGI84iBx6aMONGR_JdAnQv8Kw8f2ULP9vGgZLIr2OlUvX9FrmMuYGld7N21ABNH6CmtoWMSp71OcK_BhAT2SvZPpnUkblGLsOt_qPngyElFowqPuO-fozL2SPZYn2SiD9IoDr-upw-f9pGWI-7juJtDX0v3q6v7PKA44CunhWwZifiKhEBmLXc68ZJmRbLuRnXR3v22gl30ApYRWguZCT9o8lEZjsBZzNhJr4zCWGfK1-RYd4Cs7LwLnHQ",
                "e": "AQAB",
                "d": "UlaMyfwT5_1uyAKhdidZvCwuYjGjrFIW6bY4C_9PyfqZUplW4Hc3nuzh8k3fKDBPOKiTafOJS5GpsWjzw7HoH2MpSREr5pxrOTZeULu9fflEIiZaPbMF-YWnnWF2XclQZ86U6GWN7oDKs_mACty_MDNU_2dxGxecOXx7iAshEGGRBOGQ7j8SOiUE4yMjuqCqOOPqENOFvuzMo-cVUsc84U8D9UwX9yc3CvyTqYSRk6-BePKr_Az7lbbOcjM9TGKFePQIwdYSaqyk3zcm3mLGDAePxvZOjX6V978HBktFRmxdIU_Df6mG8TO1lA_mRM6IT_0dh1n-bnGEJcP4SaqdMQ",
                "p": "9f_FUEUVpxn7tenD_rrxlQzeNEH8WJs1y93zfmUXPho68WHFEVWe31_AHp9aLQwYx9oCu5S-HVRgPchUFjVMB_a2_jLeIMbzfucwcx3O5Gxa_nbzkkckeklAOGfZgTkjugdyWpbS4zZjgD8oBpOBIuP0oBBUVhXj6h_HCzq5Te8",
                "q": "7ehSwe4wmZyaPO27s95e0HhKsxnkSL3aYNSFpZoN18xJ7suMxw0ecIMmDHF39bpBreiIM7ZfsWX9-9IAJeLAmxvyqaegrwgEDz8fQcAXDG6eJdNmU7feB7fN5GAzv8jZ3sCjW1fiW-WO05DNKwh22mNCPC6V8GPIRwVpXvaOJ7M",
                "dp": "KHLd5sz1OnyzPr4pVAE5J-DtyHnxHECpH9Rm7SmCINv_RSFmXetOLDx6Qo7BLRcIHBRkzqMuf3QYPxBpgx1QWx7eB_4lOA5-iydIeCU2l6iZba3xbuPzw4e3345z3SOgFD6VNwAFvQZ8ZeH8mtg2K55_4rHMrDr9Nsny2I3XWlE",
                "dq": "l0Ruykvurt053J-0B0vOsXKq3HIMCoxce9DlIURwpNOJ9sGJw05-Gj_pQ2QqSB2jgTYm0-qTsbIN6b2-xlgE6xq8Ek85BdFs81zJPP8sKIV1HMvrdjOkgvfFe_4HKVxF2zJVK9EXZiLxy2d4bHI3T-hoxudAAtcPEslIFE9kV60",
                "qi": "3LjVAz8GJt_AXERcO7_850PCNu9CiTvTcua5CGvBV43B1nv97DAvI9_QBRyjeiBjT6SZZn06FUFiDQYfSYVwOdfQ9YnIub_zOJAbPOCD9cd-rdISHhnDsZtowKN-TOmAIGX5bykuKaVFaNExyZK5E6bDFBJPg7tm0RdoISHsByU",
                "kid": "QhuGR-fyikmTeNhEBc4Cbz3QXk8wMZmtGCOB3OpyLVo",
            },
            {
                "kty": "RSA",
                "n": "5J0I_Gidm_l6s4gxjSHLMsc9dJGnvOgLaE3CrmP-iftv8JWvgG9SBCB1pPtJgyOyh4ZQHIjG2wbePQZCgynRmEPFTlT_LGI84iBx6aMONGR_JdAnQv8Kw8f2ULP9vGgZLIr2OlUvX9FrmMuYGld7N21ABNH6CmtoWMSp71OcK_BhAT2SvZPpnUkblGLsOt_qPngyElFowqPuO-fozL2SPZYn2SiD9IoDr-upw-f9pGWI-7juJtDX0v3q6v7PKA44CunhWwZifiKhEBmLXc68ZJmRbLuRnXR3v22gl30ApYRWguZCT9o8lEZjsBZzNhJr4zCWGfK1-RYd4Cs7LwLnHQ",
                "e": "AQAB",
                "kid": "QhuGR-fyikmTeNhEBc4Cbz3QXk8wMZmtGCOB3OpyLVo",
            },
        ]
    }
