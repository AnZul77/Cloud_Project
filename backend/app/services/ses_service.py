from typing import Optional
from botocore.exceptions import ClientError
from backend.app.config import get_boto3_session, get_settings
from backend.app.schemas import DocumentRecord

class SESService:
    def __init__(self):
        self.settings = get_settings()
        self.session = get_boto3_session()
        self.client = self.session.client("ses")
        self.sender_email = self.settings.ses_sender_email

    def send_document_analysis_email(self, recipient_email: str, record: DocumentRecord) -> Optional[str]:
        """Sends an HTML summary report via Amazon SES upon completion of document analysis."""
        if not recipient_email:
            return None

        vendor = record.extracted_data.vendor_name if record.extracted_data else "Unknown Vendor"
        total = f"${record.extracted_data.total_amount:.2f}" if (record.extracted_data and record.extracted_data.total_amount is not None) else "N/A"
        category = record.ai_insights.category if record.ai_insights else "Uncategorized"
        summary = record.ai_insights.executive_summary if record.ai_insights else "No summary available."
        anomaly_html = ""

        if record.ai_insights and record.ai_insights.anomaly_detected:
            anomaly_html = f"""
            <div style="background-color: #fee2e2; border-left: 4px solid #ef4444; padding: 12px; margin: 15px 0;">
                <strong style="color: #991b1b;">⚠️ Anomaly Alert:</strong>
                <p style="margin: 4px 0 0; color: #7f1d1d;">{record.ai_insights.anomaly_reason or 'Suspicious pattern identified.'}</p>
            </div>
            """

        subject = f"[DocuCloud AI] Document Processed: {vendor} ({total})"
        html_body = f"""
        <html>
        <head></head>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e5e7eb; border-radius: 8px; padding: 24px;">
                <h2 style="color: #2563eb; margin-top: 0;">DocuCloud AI Processing Report</h2>
                <p>Your document <strong>{record.filename}</strong> has been successfully processed.</p>
                
                {anomaly_html}
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="border-bottom: 1px solid #e5e7eb;">
                        <td style="padding: 8px 0; font-weight: bold; width: 40%;">Document ID:</td>
                        <td style="padding: 8px 0; font-family: monospace;">{record.document_id}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e5e7eb;">
                        <td style="padding: 8px 0; font-weight: bold;">Vendor:</td>
                        <td style="padding: 8px 0;">{vendor}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e5e7eb;">
                        <td style="padding: 8px 0; font-weight: bold;">Total Amount:</td>
                        <td style="padding: 8px 0; font-size: 1.1em; color: #059669; font-weight: bold;">{total}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e5e7eb;">
                        <td style="padding: 8px 0; font-weight: bold;">Category:</td>
                        <td style="padding: 8px 0;">{category}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e5e7eb;">
                        <td style="padding: 8px 0; font-weight: bold;">Processed Engine:</td>
                        <td style="padding: 8px 0;"><span style="background: #e0f2fe; color: #0369a1; padding: 2px 6px; border-radius: 4px; font-size: 0.9em;">{record.processed_by}</span></td>
                    </tr>
                </table>

                <h3 style="color: #1f2937; margin-bottom: 6px;">Executive AI Summary</h3>
                <p style="background-color: #f9fafb; padding: 12px; border-radius: 6px; border: 1px solid #e5e7eb; margin-top: 0;">{summary}</p>
                
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;" />
                <p style="font-size: 0.85em; color: #6b7280; text-align: center;">DocuCloud AI &bull; Hybrid AWS Architecture Platform</p>
            </div>
        </body>
        </html>
        """

        try:
            response = self.client.send_email(
                Source=self.sender_email,
                Destination={"ToAddresses": [recipient_email]},
                Message={
                    "Subject": {"Data": subject},
                    "Body": {"Html": {"Data": html_body}}
                }
            )
            return response.get("MessageId")
        except ClientError as e:
            # Non-blocking if email sender isn't verified in sandbox
            print(f"[SES Warning] Could not send email via SES: {e}")
            return None
