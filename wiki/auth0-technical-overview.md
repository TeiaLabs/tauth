# Auth0

Entity relationship diagram for Auth0

## Entities

- Org N:N Apps
- API N:N Apps
- Iss 1:N Apps

```mermaid
erDiagram
    Org {
        id org-id
        string name
    }
    API {
        aud id
        name chatapi
    }
    Iss {
        id osfeuauth0
        name osf--auth0
    }
    Apps {
        azp client-id
        name chatweb
    }
    Org ||--|| Apps : "N:N"
    API ||--|| Apps : "N:N"
    Iss ||--1 Apps : "1:N"
```

## Options

1. 1 app/client-id/azp per SPA
   1. might allow more flexibility in Auth0 configs
2. 1 API/aud per SPA
   1. Cleaner setup.
