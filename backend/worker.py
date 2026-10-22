"""
EC2 Heavy Worker Daemon
------------------------
This background script runs continuously on an EC2 instance.
It long-polls Amazon SQS for heavy/multi-page document jobs dispatched by Lambda or FastAPI,
processes them through Textract and Bedrock, and updates DynamoDB.
"""

import time
import json
import logging
from backend.app.config import get_settings
from backend.app.schemas import DocumentStatus
from backend.app.services.sqs_service import SQSService
from backend.app.services.dynamodb_service import DynamoDBService
from backend.app.services.textract_service import TextractService
from backend.app.services.bedrock_service import BedrockService
from backend.app.services.ses_service import SESService

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [EC2-Worker] %(message)s"
)
logger = logging.getLogger("DocuCloudWorker")

def run_worker():
    settings = get_settings()
    sqs_svc = SQSService()
    db_svc = DynamoDBService()
    textract_svc = TextractService()
    bedrock_svc = BedrockService()
    ses_svc = SESService()

    logger.info("==================================================")
    logger.info("DocuCloud EC2 Heavy Worker Daemon started.")
    logger.info(f"Target SQS Queue: {settings.sqs_queue_name}")
    logger.info(f"Target DynamoDB Table: {settings.dynamodb_table_name}")
    logger.info("Listening for heavy document processing jobs...")
    logger.info("==================================================")

    while True:
        try:
            # Long-poll SQS (waits up to 20 seconds for messages)
            messages = sqs_svc.poll_messages(max_messages=1, wait_time_seconds=20)
            
            if not messages:
                continue

            for msg in messages:
                receipt_handle = msg.get("ReceiptHandle")
                body = json.loads(msg.get("Body", "{}"))
                
                doc_id = body.get("document_id")
                s3_key = body.get("s3_key")
                s3_bucket = body.get("s3_bucket", settings.s3_bucket_name)
                filename = body.get("filename", "unknown.pdf")
                page_count = body.get("page_count", 1)

                logger.info(f"--> Received Job for doc: {doc_id} ('{filename}', {page_count} pages)")

                try:
                    # 1. Update status to PROCESSING
                    db_svc.update_status(
                        document_id=doc_id,
                        status=DocumentStatus.PROCESSING,
                        processed_by="EC2_WORKER"
                    )

                    # 2. Perform OCR and Expense extraction via Textract
                    logger.info(f"Calling Textract on s3://{s3_bucket}/{s3_key}...")
                    extracted = textract_svc.analyze_document_from_s3(s3_bucket, s3_key)

                    # 3. Analyze with Bedrock GenAI
                    logger.info(f"Submitting extracted text to AWS Bedrock ({settings.bedrock_model_id})...")
                    insights = bedrock_svc.generate_document_insights(extracted)

                    # 4. Save results to DynamoDB
                    db_svc.save_analysis_results(
                        document_id=doc_id,
                        extracted_data=extracted.model_dump(),
                        ai_insights=insights.model_dump(),
                        processed_by="EC2_WORKER"
                    )

                    # 5. Delete message from SQS (successful completion)
                    sqs_svc.delete_message(receipt_handle)
                    logger.info(f"✓ Job {doc_id} successfully completed and removed from SQS.")

                except Exception as proc_err:
                    logger.error(f"Error processing document {doc_id}: {proc_err}", exc_info=True)
                    db_svc.update_status(
                        document_id=doc_id,
                        status=DocumentStatus.FAILED,
                        processed_by="EC2_WORKER",
                        error_message=str(proc_err)
                    )
                    # We do not delete the message immediately if we want SQS dead-letter-queue to handle retries

        except KeyboardInterrupt:
            logger.info("Worker shutdown signal received. Exiting gracefully.")
            break
        except Exception as e:
            logger.error(f"Unexpected worker loop exception: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_worker()
