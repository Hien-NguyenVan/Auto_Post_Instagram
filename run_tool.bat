@echo off
REM Instagram Automation Tool Launcher
REM This batch file launches the Python GUI application

echo ========================================
echo   Instagram Automation Tool
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.10 or newer from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

REM Check if required packages are installed
python -c "import ttkbootstrap" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Some Python packages may not be installed.
    echo.
    echo Installing required packages...
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install packages!
        echo Please run: pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
)

REM Launch the application
echo [INFO] Starting Instagram Automation Tool...
echo.
pythonw main.py

REM If pythonw fails, try python (shows console)
if errorlevel 1 (
    echo [WARNING] GUI mode failed, trying console mode...
    python main.py
)

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start application!
    echo.
    pause
)
