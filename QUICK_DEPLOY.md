# Quick Deployment Instructions

## Overview
This guide will help you deploy your Chesstic application from the new GitHub repository to your server at 159.65.140.136.

## Prerequisites
- Server: 159.65.140.136 (Digital Ocean Droplet)
- SSH access with root privileges
- New repository: https://github.com/jayongithubfinaccel/chesstic_finnacel

## Deployment Steps

### 1. Upload Deployment Script to Server

From your local machine (Windows PowerShell):
```powershell
# Navigate to your project directory
cd C:\anaconda_backup\Project\chesstic_v2

# Upload deployment script to server
scp deploy.sh root@159.65.140.136:/root/
```

### 2. Connect to Server

```powershell
ssh root@159.65.140.136
```

### 3. Run Deployment Script

```bash
# Make script executable
chmod +x /root/deploy.sh

# Run deployment (this will handle everything)
sudo bash /root/deploy.sh
```

**What the script does automatically:**
- ✅ Stops old service
- ✅ Backs up old deployment
- ✅ Deletes old files
- ✅ Clones new repository from https://github.com/jayongithubfinaccel/chesstic_finnacel
- ✅ Sets up Python environment
- ✅ Installs all dependencies
- ✅ Creates systemd service
- ✅ Configures Nginx
- ✅ Starts the application

### 4. Configure Environment Variables

After the script completes, edit the environment file:

```bash
sudo nano /var/www/chesstic/.env
```

**Update these required values:**
```env
# IMPORTANT: Change these values!
SECRET_KEY=generate-a-secure-random-key-here
OPENAI_API_KEY=your-actual-openai-api-key

# Update if you have a domain
CORS_ORIGINS=http://159.65.140.136

# Keep these as-is for production
FLASK_ENV=production
DEBUG=False
```

To generate a secure SECRET_KEY:
```bash
openssl rand -hex 32
```

### 5. Restart Service

```bash
sudo systemctl restart chesstic
```

### 6. Verify Deployment

Open your browser and navigate to:
```
http://159.65.140.136
```

You should see your Chesstic application running!

---

## Future Deployments

For subsequent deployments, you only need to:

### Option 1: Run deploy.sh (Full Redeployment)
```bash
ssh root@159.65.140.136
sudo bash /var/www/chesstic/deploy.sh
```

### Option 2: Quick Update (Code Only)
```bash
ssh root@159.65.140.136
cd /var/www/chesstic
sudo git pull origin main
sudo systemctl restart chesstic
```

---

## Useful Commands

### Check Application Status
```bash
# Check if service is running
sudo systemctl status chesstic

# View live logs
sudo journalctl -u chesstic -f

# View last 50 log lines
sudo journalctl -u chesstic -n 50
```

### Restart Application
```bash
sudo systemctl restart chesstic
```

### Edit Configuration
```bash
# Edit environment variables
sudo nano /var/www/chesstic/.env

# After editing, restart
sudo systemctl restart chesstic
```

### View Web Server Logs
```bash
# Nginx error log
sudo tail -f /var/log/nginx/chesstic_error.log

# Nginx access log
sudo tail -f /var/log/nginx/chesstic_access.log
```

### Update Code from GitHub
```bash
cd /var/www/chesstic
sudo git pull origin main
sudo systemctl restart chesstic
```

---

## Troubleshooting

### Service Won't Start
```bash
# Check what went wrong
sudo journalctl -u chesstic -n 100 --no-pager

# Common issues:
# 1. Missing .env file
# 2. Wrong permissions
# 3. Port 8000 already in use
```

### Website Not Loading
```bash
# Check if service is running
sudo systemctl status chesstic

# Check Nginx status
sudo systemctl status nginx

# Check if app is listening on port 8000
sudo netstat -tlnp | grep 8000
```

### Application Errors
```bash
# View detailed logs
sudo journalctl -u chesstic -n 100

# Test app directly (bypass Nginx)
curl http://127.0.0.1:8000
```

### Fix Permissions
```bash
sudo chown -R www-data:www-data /var/www/chesstic
sudo chmod -R 755 /var/www/chesstic
sudo chmod 600 /var/www/chesstic/.env
sudo systemctl restart chesstic
```

---

## Important Files & Locations

| Item | Location |
|------|----------|
| Application code | `/var/www/chesstic/` |
| Environment config | `/var/www/chesstic/.env` |
| Service file | `/etc/systemd/system/chesstic.service` |
| Nginx config | `/etc/nginx/sites-available/chesstic` |
| Application logs | `sudo journalctl -u chesstic` |
| Nginx logs | `/var/log/nginx/chesstic_*.log` |
| Gunicorn logs | `/var/log/gunicorn/chesstic_*.log` |

---

## Emergency Rollback

If something goes wrong, you can restore the backup:

```bash
# List available backups
ls -lh /var/www/chesstic_backup_*

# Stop current service
sudo systemctl stop chesstic

# Restore backup (replace timestamp with your backup)
sudo mv /var/www/chesstic /var/www/chesstic_failed
sudo mv /var/www/chesstic_backup_YYYYMMDD_HHMMSS /var/www/chesstic

# Restart service
sudo systemctl start chesstic
```

---

## Security Checklist

Before going live:
- [ ] Changed SECRET_KEY from default
- [ ] Added your OpenAI API key
- [ ] Set DEBUG=False
- [ ] Updated CORS_ORIGINS with your actual domain
- [ ] Secured .env file (chmod 600)
- [ ] Configured firewall: `sudo ufw allow 22,80,443/tcp`
- [ ] Consider adding SSL certificate (HTTPS)

---

## Next Steps

1. **Setup Domain** (Optional):
   - Point your domain's A record to 159.65.140.136
   - Update CORS_ORIGINS in .env
   - Update server_name in Nginx config
   - Get SSL certificate: `sudo certbot --nginx -d yourdomain.com`

2. **Setup Monitoring**:
   - Configure health checks
   - Setup log rotation
   - Consider adding uptime monitoring

3. **Optimize Performance**:
   - Adjust Gunicorn workers in gunicorn_config.py
   - Enable caching if needed
   - Setup Redis for session storage

---

## Support

If you need help:
1. Check logs: `sudo journalctl -u chesstic -n 100`
2. Check Nginx: `sudo tail -100 /var/log/nginx/chesstic_error.log`
3. Verify environment: `sudo cat /var/www/chesstic/.env | grep -v KEY`
4. Test connectivity: `curl http://127.0.0.1:8000`

For detailed instructions, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
