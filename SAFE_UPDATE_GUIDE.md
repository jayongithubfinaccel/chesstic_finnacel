# Safe Update Guide for Chesstic Production

## Overview
This guide explains how to safely update your production application without downtime or breaking issues.

## Quick Update Process

### Step 1: SSH into Your Server
```bash
ssh root@159.65.140.136
```

### Step 2: Navigate to Application Directory
```bash
cd /var/www/chesstic
```

### Step 3: Run the Safe Update Script
```bash
sudo bash update.sh
```

**That's it!** The script will:
- ✅ Create automatic backup
- ✅ Pull latest code from GitHub
- ✅ Update dependencies safely
- ✅ Verify all critical packages
- ✅ Test the application
- ✅ Auto-rollback if anything fails

---

## What the Update Script Does

### 1. **Backup Creation**
- Creates timestamped backup before any changes
- Example: `/var/www/chesstic_backup_20250122_143025`
- Keeps last 5 backups automatically

### 2. **Code Update**
- Stashes any local changes (if any)
- Pulls latest code from `main` branch
- Preserves your `.env` file

### 3. **Dependency Verification**
- Updates Python packages from `requirements.txt`
- Verifies critical packages:
  - openai
  - python-chess
  - pytz
  - Flask
  - Flask-CORS
  - requests

### 4. **Health Checks**
- Restarts the service
- Verifies service is running
- Tests HTTP endpoint (localhost:8000)
- If any check fails → automatic rollback

### 5. **Automatic Rollback**
If update fails at any step:
- Service stops
- Bad version is removed
- Backup is restored
- Service restarts with previous working version

---

## Manual Rollback (If Needed)

If you need to manually rollback to a previous version:

```bash
# 1. Stop the service
sudo systemctl stop chesstic

# 2. Find your backup (list all backups)
ls -lah /var/www/chesstic_backup_*

# 3. Replace with backup (use your specific backup name)
sudo rm -rf /var/www/chesstic
sudo cp -r /var/www/chesstic_backup_YYYYMMDD_HHMMSS /var/www/chesstic

# 4. Fix permissions
sudo chown -R www-data:www-data /var/www/chesstic

# 5. Restart service
sudo systemctl start chesstic

# 6. Verify
sudo systemctl status chesstic
curl http://localhost:8000/
```

---

## Monitoring After Update

### Check Service Status
```bash
sudo systemctl status chesstic
```

### View Live Logs
```bash
sudo journalctl -u chesstic -f
```

### View Gunicorn Logs
```bash
tail -f /var/log/gunicorn/error.log
tail -f /var/log/gunicorn/access.log
```

### Test Website
```bash
# From server
curl http://localhost:8000/

# From your browser
https://chesstic.org
```

---

## Troubleshooting

### Update Script Fails Immediately
**Problem**: Script exits with permission error

**Solution**:
```bash
# Make sure you run with sudo
sudo bash update.sh

# Or run as root
su - root
cd /var/www/chesstic
bash update.sh
```

### Service Won't Start After Update
**Problem**: `systemctl status chesstic` shows "failed"

**Solution**:
```bash
# Check error logs
sudo journalctl -u chesstic -n 50

# Common issues:
# 1. Missing dependency → pip install [package]
# 2. Permission error → sudo chown -R www-data:www-data /var/www/chesstic
# 3. Port in use → sudo lsof -i :8000
```

### Website Shows Old Version
**Problem**: Changes don't appear on website

**Solution**:
```bash
# Hard restart
sudo systemctl stop chesstic
sleep 2
sudo systemctl start chesstic

# Clear browser cache
# Press Ctrl+Shift+R in your browser
```

### Missing Dependencies
**Problem**: Import errors in logs

**Solution**:
```bash
cd /var/www/chesstic
source venv/bin/activate
pip install [missing-package]
pip freeze > requirements.txt  # Save for next time
deactivate
sudo systemctl restart chesstic
```

---

## Best Practices

### ✅ DO:
- Run updates during low-traffic hours
- Test changes locally first
- Keep backups (script does this automatically)
- Monitor logs after updates
- Commit and push all changes to GitHub before updating

### ❌ DON'T:
- Edit code directly on server (use GitHub)
- Delete backups manually (automatic cleanup keeps 5)
- Skip testing after updates
- Update without backup
- Run multiple updates simultaneously

---

## Emergency Procedures

### Quick Rollback Command
```bash
sudo systemctl stop chesstic && \
sudo rm -rf /var/www/chesstic && \
sudo cp -r /var/www/chesstic_backup_$(ls -t /var/www/ | grep chesstic_backup | head -1 | cut -d'_' -f3-) /var/www/chesstic && \
sudo chown -R www-data:www-data /var/www/chesstic && \
sudo systemctl start chesstic
```

### Complete Service Restart
```bash
sudo systemctl stop chesstic
sudo systemctl daemon-reload
sudo systemctl start chesstic
sudo systemctl status chesstic
```

### Reset Everything (Nuclear Option)
Only use if everything else fails:
```bash
cd /var/www
sudo systemctl stop chesstic
sudo rm -rf chesstic
sudo bash deploy.sh  # Run full deployment again
```

---

## Deployment Architecture

Current setup:
- **Application**: Flask on Python 3.13
- **WSGI Server**: Gunicorn (localhost:8000)
- **Web Server**: Nginx (reverse proxy)
- **SSL**: Let's Encrypt via Certbot
- **Domain**: https://chesstic.org
- **User**: www-data
- **Service**: systemd (chesstic.service)

---

## Important File Locations

| File/Directory | Purpose |
|----------------|---------|
| `/var/www/chesstic/` | Application directory |
| `/var/www/chesstic/venv/` | Python virtual environment |
| `/var/www/chesstic/.env` | Environment variables (API keys) |
| `/etc/systemd/system/chesstic.service` | Systemd service file |
| `/etc/nginx/sites-available/chesstic` | Nginx configuration |
| `/var/log/gunicorn/` | Application logs |
| `/var/www/chesstic_backup_*` | Automatic backups |

---

## Contact & Support

**GitHub Repository**: https://github.com/jayongithubfinaccel/chesstic_finnacel

**Server Details**:
- IP: 159.65.140.136
- Domain: https://chesstic.org
- Provider: Digital Ocean

**Quick Commands Reference**:
```bash
# Update application
cd /var/www/chesstic && sudo bash update.sh

# View logs
sudo journalctl -u chesstic -f

# Check status
sudo systemctl status chesstic

# Restart
sudo systemctl restart chesstic

# Test
curl http://localhost:8000/
```

---

## Version History

| Date | Change | Notes |
|------|--------|-------|
| 2025-01-22 | Initial production deployment | Full setup with SSL |
| 2025-01-22 | Created safe update script | Automatic backup & rollback |

