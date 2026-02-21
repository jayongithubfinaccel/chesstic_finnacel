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

## 🚀 Future Deployments - ONE COMMAND!

### ⭐ Recommended: One-Command Deployment (NEW!)

**From your local Windows machine, just run:**

```bash
bash quick_deploy.sh "Your commit message"
```

**That's it!** This single command automatically:
- ✅ Commits and pushes your local changes to GitHub
- ✅ Connects to your server (159.65.140.136)
- ✅ Creates automatic backup before updating
- ✅ Pulls latest code from GitHub
- ✅ Updates dependencies safely
- ✅ Verifies all critical packages are installed
- ✅ Restarts the service
- ✅ Tests that website is responding
- ✅ **Automatic rollback if anything fails!**

**Examples:**
```bash
# Deploy with a specific message
bash quick_deploy.sh "Fixed analytics bug"

# Deploy with another message  
bash quick_deploy.sh "Added new opening feature"

# Deploy with default message
bash quick_deploy.sh
```

### Your New Workflow:
1. 📝 Make changes to your code locally
2. 🚀 Run: `bash quick_deploy.sh "What you changed"`
3. ✨ Done! Your changes are live!

**No more multiple commands, no more SSH, no more worrying!** The script handles everything automatically with built-in safety features.

---

### Alternative Options (Manual Methods)

#### Option 1: Manual Safe Update
```bash
ssh root@159.65.140.136
cd /var/www/chesstic
sudo bash update.sh
```
This runs the safe update script with backup and rollback, but you need to push to GitHub first manually.

#### Option 2: Run deploy.sh (Full Redeployment)
```bash
ssh root@159.65.140.136
sudo bash /var/www/chesstic/deploy.sh
```
⚠️ Only use this for major changes or fresh installations.

#### Option 3: Quick Update (Code Only - Not Recommended)
```bash
ssh root@159.65.140.136
cd /var/www/chesstic
sudo git pull origin main
sudo systemctl restart chesstic
```
⚠️ No backup or rollback - use at your own risk!

---

## 📊 Monitoring & Verification Tools

### Check Dependencies Match Requirements.txt
**From your local machine:**
```bash
bash verify_dependencies.sh
```
This will connect to your server and verify all packages are correctly installed.

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
# Nginx error log (Manual)
```bash
cd /var/www/chesstic
sudo git pull origin main
sudo systemctl restart chesstic
```

### View Deployment Backups
```bash
# List all backups
ssh root@159.65.140.136 'ls -lah /var/www/chesstic_backup_*'

# The update script keeps the last 5 backups automaticallysstic_access.log
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
| S🔄 Emergency Rollback

### Automatic Rollback
The `quick_deploy.sh` and `update.sh` scripts **automatically rollback** if anything fails during deployment!

### Manual Rollback
If you need to manually rollback to a previous version:

```bash
# SSH to server
ssh root@159.65.140.136

# List available backups
ls -lh /var/www/chesstic_backup_*

# Stop current service
sudo systemctl stop chesstic

# Restore backup (replace timestamp with your backup)
sudo rm -rf /var/www/chesstic
sudo cp -r /var/www/chesstic_backup_YYYYMMDD_HHMMSS /var/www/chesstic

# Fix permissions
sudo chown -R www-data:www-data /var/www/chesstic

# Restart service
sudo systemctl start chesstic
```

### Quick Rollback Command
```bash
ssh root@159.65.140.136 'sudo systemctl stop chesstic && sudo rm -rf /var/www/chesstic && sudo cp -r /var/www/chesstic_backup_$(ls -t /var/www/ | grep chesstic_backup | head -1 | cut -d"_" -f3-) /var/www/chesstic && sudo chown -R www-data:www-data /var/www/chesstic && sudo systemctl start chesstic'
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
