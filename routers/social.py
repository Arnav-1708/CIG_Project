# routers/social.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone

from database import get_session
from models import Media, Like, Comment, Favourite, Share
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

    if not my_media:
        return {"likes": [], "comments": []}

    recent_likes = session.exec(
        select(Like)
        .where(Like.media_id.in_(my_media))
        .where(Like.username != current_user["username"])
        .where(Like.liked_at >= cutoff)
    ).all()

    recent_comments = session.exec(
        select(Comment)
        .where(Comment.media_id.in_(my_media))
        .where(Comment.username != current_user["username"])
        .where(Comment.created_at >= cutoff)
        .order_by(Comment.created_at.desc())
    ).all()

    return {"likes": recent_likes, "comments": recent_comments}


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