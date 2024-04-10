# TAuth Roadmap

1. CRUD orgs
2. CRUD entities (users/services)
3. CRUD authproviders
4. CRUD /users|services/:email/roles
5. Override headers for infostar fields.
6. Refactor auth into authproviders.
7. Authprovider: MELT API keys (legacy).
8. Authprovider: TAuth API keys (v2).
    1. CRUD API keys.
    2. CRUD /keys/:name/roles
    3. Rotate API keys `POST keys/:name/$rotate`.
    4. revocation (softdeleting).
    5. time-constrained.
    6. You can specify which roles a key can have based on your own roles.
    7. Auto-inheritance of user permissions (restricted to a high-level role).
9. Authprovider: "Auth0-dyn" refactor.
    1. Identify audience using the JWT, if possible (avoid iterating over audiences).
10. Caching abstraction.
    1. Seeing what's cached (root only).
    2. Purging all caches.
    3. Purging a specific entry of a specific cache.
11. Audit tables for all collections (redbaby behavior + audit routes).
12. JWT-based communication.
    1. Generate a JWT from an API key + overrides.
    2. Assymetric keys in microservices (self-signing and JWT modification).
    3. TAuth service key registry.
13. New user-data abstraction.
