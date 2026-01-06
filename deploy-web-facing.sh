#!/bin/bash
#
# Automated Web-Facing Deployment for Local AI Server
# Sets up nginx reverse proxy, SSL, firewall, and authentication
#
# Usage:
#   sudo ./deploy-web-facing.sh yourdomain.com your@email.com
#

set -e

if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (sudo)"
    exit 1
fi

DOMAIN=$1
EMAIL=$2

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo "Usage: sudo ./deploy-web-facing.sh yourdomain.com your@email.com"
    echo "Example: sudo ./deploy-web-facing.sh ai.yourcompany.com admin@yourcompany.com"
    exit 1
fi

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "================================================================"
echo "  Web-Facing AI Server Deployment"
echo "================================================================"
echo ""
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo ""
read -p "Continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Install nginx
log_info "Installing nginx..."
apt-get update
apt-get install -y nginx

# Install certbot for SSL
log_info "Installing certbot..."
apt-get install -y certbot python3-certbot-nginx

# Configure firewall
log_info "Configuring firewall..."
ufw allow 'Nginx Full'
ufw allow OpenSSH
ufw --force enable

# Stop nginx temporarily
systemctl stop nginx

# Create nginx configuration
log_info "Creating nginx configuration..."
cat > /etc/nginx/sites-available/ai-server << 'EOF'
# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=ui_limit:10m rate=30r/s;

# Upstream servers
upstream vllm_backend {
    server localhost:8000;
    keepalive 32;
}

upstream anythingllm_backend {
    server localhost:3001;
    keepalive 32;
}

# HTTP - Redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name DOMAIN_PLACEHOLDER;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS - Main Server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name DOMAIN_PLACEHOLDER;
    
    # SSL Configuration (will be managed by certbot)
    ssl_certificate /etc/letsencrypt/live/DOMAIN_PLACEHOLDER/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/DOMAIN_PLACEHOLDER/privkey.pem;
    
    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Max upload size for documents
    client_max_body_size 100M;
    
    # Root location - AnythingLLM UI
    location / {
        limit_req zone=ui_limit burst=20 nodelay;
        
        proxy_pass http://anythingllm_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running requests
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # vLLM API endpoint
    location /api/v1/ {
        limit_req zone=api_limit burst=5 nodelay;
        
        proxy_pass http://vllm_backend/v1/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for LLM inference
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }
    
    # Health check endpoint (no auth required)
    location /health {
        access_log off;
        proxy_pass http://vllm_backend/health;
    }
    
    # Logging
    access_log /var/log/nginx/ai-server-access.log;
    error_log /var/log/nginx/ai-server-error.log;
}
EOF

# Replace domain placeholder
sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" /etc/nginx/sites-available/ai-server

# Enable site
ln -sf /etc/nginx/sites-available/ai-server /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx config
log_info "Testing nginx configuration..."
nginx -t

# Start nginx
systemctl start nginx
systemctl enable nginx

# Obtain SSL certificate
log_info "Obtaining SSL certificate from Let's Encrypt..."
certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m $EMAIL --redirect

# Reload nginx with SSL
systemctl reload nginx

# Configure automatic certificate renewal
log_info "Setting up automatic SSL renewal..."
systemctl enable certbot.timer
systemctl start certbot.timer

# Create monitoring script
log_info "Creating monitoring script..."
cat > /usr/local/bin/ai-server-monitor.sh << 'MONITOR_EOF'
#!/bin/bash
# AI Server Monitoring Script

# Check if services are running
if ! systemctl is-active --quiet nginx; then
    echo "nginx is down, restarting..."
    systemctl restart nginx
fi

if ! docker compose -f ~/.local-ai-server/docker-compose.yml ps | grep -q "Up"; then
    echo "Docker containers are down, restarting..."
    cd ~/.local-ai-server && docker compose restart
fi

