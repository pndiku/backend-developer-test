import datetime
from typing import List, Optional

from pydantic import BaseModel


# Shared properties
class PostBase(BaseModel):
    text: str


# Properties to receive via API on creation
class PostCreate(PostBase):
    pass


class PostUpdate(PostBase):
    pass


class PostInDBBase(PostBase):
    id: int
    user_id: int
    created_at: datetime.datetime

    class Config:
        orm_mode = True


# Additional properties to return via API
class Post(PostInDBBase):
    pass


class PostResponse(BaseModel):
    success: bool
    data: Optional[Post]


class PostListResponse(BaseModel):
    success: bool
    data: Optional[List[Post]]
