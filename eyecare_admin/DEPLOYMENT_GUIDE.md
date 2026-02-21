# Production Deployment Guide for EyeCare Admin
# Complete step-by-step instructions

## Phase 5A: Production Deployment

### ✅ Completed (Local):
1. Database indexes (24 total) - Performance optimization
2. Database backup system - Automated backups with compression
3. Redis cache implementation - Code ready
4. Production configuration - config_production.py and .env.production.template
5. Sentry integration - Error tracking ready
6. Gunicorn configuration - WSGI server config
7. Nginx configuration - Reverse proxy config
8. Systemd service - Auto-start on boot

### 🚀 Deployment Steps:

---

## Step 1: Prepare Production Server

### Option A: DigitalOcean Droplet
```bash
# 1. Create Droplet (Ubuntu 22.04 LTS)
# - Size: Basic ($12/month - 2GB RAM, 2 vCPUs)
# - Region: Choose closest to users
# - Authentication: SSH Key recommended

# 2. Connect to server
ssh root@your-server-ip

# 3. Update system
apt update && apt upgrade -y
apt install -y python3.11 python3.11-venv python3-pip nginx mysql-server redis-server git ufw
```

### Option B: AWS EC2
```bash
# 1. Launch EC2 instance (t2.small or t2.medium)
# 2. Configure Security Group (ports: 22, 80, 443, 3306, 6379)
# 3. Connect via SSH
# 4. Install dependencies (same as above)
```

---

## Step 2: Setup Firewall

```bash
# Allow SSH, HTTP, HTTPS
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
ufw status
```

---

## Step 3: Configure MySQL

```bash
# Secure MySQL installation
mysql_secure_installation
# - Set root password: YES
# - Remove anonymous users: YES
# - Disallow root login remotely: YES
# - Remove test database: YES
# - Reload privilege tables: YES

# Create production database and user
mysql -u root -p
```

```sql
-- In MySQL shell
CREATE DATABASE eyecare_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER 'eyecare_prod'@'localhost' IDENTIFIED BY 'STRONG_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON eyecare_db.* TO 'eyecare_prod'@'localhost';
FLUSH PRIVILEGES;

-- Import your database
USE eyecare_db;
SOURCE /path/to/your/database.sql;

-- Verify
SHOW TABLES;
SELECT COUNT(*) FROM admins;
EXIT;
```

---

## Step 4: Setup Application

```bash
# Create application user
useradd -m -s /bin/bash eyecare
usermod -aG www-data eyecare

# Switch to application user
su - eyecare

# Clone or upload your application
cd /home/eyecare
# Option 1: Git
git clone https://github.com/your-repo/eyecare_admin.git
# Option 2: Upload via SCP
# scp -r D:\Users\johnv\Projects\eyecare_admin root@server-ip:/home/eyecare/

cd eyecare_admin

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create required directories
mkdir -p logs static/uploads backups

# Set permissions
chmod 755 /home/eyecare/eyecare_admin
chmod 750 logs static/uploads backups
```

---

## Step 5: Configure Environment

```bash
# Copy production environment template
cp .env.production.template .env.production

# Edit with production values
nano .env.production
```

Update these values:
```env
SECRET_KEY=<generate_with_python_secrets_token_hex>
DEBUG=False
DB_HOST=localhost
DB_USER=eyecare_prod
DB_PASSWORD=<your_mysql_password>
DB_NAME=eyecare_db
REDIS_HOST=localhost
MAIL_USERNAME=<your_gmail>
MAIL_PASSWORD=<app_password>
SENTRY_DSN=<your_sentry_dsn>
SERVER_NAME=your-domain.com
```

Generate SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## Step 6: Setup Sentry (Error Tracking)

1. **Create Sentry Account**: Visit https://sentry.io/signup/
2. **Create Project**: Select "Flask" as platform
3. **Copy DSN**: Add to `.env.production`
4. **Test**: Run test error to verify

```bash
# Test Sentry
python3 << EOF
from sentry_integration import init_sentry
from flask import Flask
app = Flask(__name__)
init_sentry(app)
1/0  # This will send error to Sentry
EOF
```

---

## Step 7: Setup Redis

```bash
# Configure Redis
sudo nano /etc/redis/redis.conf

# Update these settings:
# bind 127.0.0.1
# maxmemory 256mb
# maxmemory-policy allkeys-lru
# requirepass YOUR_REDIS_PASSWORD

# Restart Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server
sudo systemctl status redis-server

# Test Redis
redis-cli
> AUTH YOUR_REDIS_PASSWORD
> PING
> SET test "Hello"
> GET test
> DEL test
> EXIT
```

Update `.env.production` with Redis password.

---

## Step 8: Run Database Migrations

```bash
source venv/bin/activate

# Add database indexes
python add_database_indexes.py

# Verify indexes
python3 << EOF
from database import get_db_connection
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute("SHOW INDEX FROM admins")
print(cursor.fetchall())
conn.close()
EOF
```

---

## Step 9: Setup Gunicorn (WSGI Server)

