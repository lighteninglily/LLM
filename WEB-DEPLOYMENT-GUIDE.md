# Web-Facing Deployment Guide - AI Data Analysis Platform

## Overview

This guide automates the deployment of your local AI server to be web-facing with:
- **HTTPS/SSL** via Let's Encrypt
- **Authentication** (AnythingLLM built-in)
- **Rate limiting** to prevent abuse
- **Firewall** protection
- **Automatic monitoring** and SSL renewal
- **Daily backups**

## Prerequisites

1. ✓ Local AI server installed (from QUICKSTART-UBUNTU.md)
2. ✓ Server running and tested locally
3. **Domain name** pointing to your server IP
4. **Server with public IP** (not behind NAT)
5. **Ports 80 and 443** accessible from internet

## Architecture

```
Internet
    ↓
Firewall (ufw) - Port 80, 443
    ↓
Nginx (Reverse Proxy + SSL)
    ├→ Rate Limiting (10 req/s API, 30 req/s UI)
    ├→ Security Headers
    └→ Fail2ban (brute force protection)
        ↓
        ├→ AnythingLLM (Port 3001) - UI for data analysis
        └→ vLLM API (Port 8000) - Direct API access
            ↓
        Qwen3-32B on RTX 5090
```

## Step 1: Prepare Your Domain

### Option A: Using Your Own Domain

Point your domain's DNS A record to your server's public IP:

```
Type: A
Name: ai (or @ for root domain)
Value: YOUR_SERVER_PUBLIC_IP
TTL: 300
```

Wait 5-10 minutes for DNS propagation.

Test: `ping ai.yourdomain.com` should show your server IP.

### Option B: Using a Dynamic DNS Service

If you don't have a static IP, use services like:
- DuckDNS (free)
- No-IP (free tier)
- Dynu (free)

## Step 2: Run Automated Deployment

```bash
cd ~/local-ai-server

# Make script executable
chmod +x deploy-web-facing.sh

# Run deployment (requires sudo)
sudo ./deploy-web-facing.sh ai.yourdomain.com your@email.com
```

**Replace:**
- `ai.yourdomain.com` with your actual domain
- `your@email.com` with your email (for SSL certificate)

**What it does (5-10 minutes):**
1. Installs and configures nginx
2. Obtains SSL certificate from Let's Encrypt
3. Sets up firewall rules
4. Configures rate limiting
5. Installs fail2ban for security
6. Sets up automatic monitoring
7. Configures daily backups

## Step 3: Verify Deployment

```bash
# Check nginx status
sudo systemctl status nginx

# Check SSL certificate
sudo certbot certificates

# Test HTTPS
curl https://ai.yourdomain.com/health

# View logs
sudo tail -f /var/log/nginx/ai-server-access.log
```

## Step 4: Access Your Web Platform

Open: **https://ai.yourdomain.com**

First time:
1. Create admin account
2. Set up workspace
3. Configure user permissions

## Using the Platform for Data Analysis

### Upload and Analyze Data

1. **Create Workspace**
   - Click "Workspaces" → "New Workspace"
   - Name: "Data Analysis"

2. **Upload Documents**
   - Supported: CSV, Excel, PDF, JSON, TXT
   - Drag and drop files
   - Click "Move to Workspace"

3. **Chat with Your Data**
   - "Analyze the trends in sales_data.csv"
   - "What are the key findings in report.pdf?"
   - "Compare Q1 vs Q2 revenue"

### API Access for Programmatic Analysis

```python
import requests

url = "https://ai.yourdomain.com/api/v1/chat/completions"

headers = {
    "Content-Type": "application/json"
}

data = {
    "model": "Qwen/Qwen3-32B-Instruct",
    "messages": [
        {
            "role": "system",
            "content": "You are a data analyst. Analyze the provided data and give insights."
        },
        {
            "role": "user",
            "content": "Here's my dataset: [paste CSV data]. What are the key trends?"
        }
    ],
    "temperature": 0.3,
    "max_tokens": 2000
}

response = requests.post(url, headers=headers, json=data)
print(response.json()["choices"][0]["message"]["content"])
```

### Jupyter Notebook Integration

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://ai.yourdomain.com/api/v1",
    api_key="not-needed"  # Or set API key in AnythingLLM settings
)

# Analyze data
response = client.chat.completions.create(
    model="Qwen/Qwen3-32B-Instruct",
    messages=[
        {"role": "user", "content": f"Analyze this data:\n{df.to_csv()}"}
    ]
)

print(response.choices[0].message.content)
```

## Security Configuration

### User Management

1. **Admin Dashboard**: https://ai.yourdomain.com
2. Click "Settings" → "Users"
3. Add users with different roles:
   - **Admin**: Full access
   - **Manager**: Can create workspaces
   - **User**: Can use existing workspaces

### API Key Setup (Optional)

For additional API security:

1. Go to Settings → API Keys
2. Generate new API key
3. Use in requests:
   ```bash
   curl https://ai.yourdomain.com/api/v1/chat/completions \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model": "Qwen/Qwen3-32B-Instruct", "messages": [...]}'
   ```

### Rate Limiting

Default limits (configurable in `/etc/nginx/sites-available/ai-server`):
- **API**: 10 requests/second per IP
- **UI**: 30 requests/second per IP

To change:
```bash
sudo nano /etc/nginx/sites-available/ai-server
# Edit: rate=10r/s to your desired rate
sudo systemctl reload nginx
```

### Firewall Rules

```bash
# View current rules
sudo ufw status

