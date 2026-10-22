from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any
from botocore.exceptions import ClientError
from backend.app.config import get_boto3_session, get_settings
from backend.app.schemas import DocumentRecord, DocumentStatus

def _to_dynamo_safe(val: Any) -> Any:
    """Recursively converts Python float objects to Decimal for DynamoDB compliance."""
    if isinstance(val, float):
        return Decimal(str(val))
    elif isinstance(val, dict):
        return {k: _to_dynamo_safe(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [_to_dynamo_safe(item) for item in val]
    return val

def _from_dynamo_safe(val: Any) -> Any:
    """Recursively converts Decimal objects to float/int for JSON serialization."""
    if isinstance(val, Decimal):
        return float(val) if (val % 1 > 0) else int(val)
    elif isinstance(val, dict):
        return {k: _from_dynamo_safe(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [_from_dynamo_safe(item) for item in val]
    return val

class DynamoDBService:
    def __init__(self):
        self.settings = get_settings()
        self.session = get_boto3_session()
        self.dynamodb = self.session.resource("dynamodb")
        self.table = self.dynamodb.Table(self.settings.dynamodb_table_name)

    def create_initial_record(
        self,
        document_id: str,
        filename: str,
        s3_key: str,
        page_count: int = 1,
        processed_by: str = "PENDING"
    ) -> Dict[str, Any]:
        """Creates an initial document tracking record in DynamoDB."""
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "document_id": document_id,
            "filename": filename,
            "s3_key": s3_key,
            "s3_bucket": self.settings.s3_bucket_name,
            "status": DocumentStatus.PENDING.value,
            "page_count": page_count,
            "processed_by": processed_by,
            "created_at": now,
            "updated_at": now
        }
        try:
            self.table.put_item(Item=_to_dynamo_safe(item))
            return item
        except ClientError as e:
            raise RuntimeError(f"Failed to create DynamoDB document record: {e}")

    def update_status(self, document_id: str, status: DocumentStatus, processed_by: Optional[str] = None, error_message: Optional[str] = None):
        """Updates the status and timestamps of a document."""
        now = datetime.now(timezone.utc).isoformat()
        update_expr = "SET #s = :status, updated_at = :updated_at"
        expr_names = {"#s": "status"}
        expr_values: Dict[str, Any] = {
            ":status": status.value,
            ":updated_at": now
        }

        if processed_by:
            update_expr += ", processed_by = :proc"
            expr_values[":proc"] = processed_by

        if error_message:
            update_expr += ", error_message = :err"
            expr_values[":err"] = error_message

        try:
            self.table.update_item(
                Key={"document_id": document_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=_to_dynamo_safe(expr_values)
            )
        except ClientError as e:
            raise RuntimeError(f"Failed to update document status: {e}")

    def save_analysis_results(
        self,
        document_id: str,
        extracted_data: Dict[str, Any],
        ai_insights: Dict[str, Any],
        processed_by: str
    ):
        """Saves final extracted invoice/receipt data and GenAI Bedrock insights."""
        now = datetime.now(timezone.utc).isoformat()
        try:
            self.table.update_item(
                Key={"document_id": document_id},
                UpdateExpression="""
                    SET #s = :status,
                        extracted_data = :ext,
                        ai_insights = :ai,
                        processed_by = :proc,
                        updated_at = :updated_at
                """,
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues=_to_dynamo_safe({
                    ":status": DocumentStatus.COMPLETED.value,
                    ":ext": extracted_data,
                    ":ai": ai_insights,
                    ":proc": processed_by,
                    ":updated_at": now
                })
            )
        except ClientError as e:
            raise RuntimeError(f"Failed to save analysis results in DynamoDB: {e}")

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a document by document_id."""
        try:
            response = self.table.get_item(Key={"document_id": document_id})
            item = response.get("Item")
            return _from_dynamo_safe(item) if item else None
        except ClientError as e:
            raise RuntimeError(f"Failed to retrieve document {document_id}: {e}")

    def list_documents(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Scans the table for recent documents."""
        try:
            response = self.table.scan(Limit=limit)
            items = response.get("Items", [])
            # Sort newest first
            items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return [_from_dynamo_safe(i) for i in items]
        except ClientError as e:
            raise RuntimeError(f"Failed to list documents: {e}")
