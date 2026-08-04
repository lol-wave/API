from fastapi import Depends, FastAPI, HTTPException, Response, Cookie
from . import schemas
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine, get_db
from . import models
from sqlalchemy.orm import Session
from .security import create_refresh_token, get_current_refresh_user, ph, create_access_token, get_current_user
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def default_route():
    return {"message": "Hello, World!"}

@app.post("/register", response_model=schemas.UserResponse, status_code=201)
async def register_user(user: schemas.UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    
    if existing_user:
        raise HTTPException(
    status_code=409,
    detail="Email already registered."
)

    new_user = models.User(
        full_name=user.full_name,
        email=user.email,
        password_hash=ph.hash(user.password)
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user 

@app.post("/login", response_model=schemas.Token)
async def login_user(user: schemas.UserLogin, response: Response, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    
    if not db_user or not ph.verify(user.password, db_user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )
    access_token = create_access_token({"sub": str(db_user.id)})
    refresh_token = create_refresh_token({"sub": str(db_user.id)})

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=30 * 24 * 60 * 60
    )

    return {"access_token": access_token, "token_type": "bearer"}



@app.get("/me", response_model=schemas.UserResponse)
async def me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.post("/refresh", response_model=schemas.AccessToken)
async def refresh_token(refresh_token: str = Cookie(None), db: Session = Depends(get_db)):
    current_user = get_current_refresh_user(refresh_token, db)
    access_token = create_access_token({"sub": str(current_user.id)})

    return {"access_token": access_token, "token_type": "bearer"}