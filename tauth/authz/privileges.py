"""
FastAPI dependency injection for privilege checking.

is_valid_user - anyone with a valid key
is_valid_admin - token_name == default
is_valid_superuser - token_name == default and client_name == $root
"""

from typing import Callable

from fastapi import HTTPException, Request, status

from ..schemas import Infostar


def get_infostar(
    validate_access: Callable[[Infostar], bool]
) -> Callable[[Request], Infostar]:
    def wrapper(request: Request) -> Infostar:
        infostar: Infostar = request.state.infostar
        if validate_access(infostar):
            return infostar
        else:
            s = status.HTTP_403_FORBIDDEN
            d = {  # TODO: use http_error_schemas
                "msg": "You do not have access to this resource.",
                "info": {"infostar": infostar.model_dump(mode="json")},
            }
            # TODO: delegate exception raising to the wrapped function
            raise HTTPException(status_code=s, detail=d)

    return wrapper


@get_infostar
def is_valid_user(infostar: Infostar) -> bool:
    return True


@get_infostar
def is_valid_admin(infostar: Infostar) -> bool:
    return infostar.apikey_name == "default"


@get_infostar
def is_valid_superuser(infostar: Infostar) -> bool:
    return infostar.apikey_name == "default" and infostar.authprovider_org == "/"


@get_infostar
def is_direct_user(infostar: Infostar) -> bool:
    return infostar.apikey_name != "jwt"
