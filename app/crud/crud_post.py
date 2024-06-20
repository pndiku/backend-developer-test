from typing import List, Optional

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.db.models import Post
from app.schemas.post import PostCreate, PostUpdate


class CRUDPost(CRUDBase[Post, PostCreate, PostUpdate]):
    def get_for_user(self, db: Session, user_id: int) -> Optional[List[Post]]:
        r = db.query(Post).filter(Post.user_id == user_id)

        return r.all()


post = CRUDPost(Post)
