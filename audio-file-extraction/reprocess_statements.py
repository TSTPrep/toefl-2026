#!/usr/bin/env python3
"""
Reprocess Statement Files
Re-split audio files that have multi-statement issues using improved speaker detection
"""

import subprocess
import os
import sys
from pathlib import Path
import argparse
import json
from typing import List, Dict


def find_original_file(statement_dir: Path) -> Path:
    """
    Find the original "no pauses" file corresponding to a statement directory.

    Args:
        statement_dir: Path to statement directory (e.g., "02.05.02, Listen and Choose, Module 2")

    Returns:
        Path to original audio file
    """
    # Expected original file path
    # Statement dir: "output/statements/02.05.02, Listen and Choose, Module 2"
    # Original file: "input/02.05.02, Listen and Choose, Module 2 (no pauses).mp3"

    dir_name = statement_dir.name
    original_filename = f"{dir_name} (no pauses).mp3"

    # Check common input locations
    search_paths = [
        Path('input') / original_filename,
        Path('audio') / original_filename,
        Path('.') / original_filename,
        Path('..') / 'input' / original_filename,
    ]

    for path in search_paths:
        if path.exists():
            return path

    raise FileNotFoundError(f"Could not find original file: {original_filename}")


def analyze_statements(statements_dir: Path) -> Dict[str, dict]:
    """
    Analyze all statement directories to identify problematic ones.

    Returns:
        Dictionary mapping directory names to analysis results
    """
    print("Analyzing statement directories...")
    print("="*80)

    results = {}

    for module_dir in sorted(statements_dir.iterdir()):
        if not module_dir.is_dir():
            continue

        mp3_files = list(module_dir.glob('*.mp3'))
        if not mp3_files:
            continue

        # Get durations
        durations = []
        for mp3_file in mp3_files:
            cmd = [
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(mp3_file)
            ]

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                duration = float(result.stdout.strip())
                durations.append(duration)
            except:
                pass

        if not durations:
            continue

        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        count = len(mp3_files)

        # Flag suspicious directories
        # Criteria:
        # 1. Very long average duration (> 4s suggests multi-statement)
        # 2. Max duration > 6s (likely multi-statement)
        # 3. Very few statements (< 4) with long duration
        suspicious = False
        reasons = []

        if avg_duration > 4.0:
            suspicious = True
            reasons.append(f"Long avg duration ({avg_duration:.1f}s)")

        if max_duration > 6.0:
            suspicious = True
            reasons.append(f"Very long file ({max_duration:.1f}s)")

        if count < 4 and max_duration > 5.0:
            suspicious = True
            reasons.append(f"Few statements ({count}) with long files")

        results[module_dir.name] = {
            'dir': module_dir,
            'count': count,
            'avg_duration': avg_duration,
            'max_duration': max_duration,
            'suspicious': suspicious,
            'reasons': reasons
        }

        status = "⚠️  SUSPICIOUS" if suspicious else "✓ OK"
        print(f"{module_dir.name:<50} {count:>3} files | Avg: {avg_duration:.1f}s | Max: {max_duration:.1f}s | {status}")

        if suspicious and reasons:
            for reason in reasons:
                print(f"  └─ {reason}")

    print("="*80)
    return results


