#!/bin/bash

# Chesstic Deployment Script
# Server: 159.65.140.136
# Repository: https://github.com/jayongithubfinaccel/chesstic_finnacel

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="chesstic"
APP_DIR="/var/www/${APP_NAME}"
REPO_URL="https://github.com/jayongithubfinaccel/chesstic_finnacel"
BRANCH="main"
PYTHON_VERSION="3.12"
VENV_DIR="${APP_DIR}/venv"
SERVICE_NAME="chesstic"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Chesstic Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Error: Please run with sudo${NC}"
    echo "Usage: sudo bash deploy.sh"
    exit 1
fi

# Function to print step
print_step() {
    echo -e "${YELLOW}▶ $1${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Step 1: Install system dependencies
print_step "Step 1: Installing system dependencies..."
apt-get update
apt-get install -y python3 python3-pip python3-venv nginx git stockfish curl

# Install UV package manager
if ! command -v uv &> /dev/null; then
    print_step "Installing UV package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi
print_success "System dependencies installed"

# Step 2: Stop existing service
print_step "Step 2: Stopping existing service (if running)..."
if systemctl is-active --quiet ${SERVICE_NAME}; then
    systemctl stop ${SERVICE_NAME}
    print_success "Service stopped"
else
    print_success "No existing service running"
fi

# Step 3: Backup old deployment (if exists)
if [ -d "${APP_DIR}" ]; then
    print_step "Step 3: Backing up old deployment..."
    BACKUP_DIR="${APP_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
    mv ${APP_DIR} ${BACKUP_DIR}
    print_success "Old deployment backed up to ${BACKUP_DIR}"
else
    print_step "Step 3: No old deployment found, skipping backup"
fi

# Step 4: Clone fresh repository
print_step "Step 4: Cloning repository..."
mkdir -p ${APP_DIR}
git clone -b ${BRANCH} ${REPO_URL} ${APP_DIR}
cd ${APP_DIR}
print_success "Repository cloned successfully"

# Step 5: Create and setup .env file
print_step "Step 5: Setting up environment file..."
if [ -f "${APP_DIR}/.env" ]; then
    print_success ".env file already exists"
else
    if [ -f "${APP_DIR}/.env.example" ]; then
        cp ${APP_DIR}/.env.example ${APP_DIR}/.env
        print_success ".env file created from template"
        echo -e "${YELLOW}⚠  Please edit ${APP_DIR}/.env with your configuration${NC}"
    else
        # Create a basic .env file
        cat > ${APP_DIR}/.env << EOL
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)
DEBUG=False

# CORS Settings
CORS_ORIGINS=http://159.65.140.136,http://chesstic.com

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PER_MINUTE=30

# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Stockfish Configuration
STOCKFISH_PATH=/usr/games/stockfish
ENGINE_ANALYSIS_ENABLED=True
ENGINE_DEPTH=12
ENGINE_TIME_LIMIT=1.5
EOL
        print_success "Basic .env file created"
        echo -e "${YELLOW}⚠  Please edit ${APP_DIR}/.env with your OPENAI_API_KEY and other settings${NC}"
    fi
fi

# Step 6: Setup Python virtual environment
print_step "Step 6: Setting up Python virtual environment..."
if command -v uv &> /dev/null; then
    # Use UV if available
    cd ${APP_DIR}
    uv venv ${VENV_DIR}
    source ${VENV_DIR}/bin/activate
    uv pip install -r requirements.txt
else
    # Fallback to standard venv
    python3 -m venv ${VENV_DIR}
    source ${VENV_DIR}/bin/activate
    pip install --upgrade pip
    pip install -r ${APP_DIR}/requirements.txt
    pip install gunicorn  # Production WSGI server
fi
print_success "Virtual environment created and dependencies installed"

# Step 7: Create systemd service
print_step "Step 7: Creating systemd service..."
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOL
[Unit]
Description=Chesstic Flask Application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=${APP_DIR}
Environment="PATH=${VENV_DIR}/bin"
EnvironmentFile=${APP_DIR}/.env
ExecStart=${VENV_DIR}/bin/gunicorn --config ${APP_DIR}/gunicorn_config.py run:app
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOL

systemctl daemon-reload
print_success "Systemd service created"

# Step 8: Configure Nginx
print_step "Step 8: Configuring Nginx..."
cat > /etc/nginx/sites-available/${APP_NAME} << 'EOL'
server {
    listen 80;
    server_name 159.65.140.136;

    # Increase timeouts for long-running requests
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    proxy_read_timeout 300;
    send_timeout 300;

    # Max upload size
    client_max_body_size 10M;

    # Serve static files directly
    location /static {
        alias /var/www/chesstic/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy to Flask application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed in future)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Logging
    access_log /var/log/nginx/chesstic_access.log;
    error_log /var/log/nginx/chesstic_error.log;
}
EOL

# Enable the site
ln -sf /etc/nginx/sites-available/${APP_NAME} /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t
print_success "Nginx configured"

# Step 9: Set permissions
print_step "Step 9: Setting permissions..."
chown -R www-data:www-data ${APP_DIR}
chmod -R 755 ${APP_DIR}
chmod 600 ${APP_DIR}/.env  # Keep .env secure
print_success "Permissions set"

# Step 10: Start services
print_step "Step 10: Starting services..."
systemctl enable ${SERVICE_NAME}
systemctl start ${SERVICE_NAME}
systemctl reload nginx
print_success "Services started"

# Step 11: Verify deployment
print_step "Step 11: Verifying deployment..."
sleep 3

if systemctl is-active --quiet ${SERVICE_NAME}; then
    print_success "Chesstic service is running"
else
    print_error "Chesstic service failed to start"
    echo "Check logs with: sudo journalctl -u ${SERVICE_NAME} -n 50"
    exit 1
fi

if systemctl is-active --quiet nginx; then
    print_success "Nginx is running"
else
    print_error "Nginx failed to start"
    exit 1
fi

# Final status
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Completed Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Your application is now running at:"
echo -e "${GREEN}http://159.65.140.136${NC}"
echo ""
echo "Useful commands:"
echo "  • View logs: sudo journalctl -u ${SERVICE_NAME} -f"
echo "  • Restart app: sudo systemctl restart ${SERVICE_NAME}"
echo "  • Check status: sudo systemctl status ${SERVICE_NAME}"
echo "  • Restart Nginx: sudo systemctl restart nginx"
echo ""
echo -e "${YELLOW}⚠  Remember to:${NC}"
echo "  1. Edit ${APP_DIR}/.env with your API keys"
echo "  2. Restart the service after updating .env: sudo systemctl restart ${SERVICE_NAME}"
echo "  3. Configure your domain DNS if needed"
echo ""
