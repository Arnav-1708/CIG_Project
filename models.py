# models.py
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


# these two are just for cleaner swagger UI, not actual db tables
class UserCreate(SQLModel):
    username: str
    password: str
    role: str

class EventCreate(SQLModel):
    name: str
    category: str
    date: str
    description: str


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password: str
    role: str
    reference_face_encoding: str | None = Field(default=None)


class Event(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    category: str
    date: str
    description: str


class Media(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    uploader_username: str
    file_url: str
    is_private: bool = False
    # face encodings stored as comma-separated floats, multiple faces separated by |
    face_encoding: str | None = Field(default=None)
    tags: str | None = Field(default=None)
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Like(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    media_id: int = Field(foreign_key="media.id")
    username: str = Field(index=True)
    liked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Comment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    media_id: int = Field(foreign_key="media.id")
    username: str
    text: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Favourite(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    media_id: int = Field(foreign_key="media.id")
    username: str = Field(index=True)

class Share(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    media_id: int = Field(foreign_key="media.id")
    shared_by: str
    shared_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))