def reprocess_directory(
    module_dir: Path,
    use_speaker_detection: bool = True,
    hf_token: str = None,
    dry_run: bool = False
) -> bool:
    """
    Reprocess a single statement directory with improved splitting.

    Args:
        module_dir: Path to statement directory
        use_speaker_detection: Whether to use speaker detection
        hf_token: HuggingFace token
        dry_run: If True, show what would be done without doing it

    Returns:
        True if successful, False otherwise
    """
    print(f"\nReprocessing: {module_dir.name}")
    print("-"*80)

    try:
        # Find original file
        original_file = find_original_file(module_dir)
        print(f"Original file: {original_file}")

        if dry_run:
            print("[DRY RUN] Would reprocess this file")
            return True

        # Backup existing statements
        backup_dir = module_dir.parent / f"{module_dir.name}.backup"
        if backup_dir.exists():
            print(f"Backup already exists: {backup_dir}")
        else:
            print(f"Creating backup: {backup_dir}")
            module_dir.rename(backup_dir)

        # Run improved splitter
        cmd = [
            'python3',
            'split_with_speaker_detection.py',
            str(original_file),
            '-o', str(module_dir)
        ]

        if not use_speaker_detection:
            cmd.append('--no-speaker-detection')

        if hf_token:
            cmd.extend(['--hf-token', hf_token])

        print(f"Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("✓ Reprocessing successful")

            # Compare results
            old_count = len(list(backup_dir.glob('*.mp3')))
            new_count = len(list(module_dir.glob('*.mp3')))

            print(f"\nComparison:")
            print(f"  Old: {old_count} statements")
            print(f"  New: {new_count} statements")

            if new_count > old_count:
                print(f"  Improvement: +{new_count - old_count} additional statements detected")
            elif new_count == old_count:
                print(f"  Same number of statements (may have better boundaries)")
            else:
                print(f"  Warning: Fewer statements detected (-{old_count - new_count})")

            return True
        else:
            print(f"✗ Reprocessing failed:\n{result.stderr}")

            # Restore backup
            if backup_dir.exists():
                if module_dir.exists():
                    import shutil
                    shutil.rmtree(module_dir)
                backup_dir.rename(module_dir)
                print("Restored from backup")

            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Reprocess statement files with improved speaker detection'
    )
    parser.add_argument(
        '--analyze-only',
        action='store_true',
        help='Only analyze directories, do not reprocess'
    )
    parser.add_argument(
        '--dir',
        help='Specific directory to reprocess (e.g., "02.05.02, Listen and Choose, Module 2")',
        default=None
    )
    parser.add_argument(
        '--suspicious-only',
        action='store_true',
        help='Only reprocess directories flagged as suspicious'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually doing it'
    )
    parser.add_argument(
        '--no-speaker-detection',
        action='store_true',
        help='Disable speaker detection (silence only)'
    )
    parser.add_argument(
        '--hf-token',
        help='HuggingFace token for pyannote.audio',
        default=None
    )

    args = parser.parse_args()

    statements_dir = Path('output/statements')

    if not statements_dir.exists():
        print(f"ERROR: Statements directory not found: {statements_dir}")
        sys.exit(1)

    # Analyze directories
    results = analyze_statements(statements_dir)

    suspicious_count = sum(1 for r in results.values() if r['suspicious'])
    print(f"\nSummary:")
    print(f"  Total directories: {len(results)}")
    print(f"  Suspicious: {suspicious_count}")
    print(f"  OK: {len(results) - suspicious_count}")

    if args.analyze_only:
        print("\nAnalysis complete (--analyze-only specified)")
        return

    # Determine which directories to reprocess
    to_reprocess = []

    if args.dir:
        # Specific directory
        target_dir = statements_dir / args.dir
        if not target_dir.exists():
            print(f"\nERROR: Directory not found: {target_dir}")
            sys.exit(1)
        to_reprocess.append(target_dir)

    elif args.suspicious_only:
        # Only suspicious directories
        to_reprocess = [r['dir'] for r in results.values() if r['suspicious']]

    else:
        # Ask user
        print("\nOptions:")
        print("  1. Reprocess ALL directories")
        print("  2. Reprocess SUSPICIOUS directories only")
        print("  3. Cancel")

        choice = input("\nChoice (1-3): ").strip()

        if choice == '1':
            to_reprocess = [r['dir'] for r in results.values()]
        elif choice == '2':
            to_reprocess = [r['dir'] for r in results.values() if r['suspicious']]
        else:
            print("Cancelled")
            return

    if not to_reprocess:
        print("\nNo directories to reprocess")
        return

    print(f"\n{'='*80}")
    print(f"Reprocessing {len(to_reprocess)} directories...")
    print(f"{'='*80}")

    if args.dry_run:
        print("\n[DRY RUN MODE - No actual changes will be made]\n")

    success_count = 0
    failure_count = 0

    for module_dir in to_reprocess:
        success = reprocess_directory(
            module_dir,
            use_speaker_detection=not args.no_speaker_detection,
            hf_token=args.hf_token,
            dry_run=args.dry_run
        )

        if success:
            success_count += 1
        else:
            failure_count += 1

    print(f"\n{'='*80}")
    print("REPROCESSING COMPLETE")
    print(f"{'='*80}")
    print(f"  Success: {success_count}")
    print(f"  Failure: {failure_count}")

    if failure_count > 0:
        print("\nSome directories failed to reprocess. Check output above for details.")
        sys.exit(1)


if __name__ == '__main__':
    main()
