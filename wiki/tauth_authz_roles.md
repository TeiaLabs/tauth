# Meeting Notes

## Discussions

- Entity:
  - Keep modelling as it is (change to graph later)

- Roles:
  - Separate collection that manages permission lists
    - `name="teia-admin"`,
    - `permissions=["athena-admin", "datasources-admin", ...]`
  - Entities receive role IDs from database (resolve to names/permissiosn when needed)
  - Groups: management via roles
    - `name="GROUP_NAME:ROLE_NAME"`
    - `permissions=["read", "write", "add-user", "remove-user"]`

- Resource Management:
  - Done via roles
  - Create policies that return filters
    - All resources whose owner is the user
    - All resource IDs that the user has access to via roles
    - Combination of both
  - Example: group files
    - User indexes two datasources in Datasources API: `ds1` and `ds2`
    - "Group creation" in TAuth: create role named `mygroup:admin` with policies
    - User query in Datasources API: all files with `read` permission (including groups)
    - Datasources queries to TAuth:
      - `POST /authz` with policy `datasources_filter:read` and additional metadata
    - TAuth resolves role names for user entity and sends to OPA
    - Run policy in OPA, which contains two "sub-policies" (user ownership, role-based filter)
      - Create MongoDB filter user ownership
      - Check all roles with `name.startswith=mygroup:` with `read` access
      - Create MongoDB filter for `resources` collection in TAuth
      - Execute that query inside OPA (figure out how to do this)
      - Create new MongoDB filter for object IDs
      - OPA combines user filters and returns to TAuth
    - TAuth returns filters to Datasources API

### Role Manangement

Indices:

- `("entity_handle", 1)`
- `(["entity_handle", "name"], unique=True)`

```json
// Roles
{
    "_id": "...",
    "entity_handle": "/teialabs",
    "name": "athena-admin",
    "description": "...",
    "permissions": ["create-bot", "add-prompt", ...],
}
{
    "_id": "...",
    "entity_handle": "/teialabs",
    "name": "mygroup:admin",
    "description": "...",
    "permissions": ["read", "write", "delete", "remove-user", "add-user"],
}
{
    "_id": "...",
    "entity_handle": "/teialabs",
    "name": "mygroup:write",
    "description": "...",
    "permissions": ["read", "write"],
}
```

### Resource Management

Indices:

- `("role", 1)`
- `(["service", "collection", "role"], unique=True)`

```json
{
    "_id": "...",
    "service": "datasources",
    "collection": "prompts",
    "role": "mygroup",
    "ids": ["ds1", "ds2", ...],
}
```

## TODOs

- Roles
  - CRUD
  - Role copying ("inheritance" behavior)

- Refactor AuthorizationEngine:
  - `setup`: initialize engine (OPA, REST, etc.) based on settings
  - `get`: singleton pattern
  - `Depends` to get engine

- Infostar:
  - `Depends` to get object
