# TAuth Glossary

- Auth0
  - Identity provider.
  - Organization: `org-id` claim.
    - [Official docs](https://auth0.com/docs/manage-users/organizations)
    - Maps to an organization name in our DB.
    - Used to denote to which org a user who authenticated through a client's Auth0 app belongs.
- Identity Provider
  - Service that stores and verifies user identity.
  - Examples: Auth0, Azure AD, TAuth.
- JWT
  - JSON Web Token
  - [RFC](<https://datatracker.ietf.org/doc/html/rfc7519>).
  Pronounced "jot" or more formally /dʒɒt/.
  - Claim: field in JWT object.
  - Issuer: `iss` claim, e.g.: `osf.eu.auth0`.
  - Audience: `aud` claim, e.g.: `athena`.
  - Subject: `sub` claim, e.g.: `aaad|12345`.
  - Authorized Providers: `azp` claim, e.g.: `client-id`.
