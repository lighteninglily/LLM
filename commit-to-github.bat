@echo off
REM Commit all files to Lightning Lily GitHub repository
REM Run this from the local-ai-server directory

echo ================================================================
echo   Committing to GitHub - Lightning Lily LLM Repository
echo ================================================================
echo.

REM Check if in correct directory
if not exist "install-ubuntu-rtx5090.sh" (
    echo ERROR: Not in correct directory!
    echo Please run this from: C:\Users\rsbiz\Documents\LLM\local-ai-server
    pause
    exit /b 1
)

echo Step 1: Initializing Git repository...
git init
if errorlevel 1 (
    echo Git not found! Please install Git for Windows first.
    pause
    exit /b 1
)

echo.
echo Step 2: Setting executable permissions on scripts...
git update-index --chmod=+x install-ubuntu-rtx5090.sh
git update-index --chmod=+x deploy-web-facing.sh
git update-index --chmod=+x bootstrap.sh
git update-index --chmod=+x create-usb-installer.sh

echo.
echo Step 3: Adding all files...
git add .

echo.
echo Step 4: Creating commit...
git commit -m "Initial: RTX 5090 + Qwen3-32B local AI server - Automated Ubuntu 24.04 installation - NVIDIA RTX 5090 optimized - vLLM + AnythingLLM deployment - Qwen3-32B (2026 SOTA) - Web deployment with HTTPS - USB installer support - Complete documentation - All issues pre-fixed"

echo.
echo Step 5: Adding remote repository...
git remote remove origin 2>nul
git remote add origin https://github.com/lightninglily/LLM.git

echo.
echo Step 6: Pushing to GitHub...
echo NOTE: You will be prompted for GitHub credentials
echo Username: Your GitHub username
echo Password: Use Personal Access Token (not your password)
echo.
git branch -M main
git push -u origin main

if errorlevel 1 (
    echo.
    echo ================================================================
    echo   Push failed! This might be because:
    echo   1. Repository doesn't exist yet at lightninglily/LLM
    echo   2. Authentication failed
    echo   3. No internet connection
    echo ================================================================
    echo.
    echo To create repository:
    echo 1. Go to https://github.com/lightninglily
    echo 2. Click "New repository"
    echo 3. Name: LLM
    echo 4. Create repository
    echo 5. Run this script again
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo   SUCCESS! Pushed to GitHub
echo ================================================================
echo.
echo Repository: https://github.com/lightninglily/LLM
echo.
echo Next steps:
echo 1. Verify files at: https://github.com/lightninglily/LLM
echo 2. Create USB installer if needed
echo 3. Wait for your computer to arrive!
echo.
pause
