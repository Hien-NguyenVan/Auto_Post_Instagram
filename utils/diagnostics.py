"""
Diagnostic utilities for debugging and logging.

This module provides functions to check system status, ADB status, VM status,
and log detailed information for troubleshooting.

Does NOT modify any existing logic - only provides diagnostic information.
"""
import subprocess
import psutil
import time
import os
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ==================== SYSTEM DIAGNOSTICS ====================

def get_system_info() -> Dict:
    """
    Get current system resource information.

    Returns:
        Dict with RAM, CPU, disk information
    """
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            "ram_total_gb": round(memory.total / (1024**3), 2),
            "ram_available_gb": round(memory.available / (1024**3), 2),
            "ram_used_percent": memory.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "disk_used_percent": disk.percent,
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1)
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {}


def check_system_resources() -> Tuple[bool, str]:
    """
    Check if system has enough resources to run smoothly.

    Returns:
        (is_ok, message)
    """
    try:
        info = get_system_info()

        warnings = []

        # Check RAM
        if info.get("ram_available_gb", 0) < 2:
            warnings.append(f"⚠️ RAM thấp: {info['ram_available_gb']}GB available (nên có ít nhất 2GB)")

        # Check Disk
        if info.get("disk_free_gb", 0) < 5:
            warnings.append(f"⚠️ Disk thấp: {info['disk_free_gb']}GB free (nên có ít nhất 5GB)")

        # Check CPU
        if info.get("cpu_percent", 0) > 90:
            warnings.append(f"⚠️ CPU cao: {info['cpu_percent']}% (hệ thống đang quá tải)")

        if warnings:
            return False, "\n".join(warnings)
        else:
            return True, "✅ System resources OK"

    except Exception as e:
        return False, f"❌ Cannot check system resources: {e}"


def log_system_info(log_callback=None):
    """
    Log system information for debugging.

    Args:
        log_callback: Optional callback function(message)
    """
    log = log_callback or (lambda msg: print(msg))

    info = get_system_info()
    log(f"💻 System Info:")
    log(f"   RAM: {info.get('ram_available_gb', '?')}GB / {info.get('ram_total_gb', '?')}GB available ({info.get('ram_used_percent', '?')}% used)")
    log(f"   Disk: {info.get('disk_free_gb', '?')}GB / {info.get('disk_total_gb', '?')}GB free ({info.get('disk_used_percent', '?')}% used)")
    log(f"   CPU: {info.get('cpu_count', '?')} cores, {info.get('cpu_percent', '?')}% usage")


# ==================== ADB DIAGNOSTICS ====================

