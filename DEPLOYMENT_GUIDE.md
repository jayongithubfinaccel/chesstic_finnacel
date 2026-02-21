# Deployment Guide for Chesstic

This guide explains how to deploy the Chesstic application to your Digital Ocean server.

## Server Information
- **Server IP**: 159.65.140.136
- **GitHub Repository**: https://github.com/jayongithubfinaccel/chesstic_finnacel
- **Branch**: main

## Prerequisites
- Ubuntu/Debian server with root access
- SSH access to the server
- Domain configured (optional)

## Quick Deployment

### First Time Deployment

1. **Connect to your server**:
   ```bash
   ssh root@159.65.140.136
   ```

2. **Upload the deployment script** (from your local machine):
   ```bash
   scp deploy.sh root@159.65.140.136:/root/
   ```

3. **Run the deployment script**:
   ```bash
   ssh root@159.65.140.136
   cd /root
   chmod +x deploy.sh
   sudo bash deploy.sh
   ```

4. **Configure environment variables**:
   ```bash
   sudo nano /var/www/chesstic/.env
   ```
   
   Update these important values:
   - `SECRET_KEY`: Generate a secure random key
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `CORS_ORIGINS`: Your domain(s)
   - `DEBUG`: Set to `False` for production

5. **Restart the service**:
   ```bash
   sudo systemctl restart chesstic
   ```

6. **Verify deployment**:
   Open browser: http://159.65.140.136

### Subsequent Deployments

For future deployments, simply run:

```bash
ssh root@159.65.140.136
cd /var/www/chesstic
sudo bash deploy.sh
```

The script will automatically:
- Backup the old deployment
- Pull latest code from GitHub
- Install dependencies
- Restart services

## Manual Deployment Steps

If you prefer to deploy manually or need to understand what the script does:

### Step 1: Remove Old Deployment

```bash
# Connect to server
ssh root@159.65.140.136

# Stop the old service
sudo systemctl stop chesstic  # or whatever your old service name was

# Backup old files (optional but recommended)
sudo mv /var/www/your-old-directory /var/www/old-backup-$(date +%Y%m%d)

# Or completely remove old files
sudo rm -rf /var/www/your-old-directory
```

### Step 2: Install System Dependencies

```bash
# Update system
sudo apt-get update

# Install required packages
sudo apt-get install -y python3 python3-pip python3-venv nginx git stockfish curl

# Install UV package manager (optional but recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/bin/env
```

### Step 3: Clone New Repository

```bash
# Create application directory
sudo mkdir -p /var/www/chesstic

# Clone repository
sudo git clone -b main https://github.com/jayongithubfinaccel/chesstic_finnacel /var/www/chesstic

# Navigate to directory
cd /var/www/chesstic
```

### Step 4: Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

### Step 5: Configure Environment Variables

```bash
# Copy example env file
sudo cp /var/www/chesstic/.env.example /var/www/chesstic/.env

# Edit the file
sudo nano /var/www/chesstic/.env
```

Required environment variables:
```env
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here-change-this
DEBUG=False

# CORS Settings (add your domain)
CORS_ORIGINS=http://159.65.140.136,http://your-domain.com

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PER_MINUTE=30

# OpenAI API (required for AI advisor feature)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Stockfish Configuration
STOCKFISH_PATH=/usr/games/stockfish
ENGINE_ANALYSIS_ENABLED=True
ENGINE_DEPTH=12
ENGINE_TIME_LIMIT=1.5
```

### Step 6: Create Systemd Service

```bash
# Copy gunicorn config
sudo cp /var/www/chesstic/gunicorn_config.py /var/www/chesstic/

# Create systemd service
sudo nano /etc/systemd/system/chesstic.service
```

Add this content:
```ini
[Unit]
Description=Chesstic Flask Application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/chesstic
Environment="PATH=/var/www/chesstic/venv/bin"
EnvironmentFile=/var/www/chesstic/.env
ExecStart=/var/www/chesstic/venv/bin/gunicorn --config /var/www/chesstic/gunicorn_config.py run:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

### Step 7: Configure Nginx

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/chesstic
```

Add this content:
```nginx
server {
    listen 80;
    server_name 159.65.140.136;

    # Increase timeouts for long-running requests
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    proxy_read_timeout 300;
    send_timeout 300;

    client_max_body_size 10M;

    location /static {
        alias /var/www/chesstic/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    access_log /var/log/nginx/chesstic_access.log;
    error_log /var/log/nginx/chesstic_error.log;
}
```

Enable the site:
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/chesstic /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t
```

### Step 8: Set Permissions

```bash
# Create log directory
sudo mkdir -p /var/log/gunicorn

# Set ownership
sudo chown -R www-data:www-data /var/www/chesstic
sudo chown -R www-data:www-data /var/log/gunicorn

# Set permissions
sudo chmod -R 755 /var/www/chesstic
sudo chmod 600 /var/www/chesstic/.env
```

### Step 9: Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable and start chesstic service
sudo systemctl enable chesstic
sudo systemctl start chesstic

# Restart Nginx
sudo systemctl restart nginx
```