# Allow specific IP only (optional - more restrictive)
sudo ufw allow from YOUR_OFFICE_IP to any port 443

# Block all other access
sudo ufw default deny incoming
```

## Monitoring

### Real-time Monitoring

```bash
# nginx access logs
sudo tail -f /var/log/nginx/ai-server-access.log

# nginx error logs
sudo tail -f /var/log/nginx/ai-server-error.log

# System monitor log
sudo tail -f /var/log/ai-server-monitor.log

# Container status
docker compose ps

# GPU usage
watch -n 1 nvidia-smi
```

### Monitor Dashboard (Optional - Install Grafana)

```bash
# Quick install
sudo apt-get install -y grafana
sudo systemctl enable grafana-server
sudo systemctl start grafana-server

# Access: http://your-server-ip:3000
# Default login: admin/admin
```

## Backups

### Automatic Backups

Daily at 2 AM:
- AnythingLLM data
- nginx configuration
- Stored in: `/var/backups/ai-server/`
- Retention: 7 days

### Manual Backup

```bash
sudo /usr/local/bin/ai-server-backup.sh
```

### Restore from Backup

```bash
# List backups
ls -lh /var/backups/ai-server/

# Restore AnythingLLM data
sudo tar -xzf /var/backups/ai-server/anythingllm-YYYYMMDD_HHMMSS.tar.gz \
  -C ~/.local-ai-server/data/
```

## Troubleshooting

### SSL Certificate Issues

```bash
# Test certificate
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal

# Check nginx SSL config
sudo nginx -t
```

### 502 Bad Gateway

```bash
# Check if containers are running
docker compose ps

# Restart containers
cd ~/.local-ai-server
docker compose restart

# Check nginx can reach backend
curl http://localhost:3001
curl http://localhost:8000/health
```

### Rate Limit Errors (429)

```bash
# Check rate limit logs
sudo grep "limiting requests" /var/log/nginx/ai-server-error.log

# Temporarily increase limits
sudo nano /etc/nginx/sites-available/ai-server
# Change rate=10r/s to rate=50r/s
sudo systemctl reload nginx
```

### High Memory Usage

```bash
# Check GPU memory
nvidia-smi

# Check container memory
docker stats

# If needed, reduce context length
nano ~/.local-ai-server/.env
# Set: MAX_MODEL_LEN=2048
docker compose restart
```

## Performance Optimization

### Enable Caching (nginx)

```bash
sudo nano /etc/nginx/sites-available/ai-server
```

Add inside `server` block:
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=llm_cache:10m max_size=1g;
proxy_cache llm_cache;
proxy_cache_valid 200 5m;
```

### Increase Worker Connections

```bash
sudo nano /etc/nginx/nginx.conf
```

Change:
```nginx
worker_connections 2048;  # Increase from default 768
```

## Scaling Up

### Multiple GPUs

If you add more GPUs later:

```bash
nano ~/.local-ai-server/.env
# Set: TENSOR_PARALLEL_SIZE=2

docker compose restart
```

### Load Balancing (Multiple Servers)

For high traffic, use nginx load balancer pointing to multiple AI servers.

## Costs

### Estimated Monthly Costs

**If using cloud server:**
- VPS (8 cores, 64GB RAM, RTX 5090): $200-500/month
- Domain: $10-15/year
- SSL: Free (Let's Encrypt)
- Bandwidth: Depends on usage

**Self-hosted (on-premise):**
- Hardware: One-time cost
- Electricity: ~$30-50/month for 24/7 operation
- Domain: $10-15/year
- Internet: Existing connection

## Security Best Practices

1. **Change default ports** (edit docker-compose.yml)
2. **Set strong admin password** in AnythingLLM
3. **Enable 2FA** if available in future updates
4. **Regular updates**: 
   ```bash
   sudo apt-get update && sudo apt-get upgrade
   docker compose pull
   ```
5. **Monitor access logs** for suspicious activity
6. **Use VPN** for admin access if possible

## Maintenance

### Weekly Tasks
- Check logs for errors
- Review fail2ban reports
- Monitor SSL certificate expiry

### Monthly Tasks
- Update system packages
- Update Docker images
- Review and clean old backups
- Check disk space usage

### Quarterly Tasks
- Security audit
- Performance review
- Backup testing (restore test)

## Support

**Logs to check:**
- `/var/log/nginx/ai-server-*.log`
- `/var/log/ai-server-monitor.log`
- `docker compose logs`

**Configuration files:**
- `/etc/nginx/sites-available/ai-server`
- `~/.local-ai-server/.env`
- `~/.local-ai-server/docker-compose.yml`

**Useful commands:**
```bash
# Full system status
sudo /usr/local/bin/ai-server-monitor.sh

# Restart everything
sudo systemctl restart nginx
cd ~/.local-ai-server && docker compose restart
```

## Next Steps

1. Set up monitoring dashboard (Grafana)
2. Configure user accounts
3. Upload your first dataset
4. Test API integration with your tools
5. Set up automated data ingestion pipelines
