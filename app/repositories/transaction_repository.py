from typing import List
from datetime import datetime
from bson import ObjectId
from app.repositories.base import BaseRepository
from app.models_mongo import TransactionModel

class TransactionRepository(BaseRepository[TransactionModel]):
    async def create_transaction(
        self,
        user_id: ObjectId,
        transaction_type: str,
        amount: float
    ) -> ObjectId:
        transaction_dict = {
            "user_id": user_id,
            "type": transaction_type,
            "amount": amount,
            "created_at": datetime.utcnow()
        }
        return await self.create(transaction_dict)

    async def get_user_transactions(self, user_id: ObjectId) -> List[TransactionModel]:
        transactions = await self.find_many({"user_id": user_id})
        return [TransactionModel(**t) for t in transactions]

    async def create_pix_transactions(
        self,
        from_id: ObjectId,
        to_id: ObjectId,
        amount: float
    ) -> tuple[ObjectId, ObjectId]:
        async with await self.collection.database.client.start_session() as session:
            async with session.start_transaction():
                sent_id = await self.create_transaction(from_id, "pix_sent", amount)
                received_id = await self.create_transaction(to_id, "pix_received", amount)
                return sent_id, received_id
