import json
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError
from backend.app.config import get_boto3_session, get_settings

class SQSService:
    def __init__(self):
        self.settings = get_settings()
        self.session = get_boto3_session()
        self.sqs_client = self.session.client("sqs")
        self._queue_url: Optional[str] = self.settings.sqs_queue_url

    def get_or_resolve_queue_url(self) -> str:
        """Returns configured SQS queue URL, or dynamically resolves it by queue name."""
        if self._queue_url:
            return self._queue_url
        try:
            response = self.sqs_client.get_queue_url(QueueName=self.settings.sqs_queue_name)
            self._queue_url = response["QueueUrl"]
            return self._queue_url
        except ClientError as e:
            raise RuntimeError(f"Failed to resolve SQS queue URL for '{self.settings.sqs_queue_name}': {e}")

    def send_heavy_processing_job(self, document_id: str, s3_key: str, s3_bucket: str, filename: str, page_count: int) -> str:
        """Publishes a document job to SQS for the EC2 background worker to process."""
        queue_url = self.get_or_resolve_queue_url()
        message_body = {
            "document_id": document_id,
            "s3_key": s3_key,
            "s3_bucket": s3_bucket,
            "filename": filename,
            "page_count": page_count
        }

        try:
            response = self.sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(message_body),
                MessageAttributes={
                    "JobType": {"DataType": "String", "StringValue": "HEAVY_DOCUMENT_OCR"}
                }
            )
            return response["MessageId"]
        except ClientError as e:
            raise RuntimeError(f"Failed to send SQS job: {e}")

    def poll_messages(self, max_messages: int = 5, wait_time_seconds: int = 10) -> List[Dict[str, Any]]:
        """Long-polls SQS queue for incoming document processing tasks."""
        queue_url = self.get_or_resolve_queue_url()
        try:
            response = self.sqs_client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=wait_time_seconds,
                MessageAttributeNames=["All"]
            )
            return response.get("Messages", [])
        except ClientError as e:
            raise RuntimeError(f"Failed to poll SQS messages: {e}")

    def delete_message(self, receipt_handle: str):
        """Acknowledges and removes a successfully processed message from SQS."""
        queue_url = self.get_or_resolve_queue_url()
        try:
            self.sqs_client.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
        except ClientError as e:
            raise RuntimeError(f"Failed to delete SQS message: {e}")
