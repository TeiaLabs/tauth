# TAuth Roadmap

1. CRUD orgs
2. CRUD entities (users/services)
3. CRUD /users|services/:email/roles
4. CRUD authproviders
5. Override headers for infostar fields.
6. Refactor auth into authproviders.
   1. MELT API keys (legacy).
   2. TAuth API keys (v2).
      1. CRUD API keys.
      2. CRUD /keys/:name/roles
      3. Rotate API keys `POST keys/:name/$rotate`.
      4. revocation (softdeleting).
      5. time-constrained.
      6. You can specify which roles a key can have based on your own roles.
      7. Auto-inheritance of user permissions (restricted to a high-level role).
   3. refactor auth0-dyn into something decent.
7. Caching abstraction.
   1. Seeing what's cached (root only).
   2. Purging all caches.
   3. Purging a specific entry of a specific cache.
8. Audit tables for all collections (redbaby behavior + audit routes).
9.  JWT-based communication.
   1. Generate a JWT from an API key + overrides.
   2. Assymetric keys in microservices (self-signing and JWT modification).
   3. TAuth service key registry.
