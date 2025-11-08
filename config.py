"""
Configuration file for LDPlayer paths and application settings.

Auto-detects LDPlayer installation from Windows Registry or common paths.
"""
import os
import sys
import logging

# Get the directory where the script/exe is running from
if getattr(sys, 'frozen', False):
    # Running as compiled exe (PyInstaller)
    APP_DIR = os.path.dirname(sys.executable)
else:
    # Running as script
    APP_DIR = os.path.dirname(os.path.abspath(__file__))


def find_ldplayer_path():
    """
    Auto-detect LDPlayer installation path.

    Priority:
    1. Environment variable LDPLAYER_PATH
    2. Windows Registry (HKLM\\SOFTWARE\\LDPlayer)
    3. Common installation paths
    4. Manual config file

    Returns:
        str: Path to LDPlayer installation, or None if not found
    """
    # 1. Check environment variable
    env_path = os.environ.get('LDPLAYER_PATH')
    if env_path and os.path.exists(os.path.join(env_path, "ldconsole.exe")):
        return env_path

    # 2. Check Windows Registry
    try:
        import winreg
        # Try HKEY_LOCAL_MACHINE first
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\LDPlayer9")
            path = winreg.QueryValueEx(key, "InstallDir")[0]
            winreg.CloseKey(key)
            if os.path.exists(os.path.join(path, "ldconsole.exe")):
                return path
        except WindowsError:
            pass

        # Try HKEY_CURRENT_USER
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\LDPlayer9")
            path = winreg.QueryValueEx(key, "InstallDir")[0]
            winreg.CloseKey(key)
            if os.path.exists(os.path.join(path, "ldconsole.exe")):
                return path
        except WindowsError:
            pass
    except ImportError:
        # winreg not available (non-Windows)
        pass

    # 3. Check common paths
    common_paths = [
        r"C:\LDPlayer\LDPlayer9",
        r"C:\LDPlayer\LDPlayer4",
        r"C:\Program Files\LDPlayer9",
        r"C:\Program Files\LDPlayer",
        r"C:\Program Files (x86)\LDPlayer9",
        r"C:\Program Files (x86)\LDPlayer",
        r"D:\LDPlayer\LDPlayer9",
        r"D:\LDPlayer\LDPlayer4",
    ]

    for path in common_paths:
        if os.path.exists(os.path.join(path, "ldconsole.exe")):
            return path

    # 4. Check manual config file (ldplayer_path.txt in app directory)
    manual_config = os.path.join(APP_DIR, "ldplayer_path.txt")
    if os.path.exists(manual_config):
        try:
            with open(manual_config, 'r', encoding='utf-8') as f:
                path = f.read().strip()
                if os.path.exists(os.path.join(path, "ldconsole.exe")):
                    return path
        except Exception:
            pass

    return None


# ==================== LDPLAYER PATHS ====================
# Auto-detect LDPlayer path
LDPLAYER_PATH = find_ldplayer_path()

if not LDPLAYER_PATH:
    # Fallback to default if not found
    LDPLAYER_PATH = r"C:\LDPlayer\LDPlayer9"
    logging.warning(f"LDPlayer not found. Using default path: {LDPLAYER_PATH}")
    logging.warning("Create 'ldplayer_path.txt' in app directory to manually specify path.")

# Derived paths (auto-calculated from LDPLAYER_PATH)
LDCONSOLE_EXE = os.path.join(LDPLAYER_PATH, "ldconsole.exe")
ADB_EXE = os.path.join(LDPLAYER_PATH, "adb.exe")
CONFIG_DIR = os.path.join(LDPLAYER_PATH, "vms", "config")

# ==================== APPLICATION PATHS (Portable - relative to APP_DIR) ====================
# Data directory for VM configurations
DATA_DIR = os.path.join(APP_DIR, "data")
USER_DATA_DIR = DATA_DIR

# Output directory for stream results
OUTPUT_DIR = os.path.join(DATA_DIR, "output")

# API configuration file (DEPRECATED: Now using data/api/apis.json via multi_api_manager)
# API_FILE = os.path.join(DATA_DIR, "api", "youtube.txt")

# Streams metadata file
STREAMS_META = os.path.join(OUTPUT_DIR, "streams.json")

# Temporary files directory
TEMP_DIR = os.path.join(APP_DIR, "temp")

# Downloads directory
DOWNLOADS_DIR = os.path.join(APP_DIR, "downloads")

# ==================== LOGGING CONFIGURATION ====================
LOG_DIR = os.path.join(APP_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")
LOG_FORMAT = '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
LOG_LEVEL = "INFO"  # Can be: DEBUG, INFO, WARNING, ERROR, CRITICAL

# ==================== ENSURE DIRECTORIES EXIST ====================
def ensure_app_directories():
    """Create necessary directories if they don't exist."""
    dirs_to_create = [
        DATA_DIR,
        OUTPUT_DIR,
        os.path.join(DATA_DIR, "api"),
        TEMP_DIR,
        DOWNLOADS_DIR,
        LOG_DIR
    ]

    for directory in dirs_to_create:
        os.makedirs(directory, exist_ok=True)

# Auto-create directories on import
try:
    ensure_app_directories()
except Exception as e:
    logging.error(f"Failed to create app directories: {e}")
