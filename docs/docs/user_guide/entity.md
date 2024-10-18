# Entities

An [Entity][tauth.entities.models.EntityDAO] is one of the core concepts of TAuth.
It stores information that allows us to link authentication and authorization requests to a specific object (i.e., the "who" aspect of the security model).

Here is the database schema for `Entity`:

## ::: tauth.entities.models.EntityDAO
    options:
      show_source: true

Entities can be of different `type`s:

- **Organization**: models higher-level concepts, such as companies, teams, or departments.
- **Service**: used to represent applications, APIs, or other services.
- **User**: used to represent end-users.

All entities possess a unique `handle`, which is a unique identifier.
There are some restrictions that handles must follow:

- Handles must be unique across all entities of the same type and that have the same relationship to the same parent entity.
For example, two users cannot have the same handle if they are both owned by the same organization.
- Organization handles must start with `/`.
For example, `/my-company` is a valid organization handle.
- Service handles must have an organization handle prepended to it.
For example, to create a service entity for a service named `my-service` in the organization `my-company`, the handle would be `/my-company/my-service`.

Entities can also be related to each other.
This is modeled via the `owner_ref` attribute, which indicates that an entity is owned by another entity, in a parent-child relationship.

## Entities in Authentication

Organization entities are used in the authentication process to attach authentication providers.
That is, all authentication providers must be linked to an organization entity.
This allows us to determine which organization is responsible for managing the authentication process of its services and users.

## Entities in Authorization

Entities are used in the authorization process to determine whether a user, service, or organization has access to a specific resource.
One of the key attributes used in this process is the list of `roles` that an entity possesses.
You can attach and remove roles using the TAuth API.
