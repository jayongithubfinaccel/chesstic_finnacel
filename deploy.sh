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
apt-get install -y python3 python3-pip python3-venv nginx git curl
print_success "System dependencies installed"

# Step 1b: Install Stockfish chess engine
print_step "Step 1b: Installing Stockfish chess engine..."
if command -v stockfish &> /dev/null; then
    STOCKFISH_VERSION=$(stockfish <<< "uci" 2>/dev/null | head -1)
    print_success "Stockfish already installed: ${STOCKFISH_VERSION}"
else
    apt-get install -y stockfish
    if command -v stockfish &> /dev/null; then
        STOCKFISH_VERSION=$(stockfish <<< "uci" 2>/dev/null | head -1)
        print_success "Stockfish installed: ${STOCKFISH_VERSION}"
    else
        print_error "Stockfish installation failed via apt"
        print_step "Attempting manual Stockfish installation..."
        # Fallback: download from official source
        STOCKFISH_URL="https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-ubuntu-x86-64-avx2.tar"
        cd /tmp
        curl -LO ${STOCKFISH_URL} 2>/dev/null || curl -LO "https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-ubuntu-x86-64.tar" 2>/dev/null
        if [ -f stockfish-ubuntu-*.tar ]; then
            tar xf stockfish-ubuntu-*.tar
            cp stockfish/stockfish-ubuntu-* /usr/local/bin/stockfish
            chmod +x /usr/local/bin/stockfish
            rm -rf stockfish stockfish-ubuntu-*.tar
            print_success "Stockfish installed manually to /usr/local/bin/stockfish"
        else
            print_error "Failed to download Stockfish. Please install manually."
            echo "  Visit: https://stockfishchess.org/download/"
        fi
        cd ${APP_DIR}
    fi
fi

# Verify Stockfish
STOCKFISH_PATH=$(which stockfish 2>/dev/null)
if [ -n "${STOCKFISH_PATH}" ]; then
    print_success "Stockfish binary: ${STOCKFISH_PATH}"
    # Quick engine test
    echo "quit" | stockfish > /dev/null 2>&1 && print_success "Stockfish engine responds correctly" || print_error "Stockfish engine test failed"
else
    print_error "Stockfish not found in PATH. Mistake analysis will not work."
fi

# Install UV package manager
if ! command -v uv &> /dev/null; then
    print_step "Installing UV package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi
print_success "All dependencies installed"

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
        # Detect Stockfish path
        DETECTED_STOCKFISH=$(which stockfish 2>/dev/null || echo "/usr/games/stockfish")
        
        # Create a production .env file
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

# OpenAI API Configuration (Milestone 9: AI Chess Advisor)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=500
OPENAI_TEMPERATURE=0.7

# Stockfish Configuration (Milestone 8 + Iteration 12)
STOCKFISH_PATH=${DETECTED_STOCKFISH}
ENGINE_ANALYSIS_ENABLED=True
ENGINE_NODES=50000
ENGINE_DEPTH=15
ENGINE_TIME_LIMIT=2.0

# Iteration 12: Analysis Scope
MAX_ANALYSIS_GAMES=10
MOVES_PER_GAME=15

# Iteration 11: Lichess Cloud API (disabled by default for reliability)
USE_LICHESS_CLOUD=false
LICHESS_API_TIMEOUT=1.0

# Iteration 11.1: Mistake Analysis UI Control
MISTAKE_ANALYSIS_UI_ENABLED=true

# Cache Settings
AI_ADVICE_CACHE_TTL=3600

# Google Analytics & Tag Manager Configuration (Iteration 11)
GTM_ENABLED=true
GTM_CONTAINER_ID=GT-NFBTKHBS
GA_MEASUREMENT_ID=G-VMYYSZC29R
EOL
        print_success "Production .env file created with Iteration 12 defaults"
        echo -e "${YELLOW}⚠  Please edit ${APP_DIR}/.env with your OPENAI_API_KEY and other settings${NC}"
        echo -e "${YELLOW}⚠  Stockfish path auto-detected: ${DETECTED_STOCKFISH}${NC}"
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
echo "  1. Edit ${APP_DIR}/.env with your API keys (especially OPENAI_API_KEY)"
echo "  2. Restart the service after updating .env: sudo systemctl restart ${SERVICE_NAME}"
echo "  3. Configure your domain DNS if needed"
echo ""
echo "Stockfish Configuration (Iteration 12):"
echo "  • Stockfish path: $(which stockfish 2>/dev/null || echo 'NOT FOUND')"
echo "  • Engine nodes: 50000 (node-limited search)"
echo "  • Max analysis games: 10"
echo "  • Moves per game: 15 (5 early + 5 mid + 5 end)"
echo "  • Lichess Cloud API: disabled (set USE_LICHESS_CLOUD=true to enable)"
echo ""
