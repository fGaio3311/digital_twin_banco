from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class MongoBaseModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class UserModel(MongoBaseModel):
    username: str
    hashed_password: str
    balance: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TransactionModel(MongoBaseModel):
    user_id: PyObjectId
    type: str  # "deposit", "pix", "pix_received"
    amount: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LogModel(MongoBaseModel):
    user_id: PyObjectId
    action: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
