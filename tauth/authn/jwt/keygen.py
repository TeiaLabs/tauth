from pathlib import Path
from typing import TypedDict

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jwcrypto import jwk

from .constants import DEFAULT_PATH


class JWK(TypedDict, total=False):
    alg: str
    use: str
    kty: str
    n: str
    e: str
    kid: str


class JWKS(TypedDict):
    keys: list[JWK]


def generate_jwks(public_key: rsa.RSAPublicKey) -> JWKS:
    # Convert the public key PEM to a JWK object
    jwk_public_key = jwk.JWK.from_pem(public_key_bytes(public_key))
    dict_jwk: dict[str, str] = jwk_public_key.export(as_dict=True)  # type: ignore

    public_jwk = JWKS(keys=[JWK(alg="RS256", use="sig", **dict_jwk)])
    return public_jwk


def generate_signing_pair(
    key_size: int = 2048,
) -> tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    """
    Generate an RSA private key and extract the public key.
    """

    # Generate an RSA private key
    private_key = rsa.generate_private_key(
        key_size=key_size,
        public_exponent=65537,
        backend=default_backend(),
    )

    # Extract the public key from the private key
    public_key = private_key.public_key()

    return private_key, public_key


def private_key_bytes(private_key: rsa.RSAPrivateKey) -> bytes:
    """
    Serialize the private key to PEM format.
    """

    # Serialize the private key to PEM format
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return private_bytes


def public_key_bytes(public_key: rsa.RSAPublicKey) -> bytes:
    """
    Serialize the public key to PEM format.
    """

    # Serialize the public key to PEM format
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return public_bytes


def save_signing_pair(
    private_key: rsa.RSAPrivateKey,
    public_key: rsa.RSAPublicKey,
    path: Path = DEFAULT_PATH,
) -> tuple[Path, Path]:
    """
    Save the private and public keys to disk.
    """

    if not path.exists():
        path.mkdir(parents=True)

    private_path = path / "private_key.pem"
    public_path = path / "public_key.pem"

    private_bytes = private_key_bytes(private_key)

    # Write the private key PEM file to disk
    with open(private_path, "wb") as pem_file:
        pem_file.write(private_bytes)

    public_bytes = public_key_bytes(public_key)

    # Write the public key PEM file to disk
    with open(public_path, "wb") as pem_file:
        pem_file.write(public_bytes)

    return private_path, public_path
