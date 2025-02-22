import os
from datetime import datetime, timedelta
from typing import Union
from jose import jwt, JWTError
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    
    to_encode.update({"exp": expire})
    
    if not SECRET_KEY or SECRET_KEY == "fallback_secret_key":
        raise ValueError("JWT_SECRET_KEY is not set in the environment variables!")

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
