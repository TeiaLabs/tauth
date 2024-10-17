# Infostar

[Infostar][tauth.schemas.infostar.Infostar] is a Pydantic `BaseModel` object.
It is a star schema around several artifacts that interact during an authentication request.
It includes information about which entity was authenticated, which authprovider was used, and the request itself.

Here is the schema for `Infostar`:

## ::: tauth.schemas.infostar.Infostar
    options:
      show_source: true

## Creator (legacy)

!!! danger
    Creator is deprecated and will be removed in a future release.

[Creator][tauth.schemas.creator.Creator] is a legacy schema used to store information about the creator of a request.
It was mainly used in TAuth V1, and the context it provided was often insufficient.
`Creator` has been replaced by `Infostar` in TAuth V2.

Here is the schema for `Creator`:

## ::: tauth.schemas.creator.Creator
