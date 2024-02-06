# TAuth

## overview

Intended to abstract the authentication of a FastAPI app.
Supports an API key format of its own as well as OAuth2 tokens from Azure AD and Auth0.

## authproviders

External authentication providers are registered with the app, and are used to validate the tokens.
External token details are parsed and mapped into a Creator object (same as API keys) to ease the handling of the request.

### API Key

The API key is composed of:

1. a `MELT_` prefix
2. and three values separated by double dashes:
   1. a "/path/notation" namespace for the client name,
   2. a token name (possibly namespaced by dots or slashes),
   3. and a base58btc multibase-encoded 24 byte random token.

```python
def create_token(client_name: str, token_name: str) -> str:
    token_value = multibase.encode(secrets.token_bytes(24), "base58btc")
    fmt_token_value = f"MELT_{client_name}--{token_name}--{token_value}"
    return fmt_token_value
```

e.g.: `MELT_/myorg/myapp/ui--my.prod.token--z.................................`

### Azure AD

1. register an authprovider with the audience and tenant values
2. map to which app it belongs

### Auth0

1. register an authprovider with the audience and domain values
2. map to which app it belongs

## privilege levels

- `god`
  - can create new root-level clients
- `admin`
  - can impersonate other users
  - can revoke API keys
- `dev` (API key)
  - can create sub-clients
  - can create new API keys
- `guest` (OAuth2 token)
  - can access all endpoints

## overrides

The `creator` attribute can be overriden by the user, but only if the user has the `admin` privilege level.

## technical

When an X-Tauth-App-Name header is present, the Authorization header is checked against authproviders registered for that app.

If an attribute `org-id` is present in the ID Token payload, tauth will attempt to map it to a pre-registered client.

### middleware

Its middleware adds an attribute called `creator` to the request object:

```python
class Creator(BaseModel):
    client_name: str
    token_name: str
    user_email: EmailStr
    user_ip: str = "127.0.0.1"
```

This object is intended to be recorded along any resources the user creates with his requests.

Things it'll track after V2.

- whether any attributes were overriden by the user
- whether this is a machine or a human user

### datamodels

```python
class Client(BaseModel):
    name: str
    creator: Creator
    created_at: datetime
    updated_at: datetime

class Token(BaseModel):
    name: str
    client_name: str
    creator: Creator
    created_at: datetime
    updated_at: datetime

class User(BaseModel):
    email: EmailStr
    creator: Creator
    created_at: datetime
    updated_at: datetime
```

### future datamodels

```python
class AuthProvider(BaseModel):
    id: str = Field(alias="_id")
    client_name: str  # the app name, e.g.: /osf/allai/chat/slack
    type: Literal["auth0", "azuread"]
    values: dict[str, str]
    creator: Creator
    created_at: datetime
    updated_at: datetime
```
