from fastapi import Depends, FastAPI, HTTPException
from . import schemas
from .database import Base, engine, get_db
from . import models
from sqlalchemy.orm import Session
from .security import ph, create_access_token, get_current_user
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

@app.post("/login", response_model=schemas.Token)
async def login_user(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter((models.User.username == user.login) | (models.User.email == user.login)).first()
    
    if not db_user or not ph.verify(user.password, db_user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password."
        )
    access_token = create_access_token({"sub": str(db_user.id)})

    
    return {"access_token": access_token, "token_type": "bearer"}



@app.get("/me", response_model=schemas.UserResponse)
async def me(current_user: models.User = Depends(get_current_user)):
    return current_user