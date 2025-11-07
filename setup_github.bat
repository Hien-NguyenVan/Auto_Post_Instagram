@echo off
REM GitHub Setup Script for Instagram Automation Tool
REM This script helps you initialize Git and push to GitHub

echo ================================================================================
echo           GITHUB SETUP - Instagram Automation Tool
echo ================================================================================
echo.

REM Check if Git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git is not installed!
    echo.
    echo Please install Git from: https://git-scm.com/download/win
    echo Make sure to check "Add to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [OK] Git is installed
echo.

REM Check if already initialized
if exist ".git" (
    echo [INFO] Git repository already initialized.
    echo.
    git remote -v
    echo.
    echo Current remotes shown above.
    echo.
    choice /C YN /M "Do you want to reconfigure remote URL?"
    if errorlevel 2 goto skip_init
    if errorlevel 1 goto configure_remote
) else (
    echo [INFO] Initializing new Git repository...
    git init
    if errorlevel 1 (
        echo [ERROR] Failed to initialize Git repository!
        pause
        exit /b 1
    )
    echo [OK] Git initialized
    echo.
)

:configure_remote
echo ================================================================================
echo                           ENTER YOUR GITHUB INFO
echo ================================================================================
echo.
echo You need to create a GitHub repository first at: https://github.com/new
echo.
set /p username="Enter your GitHub username: "
set /p reponame="Enter repository name (e.g., instagram-tool): "
echo.

REM Remove existing remote if any
git remote remove origin 2>nul

REM Add new remote
git remote add origin https://github.com/%username%/%reponame%.git
if errorlevel 1 (
    echo [ERROR] Failed to add remote!
    pause
    exit /b 1
)

echo [OK] Remote added: https://github.com/%username%/%reponame%.git
echo.

:skip_init
echo ================================================================================
echo                         PREPARING FIRST COMMIT
echo ================================================================================
echo.

REM Check for changes
git status

echo.
echo [INFO] Adding all files to Git...
git add .
if errorlevel 1 (
    echo [ERROR] Failed to add files!
    pause
    exit /b 1
)

echo [OK] Files added
echo.

REM Create commit
echo [INFO] Creating commit...
git commit -m "Initial commit - Instagram Automation Tool v1.0"
if errorlevel 1 (
    echo [WARN] Nothing to commit or commit failed
    echo This is OK if you already committed before.
    echo.
)

echo ================================================================================
echo                           READY TO PUSH
echo ================================================================================
echo.
echo About to push code to GitHub.
echo.
echo IMPORTANT: GitHub will ask for authentication:
echo   - Username: Your GitHub username
echo   - Password: Use Personal Access Token (NOT your password)
echo.
echo How to get Personal Access Token:
echo   1. Go to: https://github.com/settings/tokens
echo   2. Click "Generate new token (classic)"
echo   3. Select scope: "repo" (all)
echo   4. Copy the token
echo   5. Paste it when prompted for password
echo.
pause

REM Set default branch to main
git branch -M main

REM Push to GitHub
echo [INFO] Pushing to GitHub...
git push -u origin main
if errorlevel 1 (
    echo.
    echo [ERROR] Push failed!
    echo.
    echo Common issues:
    echo   - Authentication failed: Use Personal Access Token
    echo   - Repository not empty: Delete repo and create new one
    echo   - Network issue: Check internet connection
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo                           SUCCESS!
echo ================================================================================
echo.
echo [OK] Code pushed to GitHub successfully!
echo.
echo Your repository: https://github.com/%username%/%reponame%
echo.
echo NEXT STEPS:
echo   1. Verify code at: https://github.com/%username%/%reponame%
echo   2. Update README.txt in dist/InstagramTool_Portable/ with your repo URL
echo   3. When you make changes, use these commands:
echo      - git add .
echo      - git commit -m "Your message"
echo      - git push origin main
echo.
echo   4. Tell users to run updater.exe to get updates!
echo.
pause
