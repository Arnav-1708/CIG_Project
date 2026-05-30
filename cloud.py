# cloud.py
import os
import boto3
import uuid
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv

load_dotenv()

BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
    endpoint_url=os.getenv("AWS_ENDPOINT_URL")
)


def upload_to_s3(file_bytes: bytes, filename: str, content_type: str = "image/jpeg"):
    try:
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=unique_filename,
            Body=file_bytes,
            ContentType=content_type
        )
        # store redirect url in db, actual presigned url is generated at access time
        return f"{BASE_URL}/api/media/view/{unique_filename}"
    except NoCredentialsError:
        print("AWS credentials not found, check .env")
        raise
    except Exception as e:
        print(f"S3 upload failed: {e}")
        raise


def generate_secure_url(filename: str):
    # presigned url valid for 1 hour
    return s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': BUCKET_NAME, 'Key': filename},
        ExpiresIn=3600
    )


def get_file_bytes_from_s3(filename: str) -> bytes:
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=filename)
        return response['Body'].read()
    except Exception as e:
        print(f"S3 download failed: {e}")
        raise