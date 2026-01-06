# PowerShell script to commit to Lightning Lily GitHub repository
# Run this from the local-ai-server directory

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Committing to GitHub - Lightning Lily LLM Repository" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if in correct directory
if (-not (Test-Path "install-ubuntu-rtx5090.sh")) {
    Write-Host "ERROR: Not in correct directory!" -ForegroundColor Red
    Write-Host "Please run this from: C:\Users\rsbiz\Documents\LLM\local-ai-server" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if git is installed
try {
    git --version | Out-Null
} catch {
    Write-Host "ERROR: Git not found!" -ForegroundColor Red
    Write-Host "Please install Git for Windows from: https://git-scm.com/download/win" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Step 1: Initializing Git repository..." -ForegroundColor Green
git init

Write-Host ""
Write-Host "Step 2: Setting executable permissions on scripts..." -ForegroundColor Green
git update-index --chmod=+x install-ubuntu-rtx5090.sh
git update-index --chmod=+x deploy-web-facing.sh
git update-index --chmod=+x bootstrap.sh
git update-index --chmod=+x create-usb-installer.sh

Write-Host ""
Write-Host "Step 3: Adding all files..." -ForegroundColor Green
git add .

Write-Host ""
Write-Host "Step 4: Creating commit..." -ForegroundColor Green
git commit -m @"
Initial: RTX 5090 + Qwen3-32B local AI server

- Automated Ubuntu 24.04 installation
- NVIDIA RTX 5090 optimized
- vLLM + AnythingLLM deployment
- Qwen3-32B (2026 SOTA)
- Web deployment with HTTPS
- USB installer support
- Complete documentation
- All issues pre-fixed
"@

Write-Host ""
Write-Host "Step 5: Adding remote repository..." -ForegroundColor Green
git remote remove origin 2>$null
git remote add origin https://github.com/lightninglily/LLM.git

Write-Host ""
Write-Host "Step 6: Pushing to GitHub..." -ForegroundColor Green
Write-Host "NOTE: You will be prompted for GitHub credentials" -ForegroundColor Yellow
Write-Host "Username: Your GitHub username" -ForegroundColor Yellow
Write-Host "Password: Use Personal Access Token (not your password)" -ForegroundColor Yellow
Write-Host ""

git branch -M main
$pushResult = git push -u origin main 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Red
    Write-Host "  Push failed! This might be because:" -ForegroundColor Red
    Write-Host "  1. Repository doesn't exist yet at lightninglily/LLM" -ForegroundColor Yellow
    Write-Host "  2. Authentication failed" -ForegroundColor Yellow
    Write-Host "  3. No internet connection" -ForegroundColor Yellow
    Write-Host "================================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "To create repository:" -ForegroundColor Cyan
    Write-Host "1. Go to https://github.com/lightninglily" -ForegroundColor White
    Write-Host "2. Click 'New repository'" -ForegroundColor White
    Write-Host "3. Name: LLM" -ForegroundColor White
    Write-Host "4. Create repository" -ForegroundColor White
    Write-Host "5. Run this script again" -ForegroundColor White
    Write-Host ""
    Write-Host "Error details:" -ForegroundColor Yellow
    Write-Host $pushResult -ForegroundColor Gray
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "  SUCCESS! Pushed to GitHub" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Repository: https://github.com/lightninglily/LLM" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Verify files at: https://github.com/lightninglily/LLM" -ForegroundColor White
Write-Host "2. Create USB installer if needed" -ForegroundColor White
Write-Host "3. Wait for your computer to arrive!" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"
