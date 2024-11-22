# Roadmap

Here we list our ideas for future development of features and improvements.
The tasks are listed in priority order.

## Tasks

- New API keys
  - Named keys
  - Rotation
  - Permission attachment
  - Soft deletion (separate collection?)

- Impersonation via new API keys
  - Header: `X-TAuth-Entity-Impersonation` containing `EntityRef` object
  - Example: `"handle:<entity_handle>;owner_handle:<owner_handle>"`
  - API key needs impersonation permission to impersonate another Entity
  - TAuth checks permission and injects the impersonated Entity instead

- Differentiate between generic permissions and resource permissions
  - Separate collection

- Add timings in TAuth
  - We need to know how long auth features take

- Allow users to execute multiple policies in one request

- Improve database functions (`Intermediate` conundrum)

- Entity graph
  - Role/permission inheritance
  - Entity groups
  - Entities "attached" to multiple organizations, entity groups, etc.

- Auditing
  - Track user activities, logins, etc.
  - Memetrics-based

- Solve cache issues

- JWT-based communication
  - Research how to be OAuth2/OIDC compliant
  - Generate a JWT from an API key + overrides.
  - Assymetric keys in microservices (self-signing and JWT modification)
  - TAuth service key registry
    - TAuth will provide utility functions for key creation, rotation, and deletion
    - Whenever a service is executed, it should create a sub-process that manages the keys
    - When a key is created/rotated, the service calls TAuth (with API key) to add new public key in registry
      - TAuth stores the last two keys to prevent services from not being able to authenticate using the previous stale key
    - TAuth validates service identity and stores JWK in registry
    - Service can now use private key to (cryptographically) sign JWTs
    - Other services can call TAuth's `.well-known/jwks.json` endpoint to GET public keys
    - TAuth also provides utility endpoint to add to APIs for manual key rotation and deletion

- Telemetry
  - We need to track requests across services
  - Research OpenTelemetry (memetrics replacement? :thinking_emoji:)

- Remove legacy MELT keys
