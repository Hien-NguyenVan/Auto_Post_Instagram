@echo off
REM Quick push script with authentication prompt

echo ================================================================================
echo                    PUSH CODE TO GITHUB
echo ================================================================================
echo.
echo Remote: https://github.com/Hien-NguyenVan/Auto_Post_Instagram.git
echo Branch: main
echo.
echo ================================================================================
echo                   AUTHENTICATION REQUIRED
echo ================================================================================
echo.
echo You need a Personal Access Token from GitHub.
echo.
echo How to get it:
echo   1. Go to: https://github.com/settings/tokens
echo   2. Click "Generate new token (classic)"
echo   3. Check "repo" scope
echo   4. Copy the token (ghp_xxxx...)
echo.
echo ================================================================================
echo.

REM Check if there are commits to push
git rev-list --count origin/main..main >nul 2>&1
if errorlevel 1 (
    echo [INFO] First push to remote
) else (
    for /f %%i in ('git rev-list --count origin/main..main') do set COMMITS=%%i
    if !COMMITS! EQU 0 (
        echo [INFO] Already up to date, nothing to push
        pause
        exit /b 0
    )
)

echo [INFO] Pushing to GitHub...
echo.
echo When prompted:
echo   - Username: Hien-NguyenVan
echo   - Password: [PASTE YOUR PERSONAL ACCESS TOKEN]
echo.
echo Note: When you paste token, you won't see it (that's normal)
echo.
pause

REM Push with -u to set upstream
git push -u origin main

if errorlevel 1 (
    echo.
    echo ================================================================================
    echo                              PUSH FAILED
    echo ================================================================================
    echo.
    echo Common issues:
    echo   1. Wrong token or expired token
    echo   2. Token doesn't have "repo" permission
    echo   3. Network connection issue
    echo.
    echo Solutions:
    echo   1. Generate new token at: https://github.com/settings/tokens
    echo   2. Make sure to check "repo" scope
    echo   3. Copy and paste the token when prompted for password
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo                          PUSH SUCCESSFUL!
echo ================================================================================
echo.
echo Code has been pushed to GitHub!
echo.
echo View your repo at:
echo https://github.com/Hien-NguyenVan/Auto_Post_Instagram
echo.
echo Next steps:
echo   1. Verify code on GitHub
echo   2. Update README.txt in dist/InstagramTool_Portable with repo URL
echo   3. Test updater.exe
echo.
pause
