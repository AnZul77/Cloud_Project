"""
DocuCloud AI - Enterprise Observability & Governance Provisioner
---------------------------------------------------------------
Provisions and links:
1. CloudWatch Log Groups (/aws/docucloud/backend, /aws/lambda/DocuCloud-S3-Triage)
2. CloudWatch Custom Unified Dashboard (DocuCloud-Executive-Dashboard)
3. CloudWatch Alarms (SQS Queue Backlog & High CPU)
4. AWS CloudTrail (Multi-region management audit logging to S3)
"""

import json
import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("AWS_REGION", "us-east-1")
SESSION = boto3.Session(
    region_name=REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

sts = SESSION.client("sts")
ACCOUNT_ID = sts.get_caller_identity()["Account"]
print(f"Target AWS Account ID: {ACCOUNT_ID} in Region: {REGION}")

cw_logs = SESSION.client("logs")
cloudwatch = SESSION.client("cloudwatch")
cloudtrail = SESSION.client("cloudtrail")
s3 = SESSION.client("s3")

# -----------------------------------------------------------------------------
# 1. CloudWatch Log Groups
# -----------------------------------------------------------------------------
def setup_log_groups():
    print("\n[1/4] Setting up CloudWatch Log Groups...")
    log_groups = [
        "/aws/docucloud/backend",
        "/aws/lambda/DocuCloud-S3-Triage"
    ]
    for lg in log_groups:
        try:
            cw_logs.create_log_group(logGroupName=lg)
            cw_logs.put_retention_policy(logGroupName=lg, retentionInDays=14)
            print(f"  [OK] Created log group: {lg} (Retention: 14 days)")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceAlreadyExistsException":
                cw_logs.put_retention_policy(logGroupName=lg, retentionInDays=14)
                print(f"  [INFO] Log group already exists: {lg}")
            else:
                print(f"  [WARN] {lg}: {e}")

# -----------------------------------------------------------------------------
# 2. CloudWatch Unified Metrics Dashboard
# -----------------------------------------------------------------------------
def setup_dashboard():
    print("\n[2/4] Creating CloudWatch Unified Executive Dashboard...")
    dashboard_name = "DocuCloud-Executive-Dashboard"

    dashboard_body = {
        "widgets": [
            {
                "type": "text",
                "x": 0, "y": 0, "width": 24, "height": 2,
                "properties": {
                    "markdown": "# 🚀 DocuCloud AI — Live Observability & Cloud Operations Dashboard\nUnified telemetry across Amazon EC2, AWS Lambda, Amazon DynamoDB, Amazon SQS, and Amazon S3."
                }
            },
            {
                "type": "metric",
                "x": 0, "y": 2, "width": 12, "height": 6,
                "properties": {
                    "title": "Amazon DynamoDB — Consumed Read & Write Units",
                    "metrics": [
                        ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", "DocuCloudProcessedDocuments", {"stat": "Sum", "period": 60, "color": "#0073bb"}],
                        [".", "ConsumedWriteCapacityUnits", ".", ".", {"stat": "Sum", "period": 60, "color": "#2ca02c"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION
                }
            },
            {
                "type": "metric",
                "x": 12, "y": 2, "width": 12, "height": 6,
                "properties": {
                    "title": "Amazon SQS — Queue Backlog & In-Flight Messages",
                    "metrics": [
                        ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", "DocuCloudHeavyProcessingQueue", {"stat": "Maximum", "period": 60, "color": "#ff7f0e"}],
                        [".", "NumberOfMessagesReceived", ".", ".", {"stat": "Sum", "period": 60, "color": "#1f77b4"}],
                        [".", "NumberOfMessagesDeleted", ".", ".", {"stat": "Sum", "period": 60, "color": "#2ca02c"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION
                }
            },
            {
                "type": "metric",
                "x": 0, "y": 8, "width": 12, "height": 6,
                "properties": {
                    "title": "AWS Lambda (DocuCloud-S3-Triage) — Invocations & Errors",
                    "metrics": [
                        ["AWS/Lambda", "Invocations", "FunctionName", "DocuCloud-S3-Triage", {"stat": "Sum", "period": 60, "color": "#2ca02c"}],
                        [".", "Errors", ".", ".", {"stat": "Sum", "period": 60, "color": "#d62728"}],
                        [".", "Duration", ".", ".", {"stat": "Average", "period": 60, "color": "#9467bd", "yAxis": "right"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION
                }
            },
            {
                "type": "metric",
                "x": 12, "y": 8, "width": 12, "height": 6,
                "properties": {
                    "title": "Amazon EC2 — CPU & Network Throughput",
                    "metrics": [
                        ["AWS/EC2", "CPUUtilization", {"stat": "Average", "period": 300, "color": "#d62728"}],
                        [".", "NetworkIn", {"stat": "Sum", "period": 300, "color": "#17becf", "yAxis": "right"}],
                        [".", "NetworkOut", {"stat": "Sum", "period": 300, "color": "#bcbd22", "yAxis": "right"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": REGION
                }
            }
        ]
    }

    try:
        cloudwatch.put_dashboard(
            DashboardName=dashboard_name,
            DashboardBody=json.dumps(dashboard_body)
        )
        print(f"  [OK] Created/Updated CloudWatch Dashboard: {dashboard_name}")
    except ClientError as e:
        print(f"  [WARN] Dashboard creation: {e}")

# -----------------------------------------------------------------------------
# 3. CloudWatch Alarms
# -----------------------------------------------------------------------------
def setup_alarms():
    print("\n[3/4] Creating CloudWatch Proactive Alarms...")
    try:
        # SQS Backlog Alarm
        cloudwatch.put_metric_alarm(
            AlarmName="DocuCloud-SQS-High-Backlog-Alarm",
            ComparisonOperator="GreaterThanThreshold",
            EvaluationPeriods=1,
            MetricName="ApproximateNumberOfMessagesVisible",
            Namespace="AWS/SQS",
            Period=60,
            Statistic="Maximum",
            Threshold=10.0,
            ActionsEnabled=False,
            AlarmDescription="Alerts if SQS queue has more than 10 documents waiting for EC2 worker processing.",
            Dimensions=[{"Name": "QueueName", "Value": "DocuCloudHeavyProcessingQueue"}]
        )
        print("  [OK] Alarm created: DocuCloud-SQS-High-Backlog-Alarm (> 10 messages)")

        # Lambda Error Alarm
        cloudwatch.put_metric_alarm(
            AlarmName="DocuCloud-Lambda-Errors-Alarm",
            ComparisonOperator="GreaterThanThreshold",
            EvaluationPeriods=1,
            MetricName="Errors",
            Namespace="AWS/Lambda",
            Period=60,
            Statistic="Sum",
            Threshold=1.0,
            ActionsEnabled=False,
            AlarmDescription="Alerts if AWS Lambda triage router encounters any unhandled exceptions.",
            Dimensions=[{"Name": "FunctionName", "Value": "DocuCloud-S3-Triage"}]
        )
        print("  [OK] Alarm created: DocuCloud-Lambda-Errors-Alarm (> 0 errors)")
    except ClientError as e:
        print(f"  [WARN] Alarms: {e}")

# -----------------------------------------------------------------------------
# 4. AWS CloudTrail (Governance & Compliance Audit)
# -----------------------------------------------------------------------------
def setup_cloudtrail():
    print("\n[4/4] Setting up AWS CloudTrail Audit Trail...")
    trail_name = "DocuCloud-Audit-Trail"
    bucket_name = f"docucloud-audit-trail-{ACCOUNT_ID}"

    # Step A: Create dedicated secure bucket for CloudTrail logs
    print(f"  Creating S3 bucket for audit logs: {bucket_name}...")
    try:
        if REGION == "us-east-1":
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": REGION}
            )
        print(f"  [OK] Created CloudTrail S3 bucket: {bucket_name}")
    except ClientError as e:
        if e.response["Error"]["Code"] in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            print(f"  [INFO] CloudTrail S3 bucket already exists: {bucket_name}")
        else:
            print(f"  [WARN] CloudTrail bucket creation: {e}")
            return

    # Step B: Attach required CloudTrail S3 bucket policy
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AWSCloudTrailAclCheck",
                "Effect": "Allow",
                "Principal": {"Service": "cloudtrail.amazonaws.com"},
                "Action": "s3:GetBucketAcl",
                "Resource": f"arn:aws:s3:::{bucket_name}"
            },
            {
                "Sid": "AWSCloudTrailWrite",
                "Effect": "Allow",
                "Principal": {"Service": "cloudtrail.amazonaws.com"},
                "Action": "s3:PutObject",
                "Resource": f"arn:aws:s3:::{bucket_name}/AWSLogs/{ACCOUNT_ID}/*",
                "Condition": {
                    "StringEquals": {
                        "s3:x-amz-acl": "bucket-owner-full-control"
                    }
                }
            }
        ]
    }

    try:
        s3.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))
        print("  [OK] Applied CloudTrail S3 bucket permissions policy.")
    except ClientError as e:
        print(f"  [WARN] Applying bucket policy: {e}")

    # Step C: Create and start the trail
    try:
        cloudtrail.create_trail(
            Name=trail_name,
            S3BucketName=bucket_name,
            IncludeGlobalServiceEvents=True,
            IsMultiRegionTrail=True,
            EnableLogFileValidation=True
        )
        print(f"  [OK] Created CloudTrail trail: {trail_name}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "TrailAlreadyExistsException":
            print(f"  [INFO] CloudTrail trail already exists: {trail_name}")
        else:
            print(f"  [WARN] Creating trail: {e}")

    try:
        cloudtrail.start_logging(Name=trail_name)
        print(f"  [OK] Started continuous audit logging on {trail_name}!")
    except ClientError as e:
        print(f"  [WARN] Starting logging: {e}")

if __name__ == "__main__":
    print("==================================================")
    print("PROVISIONING ENTERPRISE OBSERVABILITY & GOVERNANCE")
    print("==================================================")
    setup_log_groups()
    setup_dashboard()
    setup_alarms()
    setup_cloudtrail()
    print("\n==================================================")
    print("OBSERVABILITY STACK READY!")
    print("1. CloudWatch Dashboard: 'DocuCloud-Executive-Dashboard'")
    print("2. CloudWatch Log Group: '/aws/docucloud/backend'")
    print("3. CloudTrail Trail:     'DocuCloud-Audit-Trail'")
    print("==================================================")
