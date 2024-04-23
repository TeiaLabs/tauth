from typing import Any, Self

from authlib.jose.rfc7517.jwk import JsonWebKey
from pytest_mock import MockerFixture

from tauth.auth.auth0_dyn import RequestAuthenticator


class AuthProviderMock:
    def get_external_id(self, *_) -> Self:
        return "test"


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


def test_auth0_dyn(access_token: str, id_token: str, jwk: dict, mocker: MockerFixture):
    provider_target_fn = "tauth.auth.auth0_dyn.RequestAuthenticator.get_authprovider"
    mocker.patch(target=provider_target_fn, new=lambda *_, **__: [AuthProviderMock])

    jwk_target_fn = "tauth.auth.auth0_dyn.ManyJSONKeyStore.get_jwk"
    mocker.patch(
        target=jwk_target_fn, new=lambda *_, **__: JsonWebKey.import_key_set(jwk)
    )

    request = RequestMock()

    try:
        RequestAuthenticator.validate(request, access_token, id_token)
        assert True
    except Exception as e:
        assert False, str(e)
