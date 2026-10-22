"""
DocuCloud AI - AWS Infrastructure Auto-Provisioner
-------------------------------------------------
Run this script locally to automatically create all foundational AWS resources:
- Amazon S3 Bucket (with CORS configuration for uploads)
- Amazon DynamoDB Table (Pay-Per-Request billing mode - 100% Free Tier friendly)
- Amazon SQS Queue (for heavy processing decoupling)
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("AWS_REGION", "us-east-1")
BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "docucloud-ai-storage-bucket")
TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "DocuCloudProcessedDocuments")
QUEUE_NAME = os.getenv("SQS_QUEUE_NAME", "DocuCloudHeavyProcessingQueue")

session = boto3.Session(region_name=REGION)
s3 = session.client("s3")
dynamodb = session.client("dynamodb")
sqs = session.client("sqs")

def setup_s3():
    print(f"\n[1/3] Setting up S3 Bucket: {BUCKET_NAME}...")
    try:
        if REGION == "us-east-1":
            s3.create_bucket(Bucket=BUCKET_NAME)
        else:
            s3.create_bucket(
                Bucket=BUCKET_NAME,
                CreateBucketConfiguration={"LocationConstraint": REGION}
            )
        print(f"  ✓ S3 Bucket created: {BUCKET_NAME}")
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code")
        if code in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            print(f"  ℹ S3 Bucket already exists: {BUCKET_NAME}")
        else:
            print(f"  ✗ Failed creating S3 bucket: {e}")

    # Configure CORS for direct browser uploads
    cors_config = {
        "CORSRules": [
            {
                "AllowedHeaders": ["*"],
                "AllowedMethods": ["GET", "PUT", "POST", "HEAD"],
                "AllowedOrigins": ["*"],
                "ExposeHeaders": ["ETag"]
            }
        ]
    }
    s3.put_bucket_cors(Bucket=BUCKET_NAME, CORSConfiguration=cors_config)
    print("  ✓ S3 CORS configuration applied.")

def setup_dynamodb():
    print(f"\n[2/3] Setting up DynamoDB Table: {TABLE_NAME}...")
    try:
        dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {"AttributeName": "document_id", "KeyType": "HASH"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "document_id", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST"  # On-demand, zero cost when idle
        )
        print(f"  ✓ DynamoDB Table created: {TABLE_NAME}")
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") == "ResourceInUseException":
            print(f"  ℹ DynamoDB Table already exists: {TABLE_NAME}")
        else:
            print(f"  ✗ Failed creating DynamoDB table: {e}")

def setup_sqs():
    print(f"\n[3/3] Setting up SQS Queue: {QUEUE_NAME}...")
    try:
        resp = sqs.create_queue(
            QueueName=QUEUE_NAME,
            Attributes={
                "VisibilityTimeout": "300",  # 5 minutes visibility for long OCR jobs
                "MessageRetentionPeriod": "86400"  # 1 day
            }
        )
        queue_url = resp.get("QueueUrl")
        print(f"  ✓ SQS Queue created/ready: {queue_url}")
        return queue_url
    except ClientError as e:
        print(f"  ✗ Failed creating SQS queue: {e}")
        return None

if __name__ == "__main__":
    print("==================================================")
    print(f"Provisioning DocuCloud AWS Resources in [{REGION}]")
    print("==================================================")
    setup_s3()
    setup_dynamodb()
    queue_url = setup_sqs()
    print("\n==================================================")
    print("Provisioning Complete! Add this to your .env file:")
    print(f"SQS_QUEUE_URL={queue_url or '...'}")
    print("==================================================")
