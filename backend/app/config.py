import os
from functools import lru_cache
from pydantic_settings import BaseSettings
import boto3
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    aws_access_key_id: str | None = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str | None = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_session_token: str | None = os.getenv("AWS_SESSION_TOKEN")

    s3_bucket_name: str = os.getenv("S3_BUCKET_NAME", "docucloud-ai-storage-bucket")
    dynamodb_table_name: str = os.getenv("DYNAMODB_TABLE_NAME", "DocuCloudProcessedDocuments")
    sqs_queue_name: str = os.getenv("SQS_QUEUE_NAME", "DocuCloudHeavyProcessingQueue")
    sqs_queue_url: str = os.getenv("SQS_QUEUE_URL", "")
    
    bedrock_model_id: str = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
    ses_sender_email: str = os.getenv("SES_SENDER_EMAIL", "noreply@example.com")
    
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

def get_boto3_session() -> boto3.Session:
    """Returns a boto3 Session using configured credentials or defaults (IAM role if on EC2)."""
    settings = get_settings()
    kwargs = {"region_name": settings.aws_region}
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        kwargs["aws_access_key_id"] = settings.aws_access_key_id
        kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
        if settings.aws_session_token:
            kwargs["aws_session_token"] = settings.aws_session_token
    return boto3.Session(**kwargs)
