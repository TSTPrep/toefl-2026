#!/usr/bin/env python3
"""
Task 2 MCP Orchestrator: Add Narrator Prefix to Conversation Files

This script is designed to be run BY CLAUDE using MCP tools.
It provides file listing, processing logic, and validation - but Claude
handles the actual MCP tool calls for Drive operations.

Usage (from Claude):
    1. Run this script to get the conversation file list and narrator assignments
    2. Download files manually via curl (MCP doesn't support binary downloads)
    3. Process files with ffmpeg
    4. Upload back to Drive preserving file IDs (version management)
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Directories
TEMP_DIR = Path('data/temp')
PROCESSED_DIR = Path('data/processed')
TEMP_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Narrator file IDs
NARRATOR_FILES = {
    'daniel': os.getenv('NARRATOR_DANIEL_FILE_ID'),
    'matilda': os.getenv('NARRATOR_MATILDA_FILE_ID')
}

# Conversation files (from Drive listing - hardcoded for reliability)
CONVERSATION_FILES = [
    ("02.01.04, Listen to a Conversation, Module 1.mp3", "1KlwRQC1vaoLarTfFNHqrf-DGs8wAi8Xm"),
    ("02.02.03, Listen to a Conversation, Module 1.mp3", "1TYOmKTVElF6bcXjgme3PKAh3XecCvAre"),
    ("02.02.04, Listen to a Conversation, Module 1.mp3", "1N_3qrt6kSCB6-5lEKzBuPVhZ6Gs47DtM"),
    ("02.02.05, Listen to a Conversation, Module 1.mp3", "1kCF4YtErF4qVb5VH7Tn5KZr7pUkluKHp"),
    ("02.02.06, Listen to a Conversation, Module 2.mp3", "1LvNxru2Jwgv8yFIC9t2yQbBbuknmcaEN"),
    ("02.02.07, Listen to a Conversation, Module 2.mp3", "1XcfHxwAc5kBoz617fADonxrpw3oQtzjw"),
    ("02.03.03, Listen to a Conversation, Module 1.mp3", "1Yt-723kcYAb4JDPDKuPngNNIeqw7hkqD"),
    ("02.03.04, Listen to a Conversation, Module 1.mp3", "1cDJmz5WJc9iWggaZhSz1hjTxIzQOxJY3"),
    ("02.03.05, Listen to a Conversation, Module 2.mp3", "1oU8le4uHkQ-u1ZKT2sRDBDz5JerHLo2L"),
    ("02.03.06, Listen to a Conversation, Module 2.mp3", "1iTTEM_2iwTIVIas6THxvqHjXJXVmnFgB"),
    ("02.04.03, Listen to a COnversation, Module 1.mp3", "1BfKVhnDa53FKZcH86nlpCqmPatarqkJn"),
    ("02.04.04, Listen to a Conversation, Module 1.mp3", "1Tm7DW5zpAEOdJH8yifYmK9yfg5Tizc9r"),
    ("02.04.05, Listen to a Conversation, Module 1.mp3", "19fdBJYdRFFH3kqyl5_ayzOGY_ED16-kT"),
    ("02.04.06, Listen to a Conversation, Module 2.mp3", "1EqBllKiBBhX0Sbu7ZLzmxNUN81cFT7s7"),
    ("02.04.07, Listen to a Conversation, Module 2.mp3", "1oYzIyf5Iwejf7OUjx4Yd_ARIeSSQD1WH"),
    ("02.05.03, Listen to a Conversation, Module 1).mp3", "1fmEqUWy98019oE77ZhGuhg_u3EFizj8M"),
    ("02.05.04, Listen to a Conversation, Module 1).mp3", "1hUGIWdYMyT7MkMUiLLdkjoOeT1dqpDGl"),
    ("02.05.05, Listen to a Conversation, Module 2.mp3", "1C1N5Nfk_T-rK0m7Tb872ArTwkEC6qXle"),
    ("02.05.06, Listen to a Conversation, Module 2.mp3", "154sPu5guBvDaRO7jwpF6Umnn1JaxyxYy"),
]


def download_file_curl(file_id: str, output_path: Path) -> bool:
    """Download a file from Google Drive using curl."""
    url = f"https://drive.google.com/uc?export=download&id={file_id}"

    # Try direct download first
    cmd = ['curl', '-L', '-o', str(output_path), url]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Check if file exists and has content
        if output_path.exists() and output_path.stat().st_size > 0:
            return True
        else:
            print(f"  ✗ Download failed: file empty or missing")
            return False

    except subprocess.CalledProcessError as e:
        print(f"  ✗ Download failed: {e}")
        return False


def get_audio_duration(file_path: Path) -> float:
    """Get duration of audio file in seconds using ffprobe."""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(file_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        return 0.0


def concatenate_audio_ffmpeg(input_files: List[Path], output_path: Path) -> bool:
    """Concatenate audio files using ffmpeg concat demuxer."""
    # Create concat list file
    concat_list = TEMP_DIR / 'concat_list.txt'

    with open(concat_list, 'w') as f:
        for file_path in input_files:
            f.write(f"file '{file_path.absolute()}'\n")

    # Run ffmpeg
    cmd = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', str(concat_list),
        '-c', 'copy',
        '-y',  # Overwrite output
        str(output_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Verify output exists
        if output_path.exists() and output_path.stat().st_size > 0:
            return True
        else:
            print(f"  ✗ Concatenation failed: output file missing or empty")
            return False

    except subprocess.CalledProcessError as e:
        print(f"  ✗ ffmpeg failed: {e.stderr}")
        return False
    finally:
        # Clean up concat list
        if concat_list.exists():
            concat_list.unlink()


def assign_narrators(files: List[Tuple[str, str]]) -> Dict[str, List[Tuple[str, str]]]:
    """Assign narrators to files using alphabetical sorting for deterministic 50/50 rotation."""
    sorted_files = sorted(files, key=lambda x: x[0])  # Sort by filename

    assignments = {'daniel': [], 'matilda': []}
    narrators = ['daniel', 'matilda']

    for i, file_info in enumerate(sorted_files):
        narrator = narrators[i % 2]
        assignments[narrator].append(file_info)

    return assignments


def download_narrator_files() -> Dict[str, Path]:
    """Download narrator files from Drive."""
    print("=" * 80)
    print("DOWNLOADING NARRATOR FILES")
    print("=" * 80)

    narrator_paths = {}

    for narrator, file_id in NARRATOR_FILES.items():
        output_path = TEMP_DIR / f"narrator_{narrator}.mp3"

        if output_path.exists():
            print(f"✓ {narrator.capitalize()}: already exists ({output_path})")
            narrator_paths[narrator] = output_path
            continue

        print(f"Downloading {narrator.capitalize()} narrator...")
        if download_file_curl(file_id, output_path):
            print(f"✓ {narrator.capitalize()}: downloaded ({output_path.stat().st_size} bytes)")
            narrator_paths[narrator] = output_path
        else:
            print(f"✗ {narrator.capitalize()}: FAILED")
            return None

    return narrator_paths


def process_file(
    filename: str,
    file_id: str,
    narrator: str,
    narrator_path: Path,
    dry_run: bool = False
) -> Dict:
    """Process a single conversation file."""
    conversation_path = TEMP_DIR / filename
    output_path = PROCESSED_DIR / filename

    result = {
        'filename': filename,
        'file_id': file_id,
        'narrator': narrator,
        'success': False,
        'message': '',
        'original_duration': 0.0,
        'narrator_duration': 0.0,
        'output_duration': 0.0
    }

    try:
        # Download conversation file
        print(f"  Downloading conversation file...")
        if not download_file_curl(file_id, conversation_path):
            result['message'] = "Download failed"
            return result

        # Get durations
        result['original_duration'] = get_audio_duration(conversation_path)
        result['narrator_duration'] = get_audio_duration(narrator_path)
        print(f"  Original: {result['original_duration']:.1f}s, Narrator: {result['narrator_duration']:.1f}s")

        # Concatenate
        print(f"  Concatenating {narrator} narrator + conversation...")
        if not concatenate_audio_ffmpeg([narrator_path, conversation_path], output_path):
            result['message'] = "Concatenation failed"
            return result

        # Validate output
        result['output_duration'] = get_audio_duration(output_path)
        expected_duration = result['original_duration'] + result['narrator_duration']
        duration_diff = abs(result['output_duration'] - expected_duration)

        if duration_diff > 1.0:  # Allow 1 second tolerance
            result['message'] = f"Duration mismatch: expected {expected_duration:.1f}s, got {result['output_duration']:.1f}s"
            return result

        print(f"  ✓ Output: {result['output_duration']:.1f}s (expected ~{expected_duration:.1f}s)")

        # Clean up temp conversation file
        conversation_path.unlink()

        result['success'] = True
        result['message'] = "Successfully processed"

        # Note: Upload to Drive will be done by Claude using MCP tools
        if dry_run:
            result['message'] += " (DRY RUN - not uploaded)"

        return result

    except Exception as e:
        result['message'] = f"Unexpected error: {e}"
        return result


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Task 2: Add narrator prefix to conversation files')
    parser.add_argument('--dry-run', action='store_true', help='Process files but do not upload')
    parser.add_argument('--limit', type=int, help='Limit number of files to process')
    parser.add_argument('--report-only', action='store_true', help='Only show narrator assignments')

    args = parser.parse_args()

    # Show assignments
    assignments = assign_narrators(CONVERSATION_FILES)

    print("=" * 80)
    print("NARRATOR ASSIGNMENTS (Deterministic Alphabetical)")
    print("=" * 80)
    for narrator, files in assignments.items():
        print(f"\n{narrator.upper()}: {len(files)} files")
        for idx, (filename, file_id) in enumerate(files, 1):
            print(f"  {idx:2d}. {filename}")

    print(f"\nTotal: {len(CONVERSATION_FILES)} files")
    print(f"Daniel: {len(assignments['daniel'])}, Matilda: {len(assignments['matilda'])}")

    if args.report_only:
        return

    # Download narrator files
    narrator_paths = download_narrator_files()
    if not narrator_paths:
        print("\n✗ Failed to download narrator files. Exiting.")
        sys.exit(1)

    # Process files
    files_to_process = CONVERSATION_FILES[:args.limit] if args.limit else CONVERSATION_FILES

    print("\n" + "=" * 80)
    print(f"PROCESSING {len(files_to_process)} FILES" + (" (DRY RUN)" if args.dry_run else ""))
    print("=" * 80)

    results = []

    for filename, file_id in files_to_process:
        # Determine narrator
        narrator = 'daniel' if CONVERSATION_FILES.index((filename, file_id)) % 2 == 0 else 'matilda'

        print(f"\n[{len(results)+1}/{len(files_to_process)}] {filename} ({narrator.upper()})")

        result = process_file(
            filename=filename,
            file_id=file_id,
            narrator=narrator,
            narrator_path=narrator_paths[narrator],
            dry_run=args.dry_run
        )

        results.append(result)

        if result['success']:
            print(f"✓ SUCCESS")
        else:
            print(f"✗ FAILED: {result['message']}")

    # Generate report
    report_path = PROCESSED_DIR / 'task2_processing_report.json'

    summary = {
        'total': len(results),
        'successful': sum(1 for r in results if r['success']),
        'failed': sum(1 for r in results if not r['success']),
        'dry_run': args.dry_run,
        'results': results
    }

    with open(report_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 80)
    print("PROCESSING SUMMARY")
    print("=" * 80)
    print(f"Total: {summary['total']}")
    print(f"Successful: {summary['successful']}")
    print(f"Failed: {summary['failed']}")
    print(f"\nReport saved: {report_path}")

    # Show failed files
    if summary['failed'] > 0:
        print("\nFailed files:")
        for r in results:
            if not r['success']:
                print(f"  ✗ {r['filename']}: {r['message']}")

    # Show files needing upload
    if not args.dry_run and summary['successful'] > 0:
        print("\n" + "=" * 80)
        print("FILES READY FOR DRIVE UPLOAD")
        print("=" * 80)
        print("\nClaude should now upload these files to Google Drive using MCP tools:")
        print("Use mcp__google_workspace__create_drive_file with update_existing=True")
        print()
        for r in results:
            if r['success']:
                output_file = PROCESSED_DIR / r['filename']
                print(f"  • {r['filename']}")
                print(f"    Path: {output_file}")
                print(f"    File ID: {r['file_id']} (update this existing file)")
                print()


if __name__ == '__main__':
    main()
