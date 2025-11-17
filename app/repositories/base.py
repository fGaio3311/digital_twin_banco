from typing import Generic, TypeVar, List
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

T = TypeVar('T')

class BaseRepository(Generic[T]):
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def find_one(self, filter_dict: dict) -> T:
        result = await self.collection.find_one(filter_dict)
        return result

    async def find_many(self, filter_dict: dict) -> List[T]:
        cursor = self.collection.find(filter_dict)
        return await cursor.to_list(length=None)

    async def create(self, document: dict) -> ObjectId:
        result = await self.collection.insert_one(document)
        return result.inserted_id

    async def update(self, filter_dict: dict, update_dict: dict) -> bool:
        result = await self.collection.update_one(filter_dict, {"$set": update_dict})
        return result.modified_count > 0

    async def delete(self, filter_dict: dict) -> bool:
        result = await self.collection.delete_one(filter_dict)
        return result.deleted_count > 0
