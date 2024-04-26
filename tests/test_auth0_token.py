from typing import Any

from jwt import PyJWKSet
from pytest_mock import MockerFixture

from tauth.auth.auth0_dyn import RequestAuthenticator


class AuthProviderMock:
    def get_external_id(self, *_) -> str:
        return "https://test/"


class StateMock:
    def __init__(self) -> None:
        self.keys = {}

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "keys":
            object.__setattr__(self, name, value)
        else:
            self.keys[name] = value

    def __getattribute__(self, name: str) -> Any:
        if name == "keys":
            return object.__getattribute__(self, name)
        return self.keys.get(name)


class RequestMock:
    def __init__(self) -> None:
        self.state = StateMock()
        self.headers = {}
        self.client = None


def test_auth0_dyn(access_token: str, id_token: str, jwk: dict, mocker: MockerFixture):
    provider_target_fn = "tauth.auth.auth0_dyn.RequestAuthenticator.get_authprovider"
    mocker.patch(target=provider_target_fn, new=lambda *_, **__: AuthProviderMock)

    jwk_target_fn = "tauth.auth.auth0_dyn.ManyJSONKeySetStore.get_jwks"
    mocker.patch(target=jwk_target_fn, new=lambda *_, **__: PyJWKSet.from_dict(jwk))

    org_db_query_fn = "tauth.organizations.controllers.read_one"
    mocker.patch(target=org_db_query_fn, new=lambda *_, **__: {"name": "test"})

    request = RequestMock()

    RequestAuthenticator.validate(request, access_token, id_token)  # type: ignore
    assert True
