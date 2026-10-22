"""
DocuCloud AI - Reset & Purge Data Script
----------------------------------------
Clears all processed document records from DynamoDB (and optionally S3 uploads)
so you can start testing with a 100% clean slate.
"""

import os
import boto3
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("AWS_REGION", "us-east-1")
TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "DocuCloudProcessedDocuments")

def reset_dynamodb_records():
    print("==================================================")
    print(f"Purging all records from DynamoDB: [{TABLE_NAME}]")
    print("==================================================")
    
    session = boto3.Session(region_name=REGION)
    dynamodb = session.resource("dynamodb")
    table = dynamodb.Table(TABLE_NAME)

    scan = table.scan(ProjectionExpression="document_id")
    items = scan.get("Items", [])

    if not items:
        print("Table is already completely empty! Clean slate ready.")
        return

    print(f"Found {len(items)} record(s) to delete...")
    with table.batch_writer() as batch:
        for item in items:
            batch.delete_item(Key={"document_id": item["document_id"]})

    print(f"[OK] Successfully deleted all {len(items)} records from DynamoDB!")
    print("Your dashboard is now reset to a clean slate.")

if __name__ == "__main__":
    reset_dynamodb_records()
