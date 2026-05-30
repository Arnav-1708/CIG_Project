# routers/events.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import Event, EventCreate
from auth import verify_token

router = APIRouter(tags=["Events"])


@router.post("/api/events")
def create_event(
    event_data: EventCreate,
    session: Session = Depends(get_session),
    current_user: dict = Depends(verify_token)
):
    if current_user.get("role") != "Admin":
        raise HTTPException(status_code=403, detail="Admins only.")

    new_event = Event(
        name=event_data.name,
        category=event_data.category,
        date=event_data.date,
        description=event_data.description
    )
    session.add(new_event)
    session.commit()
    session.refresh(new_event)
    return {"message": "Event created!", "event": new_event}


@router.get("/api/events")
def get_events(
    sort_by: str = "date",
    order: str = "asc",
    session: Session = Depends(get_session)
):
    if sort_by == "name":
        sort_column = Event.name
    elif sort_by == "category":
        sort_column = Event.category
    else:
        sort_column = Event.date

    if order.lower() == "desc":
        sort_column = sort_column.desc()

    return session.exec(select(Event).order_by(sort_column)).all()