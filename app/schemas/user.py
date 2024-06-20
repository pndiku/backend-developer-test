import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, SecretStr


class UserJWTModel(BaseModel):
    access_token: str = Field(
        ..., description="The Bearer Token for accessing resources", examples=["eyj0exaioijkv1qilcjhbgcioijiuzi..."]
    )
    expires_at: datetime.datetime = Field(
        ..., description="The timestamp (in UTC) for when the token will expire", examples=["2021-10-30T15:00:00Z"]
    )


class UserJWTResponse(BaseModel):
    success: bool
    data: UserJWTModel


# Shared properties
class UserBase(BaseModel):
    email: EmailStr = Field(..., description="Mandatory. The email address of the user", examples=["john@example.com"])
    password: SecretStr = Field(..., description="Mandatory. The user's password", examples=["password"])


# Properties to receive via API on creation
class UserCreate(UserBase):
    pass


class UserUpdate(UserBase):
    pass


class UserInDBBase(UserBase):
    id: int = Field(..., description="The unique ID of the user in the database", examples=[1])
    created_at: datetime.datetime = Field(
        ..., description="The timestamp for when the user was created", examples=["2024-06-20T19:00:12"]
    )

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
