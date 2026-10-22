from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class DocumentStatus(str, Enum):
    PENDING = "PENDING"
    ROUTED_TO_LAMBDA = "ROUTED_TO_LAMBDA"
    ROUTED_TO_EC2_WORKER = "ROUTED_TO_EC2_WORKER"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class DocumentType(str, Enum):
    RECEIPT = "RECEIPT"
    INVOICE = "INVOICE"
    CONTRACT = "CONTRACT"
    GENERAL = "GENERAL"

class LineItem(BaseModel):
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None

class ExtractedDocumentData(BaseModel):
    vendor_name: Optional[str] = None
    invoice_or_receipt_number: Optional[str] = None
    transaction_date: Optional[str] = None
    total_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    currency: Optional[str] = "USD"
    line_items: List[LineItem] = Field(default_factory=list)
    raw_text: Optional[str] = None

class AIInsights(BaseModel):
    category: str = "Uncategorized"  # e.g., Travel, Software, Meals, Office Supplies
    is_tax_deductible: bool = False
    anomaly_detected: bool = False
    anomaly_reason: Optional[str] = None
    executive_summary: str = ""

class DocumentRecord(BaseModel):
    document_id: str
    filename: str
    s3_key: str
    s3_bucket: str
    status: DocumentStatus = DocumentStatus.PENDING
    page_count: int = 1
    processed_by: str = "UNKNOWN" # "LAMBDA" or "EC2_WORKER"
    created_at: str
    updated_at: str
    extracted_data: Optional[ExtractedDocumentData] = None
    ai_insights: Optional[AIInsights] = None
    error_message: Optional[str] = None

class PresignedUploadRequest(BaseModel):
    filename: str
    content_type: str = "application/pdf"

class PresignedUploadResponse(BaseModel):
    document_id: str
    s3_key: str
    upload_url: str
    fields: Dict[str, Any] = Field(default_factory=dict)
