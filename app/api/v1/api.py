from fastapi import APIRouter

from app.api.v1.endpoints import post, users

api_router = APIRouter()
api_router.include_router(users.router, prefix="/user", tags=["user"])
api_router.include_router(post.router, prefix="/post", tags=["posts"])
