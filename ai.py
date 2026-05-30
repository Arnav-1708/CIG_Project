# ai.py
import face_recognition
import io
import numpy as np
from PIL import Image
from transformers import pipeline

# loads on startup - first time downloads ~600MB, then its cached
try:
    print("Loading image tagger...")
    _image_tagger = pipeline(
        "zero-shot-image-classification",
        model="openai/clip-vit-base-patch32"
    )
    print("Done.")
except Exception as e:
    print(f"CLIP model failed to load: {e}")
    _image_tagger = None

CANDIDATE_LABELS = [
    "people", "crowd", "outdoor", "indoor", "sports", "music",
    "dance", "food", "nature", "mountains", "beach", "party",
    "celebration", "ceremony", "workshop", "competition",
    "night event", "portrait", "group photo", "cultural fest",
    "technical event", "award ceremony"
]


def get_image_tags(file_bytes: bytes) -> list[str]:
    if _image_tagger is None:
        return []
    try:
        image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        results = _image_tagger(image, candidate_labels=CANDIDATE_LABELS)
        tags = [r["label"].lower() for r in results if r["score"] > 0.20]
        print(f"tags: {tags}")
        return tags
    except Exception as e:
        print(f"tagging error: {e}")
        return []


def extract_face_encoding(image_bytes: bytes):
    """for user selfies - only takes the first face found"""
    try:
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        clean_bytes = io.BytesIO()
        pil_image.save(clean_bytes, format="JPEG")
        clean_bytes.seek(0)

        image = face_recognition.load_image_file(clean_bytes)
        encodings = face_recognition.face_encodings(image)

        if len(encodings) > 0:
            return encodings[0]
        return None
    except Exception as e:
        print(f"face encoding error: {e}")
        return None


def extract_all_faces(image_bytes: bytes):
    """for event photos - finds every face in the image"""
    try:
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        clean_bytes = io.BytesIO()
        pil_image.save(clean_bytes, format="JPEG")
        clean_bytes.seek(0)

        image = face_recognition.load_image_file(clean_bytes)
        encodings = face_recognition.face_encodings(image)
        print(f"found {len(encodings)} face(s)")
        return encodings if encodings else []
    except Exception as e:
        print(f"face extraction error: {e}")
        return []