# ReRoadmap

## TAuth

1. [ ] Use issuer to filter out authproviders.
   1. [x] Specification
2. [ ] Entity graph
    1. [ ] Role inheritance
    2. [ ] multiple ownership, e.g.: app might belong to its creator, to a company, and to a speficic BU.
3. [ ] How to register a new user? 
    1. [ ] Login with Melt Key
    2. [ ] Login with Auth0
    3. [ ] Handle role inheritance from parent entity
4. [ ] Use access token to retrieve id token.
5. [ ] Authprovider: TAuth API keys (v2).
    1. [ ] CRUD API keys.
    2. [ ] CRUD /keys/:name/roles
    3. [ ] Add entity owner (role assignment and access control can be managed through this entity)
    4. [ ] You can specify which roles a key can have based on your own roles.
    5. [ ] Auto-inheritance of user permissions (restricted to a high-level role).
    6. [ ] time-constrained.
    7. [ ] revocation (softdeleting).
    8. [ ] Rotate API keys `POST keys/:name/$rotate`.
6. [ ] Use redbaby behavior to record documents updates/deletions.
7. [ ] Track all user logins (outlier pattern).
8. [ ] JWT-based communication.
    1. [x] Generate a JWT from an API key + overrides.
    2. [ ] Assymetric keys in microservices (self-signing and JWT modification).
    3. [ ] TAuth service key registry.
9.  [ ] Override headers for infostar fields. (Impersonation)
   1. [ ] Implement TAuth Client (or Teia-SDK?)
10. [ ] Schema validator for different auth providers
