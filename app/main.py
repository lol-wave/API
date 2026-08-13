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
from datetime import datetime

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

@app.get("/group/{item_id}", response_model=schemas.GroupDetailResponse)
async def get_single_group(item_id: int, current_user: models.User = Depends(get_current_user), db : Session = Depends(get_db)):
    select_group = db.query(models.Groups).filter(models.Groups.id == item_id).first()
    if not select_group:
        raise HTTPException(
            status_code=404,
            detail="Group not found."
        )
    return select_group

# ============ Group Management Endpoints ============

@app.post("/group/{group_id}/members", response_model=schemas.UserMemberResponse, status_code=201)
async def add_user_to_group(
    group_id: int,
    request: schemas.AddUserToGroupRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Add a user to a group (teacher/admin only)"""
    if not current_user.teacher:
        raise HTTPException(
            status_code=403,
            detail="Only teachers can add users to groups."
        )
    
    group = db.query(models.Groups).filter(models.Groups.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=404,
            detail="Group not found."
        )
    
    user = db.query(models.User).filter(models.User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )
    
    if user.group_id == group_id:
        raise HTTPException(
            status_code=409,
            detail="User is already in this group."
        )
    
    user.group_id = group_id
    db.commit()
    db.refresh(user)
    
    return user

@app.delete("/group/{group_id}/members/{user_id}", status_code=204)
async def remove_user_from_group(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Remove a user from a group (teacher/admin only)"""
    if not current_user.teacher:
        raise HTTPException(
            status_code=403,
            detail="Only teachers can remove users from groups."
        )
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )
    
    if user.group_id != group_id:
        raise HTTPException(
            status_code=404,
            detail="User is not in this group."
        )
    
    user.group_id = None
    user.is_group_admin = False
    db.commit()

