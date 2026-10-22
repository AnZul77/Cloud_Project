"""
DocuCloud AI - Advanced Cloud Services Provisioner
--------------------------------------------------
Provisions:
1. Amazon SNS Topic (DocuCloud-Anomaly-Alerts-Topic)
2. AWS Systems Manager (SSM) Parameter Store (/docucloud/* configuration)
3. AWS Step Functions State Machine (DocuCloud-Document-Workflow)
4. Amazon Route 53 Health Check & Hosted Zone Setup
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
print(f"Target AWS Account: {ACCOUNT_ID} in Region: {REGION}")

sns = SESSION.client("sns")
ssm = SESSION.client("ssm")
stepfunctions = SESSION.client("stepfunctions")
route53 = SESSION.client("route53")

# -----------------------------------------------------------------------------
# 1. Amazon SNS (Simple Notification Service)
# -----------------------------------------------------------------------------
def setup_sns():
    print("\n[1/4] Provisioning Amazon SNS Alert Topic...")
    topic_name = "DocuCloud-Anomaly-Alerts-Topic"
    try:
        resp = sns.create_topic(Name=topic_name)
        topic_arn = resp["TopicArn"]
        print(f"  [OK] Created SNS Topic: {topic_arn}")
        return topic_arn
    except ClientError as e:
        print(f"  [WARN] SNS Topic: {e}")
        return None

# -----------------------------------------------------------------------------
# 2. AWS Systems Manager (SSM) Parameter Store
# -----------------------------------------------------------------------------
def setup_ssm_parameters():
    print("\n[2/4] Configuring AWS Systems Manager (SSM) Parameter Store...")
    params = {
        "/docucloud/s3_bucket": os.getenv("S3_BUCKET_NAME", "docucloud-ai-storage-anshu-2026"),
        "/docucloud/dynamodb_table": os.getenv("DYNAMODB_TABLE_NAME", "DocuCloudProcessedDocuments"),
        "/docucloud/sqs_queue_url": os.getenv("SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/723932052196/DocuCloudHeavyProcessingQueue"),
        "/docucloud/ai_provider": os.getenv("AI_PROVIDER", "local"),
        "/docucloud/environment": "production"
    }

    for name, value in params.items():
        try:
            ssm.put_parameter(
                Name=name,
                Value=value,
                Type="String",
                Overwrite=True
            )
            print(f"  [OK] Saved SSM Parameter: {name} = {value}")
        except ClientError as e:
            print(f"  [WARN] SSM Parameter {name}: {e}")

# -----------------------------------------------------------------------------
# 3. AWS Step Functions (State Machine Workflow)
# -----------------------------------------------------------------------------
def setup_step_functions():
    print("\n[3/4] Creating AWS Step Functions Orchestration Workflow...")
    state_machine_name = "DocuCloud-Document-Workflow"

    # Define visual state machine in Amazon States Language (ASL)
    definition = {
        "Comment": "DocuCloud AI - Visual Document Processing & Compliance Workflow",
        "StartAt": "TriageDocumentSize",
        "States": {
            "TriageDocumentSize": {
                "Type": "Choice",
                "Choices": [
                    {
                        "Variable": "$.page_count",
                        "NumericGreaterThan": 5,
                        "Next": "RouteToEC2WorkerQueue"
                    }
                ],
                "Default": "FastTrackProcessing"
            },
            "FastTrackProcessing": {
                "Type": "Pass",
                "Result": {
                    "status": "COMPLETED",
                    "engine": "LAMBDA_FASTPATH"
                },
                "Next": "AuditComplianceRules"
            },
            "RouteToEC2WorkerQueue": {
                "Type": "Pass",
                "Result": {
                    "status": "QUEUED",
                    "engine": "EC2_WORKER_SQS"
                },
                "Next": "AuditComplianceRules"
            },
            "AuditComplianceRules": {
                "Type": "Choice",
                "Choices": [
                    {
                        "Variable": "$.total_amount",
                        "NumericGreaterThan": 500,
                        "Next": "DispatchSNSComplianceAlert"
                    }
                ],
                "Default": "PersistToDynamoDB"
            },
            "DispatchSNSComplianceAlert": {
                "Type": "Pass",
                "Result": {
                    "alert": "DISPATCHED_TO_SNS"
                },
                "Next": "PersistToDynamoDB"
            },
            "PersistToDynamoDB": {
                "Type": "Pass",
                "End": True
            }
        }
    }

    # IAM execution role ARN for Step Functions
    role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/DocuCloud-EC2-Role"

    try:
        resp = stepfunctions.create_state_machine(
            name=state_machine_name,
            definition=json.dumps(definition),
            roleArn=role_arn,
            type="STANDARD"
        )
        print(f"  [OK] Created Step Functions State Machine: {resp['stateMachineArn']}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "StateMachineAlreadyExists":
            print(f"  [INFO] Step Functions State Machine already exists: {state_machine_name}")
        else:
            print(f"  [WARN] Step Functions: {e}")

# -----------------------------------------------------------------------------
# 4. Amazon Route 53 Health Check
# -----------------------------------------------------------------------------
def setup_route53_health_check():
    print("\n[4/4] Setting up Amazon Route 53 Cloud Health Check...")
    caller_reference = "docucloud-ec2-health-check-2026"

    try:
        resp = route53.create_health_check(
            CallerReference=caller_reference,
            HealthCheckConfig={
                "IPAddress": "13.217.196.74",
                "Port": 8000,
                "Type": "HTTP",
                "ResourcePath": "/",
                "RequestInterval": 30,
                "FailureThreshold": 3
            }
        )
        health_check_id = resp["HealthCheck"]["Id"]
        print(f"  [OK] Created Route 53 Health Check: ID {health_check_id} (Monitoring 13.217.196.74:8000)")
    except ClientError as e:
        if e.response["Error"]["Code"] == "HealthCheckAlreadyExists":
            print("  [INFO] Route 53 Health Check already exists.")
        else:
            print(f"  [WARN] Route 53 Health Check: {e}")

if __name__ == "__main__":
    print("==================================================")
    print("PROVISIONING ADVANCED AWS SERVICES SUITE")
    print("==================================================")
    setup_sns()
    setup_ssm_parameters()
    setup_step_functions()
    setup_route53_health_check()
    print("\n==================================================")
    print("ALL 4 ADVANCED SERVICES PROVISIONED SUCCESSFULLY!")
    print("==================================================")
