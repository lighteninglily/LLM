# Production RAG Deployment Guide

## Complete System for External Users with Bulk Data

This guide covers deploying a production-ready RAG system with all your data pre-loaded and accessible to external users.

---

## What You're Building

**Complete AI Data Analysis Platform:**
- Local AI (Qwen3-32B, no cloud)
- All your documents uploaded and indexed (RAG)
- Secure web access for external users
- User management and workspaces
- Automated backups
- Monitoring dashboard

---

## Phase 1: Initial Installation (Day 1)

### 1. Install Ubuntu + AI Server

```bash
# Copy from USB or download
wget https://raw.githubusercontent.com/lighteninglily/LLM/main/install-ubuntu-rtx5090.sh
chmod +x install-ubuntu-rtx5090.sh
./install-ubuntu-rtx5090.sh
```

**Result**: Local AI running at http://localhost:3001

---

## Phase 2: Load Your Data (Day 1-2)

### 2. Create Workspaces

```bash
cd ~/llm-installer

# Create example workspace config
python3 setup-workspaces.py --create-example

# Edit workspaces.json with your workspace names
nano workspaces.json

# Create workspaces
python3 setup-workspaces.py --config workspaces.json
```

**Example workspaces.json:**
```json
{
  "workspaces": [
    {
      "name": "Company Knowledge Base",
      "temperature": 0.3,
      "chat_history": 20
    },
    {
      "name": "Sales Data",
      "temperature": 0.5
    }
  ]
}
```

### 3. Bulk Upload Your Documents

```bash
# Upload entire folder to workspace
python3 bulk-ingest-documents.py \
  --workspace "Company Knowledge Base" \
  --folder /path/to/your/documents \
  --recursive

# Upload sales reports
python3 bulk-ingest-documents.py \
  --workspace "Sales Data" \
  --folder /path/to/sales_reports \
  --recursive
```

**Supported file types:**
- Documents: PDF, DOCX, TXT, MD
- Data: CSV, XLSX, JSON
- Code: PY, JS, etc.

**This processes hundreds/thousands of files automatically.**

---

## Phase 3: Make Web-Facing (Day 2)

### 4. Deploy Web Access

```bash
# Get a domain first (ai.yourcompany.com)
# Point DNS A record to your server IP

# Run web deployment
sudo ./deploy-web-facing.sh ai.yourcompany.com your@email.com
```

**Result**: Accessible at https://ai.yourcompany.com with:
- HTTPS/SSL
- Authentication
- Rate limiting
- Firewall
- Automatic monitoring

---

## Phase 4: User Management (Day 2)

### 5. Create User Accounts

**Admin account (you):**
- Created on first access to https://ai.yourcompany.com
- Full access to all workspaces

**External users:**

```bash
# Create user accounts
python3 manage-users.py create \
  --email user@example.com \
  --password SecurePass123 \
  --role default

# Or generate invite links
python3 manage-users.py invite \
  --workspace "Sales Data" \
  --role default
```

**User roles:**
- **admin**: Full access, can create workspaces
- **manager**: Can manage workspaces
- **default**: Can use assigned workspaces

---

## Phase 5: Setup Monitoring (Day 2)

### 6. Install Monitoring Dashboard

```bash
sudo ./setup-monitoring.sh
```

Access Grafana: http://your-server-ip:3000
- Username: admin
- Password: admin (change on first login)

**What you monitor:**
- GPU utilization and temperature
- Memory usage
- Container health
- Request rates
- User activity

---

## Phase 6: Automated Backups (Day 2)

### 7. Setup Backup Schedule

```bash
# Manual backup
./backup-rag-data.sh

# Automated daily backups (add to crontab)
crontab -e

# Add this line:
0 2 * * * /home/username/llm-installer/backup-rag-data.sh >> /var/log/rag-backup.log 2>&1
```

**Backups include:**
- Vector database (your indexed documents)
- Document files
- Configuration
- User data

**Restoration:**
```bash
./restore-rag-data.sh /path/to/backup.tar.gz
```

---

## Complete Workflow Example

### Scenario: Share Sales Data with Team

**1. Upload data:**
```bash
python3 bulk-ingest-documents.py \
  --workspace "Q4 Sales Analysis" \
  --folder ~/sales_data/Q4 \
  --recursive
```

**2. Create user:**
```bash
python3 manage-users.py create \
  --email analyst@company.com \
  --password TempPass123 \
  --role default
```

**3. Share link:**
```
Send to user:
  URL: https://ai.yourcompany.com
  Username: analyst
  Password: TempPass123
  Workspace: Q4 Sales Analysis
```

**4. User can now:**
- Login at https://ai.yourcompany.com
- Select "Q4 Sales Analysis" workspace
- Ask questions like:
  - "What were top performing products?"
  - "Show trends by region"
  - "Compare this month to last month"

**All analysis happens locally, data never leaves your server.**

---

## Security Best Practices

### Authentication
✓ PASSWORDLESS_AUTH=false (enabled by default)
✓ Strong passwords required
✓ Rate limiting active
✓ SSL/HTTPS enforced

