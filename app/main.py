from fastapi import Depends, FastAPI, HTTPException, Response, Cookie, UploadFile, File
from . import schemas
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine, get_db
from . import models
from sqlalchemy.orm import Session
from .security import check_teacher_secret_code, create_refresh_token, get_current_refresh_user, ph, create_access_token, get_current_user
import os
import uuid
from fastapi import UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles























Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
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


@app.post("/register-teacher", response_model=schemas.UserResponse, status_code=201)
async def register_teacher(user: schemas.TeacherRegister, db: Session = Depends(get_db)):
    check_teacher_secret_code(user.teacher_secret_code)
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    
    if existing_user:
        raise HTTPException(
    status_code=409,
    detail="Email already registered."
)

    new_user = models.User(
        full_name=user.full_name,
        email=user.email,
        password_hash=ph.hash(user.password),
        teacher=True
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

@app.patch("/users/me", response_model=schemas.UserResponse)
async def update_profile(
    update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if update.full_name is not None:
        current_user.full_name = update.full_name

    if update.email is not None and update.email != current_user.email:
        existing_user = db.query(models.User).filter(models.User.email == update.email).first()
        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="Email already registered."
            )
        current_user.email = update.email

    db.commit()
    db.refresh(current_user)
    return current_user

@app.post("/users/me/password", response_model=schemas.UserResponse)
async def change_password(
    passwords: schemas.UserPasswordUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not ph.verify(passwords.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Current password is incorrect."
        )

    current_user.password_hash = ph.hash(passwords.new_password)
    db.commit()
    db.refresh(current_user)
    return current_user

@app.post("/refresh", response_model=schemas.AccessToken)
async def refresh_token(refresh_token: str = Cookie(None), db: Session = Depends(get_db)):
    current_user = get_current_refresh_user(refresh_token, db)
    access_token = create_access_token({"sub": str(current_user.id)})

    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/add-object", response_model=schemas.ObjectResponse, status_code=201)
async def add_object(object: schemas.ObjectCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    existing_object = db.query(models.Objects).filter(models.Objects.name == object.name).first()
    if not current_user.teacher:
        raise HTTPException(
            status_code=403,
            detail="Only teachers can add objects."
        )
    
    if existing_object:
        raise HTTPException(
            status_code=409,
            detail="Object with this name already exists."
        )

    new_object = models.Objects(
        name=object.name,
        description=object.description,
        deadline=object.deadline,
        group_id=object.group_id
    )
    
    db.add(new_object)
    db.commit()
    db.refresh(new_object)

    return new_object

@app.get("/objects", response_model=list[schemas.ObjectResponse])
async def get_objects(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    objects = db.query(models.Objects).all()
    return objects

@app.post("/users/me/avatar", response_model=schemas.UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/webp"
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only JPEG, PNG, and WebP images are allowed."
        )

    extension = file.filename.split(".")[-1].lower()
    filename = f"{uuid.uuid4()}.{extension}"

    upload_dir = "uploads/avatars"
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    current_user.profile_pic = f"/uploads/avatars/{filename}"

    db.commit()
    db.refresh(current_user)

    return current_user

@app.get("/object/{item_id}", response_model=schemas.ObjectResponse)
async def get_single_object(item_id: int, current_user: models.User = Depends(get_current_user), db : Session = Depends(get_db)):
    select_object= db.query(models.Objects).filter(models.Objects.id == item_id).first()
    return select_object

@app.post("/object/{item_id}/submit", response_model=schemas.ObjectResponse)
async def submit_object(item_id: int, current_user: models.User = Depends(get_current_user), db : Session = Depends(get_db)):
    select_object = db.query(models.Objects).filter(models.Objects.id == item_id).first()
    if select_object.submitted == True:
        raise HTTPException(
            status_code=403,
            detail="The task is already submitted"
        )
    select_object.submitted=True

    db.commit()
    db.refresh(select_object)

    return select_object


@app.post("/create-group", response_model=schemas.GroupResponse, status_code=201)
async def create_group(group: schemas.GroupCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    existing_group = db.query(models.Groups).filter(models.Groups.name == group.name).first()
    if not current_user.teacher:
        raise HTTPException(
            status_code=403,
            detail="Only teachers can create groups."
        )

    if existing_group:
        raise HTTPException(
            status_code=409,
            detail="Group with this name already exists."
        )

    new_group = models.Groups(
        name=group.name,
        description=group.description
    )
    
    db.add(new_group)
    db.commit()
    db.refresh(new_group)

    return new_group

@app.get("/groups", response_model=list[schemas.GroupResponse])
async def get_groups(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    groups = db.query(models.Groups).all()
    return groups

@app.get("/group/{item_id}", response_model=schemas.GroupResponse)
async def get_single_group(item_id: int, current_user: models.User = Depends(get_current_user), db : Session = Depends(get_db)):
    select_group= db.query(models.Groups).filter(models.Groups.id == item_id).first()
    return select_group

