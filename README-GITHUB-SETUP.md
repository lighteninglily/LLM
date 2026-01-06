# GitHub Repository Setup Instructions

## For Lightning Lily Team

This document explains how to push this local AI server code to the Lightning Lily GitHub repository.

---

## Prerequisites

1. GitHub account with access to `lightninglily` organization
2. Git installed locally
3. Repository `LLM` should exist at: https://github.com/lightninglily/LLM

---

## Initial Push to GitHub

### Step 1: Initialize Git Repository (if not already done)

```bash
cd c:\Users\rsbiz\Documents\LLM\local-ai-server

# Initialize git if needed
git init

# Add all files
git add .

# First commit
git commit -m "Initial commit: RTX 5090 + Qwen3-32B local AI server with web deployment"
```

### Step 2: Connect to GitHub Repository

```bash
# Add remote (if repository exists)
git remote add origin https://github.com/lightninglily/LLM.git

# Or if repository doesn't exist yet, create it first on GitHub
# Then add remote
```

### Step 3: Push to GitHub

```bash
# Push to main branch
git branch -M main
git push -u origin main
```

---

## Making Scripts Executable on GitHub

**Important**: Shell scripts need executable permissions.

```bash
# Make scripts executable locally
chmod +x install-ubuntu-rtx5090.sh
chmod +x deploy-web-facing.sh
chmod +x bootstrap.sh

# Stage the permission changes
git add install-ubuntu-rtx5090.sh
git add deploy-web-facing.sh
git add bootstrap.sh

# Commit
git commit -m "Set executable permissions on shell scripts"

# Push
git push
```

---

## Repository Structure

```
LLM/
├── README.md                           # Main documentation
├── QUICKSTART-UBUNTU.md                # Quick start guide
├── DEPLOYMENT-GUIDE-RTX5090.md         # Detailed deployment
├── WEB-DEPLOYMENT-GUIDE.md             # Web-facing setup
├── PRE-DEPLOYMENT-CHECKLIST.md         # Issue tracking
├── install-ubuntu-rtx5090.sh           # Main installation script
├── deploy-web-facing.sh                # Web deployment script
├── bootstrap.sh                        # Alternative installer
├── deploy.py                           # Deployment automation
├── models.py                           # Model management
├── test_server.py                      # Testing utilities
├── docker-compose.yml                  # Docker configuration
├── docker-compose.single-gpu.yml       # Single GPU variant
├── docker-compose.ollama.yml           # Ollama variant
├── .env.example                        # Environment template
├── example-data-analysis.py            # Python API examples
└── .gitignore                          # Git ignore rules
```

---

## Branch Strategy

### Main Branch
- Production-ready code
- All files tested and working
- Default branch for users to clone

### Development Branch (Optional)
```bash
# Create dev branch for testing
git checkout -b development
# Make changes, test
git push -u origin development

# Merge to main when ready
git checkout main
git merge development
git push
```

---

## GitHub Repository Settings

### 1. Create Repository Description
```
Local AI server with Qwen3-32B for RTX 5090. Includes automated Ubuntu setup, web deployment, and data analysis platform.
```

### 2. Add Topics
- `ai`
- `llm`
- `qwen`
- `rtx-5090`
- `local-llm`
- `vllm`
- `anythingllm`
- `nvidia`
- `ubuntu`
- `data-analysis`

### 3. Set Default Branch
- Ensure `main` is the default branch

### 4. Enable GitHub Pages (Optional)
- Settings → Pages
- Source: Deploy from main branch
- Uses README.md as homepage

---

## Verifying GitHub Setup

### Test Clone from GitHub
```bash
# From another directory
git clone https://github.com/lightninglily/LLM.git
cd LLM

# Verify scripts are executable
ls -la *.sh

# Should show: -rwxr-xr-x (executable)
```

### Test Raw File Access
```bash
# Should work without error
wget https://raw.githubusercontent.com/lightninglily/LLM/main/install-ubuntu-rtx5090.sh

# Check file downloaded
ls -lh install-ubuntu-rtx5090.sh
```

---

## Updating Repository

### After Making Changes Locally

```bash
cd c:\Users\rsbiz\Documents\LLM\local-ai-server

# Check status
git status

# Stage changes
git add .

# Commit with descriptive message
git commit -m "Fix: Improved error handling in install script"

# Push to GitHub
git push
```

### Creating Releases

For major milestones:

```bash
# Tag a release
git tag -a v1.0.0 -m "v1.0.0: Production-ready RTX 5090 deployment"
git push origin v1.0.0
```

Then create release on GitHub:
1. Go to repository
2. Click "Releases"
3. "Draft a new release"
4. Select tag v1.0.0
5. Add release notes

---

## GitHub Authentication

### Using Personal Access Token

```bash
# Configure git to use token
git config --global credential.helper store

# When prompted, use:
# Username: your_github_username
# Password: your_personal_access_token (not your actual password)
```

### Using SSH (Recommended)

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add to GitHub: Settings → SSH and GPG keys → New SSH key

# Change remote to SSH
git remote set-url origin git@github.com:lightninglily/LLM.git
```

---

## README.md Badge (Optional)

Add status badges to README.md:

```markdown
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04-orange.svg)
![GPU](https://img.shields.io/badge/GPU-RTX%205090-green.svg)
```

---

## Repository Access Control

### For Team Members
1. Go to repository Settings
2. Manage Access
3. Invite collaborators
4. Set appropriate permissions:
   - **Admin**: Full access
   - **Write**: Can push commits
   - **Read**: Can only clone/view

---

## Files to Never Commit

**Already in .gitignore:**
- `.env` (contains secrets)
- `.local-ai-server/` (runtime data)
- `__pycache__/`
- IDE config files

**Always use .env.example** as template, never commit actual `.env` with tokens/keys.

---

## Quick Reference Commands

```bash
# Clone repository
git clone https://github.com/lightninglily/LLM.git

# Check status
git status

# Add all changes
git add .

# Commit changes
git commit -m "Your message here"

# Push to GitHub
git push

# Pull latest changes
git pull

# View commit history
git log --oneline

# Create new branch
git checkout -b feature-name

# Switch branches
git checkout main
```

---

## Troubleshooting

### Permission Denied
```bash
# If you get permission denied
# Use SSH or update credentials
git remote set-url origin git@github.com:lightninglily/LLM.git
```

### Large File Warnings
```bash
# If files are too large (>50MB)
# Use Git LFS for model files if needed
git lfs install
git lfs track "*.bin"
```

### Merge Conflicts
```bash
# If conflicts occur
git status  # Shows conflicted files
# Edit files to resolve conflicts
git add .
git commit -m "Resolved merge conflicts"
git push
```

---

## Ready to Push?

**Checklist before pushing:**
- [x] All placeholder URLs updated to `lightninglily/LLM`
- [x] Scripts have executable permissions
- [x] .gitignore file created
- [x] No sensitive data in files (no real tokens/passwords)
- [x] README.md is complete
- [x] All documentation files present

**You're ready to push to GitHub!**