```bash
# Test Gunicorn locally
gunicorn --bind 127.0.0.1:8000 --workers 4 --worker-class gevent app:app

# Test from another terminal
curl http://127.0.0.1:8000

# If working, setup systemd service
exit  # Back to root user

# Copy service file
cp /home/eyecare/eyecare_admin/eyecare_admin.service /etc/systemd/system/

# Edit paths if needed
nano /etc/systemd/system/eyecare_admin.service

# Start service
systemctl daemon-reload
systemctl start eyecare_admin
systemctl enable eyecare_admin
systemctl status eyecare_admin

# View logs
journalctl -u eyecare_admin -f
```

---

## Step 10: Setup Nginx (Reverse Proxy)

```bash
# Copy Nginx config
cp /home/eyecare/eyecare_admin/nginx_config.conf /etc/nginx/sites-available/eyecare_admin

# Edit domain and paths
nano /etc/nginx/sites-available/eyecare_admin
# Replace: your-domain.com with actual domain
# Replace: /home/user/ with /home/eyecare/

# Test configuration
nginx -t

# Enable site
ln -s /etc/nginx/sites-available/eyecare_admin /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default  # Remove default site

# Restart Nginx
systemctl restart nginx
systemctl enable nginx
systemctl status nginx
```

---

## Step 11: Setup SSL/HTTPS (Let's Encrypt)

```bash
# Install Certbot
apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
certbot --nginx -d your-domain.com -d www.your-domain.com

# Test renewal
certbot renew --dry-run

# Certificate auto-renewal (already configured by certbot)
systemctl status certbot.timer

# Verify SSL
curl -I https://your-domain.com
```

Alternative: Use Cloudflare for free SSL

---

## Step 12: Setup Monitoring

### Option A: Simple Monitoring Script
```bash
nano /home/eyecare/monitor.sh
```

```bash
#!/bin/bash
# Simple monitoring script

# Check if services are running
check_service() {
    if systemctl is-active --quiet $1; then
        echo "✓ $1 is running"
    else
        echo "✗ $1 is down"
        systemctl restart $1
        # Send alert email
        echo "$1 was down and restarted on $(date)" | mail -s "Service Alert" admin@yourdomain.com
    fi
}

check_service eyecare_admin
check_service nginx
check_service mysql
check_service redis-server

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "✗ Disk usage is ${DISK_USAGE}%"
fi

# Check database
mysql -u eyecare_prod -p'PASSWORD' eyecare_db -e "SELECT 1" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Database is accessible"
else
    echo "✗ Database is down"
fi
```

```bash
chmod +x /home/eyecare/monitor.sh

# Add to crontab (run every 5 minutes)
crontab -e
# Add: */5 * * * * /home/eyecare/monitor.sh >> /home/eyecare/logs/monitor.log 2>&1
```

### Option B: Use UptimeRobot (Free)
1. Visit: https://uptimerobot.com/
2. Add HTTP(s) monitor for your domain
3. Setup email/SMS alerts

---

## Step 13: Setup Automated Backups

```bash
# Create backup script
nano /home/eyecare/backup_cron.sh
```

```bash
#!/bin/bash
cd /home/eyecare/eyecare_admin
source venv/bin/activate
python database_backup.py

# Upload to cloud storage (optional)
# aws s3 cp backups/ s3://your-bucket/backups/ --recursive
# rsync -avz backups/ user@backup-server:/backups/
```

```bash
chmod +x /home/eyecare/backup_cron.sh

# Schedule daily backups at 2 AM
crontab -e -u eyecare
# Add: 0 2 * * * /home/eyecare/backup_cron.sh >> /home/eyecare/logs/backup.log 2>&1
```

---

## Step 14: Security Hardening

```bash
# Disable root SSH login
nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
systemctl restart sshd

# Install fail2ban (brute force protection)
apt install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban

# Configure fail2ban for nginx
nano /etc/fail2ban/jail.local
```

```ini
[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/eyecare_admin_error.log

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/eyecare_admin_error.log
```

```bash
systemctl restart fail2ban

# Check fail2ban status
fail2ban-client status
```

---

## Step 15: Performance Optimization

### Database Optimization
```sql
-- Add indexes (already done via add_database_indexes.py)
-- Optimize tables
OPTIMIZE TABLE admins, users, assessments, activity_logs;

-- Enable query cache (if needed)
SET GLOBAL query_cache_size = 67108864; -- 64MB
SET GLOBAL query_cache_type = 1;
```

### Nginx Caching
```nginx
# Add to nginx config
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 365d;
    add_header Cache-Control "public, immutable";
}
```

### Gunicorn Tuning
```python
# gunicorn_config.py
workers = (2 * CPU_CORES) + 1  # Calculate based on server
worker_class = "gevent"  # Better concurrency
```

---

## Step 16: Testing Production Deployment

