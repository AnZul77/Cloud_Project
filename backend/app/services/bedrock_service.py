import os
import json
from typing import Dict, Any
from botocore.exceptions import ClientError
from backend.app.config import get_boto3_session, get_settings
from backend.app.schemas import AIInsights, ExtractedDocumentData

class BedrockService:
    def __init__(self):
        self.settings = get_settings()
        self.ai_provider = os.getenv("AI_PROVIDER", "local").lower()
        self.session = None
        self.client = None
        self.model_id = self.settings.bedrock_model_id

        # Only initialize AWS Bedrock client if explicitly configured to use bedrock
        if self.ai_provider == "bedrock":
            try:
                self.session = get_boto3_session()
                self.client = self.session.client("bedrock-runtime")
            except Exception:
                self.client = None

    def generate_document_insights(self, extracted: ExtractedDocumentData) -> AIInsights:
        """
        Evaluates receipt/invoice details.
        If AI_PROVIDER is 'local' (Free Tier Mode), uses intelligent local heuristics (100% free).
        If AI_PROVIDER is 'bedrock', invokes AWS Bedrock Claude 3.
        """
        if self.ai_provider == "local" or not self.client:
            return self._local_rule_based_audit(extracted)

        return self._bedrock_claude_audit(extracted)

    def _local_rule_based_audit(self, extracted: ExtractedDocumentData) -> AIInsights:
        """100% Free heuristic auditor: categorizes, detects anomalies, and drafts summaries."""
        vendor = (extracted.vendor_name or "").lower()
        total = extracted.total_amount or 0.0
        raw = (extracted.raw_text or "").lower()

        # 1. Smart Category Detection
        category = "General Business Expense"
        if any(w in vendor or w in raw for w in ["uber", "lyft", "airline", "delta", "hotel", "marriott", "flight", "taxi"]):
            category = "Travel & Lodging"
        elif any(w in vendor or w in raw for w in ["restaurant", "cafe", "coffee", "starbucks", "mcdonald", "food", "dining", "grill"]):
            category = "Meals & Entertainment"
        elif any(w in vendor or w in raw for w in ["aws", "amazon web services", "github", "google cloud", "software", "slack", "zoom", "microsoft"]):
            category = "Software & Cloud Infrastructure"
        elif any(w in vendor or w in raw for w in ["office", "staples", "paper", "walmart", "target"]):
            category = "Office Supplies & Equipment"

        # 2. Anomaly & Policy Violation Check
        anomaly = False
        anomaly_reason = None

        if total > 500.0:
            anomaly = True
            anomaly_reason = f"High-value transaction (${total:.2f}) requires secondary manager sign-off."
        elif not extracted.vendor_name:
            anomaly = True
            anomaly_reason = "Unidentifiable vendor name detected on receipt."
        elif total == 0.0 and len(extracted.line_items) == 0:
            anomaly = True
            anomaly_reason = "Zero or unparsed total amount with no itemized lines."

        # 3. Tax Deductibility
        is_tax_deductible = category in ["Software & Cloud Infrastructure", "Office Supplies & Equipment", "Travel & Lodging"]

        # 4. Executive Summary
        vendor_display = extracted.vendor_name or "Unspecified Vendor"
        item_count = len(extracted.line_items)
        items_desc = f"with {item_count} itemized line(s)" if item_count > 0 else "single transaction"
        summary = (
            f"Verified expense from {vendor_display} totaling ${total:.2f} ({items_desc}). "
            f"Categorized under {category}. "
            f"{'Flagged for compliance review: ' + (anomaly_reason or '') if anomaly else 'Compliant with corporate expenditure guidelines.'}"
        )

        return AIInsights(
            category=category,
            is_tax_deductible=is_tax_deductible,
            anomaly_detected=anomaly,
            anomaly_reason=anomaly_reason,
            executive_summary=summary
        )

    def _bedrock_claude_audit(self, extracted: ExtractedDocumentData) -> AIInsights:
        """Invokes AWS Bedrock Claude 3 Haiku when enabled."""
        prompt_data = {
            "vendor": extracted.vendor_name,
            "invoice_number": extracted.invoice_or_receipt_number,
            "date": extracted.transaction_date,
            "total_amount": extracted.total_amount,
            "currency": extracted.currency,
            "line_items": [item.model_dump() for item in extracted.line_items],
            "raw_text_snippet": (extracted.raw_text or "")[:1500]
        }

        system_prompt = (
            "You are an expert corporate financial auditor and AI accountant. "
            "Analyze the parsed document data and respond STRICTLY in JSON format with keys: "
            "'category' (string), "
            "'is_tax_deductible' (boolean), "
            "'anomaly_detected' (boolean), "
            "'anomaly_reason' (string or null), "
            "'executive_summary' (string: 2-3 sentences)."
        )

        user_message = f"Document Data:\n{json.dumps(prompt_data, indent=2)}\n\nProvide the JSON analysis:"

        try:
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 800,
                "temperature": 0.2,
                "system": system_prompt,
                "messages": [{"role": "user", "content": [{"type": "text", "text": user_message}]}]
            }

            response = self.client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload)
            )

            response_body = json.loads(response["body"].read().decode("utf-8"))
            content_text = response_body.get("content", [{}])[0].get("text", "{}")
            clean_json = content_text.strip().strip("`").removeprefix("json").strip()
            parsed = json.loads(clean_json)

            return AIInsights(
                category=parsed.get("category", "General Expense"),
                is_tax_deductible=parsed.get("is_tax_deductible", False),
                anomaly_detected=parsed.get("anomaly_detected", False),
                anomaly_reason=parsed.get("anomaly_reason"),
                executive_summary=parsed.get("executive_summary", "")
            )
        except Exception:
            return self._local_rule_based_audit(extracted)
