#!/usr/bin/env python3
"""
Setup Validation Script

Validates that the environment is correctly configured for running the TOEFL
audio file extraction system.

Usage:
    python validate_setup.py
"""

import sys
import os
from pathlib import Path
import subprocess


def print_header(title):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_python_version():
    """Check Python version is 3.8+."""
    print("\n[1/8] Checking Python version...")
    version = sys.version_info

    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} (OK)")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} (Need 3.8+)")
        return False


def check_ffmpeg():
    """Check if ffmpeg is installed."""
    print("\n[2/8] Checking ffmpeg installation...")

    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Extract version from first line
            version_line = result.stdout.split('\n')[0]
            print(f"✓ ffmpeg installed: {version_line}")
            return True
        else:
            print("✗ ffmpeg not working properly")
            return False
    except FileNotFoundError:
        print("✗ ffmpeg not found")
        print("  Install: sudo apt-get install ffmpeg  (Ubuntu/Debian)")
        print("           brew install ffmpeg          (macOS)")
        return False
    except Exception as e:
        print(f"✗ Error checking ffmpeg: {e}")
        return False


def check_dependencies():
    """Check if Python dependencies are installed."""
    print("\n[3/8] Checking Python dependencies...")

    required_packages = [
        'google.oauth2',
        'googleapiclient',
        'dotenv',
        'tqdm',
        'pytest'
    ]

    all_installed = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} not found")
            all_installed = False

    if not all_installed:
        print("\n  Run: pip install -r requirements.txt")

    return all_installed


def check_project_structure():
    """Check if project structure exists."""
    print("\n[4/8] Checking project structure...")

    required_dirs = [
        'scripts/utils',
        'tests',
        'data/temp',
        'data/processed',
        'data/raw',
        'logs'
    ]

    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✓ {dir_path}/")
        else:
            print(f"✗ {dir_path}/ not found")
            all_exist = False

    return all_exist


def check_env_file():
    """Check if .env file exists and has required variables."""
    print("\n[5/8] Checking environment configuration...")

    env_path = Path('.env')

    if not env_path.exists():
        print("✗ .env file not found")
        print("  Run: cp .env.example .env")
        print("  Then edit .env with your values")
        return False

    print("✓ .env file exists")

    # Check for required variables
    required_vars = [
        'DRIVE_FOLDER_ID',
        'NARRATOR_DANIEL_FILE_ID',
        'NARRATOR_MATILDA_FILE_ID'
    ]

    with open(env_path) as f:
        content = f.read()

    all_set = True
    for var in required_vars:
        if f"{var}=your_" in content or f"{var}=" not in content:
            print(f"  ⚠ {var} not configured")
            all_set = False
        else:
            print(f"  ✓ {var} configured")

    if not all_set:
        print("\n  Edit .env and set the required variables")

    return all_set


def check_credentials():
    """Check if Google credentials file exists."""
    print("\n[6/8] Checking Google Drive credentials...")

    creds_path = Path('credentials.json')

    if creds_path.exists():
        print("✓ credentials.json found")
        return True
    else:
        print("✗ credentials.json not found")
        print("  Download from: https://console.cloud.google.com")
        print("  Place in project root")
        return False


def check_utilities():
    """Check if utility modules can be imported."""
    print("\n[7/8] Checking utility modules...")

    sys.path.insert(0, str(Path('scripts').absolute()))

    modules = [
        'utils.logger',
        'utils.file_parser',
        'utils.audio_processor',
        'utils.drive_manager'
    ]

    all_imported = True
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except Exception as e:
            print(f"✗ {module}: {str(e)[:50]}")
            all_imported = False

    return all_imported


def check_scripts():
    """Check if main scripts are executable."""
    print("\n[8/8] Checking main scripts...")

    scripts = [
        'scripts/task2_add_prefix.py',
        'scripts/investigate_task1.py'
    ]

    all_valid = True
    for script in scripts:
        script_path = Path(script)
        if script_path.exists():
            # Check if it compiles
            try:
                with open(script_path) as f:
                    compile(f.read(), script_path, 'exec')
                print(f"✓ {script}")
            except SyntaxError as e:
                print(f"✗ {script}: Syntax error")
                all_valid = False
        else:
            print(f"✗ {script}: Not found")
            all_valid = False

    return all_valid


def main():
    """Run all validation checks."""
    print_header("TOEFL Audio File Extraction - Setup Validation")

    checks = [
        check_python_version,
        check_ffmpeg,
        check_dependencies,
        check_project_structure,
        check_env_file,
        check_credentials,
        check_utilities,
        check_scripts
    ]

    results = [check() for check in checks]

    # Summary
    print_header("Validation Summary")

    passed = sum(results)
    total = len(results)

    print(f"\nPassed: {passed}/{total} checks")

    if all(results):
        print("\n✓ All checks passed! System is ready for use.")
        print("\nNext steps:")
        print("  1. Run authentication: python scripts/task2_add_prefix.py --dry-run --limit 1")
        print("  2. Run tests: pytest tests/ -v")
        print("  3. See QUICK_START.md for usage examples")
        sys.exit(0)
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        print("\nSee QUICK_START.md for setup instructions")
        sys.exit(1)


if __name__ == '__main__':
    main()
