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
echo [INFO] Checking required packages...
python -c "import customtkinter" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] customtkinter is not installed.
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
    echo.
    echo [SUCCESS] Packages installed successfully!
    echo.
)

REM Verify customtkinter is now available
python -c "import customtkinter" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] customtkinter still not available after installation!
    echo.
    echo Please try manually:
    echo   pip install customtkinter>=5.2.0
    echo.
    pause
    exit /b 1
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
