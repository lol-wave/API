from pydantic import BaseModel, Field, EmailStr, ConfigDict, HttpUrl
from datetime import datetime

# ============ User Schemas ============
class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

class TeacherRegister(BaseModel):
    full_name: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    teacher_secret_code: str | None = Field(None, min_length=6, max_length=6)

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    created_at: datetime
    teacher: bool
    group_id: int | None
    is_group_admin: bool
    profile_pic: str | None = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    access_token: str
    token_type: str

class AccessToken(BaseModel):
    access_token: str
    token_type: str

class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=3, max_length=50)
    email: EmailStr | None = None

class UserPasswordUpdate(BaseModel):
    current_password: str = Field(..., min_length=8, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)

class UserMemberResponse(BaseModel):
    """Lightweight user response for group member lists"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    full_name: str
    email: EmailStr
    profile_pic: str | None = None
    is_group_admin: bool
    created_at: datetime

# ============ Object Schemas ============
class ObjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=255)
    deadline: datetime | None = Field(None)
    group_id: int

class ObjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    deadline: datetime | None
    group_id: int
    submitted: bool 
    homework_url: HttpUrl | None
    created_at: datetime
    updated_at: datetime

class ObjectSubmission(BaseModel):
    url: HttpUrl

class HomeworkSubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    object_id: int
    student_id: int
    url: HttpUrl
    grade: int | None
    feedback: str | None
    submitted_at: datetime
    graded_at: datetime | None

class MyHomeworkResponse(HomeworkSubmissionResponse):
    homework: ObjectResponse

class HomeworkGrade(BaseModel):
    grade: int = Field(..., ge=0, le=100)
    feedback: str | None = Field(None, max_length=2000)

# ============ Group Schemas ============
class GroupCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: str | None = Field(None, max_length=255)

class GroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

class GroupDetailResponse(BaseModel):
    """Detailed group response with members and objects"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: str | None
    members: list[UserMemberResponse] = []
    objects: list[ObjectResponse] = []
    created_at: datetime
    updated_at: datetime

class GroupUpdate(BaseModel):
    name: str | None = Field(None, min_length=3, max_length=100)
    description: str | None = Field(None, max_length=255)

class AddUserToGroupRequest(BaseModel):
    user_id: int

# ============ Notification Schemas ============
class NotificationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None)
    notification_type: str = Field(default="info")  # info, warning, error, success
    icon_url: str | None = None
    user_ids: list[int] = Field(default_factory=list)

class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    description: str | None
    notification_type: str
    icon_url: str | None
    created_at: datetime
    updated_at: datetime

class UserNotificationResponse(BaseModel):
    """Notification response with read status for a specific user"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    description: str | None
    notification_type: str
    icon_url: str | None
    is_read: bool
    read_at: datetime | None
    created_at: datetime

class BulkNotificationCreate(BaseModel):
    """Create notification for all users in a group"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None)
    notification_type: str = Field(default="info")
    icon_url: str | None = None
    group_id: int | None = None  # If None, sends to all users

class NotificationUpdate(BaseModel):
    is_read: bool | None = None
