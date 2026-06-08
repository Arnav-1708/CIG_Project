# CIG Event & Media Management Platform

Backend API for managing club event photos and videos. Built with FastAPI + SQLite.

No frontend yet — all endpoints are accessible via Swagger UI at `/docs`.

## GitHub
[github.com/Arnav-1708/CIG_Project](https://github.com/Arnav-1708/CIG_Project)

## Features

- Event creation and management (Admin only)
- Photo/video uploads stored on AWS S3
- Public and private media with role-based access control
- AI image tagging using CLIP (runs locally, no API costs)
- Face recognition — upload a selfie, find every event photo you appear in
- Social features — likes, comments, favourites, share
- Watermarked downloads (club + event name + username stamped on image)
- Notifications endpoint for recent likes and comments on your uploads

## Roles

| Role | What they can do |
|------|-----------------|
| Admin | Create events, everything else |
| Photographer | Upload media, access private media |
| Club Member | Upload media, access private media |
| Viewer | View public media only |

First user to register gets Admin automatically.

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
SECRET_KEY=your_secret_key_here
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_BUCKET_NAME=...
AWS_REGION=ap-south-1
AWS_ENDPOINT_URL=
BASE_URL=http://127.0.0.1:8000
```

Run:
```bash
uvicorn main:app --reload
```

## Stack

- FastAPI + SQLModel (SQLite)
- AWS S3 via boto3
- face_recognition (dlib)
- CLIP via HuggingFace Transformers
- bcrypt + JWT

## Notes

- CLIP downloads ~600MB on first run, cached after that
- dlib can be painful to install on Windows — recommend using WSL or grabbing a prebuilt wheel
- Frontend is planned, ran out of time this week
- Deployment pending due to heavy AI dependencies (CLIP 600MB + dlib). Full demo in video above.

## API Docs

Auto-generated at `http://127.0.0.1:8000/docs` when server is running.

## Project Built By
Arnav[EE'29] · IIT Roorkee · June 2026