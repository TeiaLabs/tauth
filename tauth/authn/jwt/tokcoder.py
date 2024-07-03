from typing import Any, Callable, Generic, TypedDict, TypeVar

from authlib.common.encoding import to_bytes
from authlib.jose import JWTClaims, jwt, util
from authlib.jose.errors import BadSignatureError, DecodeError, InvalidClaimError
from cryptography.hazmat.primitives.asymmetric import rsa

from .errors import InvalidToken
from .keygen import private_key_bytes, public_key_bytes

T = TypeVar("T")


class ClaimValue(Generic[T], TypedDict, total=False):
    value: T
    values: list[T]
    validate: Callable[[JWTClaims, T], bool]


class Claims(TypedDict, total=False):
    iss: ClaimValue[str]
    sub: ClaimValue[str]
    aud: ClaimValue[str]
    exp: ClaimValue[float]
    nbf: ClaimValue[float]
    iat: ClaimValue[float]
    jti: ClaimValue[str]


def encode_jwt(payload: dict[str, Any], private_key: rsa.RSAPrivateKey) -> bytes:
    """
    Encodes a JWT token with the given payload and private key.
    """

    header = {"alg": "RS256"}
    key_bytes = private_key_bytes(private_key)
    return jwt.encode(header=header, payload=payload, key=key_bytes)


def decode_jwt(
    token: bytes,
    public_key: rsa.RSAPublicKey,
    claims: Claims,
) -> dict[str, Any]:
    """
    Decodes a JWT token with the given public key.
    """

    key_bytes = public_key_bytes(public_key)
    try:
        c = jwt.decode(token, key=key_bytes, claims_options=claims)
    except BadSignatureError:
        raise InvalidToken("Invalid signature.")

    if not claims:
        return c["payload"]

    try:
        c.validate()
    except InvalidClaimError:
        raise InvalidToken("Invalid token claims.")

    return c["payload"]


def unverified_headers(token: bytes):
    try:
        signing_input, _ = token.rsplit(b".", 1)
        protected_segment, _ = signing_input.split(b".", 1)
    except ValueError:
        raise DecodeError("Not enough segments")

    protected = util.extract_header(protected_segment, DecodeError)
    return protected
