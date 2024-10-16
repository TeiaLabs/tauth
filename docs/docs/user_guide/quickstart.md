# Quickstart

!!! note
    This quickstart tutorial requires TAuth to be installed.
    If you haven't already, please follow the [installation guide](./installation.md).

In this quickstart, we'll walk through the basics of using TAuth as an end-user to protect a FastAPI application.
We'll show you how to:

- [Quickstart](#quickstart)
  - [Accessing TAuth API](#accessing-tauth-api)
  - [Creating an Organization](#creating-an-organization)
  - [Registering an AuthProvider](#registering-an-authprovider)
  - [Configuring Local Repository](#configuring-local-repository)
  - [Protecting Endpoint with Authentication](#protecting-endpoint-with-authentication)
  - [Authorization Basics](#authorization-basics)
  - [Protecting Endpoint with Authorization](#protecting-endpoint-with-authorization)

## Accessing TAuth API

To access TAuth's production API, you can visit [this link](https://tauth.allai.digital/docs).
You will be presented with the API's Swagger UI, which contains documentation and a playground with example requests to test the API.
You can inspect which version of TAuth is currently running by checking the tag next to the API name.
You can also programmatically acces the API.
For instance, you can check if the API is running by making a `GET` request to the healthcheck endpoint:

```sh
curl -X 'GET' 'https://tauth.allai.digital/'
```

The API is divided into the following sections:

| Section Name | Description |
| --- | --- |
| `health` | API status check. |
| `authn` | Main authentication endpoints. |
| `authz` | Main authorization endpoints and permission, role, and policy management. |
| `entities` | Endpoints for managing entities. |
| `authproviders` | Endpoints for managing authentication providers. |
| `legacy` | Endpoints for legacy (V1) support (includes MELT Key management). |

Since TAuth is intended to be a centralized security system, you will often need to interact with its API directly to create and manage your authentication and authorization settings.
The API is secured with an API key, so you will need to obtain one from the TAuth team before you can start using the API.
Once you have an API key, you can use it to make requests to the API by including it in the `Authorization` header of your requests:

```sh
curl -X 'POST' \
  'https://tauth.allai.digital/entities/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <API_KEY>' \  # (1)
  ...  # (2)
```

1. Replace <API_KEY> with your API key
2. Continue with request information here

You can also input your API key in the Swagger UI by clicking the `Authorize` button in the top right corner of the Swagger UI and inputting your API key in the `Value` field.

Then you can either use TAuth's Python SDK (FastAPI middleware) or call the REST API directly to interact with the TAuth from your application.

## Creating an Organization

The first step to using TAuth is to create an entity to represent your organization.
This entity will be used to manage your authentication and authorization settings.
To create an organization, use the `POST /entities/` endpoint.
Let's create an organization called `MyOrg`:

```sh
curl -X 'POST' \
  'https://tauth.allai.digital/entities/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <API_KEY>' \
  -d '{
    "handle": "/MyOrg",
    "type": "organization"
  }'
```

!!! tip
    The `handle` field is used to identify your organization.
    It **must** start with a forward slash for organization entities.
    For more information on entities, see the [entities section](./entity.md).

Now that we have an organization, we can start configuring our authentication and authorization settings.

## Registering an AuthProvider

TODO.

## Configuring Local Repository

TODO.

## Protecting Endpoint with Authentication

TODO.

## Authorization Basics

TODO.

## Protecting Endpoint with Authorization

TODO.
