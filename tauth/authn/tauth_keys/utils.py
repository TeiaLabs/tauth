from ...utils.errors import TauthException


class TauthKeyParseError(TauthException):
    pass


def parse_key(key: str) -> tuple[str, str]:
    """
    return: db_id, secret
    """
    parts = key.split("_")
    try:
        return parts[1], parts[2]
    except IndexError:
        raise TauthKeyParseError("Invalid key format")
