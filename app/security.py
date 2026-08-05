from fastapi import HTTPException, Depends
import os
from . import models
from pwdlib import PasswordHash
from datetime import datetime, timedelta,timezone
from jose import jwt, JWTError
ph = PasswordHash.recommended()
from dotenv import load_dotenv
from .database import get_db
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session



load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

if SECRET_KEY is None:
    raise RuntimeError("SECRET_KEY is missing.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30

def create_token(data:dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)



def create_access_token(data: dict):
    data = data.copy()
    data["type"] = "access"
    expire = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_token(data, expire)

def create_refresh_token(data: dict):
    data = data.copy()
    data["type"] = "refresh"
    expire = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return create_token(data, expire)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(status_code=401,
    detail="Invalid authentication credentials.")

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if user is None:
        raise HTTPException(status_code=401,
    detail="Invalid authentication credentials.")

    return user


def get_current_refresh_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401,
    detail="Invalid authentication credentials.")

    user_id = payload.get("sub")
    token_type = payload.get("type")

    if user_id is None or token_type != "refresh":
        raise HTTPException(status_code=401,
    detail="Invalid authentication credentials.")

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if user is None:
        raise HTTPException(status_code=401,
    detail="Invalid authentication credentials.")

    return user

def check_teacher_secret_code(secret_code: str):
    expected_code = os.getenv("TEACHER_SECRET_CODE")
    if expected_code is None:
        raise RuntimeError("TEACHER_SECRET_CODE is missing.")
    if secret_code != expected_code:
        raise HTTPException(status_code=403, detail="Invalid teacher secret code.")

