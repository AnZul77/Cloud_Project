import uuid
from typing import Dict, Any, Tuple
from botocore.exceptions import ClientError
from backend.app.config import get_boto3_session, get_settings

class S3Service:
    def __init__(self):
        self.settings = get_settings()
        self.session = get_boto3_session()
        self.s3_client = self.session.client("s3")
        self.bucket_name = self.settings.s3_bucket_name

    def generate_presigned_upload(self, filename: str, content_type: str = "application/pdf") -> Tuple[str, str, str, Dict[str, Any]]:
        """
        Generates a unique document ID, S3 key, and a presigned POST URL
        allowing clients to upload directly to S3 without passing bytes through the server.
        """
        doc_id = str(uuid.uuid4())
        extension = filename.split(".")[-1] if "." in filename else "bin"
        s3_key = f"uploads/{doc_id}.{extension}"

        try:
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=s3_key,
                Fields={"Content-Type": content_type},
                Conditions=[
                    {"Content-Type": content_type},
                    ["content-length-range", 10, 50 * 1024 * 1024]  # Max 50 MB
                ],
                ExpiresIn=3600
            )
            return doc_id, s3_key, response["url"], response["fields"]
        except ClientError as e:
            raise RuntimeError(f"Failed to generate presigned upload URL: {e}")

    def download_file_bytes(self, s3_key: str) -> bytes:
        """Downloads document bytes directly from S3."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return response["Body"].read()
        except ClientError as e:
            raise RuntimeError(f"Failed to download object {s3_key} from S3: {e}")

    def upload_file_bytes(self, s3_key: str, data: bytes, content_type: str = "application/pdf") -> str:
        """Uploads raw bytes to S3 and returns the key."""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=data,
                ContentType=content_type
            )
            return s3_key
        except ClientError as e:
            raise RuntimeError(f"Failed to upload object {s3_key} to S3: {e}")
