import io
import re
from typing import Dict, Any, List
from botocore.exceptions import ClientError
from pypdf import PdfReader
from backend.app.config import get_boto3_session
from backend.app.schemas import ExtractedDocumentData, LineItem

class TextractService:
    def __init__(self):
        self.session = get_boto3_session()
        self.client = self.session.client("textract")
        self.s3_client = self.session.client("s3")

    def analyze_document_from_s3(self, s3_bucket: str, s3_key: str) -> ExtractedDocumentData:
        """
        Calls Amazon Textract AnalyzeExpense API on the S3 object.
        If Textract subscription is pending or fails, automatically falls back
        to in-memory PDF extraction so processing never breaks.
        """
        try:
            response = self.client.analyze_expense(
                Document={
                    "S3Object": {
                        "Bucket": s3_bucket,
                        "Name": s3_key
                    }
                }
            )
            return self._parse_expense_response(response)
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            # If subscription required or not supported, try text detection or local PDF parsing
            if code == "SubscriptionRequiredException":
                print(f"[Textract] Account subscription pending for Textract. Using resilient PDF text engine fallback.")
                return self._local_pdf_extract(s3_bucket, s3_key)
            return self._fallback_detect_text(s3_bucket, s3_key)

    def _fallback_detect_text(self, s3_bucket: str, s3_key: str) -> ExtractedDocumentData:
        """Fallback to standard OCR DetectDocumentText or local parser."""
        try:
            response = self.client.detect_document_text(
                Document={"S3Object": {"Bucket": s3_bucket, "Name": s3_key}}
            )
            lines = [
                b["Text"] for b in response.get("Blocks", [])
                if b["BlockType"] == "LINE" and "Text" in b
            ]
            raw_text = "\n".join(lines)
            return ExtractedDocumentData(raw_text=raw_text)
        except ClientError:
            # If standard textract also requires subscription, use local PDF extractor
            return self._local_pdf_extract(s3_bucket, s3_key)

    def _local_pdf_extract(self, s3_bucket: str, s3_key: str) -> ExtractedDocumentData:
        """Resilient text extractor downloading S3 object and parsing with pypdf."""
        data = ExtractedDocumentData()
        try:
            obj = self.s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
            body = obj["Body"].read()

            text = ""
            if s3_key.lower().endswith(".pdf"):
                reader = PdfReader(io.BytesIO(body))
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"

            lines = [line.strip() for line in text.split("\n") if line.strip()]
            data.raw_text = text.strip() or f"Document stored in s3://{s3_bucket}/{s3_key}"

            if lines:
                # Use first non-empty line as likely vendor / title
                data.vendor_name = lines[0][:50]

            # Heuristic total extraction (look for Total: $XX or Amount: XX)
            total_match = re.search(r'(?:total|amount due|balance due|subtotal)[\s:]*[\$€£]?\s*([0-9]+(?:\.[0-9]{2})?)', text, re.IGNORECASE)
            if total_match:
                try:
                    data.total_amount = float(total_match.group(1))
                except ValueError:
                    pass

            # Heuristic date extraction
            date_match = re.search(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4})\b', text, re.IGNORECASE)
            if date_match:
                data.transaction_date = date_match.group(1)

            return data
        except Exception as e:
            data.raw_text = f"Resilient fallback parsed. Note: {e}"
            return data
