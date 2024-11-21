# Authentication

This document describes how to use TAuth for authentication in your applications.
We go over the following topics:

- [Authentication](#authentication)
  - [Python Project Setup](#python-project-setup)
  - [Request Headers](#request-headers)
  - [Authentication Endpoint (`/authn`)](#authentication-endpoint-authn)
  - [Authproviders](#authproviders)
    - [Auth0](#auth0)
    - [MELT Key](#melt-key)
      - [Generating User Keys](#generating-user-keys)

## Python Project Setup

To use TAuth for Authentication in a Python project, we first need to set up a few environment variables to configure TAuth to use remote authentication (i.e., authenticate using the main TAuth API).
You can add the following environment variables to your `.env` file:

```sh
TAUTH_AUTHN_ENGINE="remote"
TAUTH_AUTHN_ENGINE_SETTINGS_API_URL="https://tauth.allai.digital/"
```

After setting these environment variables, we can start using the TAuth middleware in our FastAPI application (see the [tauth.dependencies.authentication][tauth.dependencies.authentication] module).

## Request Headers

Whether you're using TAuth via its REST API directly or including it in your FastAPI-based application, you will need to provide values for the following headers to authenticate your requests:

- `Authorization`: This header should contain the `Bearer` token that you received from TAuth.
- `X-ID-Token`: This header should contain an OIDC ID token for an authentication provider that is registered in TAuth. This header is unecessary for API key providers.
- `X-User-Email`: This header should contain the email address of the user that is being authenticated. This header is optional for OAuth2/OIDC providers, but is required for API key providers (specifically, MELT Key when using either a root or admin key).

## Authentication Endpoint (`/authn`)

The `/authn` endpoint is the main authentication endpoint, and is used to authenticate users using the TAuth API.
The endpoint does not accept any parameters, and instead relies on the aforementioned authentication headers.
Here is an example of a request to the `/authn` endpoint:

```sh
curl -X POST \
  https://tauth.allai.digital/authn \
  -H 'Authorization: Bearer <token>' \
  -H 'X-User-Email: <user_email>'
```

## Authproviders

TAuth supports multiple authentication providers and easily abstracts them for your application.
This includes OAuth2/OIDC providers, such as Auth0, as well as custom API key providers.

The two things in common among all providers is that:

- They are registered in the `POST /authproviders` endpoint
- They must have the following attributes:
    - `type`: provider type (e.g., `auth0`, `melt-key`, etc.).
    - `organization_name`: organization entity that the provider is associated with.

Since each provider has its own unique configuration, we will go over each provider separately.

### Auth0

[Auth0](https://auth0.com/) is a popular identity provider platform used by many companies.
Configuring an Auth0 account is beyond the scope of this document; please refer to the [Auth0 documentation](https://auth0.com/docs/) for more information.
To configure an Auth0 provider in TAuth, you will need to provide the following Auth0 attributes:

- **Issuer URL**: This is the URL of your Auth0 tenant.
It usually looks something like this: `https://<tenant>.auth0.com/` (unless you have a custom domain set up).
- **Audience**: The audience (`aud` claim in access token) defines the intended consumer of the token.
This is typically the resource server (API, in the dashboard) that a client (Application) would like to access.
- **Organization ID**: Optional field.
TAuth also support Auth0 Organizations (https://auth0.com/docs/organizations) which allows you to manage multiple tenants from a single account.
If you are using Auth0 Organizations, you can specify the organization ID here.

Additionally, you also need in TAuth:

- An organization entity.
This links the Auth0 identity provider to the organization entity.
- A service entity (optional).
This can be useful to identify which service is using the Auth0 provider (you may also have other audience values for each service and register one authprovider for each one).

Here is an example payload for the `POST /authproviders` endpoint:

```json
{
    "type": "auth0",
    "organization_name": "<org_entity_handle>",
    "external_ids": [
        {
            "name": "issuer",
            "value": "https://<issuer_url>/"
        },
        {
            "name": "audience",
            "value": "<audience>"
        }
    ],
    "service_name": "<optional_service_entity_handle>"
}
```

To log into TAuth using an Auth0 authprovider, you should use the `Authorization` and `X-ID-Token` headers, passing the values for the access token and ID token, respectively.

### MELT Key

MELT Keys are a custom API key provider that is used by TAuth.
They have the following format: `MELT_<organization>/[service]--<key_name>--<key_id>`.

To configure a MELT Key provider, you will need to provide an organization name:

```json
{
    "type": "melt-key",
    "organization_name": "<org_entity_handle>"
}
```

Once you register MELT Key as an authprovider for an organization, you still need to call a few endpoints.
The first thing to do is to call `POST /clients` to create a Client for the organization.
You can create a client with the same `name` as your organization.
If you have sub-organization or services that have your organization entity as a parent, you may also create sub-clients for those.
All sub-clients **must** be scoped with forward slashes.
For instance, if you have an organization named `/my-org` and a client for that with the same name, you can then create a sub-client named `/my-org/my-service`.
This is useful for scoping keys to specific services.

Once you create a client, you will receive a `default` key for that client.
You must copy the key value and store it somewhere safe as it cannot be retrieved later.

#### Generating User Keys

You may generate user keys for a MELT Key client (or sub-client) by calling `POST /keys`.
Here is an example payload:

```json
{
  "name": "string",
  "organization_handle": "string",
  "service_handle": "string"
}
```

This will generate a new key with the given name for the client and return it in the response.
You can then use this key to authenticate as a user for the client.
