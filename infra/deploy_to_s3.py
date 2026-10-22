"""
DocuCloud AI - Package & Deploy to S3
-------------------------------------
Packages the local application code (backend, static UI, configs) into app.zip
and uploads it to the project S3 bucket for instant EC2 bootstrap.
"""

import os
import zipfile
import boto3
from dotenv import load_dotenv

load_dotenv()

BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "docucloud-ai-storage-anshu-2026")
REGION = os.getenv("AWS_REGION", "us-east-1")
ZIP_NAME = "app.zip"
S3_KEY = "deploy/app.zip"

def create_bundle():
    print(f"Bundling application code into {ZIP_NAME}...")
    with zipfile.ZipFile(ZIP_NAME, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add backend
        for root, dirs, files in os.walk("backend"):
            for file in files:
                if "__pycache__" not in root and not file.endswith(".pyc"):
                    filepath = os.path.join(root, file)
                    arcname = os.path.relpath(filepath, ".")
                    zipf.write(filepath, arcname)

        # Add tests
        for root, dirs, files in os.walk("tests"):
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, ".")
                zipf.write(filepath, arcname)

        # Add .env
        if os.path.exists(".env"):
            zipf.write(".env", ".env")

    print(f"[OK] Created {ZIP_NAME} ({os.path.getsize(ZIP_NAME) / 1024:.1f} KB)")

def upload_to_s3():
    print(f"Uploading {ZIP_NAME} to s3://{BUCKET_NAME}/{S3_KEY}...")
    session = boto3.Session(region_name=REGION)
    s3 = session.client("s3")
    s3.upload_file(ZIP_NAME, BUCKET_NAME, S3_KEY)
    print(f"[OK] Successfully uploaded deployment bundle to s3://{BUCKET_NAME}/{S3_KEY}!")
    
    # Cleanup local zip
    if os.path.exists(ZIP_NAME):
        os.remove(ZIP_NAME)

if __name__ == "__main__":
    create_bundle()
    upload_to_s3()
