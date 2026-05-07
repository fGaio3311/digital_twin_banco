import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pymongo import MongoClient
from app.settings import Settings
from app.models.models import User, Transaction, Log, Base
from datetime import datetime
from bson import ObjectId

settings = Settings()

# SQLite connection
sqlite_engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=sqlite_engine)
db = SessionLocal()

# MongoDB connection
mongo_client = MongoClient(settings.mongodb_url)
mongo_db = mongo_client[settings.mongodb_name]

def migrate_users():
    print("Migrando usuários...")
    users = db.query(User).all()
    users_collection = mongo_db.users

    for user in users:
        mongo_user = {
            "_id": ObjectId(),
            "username": user.username,
            "hashed_password": user.hashed_password,
            "balance": user.balance,
            "created_at": datetime.utcnow()
        }
        result = users_collection.insert_one(mongo_user)
        print(f"Usuário {user.username} migrado. MongoDB ID: {result.inserted_id}")

def migrate_transactions():
    print("Migrando transações...")
    transactions = db.query(Transaction).all()
    transactions_collection = mongo_db.transactions
    users_collection = mongo_db.users

    for transaction in transactions:
        # Get user in MongoDB
        user = users_collection.find_one({"username": db.query(User).get(transaction.user_id).username})
        if user:
            mongo_transaction = {
                "_id": ObjectId(),
                "user_id": user["_id"],
                "type": transaction.type,
                "amount": transaction.amount,
                "created_at": transaction.timestamp if hasattr(transaction, 'timestamp') else datetime.utcnow()
            }
            transactions_collection.insert_one(mongo_transaction)

def migrate_logs():
    print("Migrando logs...")
    logs = db.query(Log).all()
    logs_collection = mongo_db.logs
    users_collection = mongo_db.users

    for log in logs:
        # Get user in MongoDB
        user = users_collection.find_one({"username": db.query(User).get(log.user_id).username})
        if user:
            mongo_log = {
                "_id": ObjectId(),
                "user_id": user["_id"],
                "action": log.action,
                "timestamp": log.timestamp
            }
            logs_collection.insert_one(mongo_log)

def main():
    print("Iniciando migração para MongoDB...")
    try:
        migrate_users()
        migrate_transactions()
        migrate_logs()
        print("Migração concluída com sucesso!")
    except Exception as e:
        print(f"Erro durante a migração: {e}")
    finally:
        mongo_client.close()
        db.close()

if __name__ == "__main__":
    main()
