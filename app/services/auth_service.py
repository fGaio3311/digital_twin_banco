import hashlib
from datetime import datetime, timedelta
from typing import Optional
import jwt
from jose import JWTError
from app.settings import Settings

settings = Settings()

def get_password_hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def verify_password(plain: str, hashed: str) -> bool:
    return get_password_hash(plain) == hashed

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
