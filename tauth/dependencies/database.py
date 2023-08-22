from redb.core.instance import RedB, MongoConfig

from ..models import all_models
from ..settings import Settings


def init_app(sets: Settings):
    RedB.setup(
        config=MongoConfig(
            database_uri=sets.TAUTH_MONGODB_URI,
            default_database=sets.TAUTH_MONGODB_DBNAME,
        ),
    )
    for m in all_models:
        m.create_indexes()
