# Entity Examples

## Entity Schema

```py

class AuthorizationPolicyDAO:
    description: str
    name: str
    policy: str
    type: Literal["opa"]


class PermissionDAO:
    name: str
    description: str
    entity_ref: EntityRef


class RoleDAO:
    name: str
    description: str
    inheritable: bool
    entity_ref: EntityRef
    permissions: list[PyObjectId] = Field(default_factory=list)


class ResourceDAO:
    service_ref: EntityRef
    role_ref: RoleRef

    collection: str
    ids: list[str]


class EntityRelationshipDAO:
    _id: ObjectId
    origin: EntityRef
    target: EntityRef
    type: Literal["parent", "child"]


class EntityDAO:
    external_ids: list[Attribute] = Field(
        default_factory=list
    )
    extra: list[Attribute] = Field(default_factory=list)
    handle: str
    role_refs: list[RoleRef] = Field(default_factory=list)
    type: Literal["user", "service", "organization"]

class KeyDAO:
    handle: str
    service_ref: EntityRef | None
    organization_ref: EntityRef
    extra: list[Attribute] = Field(default_factory=list)

class AuthProviderDAO:
    external_ids: list[Attribute] = Field(
        default_factory=list
    )  # issuer is here
    extra: list[Attribute] = Field(default_factory=list)
    organization_ref: OrganizationRef
    service_ref: ServiceRef
    type: Literal["auth0", "melt-key", "tauth"]
```