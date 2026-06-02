# check_db.py
from sqlmodel import Session, select
from database import engine
from models import Media

print("--- RUNNING DATABASE DIAGNOSTIC ---")
with Session(engine) as session:
    all_media = session.exec(select(Media)).all()
    
    for media in all_media:
        # Check if the face_encoding field actually has data
        status = "✅ Saved 128-Point Math" if media.face_encoding else "❌ NULL (AI missed it)"
        
        # Grab just the end of the URL so it's easy to read
        filename = media.file_url.split("/")[-1] 
        print(f"Photo ID: {media.id} | File: {filename} | Status: {status}")