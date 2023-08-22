from fastapi import Request

from ..utils import get_request_creator


class RequestAuthenticator:
    @staticmethod
    def validate(
        request: Request,
        user_email: str | None,
        api_key_header: str,
    ):
        creator = get_request_creator(token=api_key_header, user_email=user_email)
        if request.client is not None:
            creator.user_ip = request.client.host
        if request.headers.get("x-forwarded-for"):
            creator.user_ip = request.headers["x-forwarded-for"]
        request.state.creator = creator
