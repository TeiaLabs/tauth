import inspect
from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import BackgroundTasks, Header, Request, Security
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBase

UserEmail = Annotated[
    str | None,
    Header(
        alias="X-User-Email",
        description="Ignore when using OAuth.",
    ),
]

IDTokenHeader = Annotated[
    str | None,
    Header(
        alias="X-ID-Token",
        description="Auth0 ID token.",
    ),
]

AccessTokenHeader = Annotated[
    HTTPAuthorizationCredentials | None,
    Security(HTTPBase(scheme="bearer", auto_error=False)),
]

AuthHeaders = Annotated[
    *tuple[
        UserEmail,
        IDTokenHeader,
        AccessTokenHeader,
    ],
    "Headers required for authentication.",
]

AuthHeaderInjectorParams = Annotated[
    *tuple[Request, BackgroundTasks, AuthHeaders],
    "Parameter sequence for auth_headers_injector.",
]


def auth_headers_injector(
    auth_fn: Callable[
        [AuthHeaderInjectorParams], Any | Coroutine[Any, Any, Any]
    ],
) -> Callable[[AuthHeaderInjectorParams], Any]:

    async def async_wrapper(
        request: Request,
        background_tasks: BackgroundTasks,
        user_email: UserEmail = None,
        id_token: IDTokenHeader = None,
        authorization: AccessTokenHeader = None,
    ):
        result = await auth_fn(
            request,
            background_tasks,
            user_email,
            id_token,
            authorization,
        )
        return result

    def sync_wrapper(
        request: Request,
        background_tasks: BackgroundTasks,
        user_email: UserEmail = None,
        id_token: IDTokenHeader = None,
        authorization: AccessTokenHeader = None,
    ):
        result = auth_fn(
            request,
            background_tasks,
            user_email,
            id_token,
            authorization,
        )
        return result

    if inspect.iscoroutinefunction(auth_fn):
        return async_wrapper
    return sync_wrapper
