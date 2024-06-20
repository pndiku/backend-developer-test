import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator


# Shared properties
class PostBase(BaseModel):
    text: str = Field(..., description="Mandatory. The text of the post. Must be less than 1MB in size")

    @validator("text")
    def check_text_size(cls, value):
        bytesize = len(value.encode("utf-8"))
        if bytesize > 1024 * 1024 * 1024:
            raise ValueError("Text too large")
        return value


# Properties to receive via API on creation
class PostCreate(PostBase):
    pass


class PostUpdate(PostBase):
    pass


class PostInDBBase(PostBase):
    id: int = Field(..., description="The unique ID of the post in the database", examples=[1])
    created_at: datetime.datetime = Field(
        ..., description="The timestamp for when the post was created", examples=["2024-06-20T19:00:12"]
    )

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
