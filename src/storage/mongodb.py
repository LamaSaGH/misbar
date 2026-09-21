import os
from functools import lru_cache

from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()


@lru_cache
def get_mongo_client() -> MongoClient:
    mongo_uri = os.getenv("MONGODB_URI")

    if not mongo_uri:
        raise RuntimeError("MONGODB_URI is not configured.")

    return MongoClient(
        mongo_uri,
        serverSelectionTimeoutMS=5_000,
    )


def get_database():
    database_name = os.getenv("MONGODB_DATABASE")

    if not database_name:
        raise RuntimeError("MONGODB_DATABASE is not configured.")

    return get_mongo_client()[database_name]


def ping_database() -> bool:
    response = get_mongo_client().admin.command("ping")
    return response.get("ok") == 1.0