from ..models import UserDAO
from ..schemas import UserOut
from ..settings import Settings


def read_many(**kwargs) -> list[UserOut]:
    filters = {k: v for k, v in kwargs.items() if v is not None}
    users = UserDAO.collection(alias=Settings.get().TAUTH_REDBABY_ALIAS).find(
        filter=filters
    )
    users_view = [UserOut(**user) for user in users]
    return users_view
