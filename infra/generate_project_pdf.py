"""
DocuCloud AI - Comprehensive Project Documentation PDF Generator
Generates a multi-page executive architecture report and portfolio guide.
"""

import os
import pymupdf

OUTPUT_PDF = "DocuCloud_AI_Project_Documentation.pdf"

def create_documentation_pdf():
    doc = pymupdf.open()
    
    PRIMARY_COLOR = (0.08, 0.18, 0.36)     # Navy Blue
    SECONDARY_COLOR = (0.3, 0.4, 0.5)     # Slate Grey
    TEXT_COLOR = (0.15, 0.15, 0.15)        # Dark Charcoal
    ACCENT_GREEN = (0.05, 0.55, 0.3)       # Emerald Green
    ACCENT_AMBER = (0.85, 0.5, 0.05)       # Amber
    CARD_BG = (0.97, 0.98, 0.99)           # Off white / light grey
    CARD_BORDER = (0.88, 0.9, 0.92)

    def add_page_decorations(page, page_num, total_pages=5):
        # Top banner line
        page.draw_rect(pymupdf.Rect(0, 0, 595, 6), color=PRIMARY_COLOR, fill=PRIMARY_COLOR)
        # Header text
        page.insert_text((40, 32), "DOCUCLOUD AI  |  ENTERPRISE AWS ARCHITECTURE REPORT", fontsize=8, fontname="helv", color=SECONDARY_COLOR)
        # Footer line
        page.draw_line((40, 805), (555, 805), color=CARD_BORDER, width=0.8)
        page.insert_text((40, 820), "Confidential - Portfolio Project Documentation", fontsize=8, color=SECONDARY_COLOR)
        page.insert_text((500, 820), f"Page {page_num} of {total_pages}", fontsize=8, color=SECONDARY_COLOR)

    # =========================================================================
    # PAGE 1: TITLE & EXECUTIVE ARCHITECTURE SUMMARY
    # =========================================================================
    p1 = doc.new_page(width=595, height=842)
    add_page_decorations(p1, 1)

    # Title Banner Box
    p1.draw_rect(pymupdf.Rect(40, 50, 555, 145), color=CARD_BORDER, fill=CARD_BG)
    p1.insert_text((55, 80), "DocuCloud AI", fontsize=24, fontname="helv", color=PRIMARY_COLOR)
    p1.insert_text((55, 102), "Hybrid Serverless & EC2 Intelligent Financial Document Processing Platform", fontsize=11, fontname="helv", color=SECONDARY_COLOR)
    p1.insert_text((55, 126), "Author: Anshul Gupta   |   Cloud Architecture: AWS   |   Stack: Python, FastAPI, Boto3", fontsize=9, color=PRIMARY_COLOR)

    # Section 1: Executive Summary
    p1.insert_text((40, 170), "1. EXECUTIVE PROJECT SUMMARY", fontsize=13, fontname="helv", color=PRIMARY_COLOR)
    p1.draw_line((40, 175), (555, 175), color=PRIMARY_COLOR, width=1.2)

    summary_text = (
        "DocuCloud AI is a production-grade, distributed cloud platform designed to solve the real-world\n"
        "problem of automated invoice and financial receipt auditing. Traditional document processing systems\n"
        "rely either purely on monolithic servers (which struggle with sudden burst traffic) or purely on\n"
        "serverless functions (which fail when handling 100+ page documents due to AWS Lambda's 15-minute\n"
        "execution ceiling and memory boundaries).\n\n"
        "DocuCloud AI bridges this gap with an Intelligent Hybrid Architecture: it leverages AWS Lambda for\n"
        "sub-second, serverless fast-track triage of everyday receipts (<= 5 pages), while decoupling heavy,\n"
        "multi-page enterprise contracts (> 5 pages) through Amazon SQS queues into dedicated, long-polling\n"
        "Amazon EC2 background worker daemons."
    )
    p1.insert_textbox(pymupdf.Rect(40, 185, 555, 305), summary_text, fontsize=9.5, fontname="helv", color=TEXT_COLOR)

    # Section 2: Architectural Data Flow
    p1.insert_text((40, 325), "2. END-TO-END DATA FLOW & TRIAGE PATTERN", fontsize=13, fontname="helv", color=PRIMARY_COLOR)
    p1.draw_line((40, 330), (555, 330), color=PRIMARY_COLOR, width=1.2)

    flow_steps = [
        ("Step 1: Document Ingestion", "Client sends PDF via REST API or uploads directly to Amazon S3 via secure pre-signed URLs."),
        ("Step 2: Serverless Triage", "S3 triggers AWS Lambda to inspect byte structure and determine page count instantaneously."),
        ("Step 3A: Fast-Path (< 5 pgs)", "Lightweight receipts are processed in-memory by OCR & Financial Heuristics for instant return."),
        ("Step 3B: Heavy-Path (> 5 pgs)", "Heavy multi-page files are dispatched as messages to Amazon SQS to prevent server timeouts."),
        ("Step 4: EC2 Worker Polling", "Dedicated EC2 worker daemon long-polls SQS, extracts deep tables, and runs audit checks."),
        ("Step 5: NoSQL Persistence", "Standardized entities (Vendor, Amount, Tax, Anomaly Alerts) are persisted in Amazon DynamoDB."),
        ("Step 6: Dashboard Synchronization", "Single-page responsive dashboard updates dynamically, rendering audit flags & live spend metrics.")
    ]

    y_pos = 345
    for title, desc in flow_steps:
        p1.draw_rect(pymupdf.Rect(40, y_pos, 555, y_pos + 32), color=CARD_BORDER, fill=CARD_BG)
        p1.insert_text((52, y_pos + 13), title, fontsize=9, fontname="helv", color=PRIMARY_COLOR)
        p1.insert_text((52, y_pos + 25), desc, fontsize=8, color=TEXT_COLOR)
        y_pos += 37

    # Highlight Stats at Bottom
    p1.draw_rect(pymupdf.Rect(40, 625, 190, 685), color=CARD_BORDER, fill=CARD_BG)
    p1.insert_text((50, 645), "10 AWS SERVICES", fontsize=11, fontname="helv", color=PRIMARY_COLOR)
    p1.insert_text((50, 665), "Cohesive enterprise cloud architecture", fontsize=7.5, color=SECONDARY_COLOR)

    p1.draw_rect(pymupdf.Rect(205, 625, 375, 685), color=CARD_BORDER, fill=CARD_BG)
    p1.insert_text((215, 645), "100% FREE TIER SAFE", fontsize=11, fontname="helv", color=ACCENT_GREEN)
    p1.insert_text((215, 665), "Built with zero-quota local AI + SQS", fontsize=7.5, color=SECONDARY_COLOR)

    p1.draw_rect(pymupdf.Rect(390, 625, 555, 685), color=CARD_BORDER, fill=CARD_BG)
    p1.insert_text((400, 645), "HYBRID IAAS + SERVERLESS", fontsize=11, fontname="helv", color=PRIMARY_COLOR)
    p1.insert_text((400, 665), "EC2 Daemons + Lambda S3 triggers", fontsize=7.5, color=SECONDARY_COLOR)

    # =========================================================================
    # PAGE 2: THE 10 AWS SERVICES DEEP DIVE
    # =========================================================================
    p2 = doc.new_page(width=595, height=842)
    add_page_decorations(p2, 2)

    p2.insert_text((40, 50), "3. THE 10 INTEGRATED AWS SERVICES", fontsize=14, fontname="helv", color=PRIMARY_COLOR)
    p2.draw_line((40, 55), (555, 55), color=PRIMARY_COLOR, width=1.2)

    services_data = [
        ("Amazon EC2 (IaaS)", "Hosts the high-concurrency FastAPI REST API server and runs the continuous SQS background worker daemon using Python virtual environments and systemd unit supervision."),
        ("AWS Lambda (Serverless)", "Provides event-driven computing triggered immediately upon S3 ObjectCreated events, performing sub-second page triage and fast-track processing without provisioning infrastructure."),
        ("Amazon S3 (Storage Lake)", "Acts as the centralized document lake, storing all raw PDF/image files with isolated unique UUID keys. Configured with CORS rules for browser pre-signed direct uploads."),
        ("Amazon DynamoDB (Database)", "High-performance NoSQL database storing structured financial records, extracted vendor line-items, and audit outcomes using On-Demand Pay-Per-Request pricing."),
        ("Amazon SQS (Decoupling Queue)", "Distributed message queue buffering multi-page processing tasks. Employs 300-second visibility timeouts to decouple burst ingestion from asynchronous processing capacity."),
        ("Amazon Textract (ML / OCR)", "Machine learning service utilized to extract raw text, form fields, and itemized invoice receipt tables directly from S3 object bytes without custom models."),
        ("Amazon Bedrock (GenAI)", "Generative AI runtime integrating Claude 3 Haiku for complex expenditure categorization, natural language summaries, and corporate policy compliance auditing."),
        ("Amazon SES (Email Service)", "Transactional email delivery service generating formatted HTML processing reports, spending summaries, and critical compliance alerts for finance teams."),
        ("VPC & Security Groups (Networking)", "Configured with public/private network segmentation, restricting ingress to HTTP/port 8000 while maintaining secure egress for Boto3 API communication."),
        ("Amazon CloudWatch (Observability)", "Aggregates application logs, Lambda invocation metrics, SQS queue depth graphs, and system errors for unified operational observability.")
    ]

    y_pos = 70
    for name, desc in services_data:
        p2.draw_rect(pymupdf.Rect(40, y_pos, 555, y_pos + 62), color=CARD_BORDER, fill=CARD_BG)
        p2.insert_text((52, y_pos + 16), name, fontsize=10, fontname="helv", color=PRIMARY_COLOR)
        p2.insert_textbox(pymupdf.Rect(52, y_pos + 22, 545, y_pos + 58), desc, fontsize=8.2, fontname="helv", color=TEXT_COLOR)
        y_pos += 69

    # =========================================================================
    # PAGE 3: TECHNICAL INNOVATIONS & ARCHITECTURAL PATTERNS
    # =========================================================================
    p3 = doc.new_page(width=595, height=842)
    add_page_decorations(p3, 3)

    p3.insert_text((40, 50), "4. KEY TECHNICAL INNOVATIONS & ARCHITECTURAL PATTERNS", fontsize=14, fontname="helv", color=PRIMARY_COLOR)
    p3.draw_line((40, 55), (555, 55), color=PRIMARY_COLOR, width=1.2)

    innovations = [
        ("Asynchronous Queue-Based Decoupling Pattern", 
         "Synchronous web requests that process 10-20 page PDFs often crash due to client-side HTTP timeouts "
         "or AWS Lambda's 15-minute runtime ceiling. DocuCloud AI solves this by acknowledging uploads "
         "instantly (returning status ROUTED_TO_EC2_WORKER) and passing the job payload to an Amazon SQS queue. "
         "An independent EC2 daemon long-polls the queue, processes documents at its own pace, and deletes "
         "the SQS message only after successful persistence in DynamoDB."),
        
        ("Resilient Zero-Downtime Fallback Pipeline",
         "When AWS accounts are newly provisioned, enterprise AI services like Amazon Textract may experience "
         "subscription activation delays (SubscriptionRequiredException). Instead of throwing 500 errors, "
         "the DocuCloud backend implements an automatic fallback engine: it dynamically downloads the S3 "
         "bytes into memory and performs heuristic PDF extraction and regex parsing. When Textract finishes "
         "subscribing, the platform automatically upgrades to full Textract OCR without code changes."),

        ("Type-Safe DynamoDB Serialization (Float-to-Decimal)",
         "Amazon DynamoDB natively rejects standard Python float types to avoid precision errors in financial "
         "ledgers. DocuCloud AI implements recursive type-safe converters (_to_dynamo_safe and _from_dynamo_safe) "
         "that seamlessly convert floats to Python Decimal types before writes and restore floats for "
         "high-performance JSON serialization on API read operations."),

        ("IAM Role-Based Credential Isolation (Zero Hardcoded Secrets)",
         "Rather than embedding long-lived AWS Access Keys into EC2 configuration files, the EC2 instance "
         "authenticates via an attached IAM Instance Profile (DocuCloud-EC2-Role). Boto3 retrieves short-lived "
         "rotating credentials via the EC2 Instance Metadata Service (IMDSv2), adhering to AWS Well-Architected "
         "Security Pillar standards.")
    ]

    y_pos = 75
    for title, desc in innovations:
        p3.draw_rect(pymupdf.Rect(40, y_pos, 555, y_pos + 125), color=CARD_BORDER, fill=CARD_BG)
        p3.insert_text((52, y_pos + 20), title, fontsize=11, fontname="helv", color=PRIMARY_COLOR)
        p3.insert_textbox(pymupdf.Rect(52, y_pos + 30, 545, y_pos + 120), desc, fontsize=8.8, fontname="helv", color=TEXT_COLOR)
        y_pos += 135

    # =========================================================================
    # PAGE 4: INTERVIEW MASTER GUIDE & RESUME TALKING POINTS
    # =========================================================================
    p4 = doc.new_page(width=595, height=842)
    add_page_decorations(p4, 4)

    p4.insert_text((40, 50), "5. RESUME BULLETS & INTERVIEW TALKING POINTS", fontsize=14, fontname="helv", color=PRIMARY_COLOR)
    p4.draw_line((40, 55), (555, 55), color=PRIMARY_COLOR, width=1.2)

    p4.insert_text((40, 75), "Resume Ready Bullets (Copy directly into your CV):", fontsize=10.5, fontname="helv", color=PRIMARY_COLOR)
    
    bullets = [
        "Architected an end-to-end hybrid cloud document processing system on AWS combining IaaS (EC2) and Serverless (Lambda) to ingest, audit, and extract financial receipt line-items.",
        "Implemented an asynchronous SQS messaging pipeline with dedicated EC2 worker daemons to handle heavy, multi-page document parsing, eliminating runtime timeout bottlenecks.",
        "Engineered an automated S3-triggered event pipeline that triages incoming documents in sub-seconds and persists structured audit records in Amazon DynamoDB.",
        "Developed a policy-compliance AI auditor that detects anomalous expenditures (> $500, unverified vendors) and automatically categorizes transactions across financial tax tiers.",
        "Configured secure AWS networking with custom Security Groups, IAM Role instance profiles, and CORS-enabled pre-signed S3 upload channels."
    ]

    y_b = 95
    for b in bullets:
        p4.insert_text((45, y_b), "•", fontsize=11, color=PRIMARY_COLOR)
        p4.insert_textbox(pymupdf.Rect(58, y_b - 10, 550, y_b + 30), b, fontsize=8.5, fontname="helv", color=TEXT_COLOR)
        y_b += 35

    p4.insert_text((40, 280), "Top 3 Interview Questions & Model Answers:", fontsize=11, fontname="helv", color=PRIMARY_COLOR)
    p4.draw_line((40, 285), (555, 285), color=CARD_BORDER, width=1)

    qa_list = [
        ("Q: Why did you use both Amazon EC2 and AWS Lambda instead of just Lambda?",
         "A: AWS Lambda is optimal for lightweight, bursty tasks, but enforces a strict 15-minute runtime ceiling and memory limits. For 50-100 page enterprise contracts, parsing OCR and chunking text can exceed Lambda limits. Using a hybrid architecture allows lightweight receipts (<= 5 pages) to run fast-path on Lambda, while offloading heavy documents to an SQS queue consumed by an EC2 worker."),
        
        ("Q: How does Amazon SQS prevent message duplication and loss?",
         "A: We utilize SQS with a 300-second visibility timeout. When an EC2 worker pulls a task, the message becomes invisible to other workers while processing. The worker only issues an explicit delete_message call after DynamoDB persistence succeeds. If the worker crashes, the message reappears for retry."),
        
        ("Q: How did you ensure data consistency in DynamoDB without fixed schemas?",
         "A: We leveraged DynamoDB's NoSQL flexibility with a single-table design partitioned by document_id. We enforced runtime validation using Pydantic schemas in Python before writes, and applied recursive float-to-Decimal converters to ensure precision financial consistency.")
    ]

    y_qa = 300
    for q, a in qa_list:
        p4.draw_rect(pymupdf.Rect(40, y_qa, 555, y_qa + 105), color=CARD_BORDER, fill=CARD_BG)
        p4.insert_text((50, y_qa + 15), q, fontsize=9, fontname="helv", color=PRIMARY_COLOR)
        p4.insert_textbox(pymupdf.Rect(50, y_qa + 25, 545, y_qa + 100), a, fontsize=8, fontname="helv", color=TEXT_COLOR)
        y_qa += 115

    # =========================================================================
    # PAGE 5: DEPLOYMENT VERIFICATION & RUNBOOK
    # =========================================================================
    p5 = doc.new_page(width=595, height=842)
    add_page_decorations(p5, 5)

    p5.insert_text((40, 50), "6. SYSTEM VERIFICATION & RUNBOOK", fontsize=14, fontname="helv", color=PRIMARY_COLOR)
    p5.draw_line((40, 55), (555, 55), color=PRIMARY_COLOR, width=1.2)

    p5.insert_text((40, 75), "Local vs. Cloud Production Architecture:", fontsize=10.5, fontname="helv", color=PRIMARY_COLOR)

    p5.draw_rect(pymupdf.Rect(40, 95, 290, 240), color=CARD_BORDER, fill=CARD_BG)
    p5.insert_text((50, 115), "LOCAL DEVELOPMENT ENVIRONMENT", fontsize=10, fontname="helv", color=PRIMARY_COLOR)
    p5.insert_textbox(pymupdf.Rect(50, 125, 280, 230),
        "• URL: http://localhost:8000/dashboard\n"
        "• Process 1: uvicorn backend.app.main:app\n"
        "• Process 2: python -m backend.worker\n"
        "• Config: Loaded via local .env file\n"
        "• Storage: Direct Boto3 calls to AWS S3 & DynamoDB\n"
        "• Purpose: Rapid testing, feature iteration & debugging",
        fontsize=8.5, fontname="helv", color=TEXT_COLOR)

    p5.draw_rect(pymupdf.Rect(305, 95, 555, 240), color=CARD_BORDER, fill=CARD_BG)
    p5.insert_text((315, 115), "AMAZON EC2 PRODUCTION ENVIRONMENT", fontsize=10, fontname="helv", color=ACCENT_GREEN)
    p5.insert_textbox(pymupdf.Rect(315, 125, 545, 230),
        "• Public IP: http://13.217.196.74:8000/dashboard\n"
        "• Instance Type: t2.micro (Amazon Linux 2023)\n"
        "• Security: IAM Instance Profile (DocuCloud-EC2-Role)\n"
        "• Networking: Security Group allowing TCP 8000 / 80\n"
        "• Process Mgmt: Systemd / nohup background daemons\n"
        "• Availability: 24/7 public access on AWS infrastructure",
        fontsize=8.5, fontname="helv", color=TEXT_COLOR)

    p5.insert_text((40, 265), "Comprehensive Test Document Reference:", fontsize=10.5, fontname="helv", color=PRIMARY_COLOR)

    test_docs = [
        ("01_starbucks_meals_receipt.pdf", "1 Page", "$16.00", "Meals & Entertainment", "Fast-path sync execution"),
        ("02_delta_travel_ticket.pdf", "1 Page", "$482.50", "Travel & Lodging", "Tax deductible travel verification"),
        ("03_staples_office_supplies.pdf", "1 Page", "$66.69", "Office Supplies", "Itemized stationery parsing"),
        ("04_high_value_anomaly_alert.pdf", "1 Page", "$3,450.00", "Luxury Goods", "Triggers Policy Anomaly Alert (> $500)"),
        ("05_heavy_7_page_contract.pdf", "7 Pages", "$8,750.00", "Datacenter Lease", "Triggers SQS Queue + EC2 Worker")
    ]

    # Table Header
    y_t = 285
    p5.draw_rect(pymupdf.Rect(40, y_t, 555, y_t + 22), color=PRIMARY_COLOR, fill=PRIMARY_COLOR)
    p5.insert_text((45, y_t + 14), "Filename", fontsize=8, fontname="helv", color=(1, 1, 1))
    p5.insert_text((220, y_t + 14), "Pages", fontsize=8, fontname="helv", color=(1, 1, 1))
    p5.insert_text((265, y_t + 14), "Amount", fontsize=8, fontname="helv", color=(1, 1, 1))
    p5.insert_text((320, y_t + 14), "Category", fontsize=8, fontname="helv", color=(1, 1, 1))
    p5.insert_text((425, y_t + 14), "Test Scenario", fontsize=8, fontname="helv", color=(1, 1, 1))

    y_t += 22
    for fn, pgs, amt, cat, scn in test_docs:
        p5.draw_rect(pymupdf.Rect(40, y_t, 555, y_t + 20), color=CARD_BORDER, fill=CARD_BG)
        p5.insert_text((45, y_t + 13), fn, fontsize=7.5, fontname="helv", color=PRIMARY_COLOR)
        p5.insert_text((220, y_t + 13), pgs, fontsize=7.5, color=TEXT_COLOR)
        p5.insert_text((265, y_t + 13), amt, fontsize=7.5, fontname="helv", color=ACCENT_GREEN)
        p5.insert_text((320, y_t + 13), cat, fontsize=7.5, color=TEXT_COLOR)
        p5.insert_text((425, y_t + 13), scn, fontsize=7.5, color=SECONDARY_COLOR)
        y_t += 20

    # Project Summary Sign-Off Box
    p5.draw_rect(pymupdf.Rect(40, 415, 555, 520), color=CARD_BORDER, fill=CARD_BG)
    p5.insert_text((55, 435), "PROJECT COMPLETION VERIFICATION", fontsize=11, fontname="helv", color=PRIMARY_COLOR)
    p5.insert_textbox(pymupdf.Rect(55, 445, 540, 510),
        "This project successfully proves advanced competency across core AWS infrastructure domains: "
        "Compute (EC2, Lambda), Storage (S3), NoSQL Databases (DynamoDB), Message Queuing (SQS), "
        "Machine Learning (Textract), Networking (VPC, Security Groups), and Observability (CloudWatch). "
        "The architecture adheres strictly to AWS Well-Architected Framework principles of reliability, "
        "security, and cost optimization.",
        fontsize=8.5, fontname="helv", color=TEXT_COLOR)

    doc.save(OUTPUT_PDF)
    doc.close()
    print(f"Successfully generated {OUTPUT_PDF}!")

if __name__ == "__main__":
    create_documentation_pdf()
