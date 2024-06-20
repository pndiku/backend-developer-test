from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.db.models import User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def create(self, db: Session, obj_in: UserCreate) -> User:
        if obj_in.password:
            obj_in.password = get_password_hash(obj_in.password.get_secret_value())

        _user = super().create(db, obj_in=obj_in)

        return _user

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        r = db.query(User).filter(User.email.ilike(email))

        return r.first()


user = CRUDUser(User)
