from authlib.jose import jwt

max_timestamp = 2**31 - 1

header = {"alg": "RS256"}
payload = {
    "iss": "https://test/",
    "aud": "test",
    "exp": max_timestamp,
}
with open("private_key.pem") as f:
    private_key = f.read()

s = jwt.encode(header, payload, private_key)

with open("public_key.pem") as f:
    public_key = f.read()

claims = jwt.decode(s, public_key)
print("Token:", s)
print("Claims:", claims)
try:
    claims.validate()
    is_valid = True
except:
    is_valid = False

print("Is valid:", is_valid)
