from pydantic import BaseModel, Field, EmailStr, ConfigDict
from datetime import datetime

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

class ObjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=255)
    deadline: datetime | None = Field(None)
    group_id: int

class GroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None

class ObjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    deadline: datetime | None
    group_id: int
    group: GroupResponse | None = None
    submitted: bool 
    created_at: datetime

class GroupCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: str | None = Field(None, max_length=255)

class GroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
