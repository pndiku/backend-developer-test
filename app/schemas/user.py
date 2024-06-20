import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, SecretStr


class UserJWTModel(BaseModel):
    access_token: str
    expires_at: datetime.datetime


class UserJWTResponse(BaseModel):
    success: bool
    data: UserJWTModel


# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    password: SecretStr


# Properties to receive via API on creation
class UserCreate(UserBase):
    pass


class UserUpdate(UserBase):
    pass


class UserInDBBase(UserBase):
    id: int
    created_at: Optional[datetime.datetime]

    class Config:
        orm_mode = True


# Additional properties to return via API
class User(UserInDBBase):
    pass


class UserResponse(BaseModel):
    success: bool
    data: Optional[User]


class UserListResponse(BaseModel):
    success: bool
    data: Optional[List[User]]
