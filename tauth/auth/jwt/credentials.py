import time
from collections import deque
from typing import Any, TypedDict

from cryptography.hazmat.primitives.asymmetric import rsa

from .constants import DEFAULT_ROTATION_LENGTH, DEFAULT_ROTATION_TTL
from .errors import InvalidToken
from .keygen import JWKS, generate_jwks, generate_signing_pair
from .tokcoder import Claims, decode_jwt, encode_jwt, unverified_headers


class KeyPair(TypedDict):
    private: rsa.RSAPrivateKey
    public: rsa.RSAPublicKey
    jwks: JWKS
    ttl: float


def init_key_pair() -> KeyPair:
    private, public = generate_signing_pair()
    return {
        "private": private,
        "public": public,
        "jwks": generate_jwks(public),
        "ttl": time.time(),
    }


class CredentialStore:
    _rotations: deque[KeyPair] = deque([], maxlen=DEFAULT_ROTATION_LENGTH)
    _rotation_ttl: float = DEFAULT_ROTATION_TTL
    _current: KeyPair = init_key_pair()

    @classmethod
    def setup(
        cls,
        rotation_length: int | None = None,
        rotation_ttl: int | None = None,
        key_pair: KeyPair | None = None,
    ):
        if rotation_length is not None:
            cls._rotations = deque([], maxlen=rotation_length)

        if rotation_ttl is not None:
            cls._rotation_ttl = rotation_ttl

        if key_pair is not None:
            cls._current = key_pair

    @classmethod
    def rotate(cls):
        private, public = generate_signing_pair()
        cls._rotations.append(cls._current)
        cls._current = {
            "private": private,
            "public": public,
            "jwks": generate_jwks(public),
            "ttl": time.time(),
        }
        return cls._current

    @classmethod
    def pair(cls):
        return cls._current

    @classmethod
    def public(cls):
        return cls._current["public"]

    @classmethod
    def private(cls):
        return cls._current["private"]

    @classmethod
    def jwks(cls) -> JWKS:
        return cls._current["jwks"]

    @classmethod
    def alive(cls):
        return cls._current["ttl"] + DEFAULT_ROTATION_TTL < time.time()

    @classmethod
    def rotations(cls):
        return deque([cls._current]) + cls._rotations

    @classmethod
    def encode(cls, payload: dict[str, Any]) -> bytes:
        if not cls.alive():
            cls.rotate()
        return encode_jwt(payload=payload, private_key=cls.private())

    @classmethod
    def decode(cls, token: str | bytes, claims: Claims) -> dict[str, Any]:
        if isinstance(token, str):
            token = token.encode("utf-8")

        e = "Invalid token."
        for rotation in cls.rotations():
            try:
                decoded = decode_jwt(
                    token=token,
                    public_key=rotation["public"],
                    claims=claims,
                )
                return decoded
            except InvalidToken as err:
                e = str(err)

        raise InvalidToken(e)

    @classmethod
    def headers(cls, token: str | bytes) -> dict[str, Any]:
        if isinstance(token, str):
            token = token.encode("utf-8")

        return unverified_headers(token=token)
