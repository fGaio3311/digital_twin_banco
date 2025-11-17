from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from app.repositories.base import BaseRepository
from app.models_mongo import UserModel

class UserRepository(BaseRepository[UserModel]):
    async def find_by_username(self, username: str) -> Optional[UserModel]:
        user_dict = await self.find_one({"username": username})
        return UserModel(**user_dict) if user_dict else None

    async def create_user(self, username: str, hashed_password: str) -> ObjectId:
        user_dict = {
            "username": username,
            "hashed_password": hashed_password,
            "balance": 0.0,
            "created_at": datetime.utcnow()
        }
        return await self.create(user_dict)

    async def update_balance(self, user_id: ObjectId, amount: float) -> bool:
        return await self.collection.update_one(
            {"_id": user_id},
            {"$inc": {"balance": amount}}
        )

    async def atomic_transfer(self, from_id: ObjectId, to_id: ObjectId, amount: float) -> bool:
        async with await self.collection.database.client.start_session() as session:
            async with session.start_transaction():
                # Deduz do remetente
                from_result = await self.collection.update_one(
                    {"_id": from_id, "balance": {"$gte": amount}},
                    {"$inc": {"balance": -amount}},
                    session=session
                )

                if from_result.modified_count == 0:
                    return False

                # Adiciona ao destinatário
                to_result = await self.collection.update_one(
                    {"_id": to_id},
                    {"$inc": {"balance": amount}},
                    session=session
                )

                if to_result.modified_count == 0:
                    return False

                return True
