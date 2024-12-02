from typing import Any
from unittest.mock import Mock

from jwt import PyJWKSet
from pytest_mock import MockerFixture

from tauth.authn.oauth2.authentication import RequestAuthenticator


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


def test_auth0_dyn(access_token: str, jwk: dict, mocker: MockerFixture):
    provider_target_fn = (
        "tauth.authn.oauth2.authentication.RequestAuthenticator.get_authprovider"
    )
    mocker.patch(target=provider_target_fn, new=lambda *_, **__: AuthProviderMock)

    jwk_target_fn = "tauth.authn.oauth2.utils.ManyJSONKeySetStore.get_jwks"
    mocker.patch(target=jwk_target_fn, new=lambda *_, **__: PyJWKSet.from_dict(jwk))

    request = RequestMock()

    RequestAuthenticator.validate(request, access_token, Mock())  # type: ignore
    assert True
