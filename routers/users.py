# routers/users.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select

from database import get_session
from models import User, UserCreate
from auth import get_password_hash, verify_password, create_access_token, verify_token
from ai import extract_face_encoding

router = APIRouter(tags=["Users"])

ALLOWED_ROLES = {"Admin", "Photographer", "Club Member", "Viewer"}
SELF_ASSIGNABLE_ROLES = {"Photographer", "Club Member", "Viewer"}


@router.post("/api/register")
def register_user(user_data: UserCreate, session: Session = Depends(get_session)):
    if user_data.role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail=f"Role must be one of {ALLOWED_ROLES}")

    # first user to register becomes admin, no one else can self-assign it
    is_first_user = session.exec(select(User)).first() is None
    if not is_first_user and user_data.role not in SELF_ASSIGNABLE_ROLES:
        raise HTTPException(status_code=400, detail="Only the initial user can be Admin.")

    existing = session.exec(select(User).where(User.username == user_data.username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    new_user = User(
        username=user_data.username,
        password=get_password_hash(user_data.password),
        role=user_data.role
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return {"message": f"User {new_user.username} registered with role: {new_user.role}"}


@router.post("/api/login")
def login(username: str, password: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Wrong password")

    token = create_access_token({"username": user.username, "role": user.role})
    return {"access_token": token, "token_type": "bearer", "role": user.role}


@router.post("/api/users/selfie")
async def upload_reference_selfie(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user_dict: dict = Depends(verify_token)
):
    user = session.exec(
        select(User).where(User.username == current_user_dict["username"])
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    file_bytes = await file.read()
    encoding_array = extract_face_encoding(file_bytes)

    if encoding_array is None:
        raise HTTPException(
            status_code=400,
            detail="No face detected. Try a clearer photo with better lighting."
        )

    user.reference_face_encoding = ",".join(str(x) for x in encoding_array)
    session.add(user)
    session.commit()
    session.refresh(user)

    return {"message": "Selfie saved!", "username": user.username}