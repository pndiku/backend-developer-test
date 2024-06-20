import datetime
import json
from typing import Any

import fastapi_plugins
from fastapi import APIRouter, Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from redis import asyncio as aioredis
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps

router = APIRouter()


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "dict"):
            return obj.dict()
        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        else:
            return json.JSONEncoder.default(self, obj)


async def reCachePosts(db: Session, cache: aioredis.Redis, user_id: int):
    posts = crud.post.get_for_user(db, user_id)

    rows = [r.__dict__ for r in posts]

    await cache.set(f"post-{user_id}", json.dumps(rows), ex=300)


@router.post("/", response_model=schemas.PostResponse)
async def create_post(
    post_in: schemas.PostCreate,
    db: Session = Depends(deps.get_db),
    Authorize: AuthJWT = Depends(),
    cache: aioredis.Redis = Depends(fastapi_plugins.depends_redis),
) -> Any:
    """
    Create new post
    """
    Authorize.jwt_required()

    user_id = Authorize.get_jwt_subject()

    r = crud.post.create(db, obj_in={"user_id": user_id, "text": post_in.text})

    # re-cache posts
    await reCachePosts(db, cache, Authorize.get_jwt_subject)

    return {"success": True, "data": r}


@router.delete("/{id}", response_model=schemas.PostResponse)
async def delete_post(
    id: int,
    db: Session = Depends(deps.get_db),
    Authorize: AuthJWT = Depends(),
    cache: aioredis.Redis = Depends(fastapi_plugins.depends_redis),
) -> Any:
    """
    Delete post
    """
    Authorize.jwt_required()

    post = crud.post.get(db, id)

    if not post:
        raise HTTPException(status_code=404, detail="Invalid post specified")

    if post.user_id != Authorize.get_jwt_subject():
        raise HTTPException(status_code=401, detail="You don't have permission to delete this post")

    crud.post.remove(db, id=id)

    # re-cache posts
    await reCachePosts(db, cache, Authorize.get_jwt_subject)

    return {"success": True, "data": None}


@router.get("/", response_model=schemas.PostListResponse)
async def get_posts_for_user(
    db: Session = Depends(deps.get_db),
    Authorize: AuthJWT = Depends(),
    cache: aioredis.Redis = Depends(fastapi_plugins.depends_redis),
) -> Any:
    """
    Get posts for a user
    """
    Authorize.jwt_required()

    user_id = Authorize.get_jwt_subject()

    cachedRows = await cache.get(f"post-{user_id}")
    if cachedRows:
        return {"success": True, "data": json.loads(cachedRows)}

    posts = crud.post.get_for_user(db, user_id=user_id)

    # re-cache posts
    await reCachePosts(db, cache, Authorize.get_jwt_subject)

    return {"success": True, "data": posts}
