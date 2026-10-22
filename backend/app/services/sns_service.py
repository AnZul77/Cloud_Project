import json
from botocore.exceptions import ClientError
from backend.app.config import get_boto3_session, get_settings

class SNSService:
    def __init__(self):
        self.settings = get_settings()
        self.session = get_boto3_session()
        self.client = self.session.client("sns")
        self.topic_arn = "arn:aws:sns:us-east-1:723932052196:DocuCloud-Anomaly-Alerts-Topic"

    def publish_anomaly_alert(self, document_id: str, vendor: str, total: float, anomaly_reason: str):
        """Dispatches real-time compliance alert to Amazon SNS topic."""
        subject = f"⚠️ [DocuCloud Alert] High-Value / Anomaly Expense: {vendor} (${total:.2f})"
        message = (
            f"DocuCloud AI Policy Compliance Warning\n"
            f"-----------------------------------------\n"
            f"Document ID: {document_id}\n"
            f"Vendor:      {vendor}\n"
            f"Total:       ${total:.2f}\n"
            f"Alert:       {anomaly_reason}\n\n"
            f"Action: Secondary managerial sign-off required."
        )

        try:
            resp = self.client.publish(
                TopicArn=self.topic_arn,
                Subject=subject[:100],
                Message=message
            )
            return resp.get("MessageId")
        except ClientError as e:
            print(f"[SNS Warn] Failed to publish anomaly alert: {e}")
            return None
