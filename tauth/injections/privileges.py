"""
FastAPI dependency injection for privilege checking.

is_valid_user - anyone with a valid key
is_valid_admin - token_name == default
is_valid_superuser - token_name == default and client_name == $root
"""

from typing import Callable

from fastapi import HTTPException, Request, status

from ..schemas import Creator


def get_creator(
    validate_access: Callable[[Creator], bool]
) -> Callable[[Request], Creator]:
    def wrapper(request: Request) -> Creator:
        c = request.state.creator
        if validate_access(c):
            return c
        else:
            s = status.HTTP_403_FORBIDDEN
            d = {  # TODO: use http_error_schemas
                "msg": "You do not have access to this resource.",
                "info": {"creator": c.dict()},
            }
            # TODO: delegate exception raising to the wrapped function
            raise HTTPException(status_code=s, detail=d)

    return wrapper


@get_creator
def is_valid_user(creator: Creator) -> bool:
    return True


@get_creator
def is_valid_admin(creator: Creator) -> bool:
    return creator.token_name == "default"


@get_creator
def is_valid_superuser(creator: Creator) -> bool:
    return creator.token_name == "default" and creator.client_name == "/"


@get_creator
def is_direct_user(creator: Creator) -> bool:
    return creator.token_name not in ("auth0-jwt", "azure-jwt")
