# routers/media.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import cast, String
import numpy as np

from database import get_session
from models import Media, User, Event
from auth import verify_token
from cloud import upload_to_s3, generate_secure_url, get_file_bytes_from_s3
from utils import apply_watermark
from ai import extract_all_faces, get_image_tags

router = APIRouter(tags=["Media"])
optional_security = HTTPBearer(auto_error=False)


@router.post("/api/upload")
async def upload_media(
    event_id: int = Form(...),
    is_private: bool = Form(False),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: dict = Depends(verify_token)
):
    if current_user["role"] == "Viewer":
        raise HTTPException(status_code=403, detail="Viewers cannot upload.")

    file_bytes = await file.read()
    cloud_url = upload_to_s3(file_bytes, file.filename, file.content_type)

    tags_list = get_image_tags(file_bytes)
    tags_str = ",".join(tags_list) if tags_list else None

    encoding_arrays = extract_all_faces(file_bytes)
    face_encoding_str = None
    if encoding_arrays:
        stringified = [",".join(str(x) for x in face) for face in encoding_arrays]
        face_encoding_str = "|".join(stringified)

    new_media = Media(
        event_id=event_id,
        uploader_username=current_user["username"],
        file_url=cloud_url,
        is_private=is_private,
        face_encoding=face_encoding_str,
        tags=tags_str
    )
    session.add(new_media)
    session.commit()
    session.refresh(new_media)
    return {"message": "Uploaded!", "media": new_media}


@router.get("/api/media/view/{filename}")
def view_media(
    filename: str,
    session: Session = Depends(get_session),
    credentials: HTTPAuthorizationCredentials = Depends(optional_security)
):
    media = session.exec(select(Media).where(Media.file_url.contains(filename))).first()
    if not media:
        raise HTTPException(status_code=404, detail="File not found")

    if media.is_private:
        if not credentials:
            raise HTTPException(status_code=401, detail="This media is private. Please log in.")
        try:
            current_user = verify_token(credentials)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")
        if current_user["role"] == "Viewer":
            raise HTTPException(status_code=403, detail="Viewers can't access private media.")

    return RedirectResponse(generate_secure_url(filename))


@router.get("/api/media/download/{filename}")
def download_watermarked_media(
    filename: str,
    session: Session = Depends(get_session),
    current_user: dict = Depends(verify_token)
):
    media = session.exec(select(Media).where(Media.file_url.contains(filename))).first()
    if not media:
        raise HTTPException(status_code=404, detail="File not found")

    if media.is_private and current_user["role"] == "Viewer":
        raise HTTPException(status_code=403, detail="Viewers can't download private media.")

    event = session.get(Event, media.event_id)
    event_name = event.name if event else "Unknown Event"

    try:
        raw_bytes = get_file_bytes_from_s3(filename)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found in cloud storage")

    watermark_text = f"CIG | {event_name} | {current_user['username']} ({current_user['role']})"
    watermarked = apply_watermark(raw_bytes, watermark_text)

    return Response(
        content=watermarked,
        media_type="image/jpeg",
        headers={"Content-Disposition": f"attachment; filename=watermarked_{filename}"}
    )


@router.get("/api/media")
def search_media(
    event_id: int | None = None,
    event_name: str | None = None,
    tag: str | None = None,
    uploader: str | None = None,
    date: str | None = None,
    session: Session = Depends(get_session)
):
    query = select(Media).where(Media.is_private == False)

    if event_id:
        query = query.where(Media.event_id == event_id)
    if event_name:
        matching_events = session.exec(
            select(Event.id).where(Event.name.contains(event_name))
        ).all()
        query = query.where(Media.event_id.in_(matching_events))
    if uploader:
        query = query.where(Media.uploader_username == uploader)
    if tag:
        query = query.where(Media.tags.contains(tag.lower()))
    if date:
        query = query.where(cast(Media.uploaded_at, String).contains(date))

    return session.exec(query).all()


@router.get("/api/media/my-photos")
def find_my_photos(
    session: Session = Depends(get_session),
    current_user_dict: dict = Depends(verify_token)
):
    user = session.exec(
        select(User).where(User.username == current_user_dict["username"])
    ).first()

    if not user or not user.reference_face_encoding:
        raise HTTPException(
            status_code=400,
            detail="Upload a selfie first via /api/users/selfie"
        )

    user_encoding = np.array([float(x) for x in user.reference_face_encoding.split(",")])
    all_media = session.exec(select(Media).where(Media.face_encoding != None)).all()

    matched = []
    tolerance = 0.65  # lower this if getting too many false positives

    for media in all_media:
        for face_str in media.face_encoding.split("|"):
            media_encoding = np.array([float(x) for x in face_str.split(",")])
            distance = np.linalg.norm(user_encoding - media_encoding)
            if distance <= tolerance:
                matched.append(media)
                break

    return {
        "message": f"Found {len(matched)} photos with you in them",
        "matches": matched
    }