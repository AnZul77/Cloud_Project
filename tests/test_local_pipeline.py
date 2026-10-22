"""
Local Pipeline & AWS Connectivity Verification Script
------------------------------------------------------
Tests:
1. Environment variables and Boto3 session setup
2. S3 bucket connectivity
3. DynamoDB table connectivity
4. SQS queue reachability
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def verify_aws_connectivity():
    print("==================================================")
    print("Testing AWS Service Connections for DocuCloud AI")
    print("==================================================")

    import boto3
    from botocore.exceptions import ClientError

    region = os.getenv("AWS_REGION", "us-east-1")
    bucket_name = os.getenv("S3_BUCKET_NAME")
    table_name = os.getenv("DYNAMODB_TABLE_NAME")
    queue_name = os.getenv("SQS_QUEUE_NAME")

    print(f"Region: {region}")
    print(f"S3 Bucket: {bucket_name}")
    print(f"DynamoDB Table: {table_name}")
    print(f"SQS Queue: {queue_name}\n")

    session = boto3.Session(region_name=region)

    # 1. Test S3
    try:
        s3 = session.client("s3")
        s3.head_bucket(Bucket=bucket_name)
        print("✓ [S3] Bucket exists and is accessible.")
    except ClientError as e:
        print(f"✗ [S3] Notice: {e}")

    # 2. Test DynamoDB
    try:
        dynamodb = session.client("dynamodb")
        resp = dynamodb.describe_table(TableName=table_name)
        status = resp["Table"]["TableStatus"]
        print(f"✓ [DynamoDB] Table found with status: {status}")
    except ClientError as e:
        print(f"✗ [DynamoDB] Notice: {e}")

    # 3. Test SQS
    try:
        sqs = session.client("sqs")
        resp = sqs.get_queue_url(QueueName=queue_name)
        print(f"✓ [SQS] Queue URL resolved: {resp['QueueUrl']}")
    except ClientError as e:
        print(f"✗ [SQS] Notice: {e}")

    # 4. Test Textract & Bedrock Clients
    try:
        _ = session.client("textract")
        print("✓ [Textract] Client initialized.")
    except Exception as e:
        print(f"✗ [Textract] Initialization error: {e}")

    try:
        _ = session.client("bedrock-runtime")
        print("✓ [Bedrock] Runtime client initialized.")
    except Exception as e:
        print(f"✗ [Bedrock] Initialization error: {e}")

    print("\nVerification check finished. If resources are missing, run: python infra/setup_aws.py")

if __name__ == "__main__":
    verify_aws_connectivity()
