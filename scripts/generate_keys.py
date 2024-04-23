from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jwcrypto import jwk

# Generate an RSA private key
private_key = rsa.generate_private_key(
    public_exponent=65537, key_size=2048, backend=default_backend()
)

# Serialize the private key to PEM format
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)

# Write the private key PEM file to disk
with open("private_key.pem", "wb") as pem_file:
    pem_file.write(private_pem)

# Extract the public key from the private key
public_key = private_key.public_key()

# Serialize the public key to PEM format
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)

# Write the public key PEM file to disk
with open("public_key.pem", "wb") as pem_file:
    pem_file.write(public_pem)

print("The private key has been generated and saved to 'private_key.pem'")
print("The public key has been generated and saved to 'public_key.pem'")


# Load the private key from the PEM file
with open("private_key.pem", "rb") as pem_file:
    private_key_pem = pem_file.read()

# Load the public key from the PEM file
with open("public_key.pem", "rb") as pem_file:
    public_key_pem = pem_file.read()

# Convert the private key PEM to a JWK object
private_key = jwk.JWK.from_pem(private_key_pem)

# Convert the public key PEM to a JWK object
public_key = jwk.JWK.from_pem(public_key_pem)

# Create a JWKS with both the private and public keys
jwks = {
    "keys": [
        private_key.export(private_key=True, as_dict=True),
        public_key.export(as_dict=True),
    ]
}

# Convert JWKS to a JSON string
import json

jwks_json = json.dumps(jwks, indent=4)

# Print the JWKS JSON
print(jwks_json)

# Optionally, save the JWKS to a file
with open("jwks.json", "w") as jwks_file:
    jwks_file.write(jwks_json)

print("The JWKS has been generated and saved to 'jwks.json'")
