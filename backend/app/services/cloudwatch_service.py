import time
from typing import Optional
from botocore.exceptions import ClientError
from backend.app.config import get_boto3_session, get_settings

class CloudWatchLoggingService:
    def __init__(self):
        self.settings = get_settings()
        self.session = get_boto3_session()
        self.client = self.session.client("logs")
        self.log_group_name = "/aws/docucloud/backend"

    def ensure_log_stream(self, stream_name: str):
        """Creates the stream in the CloudWatch Log Group if not already present."""
        try:
            self.client.create_log_stream(
                logGroupName=self.log_group_name,
                logStreamName=stream_name
            )
        except ClientError as e:
            if e.response["Error"]["Code"] != "ResourceAlreadyExistsException":
                # Silently pass to avoid breaking request flow
                pass

    def log_event(self, stream_name: str, message: str, level: str = "INFO"):
        """Pushes structured log entries directly into AWS CloudWatch Logs."""
        try:
            self.ensure_log_stream(stream_name)
            timestamp_ms = int(time.time() * 1000)
            formatted_message = f"[{level}] {message}"
            
            self.client.put_log_events(
                logGroupName=self.log_group_name,
                logStreamName=stream_name,
                logEvents=[
                    {
                        "timestamp": timestamp_ms,
                        "message": formatted_message
                    }
                ]
            )
        except Exception as e:
            # Observability logging should be non-blocking
            print(f"[CloudWatch Warn] Could not send log event: {e}")
