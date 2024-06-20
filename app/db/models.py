# coding: utf-8
from sqlalchemy import CHAR, Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()
metadata = Base.metadata


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(Text, unique=True)
    password = Column(CHAR(255))
    created_at = Column(DateTime, server_default=func.now())

    post = relationship("Post", lazy="selectin")


class Post(Base):
    __tablename__ = "post"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"))
    created_at = Column(DateTime, server_default=func.now())
    text = Column(Text)