### Network
✓ Firewall configured (only ports 80, 443)
✓ fail2ban protecting against brute force
✓ Optional: VPN for admin access

### Data
✓ All processing local (no cloud)
✓ Automated backups
✓ User permissions per workspace
✓ Audit logs enabled

---

## Testing Before External Users

### Pre-Launch Checklist

1. **Test upload:**
```bash
python3 bulk-ingest-documents.py \
  --workspace "Test" \
  --folder ~/test_docs
```

2. **Test queries:**
- Login at https://ai.yourcompany.com
- Select workspace
- Ask test questions
- Verify answers use your documents

3. **Test user access:**
```bash
python3 manage-users.py create \
  --email test@test.com \
  --password test123 \
  --role default
```
- Login as test user
- Verify permissions
- Delete test user

4. **Test backup/restore:**
```bash
./backup-rag-data.sh
./restore-rag-data.sh ~/rag-backups/latest.tar.gz
```

5. **Check monitoring:**
- Open Grafana
- Verify all metrics showing
- Set up alerts if needed

---

## Common Use Cases

### 1. Company Knowledge Base
```bash
# Upload all company docs
python3 bulk-ingest-documents.py \
  --workspace "Company Docs" \
  --folder ~/company_documentation \
  --recursive

# Employees can ask:
# "What's our vacation policy?"
# "How do I submit expenses?"
# "What are the Q1 goals?"
```

### 2. Legal Document Analysis
```bash
# Upload contracts and legal docs
python3 bulk-ingest-documents.py \
  --workspace "Legal" \
  --folder ~/legal_docs \
  --recursive

# Lawyers can ask:
# "Find all contracts with Company X"
# "What are standard termination clauses?"
# "Compare these two agreements"
```

### 3. Customer Support
```bash
# Upload support docs and FAQs
python3 bulk-ingest-documents.py \
  --workspace "Support" \
  --folder ~/support_knowledge_base \
  --recursive

# Support team can ask:
# "How do customers reset passwords?"
# "What's the refund policy?"
# "Troubleshoot error code 500"
```

### 4. Research Analysis
```bash
# Upload research papers
python3 bulk-ingest-documents.py \
  --workspace "Research" \
  --folder ~/papers \
  --recursive

# Researchers can ask:
# "Summarize recent findings on topic X"
# "What methodologies were used?"
# "Compare results across studies"
```

---

## Scaling

### More Users
- Create additional user accounts (unlimited)
- Separate workspaces for different teams
- Monitor usage via Grafana

### More Data
- Current: RTX 5090 handles ~50GB documents
- Scaling: Add more storage
- Performance: Increase `top_n_results` in workspace config

### More Servers
- Deploy multiple instances for different departments
- Each runs independently
- Load balancer for high traffic (advanced)

---

## Troubleshooting

### Documents Not Uploading
```bash
# Check supported file types
python3 bulk-ingest-documents.py --help

# Check AnythingLLM logs
docker compose logs anythingllm

# Verify disk space
df -h
```

### Slow Queries
```bash
# Check GPU usage
nvidia-smi

# Reduce similarity threshold in workspace settings
# Lower = more relevant results only
```

### Users Can't Access
```bash
# Verify web deployment
curl https://ai.yourcompany.com/health

# Check nginx logs
sudo tail -f /var/log/nginx/ai-server-access.log

# Verify firewall
sudo ufw status
```

---

## Maintenance Schedule

### Daily
- Automatic backups (2 AM)
- Log rotation
- Monitoring checks

### Weekly
- Review user activity logs
- Check disk space
- Update any docs that changed

### Monthly
- Update system packages
- Update Docker images
- Test restore from backup
- Review and clean old backups

---

## Cost Breakdown

### Hardware (One-Time)
- RTX 5090 system: $3,000-5,000
- Or cloud VPS: $200-500/month

### Ongoing
- Domain: $10-15/year
- Electricity: $30-50/month (24/7 operation)
- SSL: Free (Let's Encrypt)
- No per-user costs
- No API usage costs
- No cloud storage costs

**Compare to cloud AI:**
- GPT-4 API: $30 per 1M tokens
- Heavy usage: $500-2000/month
- **Break-even: 2-4 months**

---

## Success Metrics

Track in Grafana:
- Active users per day
- Queries per workspace
- Average response time
- GPU utilization
- Document count per workspace

**You're production-ready when:**
- ✓ All your data uploaded and indexed
- ✓ External users can access securely
- ✓ Backups running automatically
- ✓ Monitoring shows healthy system
- ✓ Users getting accurate answers from your docs

---

## Support

**Logs to check:**
- AnythingLLM: `docker compose logs anythingllm`
- vLLM: `docker compose logs vllm`
- nginx: `/var/log/nginx/ai-server-*.log`
- System: `journalctl -u grafana-server`

**Configuration:**
- Workspaces: Web UI → Settings
- Users: `python3 manage-users.py list`
- Backups: `ls ~/rag-backups/`

**Repository:** https://github.com/lighteninglily/LLM
