#!/bin/bash
# ==============================================================================
# DocuCloud AI - EC2 Bootstrap User Data Script (Amazon Linux 2023 / Ubuntu)
# ==============================================================================
set -e

echo "Starting DocuCloud EC2 Provisioning..."

# 1. Update OS and install runtime packages
if command -v dnf &> /dev/null; then
    dnf update -y
    dnf install -y python3.11 python3.11-pip git nginx
elif command -v apt-get &> /dev/null; then
    apt-get update -y
    apt-get install -y python3 python3-pip python3-venv git nginx
fi

# 2. Setup Application Directory
APP_DIR="/opt/docucloud"
mkdir -p $APP_DIR
cd $APP_DIR

# 3. Create Virtualenv
python3 -m venv venv
source venv/bin/activate

# 4. Install backend requirements
cat << 'EOF' > requirements.txt
fastapi>=0.110.0
uvicorn[standard]>=0.28.0
pydantic>=2.6.0
pydantic-settings>=2.2.0
boto3>=1.34.0
python-multipart>=0.0.9
python-dotenv>=1.0.1
pypdf>=4.1.0
requests>=2.31.0
EOF

pip install --upgrade pip
pip install -r requirements.txt

# 5. Setup Systemd Service for FastAPI API Server
cat << EOF > /etc/systemd/system/docucloud-api.service
[Unit]
Description=DocuCloud FastAPI Backend Service
After=network.target

[Service]
User=root
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
EnvironmentFile=$APP_DIR/.env

[Install]
WantedBy=multi-user.target
EOF

# 6. Setup Systemd Service for EC2 Heavy Worker Daemon
cat << EOF > /etc/systemd/system/docucloud-worker.service
[Unit]
Description=DocuCloud EC2 Heavy Worker SQS Daemon
After=network.target

[Service]
User=root
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/python -m backend.worker
Restart=always
RestartSec=10
EnvironmentFile=$APP_DIR/.env

[Install]
WantedBy=multi-user.target
EOF

# 7. Reload systemd and enable services
systemctl daemon-reload
systemctl enable docucloud-api
systemctl enable docucloud-worker

echo "EC2 bootstrap complete. Place your code and .env in $APP_DIR, then start services with: systemctl start docucloud-api docucloud-worker"
