# Roadmap

## TAuth

1. [ ] Authprovider: "Auth0-dyn" refactor (use AZP field).
2. [ ] Fix MELT API keys (legacy).
   1. [ ] Fix lookup on entity graph
   2. [ ] Maybe there are some wrong variables
3. [ ] Override headers for infostar fields. (Impersonation)
   1. [ ] Implement TAuth Client (or Teia-SDK?)
4. [ ] Caching abstraction.
   1. [ ] Review Cacheia
5. [ ] JWT-based communication.
    1. [ ] Generate a JWT from an API key + overrides.
    2. [ ] Assymetric keys in microservices (self-signing and JWT modification).
    3. [ ] TAuth service key registry.
6. [ ] Track all user logins (outlier pattern).
7. [ ] Use redbaby behavior to record documents updates/deletions.
8. [ ] Authprovider: TAuth API keys (v2).
    1. [ ] CRUD API keys.
    2. [ ] CRUD /keys/:name/roles
    3. [ ] Rotate API keys `POST keys/:name/$rotate`.
    4. [ ] revocation (softdeleting).
    5. [ ] time-constrained.
    6. [ ] You can specify which roles a key can have based on your own roles.
    7. [ ] Auto-inheritance of user permissions (restricted to a high-level role).
9. [ ] True entity graph (with relationships).
    1. [ ] multiple ownership, e.g.: app might belong to its creator, to a company, and to a speficic BU.
10. [ ] AuthZ stuff.
11. [ ] Docs.
12. [ ] New user-data abstraction.

## Meltingface

1. [ ] Update Tool Calling endpoints.
   1. [ ] Static tools.
   2. [ ] Update current database schemas.
   3. [ ] Use new tool schemas: save tool runs on a separate collection from completions.
   4. [ ] Extract tool caller to outside core.
   5. [ ] Separate tool calling logic into three stages: raw (only call openai and return), call (iterate between openai and plugin calls) and Amir (build static tools and use "call" flow to run the remaining)
2. [ ] Integrate with TAuth V2.Authprovider: TAuth API keys (v2).
    1. [ ] CRUD API keys.
    2. [ ] CRUD /keys/:name/roles
    3. [ ] Rotate API keys `POST keys/:name/$rotate`.
    4. [ ] revocation (softdeleting).
    5. [ ] time-constrained.
    6. [ ] You can specify which roles a key can have based on your own roles.
3. [ ] Integrate with Prompts V2.
   1. CRUD for prompt templates.

## Athena

1. [ ] Reorg threads and messages app into a single app with submodules.
2. [ ] CRUD convostarters.
3. [ ] CRUD bots
4. [ ] Review and implement canvas:
   1. [ ] Create canvas
   2. [ ] Create canvas objects
   3. [ ] Retrieve canvas objects
   4. [ ] Delete canvas object
   5. [ ] Delete canvas
   6. [ ] Connect with datasources (files, ...)

### Redbaby

1. [ ] Collection-based document versioning.
