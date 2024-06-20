import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.core.logger import log
from app.core.security import verify_password

router = APIRouter()


@router.post("/login", response_model=schemas.UserJWTResponse)
async def login_user(
    obj_in: schemas.UserBase,
    db: Session = Depends(deps.get_db),
    Authorize: AuthJWT = Depends(),
) -> Any:
    """
    User login
    """
    user = crud.user.get_by_email(db, obj_in.email)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    log.debug(f"{obj_in.password.get_secret_value()}, {user.password}")
    if not verify_password(
        plain_password=obj_in.password.get_secret_value(),
        hashed_password=user.password,
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=24)

    access_token = Authorize.create_access_token(
        subject=user.id,
        expires_time=datetime.timedelta(hours=24),
        fresh=True,
    )

    return {
        "success": True,
        "data": {
            "access_token": access_token,
            "expires_at": expires_at,
        },
    }


@router.post("/", response_model=schemas.UserResponse)
async def signup_user(
    user_in: schemas.UserCreate,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Create new user.
    """
    existing_user = crud.user.get_by_email(db, user_in.email)

    if existing_user:
        raise HTTPException(status_code=400, detail="A user already exists in the system with this email address")

    user = crud.user.create(db, obj_in=user_in)

    return {"success": True, "data": user}
