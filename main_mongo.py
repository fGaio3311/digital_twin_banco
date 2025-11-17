from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
import jwt
from datetime import datetime, timedelta
import hashlib
from typing import Optional
from bson import ObjectId

from app.settings import Settings
from app.database import (
    get_mongodb,
    users_collection,
    transactions_collection,
    logs_collection
)
from app.models_mongo import UserModel, TransactionModel, LogModel

settings = Settings()
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:80",
        "http://localhost",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:80",
        "http://127.0.0.1"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600
)

# Auth
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm

def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception

    user = await users_collection().find_one({"username": username})
    if user is None:
        raise credentials_exception
    return UserModel(**user)

# Routes
@app.post("/register")
async def register(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        raise HTTPException(
            status_code=400,
            detail="Username and password are required"
        )

    if await users_collection().find_one({"username": username}):
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )

    user_dict = {
        "username": username,
        "hashed_password": get_password_hash(password),
        "balance": 0.0,
        "created_at": datetime.utcnow()
    }

    result = await users_collection().insert_one(user_dict)
    return {"message": "User created", "id": str(result.inserted_id)}

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await users_collection().find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user["username"]})

    # Log login
    await logs_collection().insert_one({
        "user_id": user["_id"],
        "action": "login",
        "timestamp": datetime.utcnow()
    })

    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/user/me")
async def get_current_user_info(current_user: UserModel = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "balance": current_user.balance
    }

@app.get("/balance")
async def get_balance(current_user: UserModel = Depends(get_current_user)):
    user = await users_collection().find_one({"_id": current_user.id})
    await logs_collection().insert_one({
        "user_id": current_user.id,
        "action": "balance_check",
        "timestamp": datetime.utcnow()
    })
    return {"balance": user["balance"]}

@app.post("/deposit")
async def deposit(amount: float, current_user: UserModel = Depends(get_current_user)):
    if amount <= 0:
        raise HTTPException(400, "Amount must be positive")

    # Update balance
    result = await users_collection().update_one(
        {"_id": current_user.id},
        {"$inc": {"balance": amount}}
    )

    if result.modified_count == 0:
        raise HTTPException(400, "Failed to update balance")

    # Record transaction
    await transactions_collection().insert_one({
        "user_id": current_user.id,
        "type": "deposit",
        "amount": amount,
        "created_at": datetime.utcnow()
    })

    # Get updated user
    user = await users_collection().find_one({"_id": current_user.id})
    return {"balance": user["balance"]}

@app.post("/pix")
async def pix(to_username: str, amount: float, current_user: UserModel = Depends(get_current_user)):
    if amount <= 0:
        raise HTTPException(400, "Amount must be positive")

    # Get recipient
    recipient = await users_collection().find_one({"username": to_username})
    if not recipient:
        raise HTTPException(404, "Recipient not found")

    # Check balance
    sender = await users_collection().find_one({"_id": current_user.id})
    if sender["balance"] < amount:
        raise HTTPException(400, "Insufficient balance")

    # Update balances
    await users_collection().update_one(
        {"_id": current_user.id},
        {"$inc": {"balance": -amount}}
    )
    await users_collection().update_one(
        {"_id": recipient["_id"]},
        {"$inc": {"balance": amount}}
    )

    # Record transactions
    await transactions_collection().insert_many([
        {
            "user_id": current_user.id,
            "type": "pix_sent",
            "amount": amount,
            "created_at": datetime.utcnow()
        },
        {
            "user_id": recipient["_id"],
            "type": "pix_received",
            "amount": amount,
            "created_at": datetime.utcnow()
        }
    ])

    # Get updated sender
    sender = await users_collection().find_one({"_id": current_user.id})
    return {"balance": sender["balance"]}

@app.get("/transactions")
async def get_transactions(current_user: UserModel = Depends(get_current_user)):
    transactions = []
    async for transaction in transactions_collection().find({"user_id": current_user.id}):
        transactions.append(TransactionModel(**transaction))
    return transactions

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