### Step 10: Verify Deployment

```bash
# Check service status
sudo systemctl status chesstic
sudo systemctl status nginx

# Check logs
sudo journalctl -u chesstic -n 50
sudo tail -f /var/log/nginx/chesstic_error.log
```

## Useful Commands

### Service Management
```bash
# Start service
sudo systemctl start chesstic

# Stop service
sudo systemctl stop chesstic

# Restart service
sudo systemctl restart chesstic

# Check status
sudo systemctl status chesstic

# View logs (real-time)
sudo journalctl -u chesstic -f

# View last 100 lines
sudo journalctl -u chesstic -n 100
```

### Nginx Management
```bash
# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status nginx

# View error logs
sudo tail -f /var/log/nginx/chesstic_error.log

# View access logs
sudo tail -f /var/log/nginx/chesstic_access.log
```

### Application Management
```bash
# Update code only (without full redeployment)
cd /var/www/chesstic
sudo git pull origin main
sudo systemctl restart chesstic

# Update dependencies
cd /var/www/chesstic
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart chesstic

# Edit environment variables
sudo nano /var/www/chesstic/.env
sudo systemctl restart chesstic  # Always restart after changing .env
```

### Troubleshooting
```bash
# Check if app is running
sudo systemctl status chesstic

# Check recent logs for errors
sudo journalctl -u chesstic -n 100 --no-pager

# Check Nginx errors
sudo tail -100 /var/log/nginx/chesstic_error.log

# Check if port 8000 is listening
sudo netstat -tlnp | grep 8000

# Test application directly (bypass Nginx)
curl http://127.0.0.1:8000

# Check disk space
df -h

# Check memory usage
free -h

# Check if Stockfish is installed
which stockfish
stockfish --version
```

## SSL/HTTPS Setup (Optional)

To enable HTTPS with Let's Encrypt:

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com

# Certbot will modify your Nginx config automatically
# Certificates auto-renew, but you can test with:
sudo certbot renew --dry-run
```

## Backup Strategy

### Manual Backup
```bash
# Backup application
sudo tar -czf chesstic-backup-$(date +%Y%m%d).tar.gz /var/www/chesstic

# Backup environment file (separate for security)
sudo cp /var/www/chesstic/.env ~/chesstic-env-backup-$(date +%Y%m%d)
```

### Automated Backup Script
Create `/root/backup-chesstic.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/root/backups"
mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/chesstic-$(date +%Y%m%d-%H%M%S).tar.gz /var/www/chesstic
# Keep only last 7 days
find $BACKUP_DIR -name "chesstic-*.tar.gz" -mtime +7 -delete
```

Add to crontab for daily backups:
```bash
sudo crontab -e
# Add: 0 2 * * * /root/backup-chesstic.sh
```

## Monitoring

### Check Service Health
```bash
# Create health check script
cat > /root/check-chesstic.sh << 'EOF'
#!/bin/bash
if ! systemctl is-active --quiet chesstic; then
    echo "Chesstic service is down! Restarting..."
    systemctl start chesstic
    echo "Service restarted at $(date)" >> /var/log/chesstic-restarts.log
fi
EOF

chmod +x /root/check-chesstic.sh

# Add to crontab (check every 5 minutes)
sudo crontab -e
# Add: */5 * * * * /root/check-chesstic.sh
```

## Performance Tuning

### Gunicorn Workers
Edit `/var/www/chesstic/gunicorn_config.py`:
- For CPU-intensive tasks: `workers = (2 * cpu_count) + 1`
- For I/O-intensive tasks: `workers = (4 * cpu_count) + 1`

### Database Caching (if needed)
Add Redis for caching:
```bash
sudo apt-get install redis-server
pip install redis flask-caching
```

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Set DEBUG=False in production
- [ ] Secure .env file (chmod 600)
- [ ] Configure firewall (ufw allow 80, 443, 22)
- [ ] Enable HTTPS with SSL certificate
- [ ] Regular system updates (apt-get update && apt-get upgrade)
- [ ] Monitor logs for suspicious activity
- [ ] Backup .env file securely
- [ ] Use strong SSH keys, disable password authentication

## Support

If you encounter issues:
1. Check service logs: `sudo journalctl -u chesstic -n 100`
2. Check Nginx logs: `sudo tail -100 /var/log/nginx/chesstic_error.log`
3. Verify .env configuration
4. Ensure all dependencies are installed
5. Check firewall rules: `sudo ufw status`

## Quick Reference

| Task | Command |
|------|---------|
| Deploy | `sudo bash deploy.sh` |
| View logs | `sudo journalctl -u chesstic -f` |
| Restart app | `sudo systemctl restart chesstic` |
| Update code | `cd /var/www/chesstic && sudo git pull && sudo systemctl restart chesstic` |
| Edit config | `sudo nano /var/www/chesstic/.env` |
| Check status | `sudo systemctl status chesstic nginx` |
