from pydantic import ConfigDict
from pymongo import IndexModel
from redbaby.document import Document


class UserInfoDAO(Document):
    hashed_token: str
    exp: float

    model_config = ConfigDict(extra="allow")

    @classmethod
    def collection_name(cls) -> str:
        return "userinfo"

    @classmethod
    def indexes(cls) -> list[IndexModel]:
        idxs = [
            IndexModel([("hashed_token", 1)], unique=True),
            IndexModel([("exp", 1)]),
        ]
        return idxs
