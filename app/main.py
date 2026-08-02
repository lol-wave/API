from fastapi import Depends, FastAPI, HTTPException
from . import schemas
from .database import Base, engine, get_db
from . import models
from sqlalchemy.orm import Session
from .security import ph


Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
async def default_route():
    return {"message": "Hello, World!"}

@app.post("/register", response_model=schemas.UserResponse, status_code=201)
async def register_user(user: schemas.UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.email == user.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
    status_code=409,
    detail="Username or email already exists."
)

    new_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=ph.hash(user.password)
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user 