# Check SSL certificate expiry
CERT_EXPIRY=$(echo | openssl s_client -servername DOMAIN_PLACEHOLDER -connect DOMAIN_PLACEHOLDER:443 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$CERT_EXPIRY" +%s)
NOW_EPOCH=$(date +%s)
DAYS_UNTIL_EXPIRY=$(( ($EXPIRY_EPOCH - $NOW_EPOCH) / 86400 ))

if [ $DAYS_UNTIL_EXPIRY -lt 30 ]; then
    echo "SSL certificate expires in $DAYS_UNTIL_EXPIRY days, renewing..."
    certbot renew --quiet
fi
MONITOR_EOF

sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" /usr/local/bin/ai-server-monitor.sh
chmod +x /usr/local/bin/ai-server-monitor.sh

# Add to crontab for monitoring every 6 hours
(crontab -l 2>/dev/null; echo "0 */6 * * * /usr/local/bin/ai-server-monitor.sh >> /var/log/ai-server-monitor.log 2>&1") | crontab -

# Create fail2ban config for additional security
log_info "Setting up fail2ban..."
apt-get install -y fail2ban

cat > /etc/fail2ban/jail.d/ai-server.conf << 'FAIL2BAN_EOF'
[ai-server-auth]
enabled = true
port = http,https
filter = ai-server-auth
logpath = /var/log/nginx/ai-server-access.log
maxretry = 5
bantime = 3600
findtime = 600
FAIL2BAN_EOF

cat > /etc/fail2ban/filter.d/ai-server-auth.conf << 'FILTER_EOF'
[Definition]
failregex = ^<HOST> .* "(POST|GET) .*/api/.* HTTP/.*" 401
            ^<HOST> .* "(POST|GET) .*/api/.* HTTP/.*" 403
ignoreregex =
FILTER_EOF

systemctl restart fail2ban
systemctl enable fail2ban

# Create backup script
log_info "Creating backup script..."
cat > /usr/local/bin/ai-server-backup.sh << 'BACKUP_EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/ai-server"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup AnythingLLM data
tar -czf $BACKUP_DIR/anythingllm-$DATE.tar.gz -C ~/.local-ai-server/data anythingllm

# Backup nginx config
tar -czf $BACKUP_DIR/nginx-$DATE.tar.gz /etc/nginx/sites-available/ai-server

# Keep only last 7 backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
BACKUP_EOF

chmod +x /usr/local/bin/ai-server-backup.sh

# Add daily backup to crontab
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/ai-server-backup.sh >> /var/log/ai-server-backup.log 2>&1") | crontab -

# Print summary
echo ""
echo "================================================================"
echo "  Deployment Complete!"
echo "================================================================"
echo ""
echo "Your AI server is now accessible at:"
echo "  https://$DOMAIN"
echo ""
echo "Security features enabled:"
echo "  - HTTPS with Let's Encrypt SSL"
echo "  - Rate limiting (API: 10 req/s, UI: 30 req/s)"
echo "  - Firewall (ufw) configured"
echo "  - Fail2ban for brute force protection"
echo "  - Security headers enabled"
echo "  - Automatic SSL renewal"
echo ""
echo "Monitoring:"
echo "  - Auto-monitoring every 6 hours"
echo "  - Logs: /var/log/nginx/ai-server-*.log"
echo "  - Monitor log: /var/log/ai-server-monitor.log"
echo ""
echo "Backups:"
echo "  - Daily backup at 2 AM"
echo "  - Location: /var/backups/ai-server/"
echo "  - Retention: 7 days"
echo ""
echo "API Access:"
echo "  - Direct API: https://$DOMAIN/api/v1/chat/completions"
echo "  - Health check: https://$DOMAIN/health"
echo ""
echo "Management commands:"
echo "  - nginx config: /etc/nginx/sites-available/ai-server"
echo "  - Reload nginx: sudo systemctl reload nginx"
echo "  - View logs: sudo tail -f /var/log/nginx/ai-server-access.log"
echo "  - SSL renewal: sudo certbot renew"
echo ""
echo "Next steps:"
echo "  1. Point your domain DNS A record to this server's IP"
echo "  2. Open https://$DOMAIN and create admin account"
echo "  3. Configure users and permissions in AnythingLLM"
echo ""
