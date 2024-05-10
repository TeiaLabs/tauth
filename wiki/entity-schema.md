# Entity Examples

## Entity Schema

```py
class EntityDAO(BaseModel):
    created_at: datetime
    created_by: InfoStar
    updated_at: datetime
    updated_by: InfoStar

    external_ids: list[Attribute]  # e.g., url, azuread-id/auth0-id, ...
    extra: list[Attribute]  # birthday
    handle: str  # nei@teialabs.com, athena--api, /osf/innovation
    owner_ref: Optional[EntityRef]
    roles: list[str]  # ["teia-admin", "allai-user-basic"]
    type: Literal["user", "service", "organization"]
```

Rules:

- Organizations must be scoped using slashes (`/`).
  - Sub-organizations must be explicit in the handle.
- Services must be owned by organizations.
  - Services must be scoped using double dashes (`--`).
- User handles must be email addresses.
- External IDs must be scoped using double dashes (`--`).
- External IDs must be unique per entity.
- Roles can be inherited from the owner using `inherit-roles`.

## Teia Labs

```json
{
    "_id": "1",
    "handle": "/teialabs",
    "owner_ref": null,
    "extra": [
        {
            "key": "name",
            "value": "Teia Labs"
        }
    ],
    "roles": ["api-admin", "api-user"],
    "external_ids": [
        {
            "key": "cnpj",
            "value": "28.2xx.xxx/0001-xx"
        },
        {
            "key": "teialabs--auth0--org-id",
            "value": "org_1234567890"
        }
    ],
    "type": "organization",
}
```

### User

```json
{
    "_id": "2",
    "handle": "martin@teialabs.com",
    "owner": {
        "id": "1",
        "handle": "teialabs",
        "type": "organization"
    },
    "extra": [
        {
            "key": "name",
            "value": "Martin More"
        }
    ],
    "roles": ["inherit-roles"],
    "external_ids": [
        {
            "key": "/teialabs--auth0--user-id",
            "value": "auth0|1234567890"
        }
    ],
    "type": "user",
}
```

### Service

```json
{
    "_id": "3",
    "handle": "allai--vscode--chat",
    "owner": {
        "id": "1",
        "handle": "/osf/innovation",
        "type": "organization"
    },
    "extra": [
        {
            "key": "name",
            "value": "Athena API"
        }
    ],
    "roles": ["inherit-roles"],
    "external_ids": [
        {
            "key": "teialabs--auth0--client-id",
            "value": "client_1234567890"
        }
    ],
    "type": "service",
}
```

## entity data

```py
class EntityData(Subtypeable):
    _id: Hash(handle, name, value)
    handle: str
    name: str  # ClientData | CompanyData
    value: any # {ip, user-agent} | {position-name, department-name}
    created_at: datetime
    last_seen_at: datetime
```
