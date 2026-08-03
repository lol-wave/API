from fastapi import HTTPException, Depends
import os
from . import models
from pwdlib import PasswordHash
from datetime import datetime, timedelta,timezone
from jose import jwt
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

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = jwt.decode(...)
    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(...)

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if user is None:
        raise HTTPException(...)

    return user