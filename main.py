# main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import create_db_and_tables
from routers import users, events, media, social


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="CIG Media Platform", lifespan=lifespan)

app.include_router(users.router)
app.include_router(events.router)
app.include_router(media.router)
app.include_router(social.router)