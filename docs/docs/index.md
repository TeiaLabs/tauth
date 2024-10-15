# TAuth - **T**eia **Auth**entication and **Auth**orization

TAuth is Teia's authentication and authorization service.
It provides a centralized security experience for your applications.
TAuth provides FastAPI-compatible dependencies to integrate into Python projects and a REST API to be used as a standalone service.

To begin using TAuth, please refer to the following pages:

- [End-user guide](./user_guide/index.md)
- [Development guide](./dev_guide/index.md)

If you want to access the service directly, you can use the following links:

| Environment | URL | Usage |
| --- | --- | --- |
| Alpha | [https://tauth.alpha.allai.digital](https://tauth.alpha.allai.digital) | Development and nightly testing. High potential for breaking changes, data loss, and overall service instability. |
| Beta | [https://tauth.beta.allai.digital](https://tauth.beta.allai.digital) | New features and pre-release testing. Frequent breaking changes and data loss. |
| Production | [https://tauth.allai.digital](https://tauth.allai.digital) | Stable and tested. Data migrations are done when needed to ensure service integrity. Changes are tested and announced in advance. |

## Core Features

- **Centralized Security**: authentication and authorization features abstraced away.
- **FastAPI-compatible**: ready-to-use dependencies for existing FastAPI applications.
- **Authentication**: supports multiple providers (OAuth2/OIDC, API keys) to manage users.
- **Authorization**: manage users, permissions, roles, and policies to control access.

## Quick Links

- [API Reference][tauth]
- [GitHub Repository](https://github.com/teialabs/tauth)
- [PyPI Package](https://pypi.org/project/tauth/)
