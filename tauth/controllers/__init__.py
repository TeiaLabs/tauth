# import os
# from pathlib import Path

# from pymongo import MongoClient
# from pymongo.database import Database
# from pymongo.collection import Collection
# from bson import ObjectId
# from pydantic import BaseModel


# class DB:
#     client: MongoClient = MongoClient(os.environ["TAUTH_MONGODB_URI"])
#     db: Database = client[os.environ["TAUTH_MONGODB_DBNAME"]]

#     @classmethod
#     def get(cls, db_name) -> Database:
#         return cls.client[db_name]


# class PymongoModel(BaseModel):

#     class Config:
#         json_encoders = {
#             ObjectId: str,
#             Path: str,
#         }

#     @classmethod
#     def

#     @classmethod
#     def find_many(cls, filter=None, projection=None, skip=0, limit=0, sort=None):
#         return [cls(**doc) for doc in d.collection.find(filter, projection, skip, limit, sort)]
