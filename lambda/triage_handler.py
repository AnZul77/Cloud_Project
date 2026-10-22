"""
AWS Lambda S3 Triage Handler (Pure Python - Zero External Layers Needed)
------------------------------------------------------------------------
Triggered by: S3 ObjectCreated event (e.g. uploads/*.pdf or uploads/*.png)

Logic:
1. Parse S3 bucket and key from event.
2. Read PDF page count using lightweight byte inspection (no external pip dependencies).
3. If page_count <= 5 (Lightweight document):
   - Fast-path: Process in-Lambda, update DynamoDB with status COMPLETED and engine 'LAMBDA'.
4. If page_count > 5 (Heavy multi-page document):
   - Route to Amazon SQS for the EC2 Background Worker to handle.
   - Update DynamoDB status to ROUTED_TO_EC2_WORKER.
"""

import json
import os
import re
import urllib.parse
from decimal import Decimal
from datetime import datetime, timezone
import boto3

# Initialize AWS clients
s3_client = boto3.client("s3")
sqs_client = boto3.client("sqs")
dynamodb = boto3.resource("dynamodb")

TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "DocuCloudProcessedDocuments")
QUEUE_URL = os.environ.get("SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/723932052196/DocuCloudHeavyProcessingQueue")

table = dynamodb.Table(TABLE_NAME)

def count_pdf_pages_pure_python(file_bytes: bytes) -> int:
    """Lightweight pure-python PDF page counter requiring no external libraries."""
    try:
        pages = len(re.findall(rb"/Type\s*/Page\b", file_bytes))
        return max(pages, 1)
    except Exception:
        return 1

def lambda_handler(event, context):
    print("Received S3 Event:", json.dumps(event))

    records = event.get("Records", [])
    for record in records:
        bucket = record["s3"]["bucket"]["name"]
        raw_key = record["s3"]["object"]["key"]
        key = urllib.parse.unquote_plus(raw_key)

        print(f"Processing upload: s3://{bucket}/{key}")

        filename = key.split("/")[-1]
        doc_id = filename.split(".")[0]

        try:
            # 1. Download file bytes from S3
            s3_obj = s3_client.get_object(Bucket=bucket, Key=key)
            file_bytes = s3_obj["Body"].read()

            page_count = 1
            if key.lower().endswith(".pdf"):
                page_count = count_pdf_pages_pure_python(file_bytes)

            print(f"Document {doc_id}: Detected {page_count} page(s).")

            # 2. Decision Engine
            if page_count > 5:
                # Heavy path: Dispatch to SQS for EC2 Worker
                print(f"Routing document {doc_id} (>5 pages) to EC2 SQS queue...")
                sqs_msg = {
                    "document_id": doc_id,
                    "s3_key": key,
                    "s3_bucket": bucket,
                    "filename": filename,
                    "page_count": page_count
                }
                if QUEUE_URL:
                    sqs_client.send_message(
                        QueueUrl=QUEUE_URL,
                        MessageBody=json.dumps(sqs_msg)
                    )

                # Update DynamoDB
                table.update_item(
                    Key={"document_id": doc_id},
                    UpdateExpression="SET #s = :s, processed_by = :p, page_count = :pg",
                    ExpressionAttributeNames={"#s": "status"},
                    ExpressionAttributeValues={
                        ":s": "ROUTED_TO_EC2_WORKER",
                        ":p": "EC2_WORKER",
                        ":pg": page_count
                    }
                )
            else:
                # Fast path: Process directly inside Lambda
                print(f"Fast-path processing document {doc_id} directly inside Lambda...")
                
                # Heuristic text and total parsing
                text_sample = file_bytes[:2000].decode("latin-1", errors="ignore")
                vendor = "Uploaded Receipt"
                total_val = Decimal("0.00")

                total_match = re.search(r'(?:total|amount due|balance due)[\s:]*[\$€£]?\s*([0-9]+(?:\.[0-9]{2})?)', text_sample, re.IGNORECASE)
                if total_match:
                    try:
                        total_val = Decimal(total_match.group(1))
                    except Exception:
                        pass

                # Save results in DynamoDB with LAMBDA engine
                now_str = datetime.now(timezone.utc).isoformat()
                table.update_item(
                    Key={"document_id": doc_id},
                    UpdateExpression="SET #s = :s, processed_by = :p, page_count = :pg, filename = :fn, s3_key = :k, created_at = :now, updated_at = :now, extracted_data = :ext, ai_insights = :ai",
                    ExpressionAttributeNames={"#s": "status"},
                    ExpressionAttributeValues={
                        ":s": "COMPLETED",
                        ":p": "LAMBDA",
                        ":pg": page_count,
                        ":fn": filename,
                        ":k": key,
                        ":now": now_str,
                        ":ext": {
                            "vendor_name": vendor,
                            "total_amount": total_val,
                            "raw_text": f"Serverless Lambda processed s3://{bucket}/{key}"
                        },
                        ":ai": {
                            "executive_summary": "Processed instantly via AWS Lambda event trigger without servers.",
                            "category": "Cloud Automated Expense",
                            "is_tax_deductible": True,
                            "anomaly_detected": False
                        }
                    }
                )
                print(f"Fast-path completed for document {doc_id} by Lambda.")

        except Exception as err:
            print(f"Error handling document {doc_id}: {err}")
            try:
                table.update_item(
                    Key={"document_id": doc_id},
                    UpdateExpression="SET #s = :s, error_message = :err",
                    ExpressionAttributeNames={"#s": "status"},
                    ExpressionAttributeValues={":s": "FAILED", ":err": str(err)}
                )
            except Exception:
                pass

    return {"statusCode": 200, "body": "Processing batch completed."}
