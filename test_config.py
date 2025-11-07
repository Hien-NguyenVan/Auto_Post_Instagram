"""
Test script to verify config.py auto-detection and paths.

Run this before building the package to ensure everything works.
"""
import os
import sys


def print_header():
    print("=" * 70)
    print("     CONFIG TEST - Instagram Automation Tool")
    print("=" * 70)
    print()


def test_import_config():
    """Test if config.py can be imported"""
    try:
        import config
        print("[OK] config.py imported successfully")
        return config
    except Exception as e:
        print(f"[FAIL] Failed to import config.py: {e}")
        return None


def test_ldplayer_detection(config):
    """Test LDPlayer auto-detection"""
    print("\nTesting LDPlayer Detection:")
    print("-" * 70)

    if config.LDPLAYER_PATH:
        print(f"[OK] LDPlayer detected at: {config.LDPLAYER_PATH}")

        # Check if ldconsole.exe exists
        if os.path.exists(config.LDCONSOLE_EXE):
            print(f"[OK] ldconsole.exe found: {config.LDCONSOLE_EXE}")
        else:
            print(f"[WARN] ldconsole.exe NOT found at: {config.LDCONSOLE_EXE}")

        # Check if adb.exe exists
        if os.path.exists(config.ADB_EXE):
            print(f"[OK] adb.exe found: {config.ADB_EXE}")
        else:
            print(f"[WARN] adb.exe NOT found at: {config.ADB_EXE}")

        return True
    else:
        print("[FAIL] LDPlayer NOT detected!")
        print("\nSolutions:")
        print("   1. Install LDPlayer 9")
        print("   2. Set LDPLAYER_PATH environment variable")
        print("   3. Create 'ldplayer_path.txt' with LDPlayer path")
        return False


def test_app_directories(config):
    """Test if application directories are created"""
    print("\n Testing Application Directories:")
    print("-" * 70)

    dirs_to_check = [
        ("DATA_DIR", config.DATA_DIR),
        ("OUTPUT_DIR", config.OUTPUT_DIR),
        ("LOG_DIR", config.LOG_DIR),
        ("TEMP_DIR", config.TEMP_DIR),
        ("DOWNLOADS_DIR", config.DOWNLOADS_DIR)
    ]

    all_ok = True
    for name, path in dirs_to_check:
        if os.path.exists(path):
            print(f"[OK] {name}: {path}")
        else:
            print(f"[FAIL] {name} NOT created: {path}")
            all_ok = False

    return all_ok


def test_app_dir_detection(config):
    """Test APP_DIR detection"""
    print("\n Testing APP_DIR Detection:")
    print("-" * 70)

    print(f"APP_DIR: {config.APP_DIR}")

    if getattr(sys, 'frozen', False):
        print("[OK] Running as compiled EXE")
    else:
        print("[OK] Running as Python script")

    return True


def test_dependencies():
    """Test if required Python packages are installed"""
    print("\n Testing Python Dependencies:")
    print("-" * 70)

    required_packages = [
        "ttkbootstrap",
        "uiautomator2",
        "requests",
        "googleapiclient"
    ]

    all_ok = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"[OK] {package}")
        except ImportError:
            print(f"[FAIL] {package} NOT installed")
            all_ok = False

    if not all_ok:
        print("\n Install missing packages:")
        print("   pip install -r requirements.txt")

    return all_ok


def generate_summary(results):
    """Generate test summary"""
    print("\n" + "=" * 70)
    print("     TEST SUMMARY")
    print("=" * 70)

    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed

    for test_name, result in results.items():
        status = "[OK] PASS" if result else "[FAIL] FAIL"
        print(f"{status} - {test_name}")

    print("-" * 70)
    print(f"Total: {total} | Passed: {passed} | Failed: {failed}")

    if failed == 0:
        print("\n All tests passed! Ready to build package.")
        print("   Run: python build_package.py")
    else:
        print("\n[WARN]  Some tests failed. Fix issues before building.")

    return failed == 0


def main():
    print_header()

    results = {}

    # Test 1: Import config
    config = test_import_config()
    results["Import config.py"] = config is not None

    if not config:
        print("\n[FAIL] Cannot proceed without valid config.py")
        input("\nPress Enter to exit...")
        return

    # Test 2: LDPlayer detection
    results["LDPlayer Detection"] = test_ldplayer_detection(config)

    # Test 3: APP_DIR detection
    results["APP_DIR Detection"] = test_app_dir_detection(config)

    # Test 4: Application directories
    results["Application Directories"] = test_app_directories(config)

    # Test 5: Dependencies
    results["Python Dependencies"] = test_dependencies()

    # Generate summary
    all_passed = generate_summary(results)

    print()
    input("Press Enter to exit...")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
