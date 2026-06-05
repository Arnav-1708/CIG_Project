# routers/social.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone

from database import get_session
from models import Media, User, Like, Comment, Favourite, Share, Tag
from auth import verify_token

router = APIRouter(tags=["Social"])


class CommentCreate(BaseModel):
    text: str


@router.post("/api/media/{media_id}/like")
def toggle_like(media_id: int, session: Session = Depends(get_session), current_user: dict = Depends(verify_token)):
    if not session.get(Media, media_id):
        raise HTTPException(status_code=404, detail="Media not found")

    existing = session.exec(
        select(Like).where(Like.media_id == media_id, Like.username == current_user["username"])
    ).first()

    if existing:
        session.delete(existing)
        session.commit()
        return {"message": "Like removed", "liked": False}

    session.add(Like(media_id=media_id, username=current_user["username"]))
    session.commit()
    return {"message": "Liked!", "liked": True}


@router.post("/api/media/{media_id}/comment")
def add_comment(media_id: int, comment: CommentCreate, session: Session = Depends(get_session), current_user: dict = Depends(verify_token)):
    if not session.get(Media, media_id):
        raise HTTPException(status_code=404, detail="Media not found")

    new_comment = Comment(
        media_id=media_id,
        username=current_user["username"],
        text=comment.text
    )
    session.add(new_comment)
    session.commit()
    session.refresh(new_comment)
    return {"message": "Comment added", "comment": new_comment}


@router.get("/api/media/{media_id}/comments")
def get_comments(media_id: int, session: Session = Depends(get_session)):
    comments = session.exec(
        select(Comment).where(Comment.media_id == media_id).order_by(Comment.created_at.desc())
    ).all()
    return {"comments": comments}


@router.get("/api/notifications")
def get_notifications(
    since_minutes: int = 60,
    session: Session = Depends(get_session),
    current_user: dict = Depends(verify_token)
):
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=since_minutes)

    my_media = session.exec(
        select(Media.id).where(Media.uploader_username == current_user["username"])
    ).all()

    recent_likes = session.exec(
        select(Like)
        .where(Like.media_id.in_(my_media))
        .where(Like.username != current_user["username"])
        .where(Like.liked_at >= cutoff)
    ).all() if my_media else []

    recent_comments = session.exec(
        select(Comment)
        .where(Comment.media_id.in_(my_media))
        .where(Comment.username != current_user["username"])
        .where(Comment.created_at >= cutoff)
        .order_by(Comment.created_at.desc())
    ).all() if my_media else []

    # tags are user-specific, not tied to media ownership
    recent_tags = session.exec(
        select(Tag)
        .where(Tag.tagged_username == current_user["username"])
        .where(Tag.tagged_at >= cutoff)
    ).all()

    return {
        "likes": recent_likes,
        "comments": recent_comments,
        "tags": recent_tags
    }


@router.post("/api/media/{media_id}/favourite")
def toggle_favourite(media_id: int, session: Session = Depends(get_session), current_user: dict = Depends(verify_token)):
    if not session.get(Media, media_id):
        raise HTTPException(status_code=404, detail="Media not found")

    existing = session.exec(
        select(Favourite).where(Favourite.media_id == media_id, Favourite.username == current_user["username"])
    ).first()

    if existing:
        session.delete(existing)
        session.commit()
        return {"message": "Removed from favourites", "favourited": False}

    session.add(Favourite(media_id=media_id, username=current_user["username"]))
    session.commit()
    return {"message": "Added to favourites", "favourited": True}


@router.get("/api/users/me/favourites")
def get_my_favourites(session: Session = Depends(get_session), current_user: dict = Depends(verify_token)):
    fav_ids = session.exec(
        select(Favourite.media_id).where(Favourite.username == current_user["username"])
    ).all()

    if not fav_ids:
        return {"favourites": []}

    return {"favourites": session.exec(select(Media).where(Media.id.in_(fav_ids))).all()}


@router.post("/api/media/{media_id}/share")
def share_media(media_id: int, session: Session = Depends(get_session), current_user: dict = Depends(verify_token)):
    media = session.get(Media, media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    session.add(Share(media_id=media_id, shared_by=current_user["username"]))
    session.commit()
    return {"message": "Shared!", "media_url": media.file_url}


@router.post("/api/media/{media_id}/tag")
def tag_user(
    media_id: int,
    username: str,
    session: Session = Depends(get_session),
    current_user: dict = Depends(verify_token)
):
    if not session.get(Media, media_id):
        raise HTTPException(status_code=404, detail="Media not found")

    # make sure the person being tagged actually has an account
    tagged_user = session.exec(select(User).where(User.username == username)).first()
    if not tagged_user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = session.exec(
        select(Tag).where(Tag.media_id == media_id, Tag.tagged_username == username)
    ).first()
    if existing:
        return {"message": "User already tagged in this photo"}

    session.add(Tag(media_id=media_id, tagged_username=username, tagged_by=current_user["username"]))
    session.commit()
    return {"message": f"{username} tagged successfully"}


@router.get("/api/users/me/tags")
def get_my_tags(session: Session = Depends(get_session), current_user: dict = Depends(verify_token)):
    tags = session.exec(
        select(Tag).where(Tag.tagged_username == current_user["username"])
    ).all()

    if not tags:
        return {"message": "You haven't been tagged in any photos yet", "tagged_media": []}

    media_ids = [t.media_id for t in tags]
    tagged_media = session.exec(select(Media).where(Media.id.in_(media_ids))).all()

    return {"tagged_media": tagged_media}