def check_adb_server_running(adb_exe: str) -> bool:
    """
    Check if ADB server is running.

    Args:
        adb_exe: Path to adb.exe

    Returns:
        True if ADB server is running
    """
    try:
        result = subprocess.run(
            [adb_exe, "devices"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def get_adb_devices(adb_exe: str) -> List[str]:
    """
    Get list of connected ADB devices.

    Args:
        adb_exe: Path to adb.exe

    Returns:
        List of device serials
    """
    try:
        result = subprocess.run(
            [adb_exe, "devices"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=5
        )

        devices = []
        for line in result.stdout.splitlines()[1:]:  # Skip first line "List of devices"
            if line.strip() and "\tdevice" in line:
                device = line.split("\t")[0]
                devices.append(device)

        return devices
    except Exception as e:
        logger.error(f"Error getting ADB devices: {e}")
        return []


def count_adb_processes() -> int:
    """
    Count number of ADB processes running.

    Returns:
        Number of adb.exe processes
    """
    try:
        count = 0
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and 'adb.exe' in proc.info['name'].lower():
                count += 1
        return count
    except Exception:
        return -1


def diagnose_adb(adb_exe: str) -> Dict:
    """
    Full ADB diagnostics.

    Args:
        adb_exe: Path to adb.exe

    Returns:
        Dict with ADB diagnostic information
    """
    return {
        "server_running": check_adb_server_running(adb_exe),
        "devices": get_adb_devices(adb_exe),
        "adb_processes": count_adb_processes(),
        "adb_exe_exists": os.path.exists(adb_exe)
    }


def log_adb_info(adb_exe: str, log_callback=None):
    """
    Log ADB information for debugging.

    Args:
        adb_exe: Path to adb.exe
        log_callback: Optional callback function(message)
    """
    log = log_callback or (lambda msg: print(msg))

    info = diagnose_adb(adb_exe)
    log(f"🔧 ADB Info:")
    log(f"   Server running: {'✅' if info['server_running'] else '❌'}")
    log(f"   Connected devices: {len(info['devices'])} - {info['devices']}")
    log(f"   ADB processes: {info['adb_processes']}")
    log(f"   ADB.exe exists: {'✅' if info['adb_exe_exists'] else '❌'}")


# ==================== VM DIAGNOSTICS ====================

def check_vm_running(vm_name: str, ldconsole_exe: str) -> bool:
    """
    Check if VM is running.

    Args:
        vm_name: VM name
        ldconsole_exe: Path to ldconsole.exe

    Returns:
        True if VM is running
    """
    try:
        result = subprocess.run(
            [ldconsole_exe, "list2"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=10
        )

        for line in result.stdout.splitlines():
            parts = line.split(",")
            if len(parts) >= 5 and parts[1].strip() == vm_name:
                return parts[4].strip() == "1"

        return False
    except Exception as e:
        logger.error(f"Error checking VM status: {e}")
        return False


def get_vm_port(vm_name: str, data_dir: str) -> Optional[str]:
    """
    Get VM's ADB port from JSON file.

    Args:
        vm_name: VM name
        data_dir: Path to data directory

    Returns:
        Port string or None
    """
    try:
        import json
        json_path = os.path.join(data_dir, f"{vm_name}.json")

        if not os.path.exists(json_path):
            return None

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data.get("port")
    except Exception as e:
        logger.error(f"Error getting VM port: {e}")
        return None


def diagnose_vm(vm_name: str, ldconsole_exe: str, data_dir: str, adb_exe: str) -> Dict:
    """
    Full VM diagnostics.

    Args:
        vm_name: VM name
        ldconsole_exe: Path to ldconsole.exe
        data_dir: Path to data directory
        adb_exe: Path to adb.exe

    Returns:
        Dict with VM diagnostic information
    """
    port = get_vm_port(vm_name, data_dir)
    adb_address = f"emulator-{port}" if port else None

    adb_connected = False
    if adb_address:
        devices = get_adb_devices(adb_exe)
        adb_connected = adb_address in devices

    return {
        "running": check_vm_running(vm_name, ldconsole_exe),
        "port": port,
        "adb_address": adb_address,
        "adb_connected": adb_connected
    }


def log_vm_info(vm_name: str, ldconsole_exe: str, data_dir: str, adb_exe: str, log_callback=None):
    """
    Log VM information for debugging.

    Args:
        vm_name: VM name
        ldconsole_exe: Path to ldconsole.exe
        data_dir: Path to data directory
        adb_exe: Path to adb.exe
        log_callback: Optional callback function(message)
    """
    log = log_callback or (lambda msg: print(msg))

    info = diagnose_vm(vm_name, ldconsole_exe, data_dir, adb_exe)
    log(f"📱 VM Info ({vm_name}):")
    log(f"   Running: {'✅' if info['running'] else '❌'}")
    log(f"   Port: {info['port']}")
    log(f"   ADB address: {info['adb_address']}")
    log(f"   ADB connected: {'✅' if info['adb_connected'] else '❌'}")


# ==================== FILE OPERATION DIAGNOSTICS ====================

def check_file_exists_and_size(file_path: str) -> Tuple[bool, int]:
    """
    Check if file exists and get its size.

    Args:
        file_path: Path to file

    Returns:
        (exists, size_in_bytes)
    """
    try:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            return True, size
        else:
            return False, 0
    except Exception as e:
        logger.error(f"Error checking file: {e}")
        return False, 0


def log_file_info(file_path: str, log_callback=None):
    """
    Log file information for debugging.

    Args:
        file_path: Path to file
        log_callback: Optional callback function(message)
    """
    log = log_callback or (lambda msg: print(msg))

    exists, size = check_file_exists_and_size(file_path)
    log(f"📄 File Info: {os.path.basename(file_path)}")
    log(f"   Exists: {'✅' if exists else '❌'}")
    log(f"   Size: {size / (1024*1024):.2f} MB" if size > 0 else "   Size: 0 MB")
    log(f"   Path: {file_path}")


# ==================== TIMING UTILITIES ====================

class Timer:
    """
    Simple timer for measuring operation duration.

    Usage:
        timer = Timer()
        # ... do operation ...
        elapsed = timer.elapsed()
    """

    def __init__(self):
        self.start_time = time.time()

    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time

    def reset(self):
        """Reset timer."""
        self.start_time = time.time()


def log_with_timing(operation_name: str, log_callback=None):
    """
    Decorator to log operation timing.

    Usage:
        @log_with_timing("Push file")
        def push_file():
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            log = log_callback or (lambda msg: print(msg))
            timer = Timer()
            log(f"⏱️ [{operation_name}] Starting...")

            try:
                result = func(*args, **kwargs)
                elapsed = timer.elapsed()
                log(f"⏱️ [{operation_name}] Completed in {elapsed:.2f}s")
                return result
            except Exception as e:
                elapsed = timer.elapsed()
                log(f"⏱️ [{operation_name}] Failed after {elapsed:.2f}s: {e}")
                raise

        return wrapper
    return decorator


# ==================== COMPREHENSIVE DIAGNOSTIC ====================

def run_full_diagnostics(vm_name: str, ldconsole_exe: str, adb_exe: str, data_dir: str, log_callback=None):
    """
    Run all diagnostic checks and log everything.

    Args:
        vm_name: VM name to check
        ldconsole_exe: Path to ldconsole.exe
        adb_exe: Path to adb.exe
        data_dir: Path to data directory
        log_callback: Optional callback function(message)
    """
    log = log_callback or (lambda msg: print(msg))

    log("=" * 60)
    log("🔍 DIAGNOSTIC REPORT")
    log("=" * 60)

    log_system_info(log)
    log("")
    log_adb_info(adb_exe, log)
    log("")
    log_vm_info(vm_name, ldconsole_exe, data_dir, adb_exe, log)

    log("=" * 60)
