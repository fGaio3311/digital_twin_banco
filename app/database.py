from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from app.settings import Settings

settings = Settings()

def get_mongodb():
    """
    Get MongoDB connection
    """
    client = MongoClient(settings.mongodb_url)
    return client[settings.mongodb_name]

def get_async_mongodb():
    """
    Get async MongoDB connection
    """
    client = AsyncIOMotorClient(settings.mongodb_url)
    return client[settings.mongodb_name]

# Collections
def users_collection():
    # Return async collection for use with await
    return get_async_mongodb().users

def transactions_collection():
    return get_async_mongodb().transactions

def logs_collection():
    return get_async_mongodb().logs