```bash
# Test 1: Health Check
curl https://your-domain.com/health

# Test 2: Login
curl -X POST https://your-domain.com/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'

# Test 3: SSL Grade
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=your-domain.com

# Test 4: Performance
# Visit: https://pagespeed.web.dev/

# Test 5: Security Headers
# Visit: https://securityheaders.com/?q=your-domain.com

# Test 6: Load Testing (optional)
apt install -y apache2-utils
ab -n 1000 -c 10 https://your-domain.com/
```

---

## Step 17: Post-Deployment Checklist

- [ ] All services running (Gunicorn, Nginx, MySQL, Redis)
- [ ] SSL certificate valid (A+ grade on SSLLabs)
- [ ] Firewall configured (UFW enabled)
- [ ] Backups automated (daily at 2 AM)
- [ ] Monitoring configured (UptimeRobot or monitor.sh)
- [ ] Sentry error tracking working
- [ ] Redis caching enabled
- [ ] Database indexes created
- [ ] Security headers present
- [ ] Fail2ban configured
- [ ] Logs rotating properly
- [ ] Email notifications working
- [ ] Admin account created
- [ ] Rate limiting enabled
- [ ] CSRF protection enabled
- [ ] Production environment variables set

---

## Troubleshooting

### Gunicorn won't start
```bash
journalctl -u eyecare_admin -n 50
# Check logs for Python errors
sudo -u eyecare /home/eyecare/eyecare_admin/venv/bin/python /home/eyecare/eyecare_admin/app.py
```

### Nginx 502 Bad Gateway
```bash
# Check if Gunicorn is running
systemctl status eyecare_admin
# Check if port 8000 is listening
ss -tlnp | grep 8000
# Check Nginx error log
tail -f /var/log/nginx/eyecare_admin_error.log
```

### Database connection error
```bash
# Test MySQL connection
mysql -u eyecare_prod -p eyecare_db
# Check if MySQL is running
systemctl status mysql
# Check firewall
ufw status
```

### Redis connection error
```bash
# Test Redis
redis-cli PING
# Check if Redis is running
systemctl status redis-server
# Check logs
tail -f /var/log/redis/redis-server.log
```

---

## Maintenance Tasks

### Daily
- Monitor error logs
- Check Sentry dashboard
- Verify backups completed

### Weekly
- Review database size
- Check disk space
- Analyze performance metrics
- Review activity logs

### Monthly
- Update system packages
- Rotate logs manually if needed
- Test backup restore
- Security audit
- Performance optimization

---

## Useful Commands

```bash
# View application logs
tail -f /home/eyecare/eyecare_admin/logs/app.log

# View Gunicorn logs
journalctl -u eyecare_admin -f

# View Nginx access logs
tail -f /var/log/nginx/eyecare_admin_access.log

# Restart application
systemctl restart eyecare_admin

# Reload Nginx (no downtime)
nginx -s reload

# Check all services
systemctl status eyecare_admin nginx mysql redis-server

# Database backup
cd /home/eyecare/eyecare_admin
source venv/bin/activate
python database_backup.py

# Database restore
python database_backup.py restore backups/filename.sql.gz

# Clear Redis cache
redis-cli FLUSHALL

# Monitor server resources
htop
```

---

## Estimated Timeline

| Task | Time | Difficulty |
|------|------|------------|
| Server setup | 1 hour | Easy |
| MySQL configuration | 30 min | Easy |
| Application deployment | 1 hour | Medium |
| Gunicorn setup | 30 min | Easy |
| Nginx setup | 30 min | Medium |
| SSL setup | 30 min | Easy |
| Sentry setup | 30 min | Easy |
| Redis setup | 30 min | Easy |
| Monitoring setup | 1 hour | Medium |
| Security hardening | 1 hour | Medium |
| Testing | 1 hour | Medium |
| **Total** | **8 hours** | **Medium** |

---

## Cost Estimate

### Cloud Hosting (Monthly)
- **DigitalOcean Droplet**: $12/month (2GB RAM, 2 vCPUs, 50GB SSD)
- **AWS EC2**: ~$15/month (t2.small)
- **Domain**: $12/year (~$1/month)
- **SSL**: Free (Let's Encrypt)
- **Sentry**: Free (5K errors/month)
- **UptimeRobot**: Free (50 monitors)
- **Total**: ~$13-16/month

### Self-Hosted (One-time + Electricity)
- **VPS/Server**: $200-500 (one-time hardware)
- **Electricity**: ~$5-10/month
- **Internet**: Existing
- **Domain**: $12/year
- **SSL**: Free
- **Total**: $5-10/month after initial investment

---

## Need Help?

1. **Documentation**: Check Flask, Gunicorn, Nginx docs
2. **Logs**: Always check logs first
3. **Sentry**: Review error dashboard
4. **Community**: Stack Overflow, Flask Discord
5. **Support**: Hire DevOps consultant if needed

---

## Congratulations! 🎉

Your EyeCare Admin application is now production-ready and deployed!

**Next Steps:**
1. Add your domain to DNS
2. Test all functionality
3. Create admin accounts
4. Import production data
5. Monitor performance
6. Set up analytics (optional)