@app.get("/group/{group_id}/members", response_model=list[schemas.UserMemberResponse])
async def get_group_members(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all members of a group"""
    group = db.query(models.Groups).filter(models.Groups.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=404,
            detail="Group not found."
        )
    
    members = db.query(models.User).filter(models.User.group_id == group_id).all()
    return members

@app.get("/me/group", response_model=schemas.GroupDetailResponse)
async def get_current_user_group(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get current user's group"""
    if not current_user.group_id:
        raise HTTPException(
            status_code=404,
            detail="User is not in any group."
        )
    
    group = db.query(models.Groups).filter(models.Groups.id == current_user.group_id).first()
    if not group:
        raise HTTPException(
            status_code=404,
            detail="Group not found."
        )
    
    return group

@app.patch("/group/{group_id}", response_model=schemas.GroupResponse)
async def update_group(
    group_id: int,
    update: schemas.GroupUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update group details (teacher/admin only)"""
    if not current_user.teacher:
        raise HTTPException(
            status_code=403,
            detail="Only teachers can update groups."
        )
    
    group = db.query(models.Groups).filter(models.Groups.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=404,
            detail="Group not found."
        )
    
    if update.name is not None:
        existing_group = db.query(models.Groups).filter(
            models.Groups.name == update.name,
            models.Groups.id != group_id
        ).first()
        if existing_group:
            raise HTTPException(
                status_code=409,
                detail="Group name already exists."
            )
        group.name = update.name
    
    if update.description is not None:
        group.description = update.description
    
    db.commit()
    db.refresh(group)
    return group

@app.delete("/group/{group_id}", status_code=204)
async def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a group (teacher only)"""
    if not current_user.teacher:
        raise HTTPException(
            status_code=403,
            detail="Only teachers can delete groups."
        )
    
    group = db.query(models.Groups).filter(models.Groups.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=404,
            detail="Group not found."
        )
    
    db.delete(group)
    db.commit()

@app.post("/group/{group_id}/members/{user_id}/admin", response_model=schemas.UserMemberResponse)
async def promote_user_to_group_admin(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Promote a user to group admin (teacher only)"""
    if not current_user.teacher:
        raise HTTPException(
            status_code=403,
            detail="Only teachers can promote users to admin."
        )
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )
    
    if user.group_id != group_id:
        raise HTTPException(
            status_code=404,
            detail="User is not in this group."
        )
    
    if user.is_group_admin:
        raise HTTPException(
            status_code=409,
            detail="User is already a group admin."
        )
    
    user.is_group_admin = True
    db.commit()
    db.refresh(user)
    
    return user

@app.delete("/group/{group_id}/members/{user_id}/admin", response_model=schemas.UserMemberResponse)
async def demote_group_admin(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Demote a group admin back to regular member (teacher only)"""
    if not current_user.teacher:
        raise HTTPException(
            status_code=403,
            detail="Only teachers can demote admins."
        )
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )
    
    if user.group_id != group_id:
        raise HTTPException(
            status_code=404,
            detail="User is not in this group."
        )
    
    if not user.is_group_admin:
        raise HTTPException(
            status_code=409,
            detail="User is not a group admin."
        )
    
    user.is_group_admin = False
    db.commit()
    db.refresh(user)
    
    return user

# ============ Notification System Endpoints ============

@app.post("/notifications", response_model=schemas.NotificationResponse, status_code=201)
async def create_notification(
    notification: schemas.NotificationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new notification (teacher/admin only)"""
    if not current_user.teacher:
        raise HTTPException(
            status_code=403,
            detail="Only teachers can create notifications."
        )
    
    new_notification = models.Notification(
        title=notification.title,
        description=notification.description,
        notification_type=notification.notification_type,
        icon_url=notification.icon_url
    )
    
    db.add(new_notification)
    db.flush()
    
    # Add users to notification
    if notification.user_ids:
        users = db.query(models.User).filter(models.User.id.in_(notification.user_ids)).all()
        new_notification.users.extend(users)
    
    db.commit()
    db.refresh(new_notification)
    
    return new_notification

@app.post("/notifications/bulk", response_model=schemas.NotificationResponse, status_code=201)
async def create_bulk_notification(
    notification: schemas.BulkNotificationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create notification for all users in a group or all users"""
    if not current_user.teacher:
        raise HTTPException(
            status_code=403,
            detail="Only teachers can create notifications."
        )
    
    new_notification = models.Notification(
        title=notification.title,
        description=notification.description,
        notification_type=notification.notification_type,
        icon_url=notification.icon_url
    )
    
    db.add(new_notification)
    db.flush()
    
    if notification.group_id:
        # Add all users in the group
        group_users = db.query(models.User).filter(models.User.group_id == notification.group_id).all()
        if not group_users:
            raise HTTPException(
                status_code=404,
                detail="Group not found or has no members."
            )
        new_notification.users.extend(group_users)
    else:
        # Add all users
        all_users = db.query(models.User).all()
        new_notification.users.extend(all_users)
    
    db.commit()
    db.refresh(new_notification)
    
    return new_notification

@app.get("/notifications", response_model=list[schemas.UserNotificationResponse])
async def get_user_notifications(
    skip: int = 0,
    limit: int = 50,
    is_read: bool | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get notifications for current user with optional filtering"""
    query = db.query(
        models.Notification,
        models.user_notifications.c.is_read,
        models.user_notifications.c.read_at
    ).join(
        models.user_notifications,
        models.Notification.id == models.user_notifications.c.notification_id
    ).filter(
        models.user_notifications.c.user_id == current_user.id
    )
    
    if is_read is not None:
        query = query.filter(models.user_notifications.c.is_read == is_read)
    
    notifications = query.order_by(models.Notification.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for notification, is_read_value, read_at in notifications:
        notification_dict = {
            'id': notification.id,
            'title': notification.title,
            'description': notification.description,
            'notification_type': notification.notification_type,
            'icon_url': notification.icon_url,
            'is_read': is_read_value,
            'read_at': read_at,
            'created_at': notification.created_at
        }
        result.append(notification_dict)
    
    return result

@app.get("/notifications/unread-count", response_model=dict)
async def get_unread_notification_count(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get count of unread notifications for current user"""
    unread_count = db.query(models.user_notifications).filter(
        models.user_notifications.c.user_id == current_user.id,
        models.user_notifications.c.is_read == False
    ).count()
    
    return {"unread_count": unread_count}

@app.patch("/notifications/{notification_id}", response_model=schemas.UserNotificationResponse)
async def mark_notification_as_read(
    notification_id: int,
    update: schemas.NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Mark a notification as read or unread for current user"""
    notification = db.query(models.Notification).filter(models.Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found."
        )
    
    # Check if user has this notification
    user_notif = db.query(models.user_notifications).filter(
        models.user_notifications.c.user_id == current_user.id,
        models.user_notifications.c.notification_id == notification_id
    ).first()
    
    if not user_notif:
        raise HTTPException(
            status_code=404,
            detail="User does not have access to this notification."
        )
    
    if update.is_read is not None:
        db.query(models.user_notifications).filter(
            models.user_notifications.c.user_id == current_user.id,
            models.user_notifications.c.notification_id == notification_id
        ).update({
            models.user_notifications.c.is_read: update.is_read,
            models.user_notifications.c.read_at: datetime.utcnow() if update.is_read else None
        })
    
    db.commit()
    
    # Fetch updated notification
    updated_notif = db.query(
        models.Notification,
        models.user_notifications.c.is_read,
        models.user_notifications.c.read_at
    ).join(
        models.user_notifications,
        models.Notification.id == models.user_notifications.c.notification_id
    ).filter(
        models.user_notifications.c.user_id == current_user.id,
        models.Notification.id == notification_id
    ).first()
    
    notification, is_read_value, read_at = updated_notif
    
    return {
        'id': notification.id,
        'title': notification.title,
        'description': notification.description,
        'notification_type': notification.notification_type,
        'icon_url': notification.icon_url,
        'is_read': is_read_value,
        'read_at': read_at,
        'created_at': notification.created_at
    }

@app.delete("/notifications/{notification_id}", status_code=204)
async def delete_notification_for_user(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Remove a notification from current user's list"""
    notification = db.query(models.Notification).filter(models.Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found."
        )
    
    # Remove user from notification's users
    user_notif = db.query(models.user_notifications).filter(
        models.user_notifications.c.user_id == current_user.id,
        models.user_notifications.c.notification_id == notification_id
    ).first()
    
    if not user_notif:
        raise HTTPException(
            status_code=404,
            detail="User does not have this notification."
        )
    
    db.query(models.user_notifications).filter(
        models.user_notifications.c.user_id == current_user.id,
        models.user_notifications.c.notification_id == notification_id
    ).delete()
    
    db.commit()

@app.delete("/notifications", status_code=204)
async def clear_all_notifications(
    is_read: bool | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Clear all notifications for current user (optionally by read status)"""
    query = db.query(models.user_notifications).filter(
        models.user_notifications.c.user_id == current_user.id
    )
    
    if is_read is not None:
        query = query.filter(models.user_notifications.c.is_read == is_read)
    
    query.delete()
    db.commit()

