def parse_key(key: str) -> tuple[str, str]:
    """
    return: db_id, secret
    """
    parts = key.split("_")
    return parts[1], parts[2]
