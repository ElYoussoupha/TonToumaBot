#!/bin/bash
# ==============================================================================
# TonToumaBot VPS Deployment Script
# Target: Ubuntu 25.04 (fresh install)
# Run as: ubuntu user with sudo privileges
# ==============================================================================

set -e

echo "=============================================="
echo "   TonToumaBot VPS Deployment"
echo "=============================================="

# --- Configuration ---
PROJECT_NAME="tontouma"
PROJECT_DIR="/opt/tontouma"
BACKEND_PORT=9000
FRONTEND_PORT=3000
POSTGRES_DB="tontouma"
POSTGRES_USER="tontouma"
POSTGRES_PASSWORD="CHANGE_THIS_PASSWORD"  # <-- CHANGE THIS!
MINIO_ROOT_USER="minioadmin"
MINIO_ROOT_PASSWORD="minioadmin"
MINIO_PORT=9100
DOMAIN="51.210.245.250"  # or your domain name

# --- 1. System Update & Dependencies ---
echo "[1/8] Installing system dependencies..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    python3.12 python3.12-venv python3-pip \
    postgresql postgresql-contrib \
    nginx \
    git curl wget \
    build-essential libpq-dev \
    ffmpeg  # For audio processing

# --- 2. Node.js 20 LTS ---
echo "[2/8] Installing Node.js 20..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node --version
npm --version

# --- 3. PostgreSQL + pgvector ---
echo "[3/8] Configuring PostgreSQL..."
sudo -u postgres psql <<EOF
CREATE USER ${POSTGRES_USER} WITH PASSWORD '${POSTGRES_PASSWORD}';
CREATE DATABASE ${POSTGRES_DB} OWNER ${POSTGRES_USER};
\c ${POSTGRES_DB}
CREATE EXTENSION IF NOT EXISTS vector;
EOF

# --- 4. MinIO (Object Storage) ---
echo "[4/8] Installing MinIO..."
if ! command -v minio &> /dev/null; then
    wget https://dl.min.io/server/minio/release/linux-amd64/minio
    chmod +x minio
    sudo mv minio /usr/local/bin/
fi

# Create MinIO data directory
sudo mkdir -p /data/minio
sudo chown ubuntu:ubuntu /data/minio

# Create MinIO systemd service
sudo tee /etc/systemd/system/minio.service > /dev/null <<EOF
[Unit]
Description=MinIO Object Storage
After=network.target

[Service]
User=ubuntu
Group=ubuntu
Environment="MINIO_ROOT_USER=${MINIO_ROOT_USER}"
Environment="MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}"
ExecStart=/usr/local/bin/minio server /data/minio --address ":${MINIO_PORT}"
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable minio
sudo systemctl start minio

# --- 5. Clone/Copy Project ---
echo "[5/8] Setting up project directory..."
sudo mkdir -p ${PROJECT_DIR}
sudo chown ubuntu:ubuntu ${PROJECT_DIR}

# If project not yet copied, show instructions
if [ ! -d "${PROJECT_DIR}/app" ]; then
    echo "======================================================"
    echo "Please copy project files to ${PROJECT_DIR}"
    echo "From your local machine:"
    echo "  scp -r ./* ubuntu@${DOMAIN}:${PROJECT_DIR}/"
    echo "======================================================"
    # For now, assume files are already there or will be copied
fi

# --- 6. Backend Setup ---
echo "[6/8] Setting up Backend (FastAPI)..."
cd ${PROJECT_DIR}

# Create Python virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install httpx librosa imageio-ffmpeg  # Additional deps

# Create .env file
cat > .env <<EOF
# Database
POSTGRES_SERVER=localhost
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_PORT=5432

# OpenAI
OPENAI_API_KEY=YOUR_OPENAI_API_KEY_HERE

# MinIO
MINIO_ENDPOINT=localhost:${MINIO_PORT}
MINIO_ACCESS_KEY=${MINIO_ROOT_USER}
MINIO_SECRET_KEY=${MINIO_ROOT_PASSWORD}
MINIO_BUCKET=tontouma-knowledge
MINIO_SECURE=false

# LAfricaMobile (Wolof TTS/STT)
LAFRICAMOBILE_USERNAME=YOUR_USERNAME
LAFRICAMOBILE_PASSWORD=YOUR_PASSWORD
EOF

echo ">>> IMPORTANT: Edit ${PROJECT_DIR}/.env with your API keys!"

# Run database migrations
alembic upgrade head

# Create uploads directory
mkdir -p uploads

# Create Backend systemd service
sudo tee /etc/systemd/system/tontouma-backend.service > /dev/null <<EOF
[Unit]
Description=TonToumaBot Backend (FastAPI)
After=network.target postgresql.service minio.service

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=${PROJECT_DIR}
Environment="PATH=${PROJECT_DIR}/venv/bin"
ExecStart=${PROJECT_DIR}/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port ${BACKEND_PORT}
Restart=always

[Install]
WantedBy=multi-user.target
EOF

deactivate

# --- 7. Frontend Setup ---
echo "[7/8] Setting up Frontend (Next.js)..."
cd ${PROJECT_DIR}/front_app

# Install Node dependencies
npm install

# Create frontend .env.local
cat > .env.local <<EOF
NEXT_PUBLIC_API_URL=http://${DOMAIN}:${BACKEND_PORT}/api/v1
EOF

# Build production bundle
npm run build

# Create Frontend systemd service
sudo tee /etc/systemd/system/tontouma-frontend.service > /dev/null <<EOF
[Unit]
Description=TonToumaBot Frontend (Next.js)
After=network.target tontouma-backend.service

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=${PROJECT_DIR}/front_app
ExecStart=/usr/bin/npm run start -- -p ${FRONTEND_PORT}
Restart=always
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
EOF

# --- 8. Nginx Reverse Proxy ---
echo "[8/8] Configuring Nginx..."
sudo tee /etc/nginx/sites-available/tontouma > /dev/null <<EOF
server {
    listen 80;
    server_name ${DOMAIN};

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:${FRONTEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:${BACKEND_PORT}/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # For file uploads
        client_max_body_size 50M;
    }

    # Uploads (audio files)
    location /uploads/ {
        proxy_pass http://127.0.0.1:${BACKEND_PORT}/uploads/;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/tontouma /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

# --- Enable and Start Services ---
echo "=============================================="
echo "   Enabling and Starting Services..."
echo "=============================================="
sudo systemctl daemon-reload
sudo systemctl enable tontouma-backend tontouma-frontend
sudo systemctl start tontouma-backend tontouma-frontend

echo ""
echo "=============================================="
echo "   DEPLOYMENT COMPLETE!"
echo "=============================================="
echo ""
echo "Services status:"
sudo systemctl status minio --no-pager | head -5
sudo systemctl status tontouma-backend --no-pager | head -5
sudo systemctl status tontouma-frontend --no-pager | head -5
echo ""
echo "Access your app at: http://${DOMAIN}"
echo "Backend API docs: http://${DOMAIN}:${BACKEND_PORT}/docs"
echo ""
echo ">>> NEXT STEPS:"
echo "1. Edit ${PROJECT_DIR}/.env with your OPENAI_API_KEY"
echo "2. Run: sudo systemctl restart tontouma-backend"
echo "3. Run seeding scripts to populate data"
echo ""
