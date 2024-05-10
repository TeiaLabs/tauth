# AuthN

App user:

1. User authenticates with OAuth and the app gets a JWT.
2. App sends the JWT to 1st layer API.
3. 1st layer API validates the JWT against provider.
    - 1st layer API forwards JWT in any requests to 2nd layer APIs and they validate it against provider.
    - 1st layer API creates a new JWT that can be validated locally/against tauth.
    - 1st layer API uses its own API key along with override headers to communicate with 2nd layer.

CLI user:

1. User saves an API key to his env vars.
2. CLI apps send the API key to authenticate with 1st layer APIs.
3. 1st layer API validates the API key against tauth.
    - 1st layer forwards API key to communicate with 2nd layer and they validate it against tauth.
    - 1st layer API creates a new JWT that can be validated locally/against tauth.
    - 1st layer API uses its own API key along with override headers to communicate with 2nd layer.

## Authproviders

- versioned (audit table needed)
- unique(app_name, org_name, type)

```py
class AuthProvider(BaseModel):
    service_handle: Optional[str] = None # /allai/chat/slack
    created_at: datetime
    created_by: InfoStar
    extra: list[Attribute]  # dynamic provider selection
    id: str = Field(alias="_id")
    org_name: str  # /osf
    type: Literal["auth0", "melt-key", "tauth-key", ...]
    updated_at: datetime
    updated_by: InfoStar
```

### Melt API Keys (legacy)

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

### TAuth API Keys

1. a `TAUTH_` prefix
2. and two values separated by double dashes:
    1. a unique name for the key,
    2. and a base58btc multibase-encoded 24 byte random token.

```py
class APIKey(SoftDeleteable):  # allows revocation
    id: Hash(name, value, soft_deleted)
    created_at: datetime
    created_by: InfoStar
    name: str
    type: Literal["tauth-key"]
    value: str
```
