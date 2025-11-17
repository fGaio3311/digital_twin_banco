from datetime import datetime
from bson import ObjectId
from app.repositories.base import BaseRepository
from app.models_mongo import LogModel

class LogRepository(BaseRepository[LogModel]):
    async def create_log(self, user_id: ObjectId, action: str) -> ObjectId:
        log_dict = {
            "user_id": user_id,
            "action": action,
            "timestamp": datetime.utcnow()
        }
        return await self.create(log_dict)

    async def get_user_logs(self, user_id: ObjectId, limit: int = 50):
        return await self.find_many(
            {"user_id": user_id},
            {"$sort": {"timestamp": -1}, "$limit": limit}
        )
