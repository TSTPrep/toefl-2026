#!/usr/bin/env python3
"""
Test Setup for Speaker Detection
Verifies that all required dependencies and configurations are ready
"""

import sys
import os
import subprocess
from pathlib import Path


def check_command(command):
    """Check if a command line tool is available."""
    try:
        subprocess.run(
            [command, '--version'],
            capture_output=True,
            check=True
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def check_python_package(package_name):
    """Check if a Python package is installed."""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False


def check_hf_token():
    """Check if HuggingFace token is configured."""
    token = os.environ.get('HF_TOKEN')
    if token:
        return True, f"Set (length: {len(token)})"
    else:
        return False, "Not set"


def test_pyannote():
    """Test pyannote.audio functionality."""
    try:
        from pyannote.audio import Pipeline
        token = os.environ.get('HF_TOKEN')

        if not token:
            return False, "No HF_TOKEN set"

        # Try to load model (will download if needed)
        print("    Testing model loading (this may take a minute on first run)...")
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            token=token
        )
        return True, "Model loaded successfully"

    except Exception as e:
        return False, str(e)


def main():
    print("="*80)
    print("SPEAKER DETECTION SETUP TEST")
    print("="*80)

    results = []

    # Check system dependencies
    print("\n1. System Dependencies")
    print("-"*80)

    tools = ['ffmpeg', 'ffprobe', 'python3']
    for tool in tools:
        available = check_command(tool)
        status = "✓ OK" if available else "✗ MISSING"
        print(f"  {tool:<20} {status}")
        results.append(('System', tool, available))

    # Check Python packages
    print("\n2. Python Packages")
    print("-"*80)

    packages = {
        'numpy': 'numpy',
        'scipy': 'scipy',
        'torch': 'torch',
        'torchaudio': 'torchaudio',
        'pyannote.audio': 'pyannote.audio',
        'pydub': 'pydub',
        'librosa': 'librosa',
    }

    for display_name, import_name in packages.items():
        available = check_python_package(import_name)
        status = "✓ OK" if available else "✗ MISSING"
        print(f"  {display_name:<20} {status}")
        results.append(('Python', display_name, available))

    # Check configuration
    print("\n3. Configuration")
    print("-"*80)

    token_set, token_info = check_hf_token()
    status = "✓ OK" if token_set else "✗ NOT SET"
    print(f"  HF_TOKEN             {status} - {token_info}")
    results.append(('Config', 'HF_TOKEN', token_set))

    # Check directories
    print("\n4. Project Structure")
    print("-"*80)

    paths = {
        'input/': 'Input directory',
        'output/statements/': 'Statements directory',
        'split_no_pauses.py': 'Original script',
        'split_with_speaker_detection.py': 'Improved script',
        'reprocess_statements.py': 'Reprocessing script',
    }

    for path, description in paths.items():
        exists = Path(path).exists()
        status = "✓ OK" if exists else "✗ MISSING"
        print(f"  {description:<30} {status}")
        results.append(('Files', description, exists))

    # Test pyannote if available
    if check_python_package('pyannote.audio'):
        print("\n5. Speaker Diarization Test")
        print("-"*80)
        print("  Testing pyannote.audio...")

        success, message = test_pyannote()
        status = "✓ OK" if success else "✗ FAILED"
        print(f"  {status} - {message}")
        results.append(('Function', 'Speaker Diarization', success))

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    categories = {}
    for category, item, status in results:
        if category not in categories:
            categories[category] = {'ok': 0, 'fail': 0}

        if status:
            categories[category]['ok'] += 1
        else:
            categories[category]['fail'] += 1

    all_ok = True
    for category, counts in categories.items():
        total = counts['ok'] + counts['fail']
        print(f"  {category:<15} {counts['ok']}/{total} OK")
        if counts['fail'] > 0:
            all_ok = False

    print()

    if all_ok:
        print("✓ All checks passed! Ready to use speaker detection.")
        print("\nNext steps:")
        print("  1. Analyze existing statements:")
        print("     python3 reprocess_statements.py --analyze-only")
        print()
        print("  2. Test on one file:")
        print("     python3 split_with_speaker_detection.py \"input/[file].mp3\"")
        print()
        print("  3. Reprocess suspicious files:")
        print("     python3 reprocess_statements.py --suspicious-only --dry-run")
        return 0
    else:
        print("✗ Some checks failed. Please review the issues above.")
        print("\nCommon fixes:")

        if not check_command('ffmpeg'):
            print("  - Install ffmpeg: apt install ffmpeg (Ubuntu) or brew install ffmpeg (Mac)")

        missing_packages = [
            pkg for pkg, imp in packages.items()
            if not check_python_package(imp)
        ]

        if missing_packages:
            print("  - Install Python packages:")
            print("    pip install -r requirements_speaker_detection.txt")

        if not token_set:
            print("  - Set HuggingFace token:")
            print("    export HF_TOKEN='your_token_here'")
            print("    Get token at: https://huggingface.co/settings/tokens")

        return 1


if __name__ == '__main__':
    sys.exit(main())
