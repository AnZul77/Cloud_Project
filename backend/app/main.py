import io
import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader

from backend.app.config import get_settings
from backend.app.schemas import (
    DocumentStatus,
    PresignedUploadRequest,
    PresignedUploadResponse,
)
from backend.app.services.s3_service import S3Service
from backend.app.services.dynamodb_service import DynamoDBService
from backend.app.services.sqs_service import SQSService
from backend.app.services.textract_service import TextractService
from backend.app.services.bedrock_service import BedrockService
from backend.app.services.ses_service import SESService
from backend.app.services.cloudwatch_service import CloudWatchLoggingService
from backend.app.services.sns_service import SNSService

app = FastAPI(
    title="DocuCloud AI - Intelligent Document Processing Platform",
    description="Hybrid AWS Architecture combining EC2, Lambda, S3, SQS, DynamoDB, Textract, Bedrock, SES, CloudWatch & SNS.",
    version="1.0.0"
)

# Enable CORS for frontend clients / dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service singletons
settings = get_settings()
s3_svc = S3Service()
db_svc = DynamoDBService()
sqs_svc = SQSService()
textract_svc = TextractService()
bedrock_svc = BedrockService()
ses_svc = SESService()
cw_logger = CloudWatchLoggingService()
sns_svc = SNSService()

@app.get("/dashboard", tags=["UI"])
def serve_dashboard():
    static_file = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(static_file):
        return FileResponse(static_file)
    return {"message": "Dashboard UI not found."}

@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "DocuCloud AI Backend",
        "aws_region": settings.aws_region,
        "integrated_aws_services": [
            "Amazon EC2 (FastAPI Host & Async Worker)",
            "AWS Lambda (Serverless Triage Router)",
            "Amazon S3 (Document Lake)",
            "Amazon DynamoDB (Structured Storage)",
            "Amazon SQS (Job Buffering)",
            "Amazon Textract (OCR & Expense Parser)",
            "Amazon Bedrock (Claude 3 GenAI Insights)",
            "Amazon SES (Email Alerts)",
            "Amazon CloudWatch (Logs & Metrics)"
        ]
    }

@app.post("/api/documents/presigned-upload", response_model=PresignedUploadResponse, tags=["Documents"])
def create_presigned_upload(req: PresignedUploadRequest):
    """
    Step 1 of direct S3 upload: Generates a signed S3 upload URL
    and initializes a document record in DynamoDB with PENDING status.
    """
    try:
        doc_id, s3_key, upload_url, fields = s3_svc.generate_presigned_upload(
            filename=req.filename,
            content_type=req.content_type
        )
        db_svc.create_initial_record(
            document_id=doc_id,
            filename=req.filename,
            s3_key=s3_key,
            page_count=1,
            processed_by="PENDING"
        )
        return PresignedUploadResponse(
            document_id=doc_id,
            s3_key=s3_key,
            upload_url=upload_url,
            fields=fields
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/documents/upload-direct", tags=["Documents"])
async def upload_direct_file(
    file: UploadFile = File(...),
    notification_email: str = Form(None)
):
    """
    Direct file upload endpoint for testing or local dashboard.
    Inspects document page count:
    - If > 5 pages: Enqueues to SQS for the EC2 Heavy Worker.
    - If <= 5 pages: Runs standard processing directly through Textract + Bedrock.
    """
    try:
        content = await file.read()
        page_count = 1
        if file.filename.lower().endswith(".pdf"):
            try:
                reader = PdfReader(io.BytesIO(content))
                page_count = len(reader.pages)
            except Exception:
                page_count = 1

        import uuid
        doc_id = str(uuid.uuid4())
        extension = file.filename.split(".")[-1] if "." in file.filename else "pdf"
        s3_key = f"uploads/{doc_id}.{extension}"

        # 1. Upload to S3
        s3_svc.upload_file_bytes(s3_key=s3_key, data=content, content_type=file.content_type or "application/pdf")

        # 2. Track in DynamoDB
        db_svc.create_initial_record(
            document_id=doc_id,
            filename=file.filename,
            s3_key=s3_key,
            page_count=page_count,
            processed_by="UNKNOWN"
        )

        # 3. Triage Logic: Heavy Document vs Fast Track
        if page_count > 5:
            # Route to SQS for EC2 Worker
            cw_logger.log_event("api-server", f"Heavy document {doc_id} ('{file.filename}', {page_count} pages) dispatched to Amazon SQS", level="INFO")
            sqs_svc.send_heavy_processing_job(
                document_id=doc_id,
                s3_key=s3_key,
                s3_bucket=settings.s3_bucket_name,
                filename=file.filename,
                page_count=page_count
            )
            db_svc.update_status(document_id=doc_id, status=DocumentStatus.ROUTED_TO_EC2_WORKER, processed_by="EC2_WORKER")
            return {
                "document_id": doc_id,
                "status": DocumentStatus.ROUTED_TO_EC2_WORKER,
                "page_count": page_count,
                "message": f"Document has {page_count} pages (> 5 limit). Dispatched to SQS queue for EC2 Background Worker."
            }
        else:
            # Fast Track: Process immediately
            cw_logger.log_event("api-server", f"Processing lightweight receipt {doc_id} ('{file.filename}') synchronously", level="INFO")
            db_svc.update_status(document_id=doc_id, status=DocumentStatus.PROCESSING, processed_by="FAST_API_SYNC")
            extracted = textract_svc.analyze_document_from_s3(settings.s3_bucket_name, s3_key)
            insights = bedrock_svc.generate_document_insights(extracted)

            db_svc.save_analysis_results(
                document_id=doc_id,
                extracted_data=extracted.model_dump(),
                ai_insights=insights.model_dump(),
                processed_by="FAST_API_SYNC"
            )
            cw_logger.log_event("api-server", f"Completed extraction & audit for {doc_id}. Category: {insights.category}, Total: ${extracted.total_amount}", level="INFO")

            # Dispatch Amazon SNS alert if compliance anomaly flagged
            if insights.anomaly_detected:
                sns_svc.publish_anomaly_alert(
                    document_id=doc_id,
                    vendor=extracted.vendor_name or "Unknown",
                    total=extracted.total_amount or 0.0,
                    anomaly_reason=insights.anomaly_reason or "Flagged transaction"
                )
                cw_logger.log_event("api-server", f"Dispatched Amazon SNS alert for document {doc_id}", level="WARN")

            # Optional SES email notification
            if notification_email:
                record = db_svc.get_document(doc_id)
                # ses_svc.send_document_analysis_email(notification_email, record)

            return {
                "document_id": doc_id,
                "status": DocumentStatus.COMPLETED,
                "page_count": page_count,
                "extracted_data": extracted,
                "ai_insights": insights
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {str(e)}")

@app.get("/api/documents", tags=["Documents"])
def list_documents(limit: int = 25):
    """Retrieves all tracked documents from DynamoDB."""
    try:
        return db_svc.list_documents(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/{document_id}", tags=["Documents"])
def get_document(document_id: str):
    """Retrieves single document extraction and AI insight record."""
    record = db_svc.get_document(document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")
    return record

@app.delete("/api/documents/reset", tags=["Documents"])
def reset_all_documents():
    """Purges all tracked document records from DynamoDB for a clean testing slate."""
    try:
        scan = db_svc.table.scan(ProjectionExpression="document_id")
        items = scan.get("Items", [])
        with db_svc.table.batch_writer() as batch:
            for item in items:
                batch.delete_item(Key={"document_id": item["document_id"]})
        return {"status": "success", "deleted_count": len(items), "message": f"Successfully deleted {len(items)} records."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
