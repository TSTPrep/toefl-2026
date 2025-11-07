#!/usr/bin/env python3
"""
Process Batch 100 Conversation Files with Narrator Prefixes
Adapted from task2_mcp_orchestrator.py for batch 100.XX files
"""

import os
import subprocess
from pathlib import Path
from typing import List, Tuple

# Directories
DOWNLOADS_DIR = Path('downloads')
OUTPUT_DIR = Path('data/processed')
TEMP_DIR = Path('data/temp')

TEMP_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Batch 100 conversation files (from BATCH_100_EXECUTION_REPORT.md)
CONVERSATION_FILES = [
    ("100.04, Listen to a Conversation 1.mp3", "1TEmBiBvwYqJJwpjSN-7FZ7JZ2IgT4kDp"),
    ("100.05, Listen to a Conversation 2.mp3", "1YWQ7I4l8p8JiACCqYIivX4-pngNJT2kR"),
    ("100.06, Listen to a Conversation 3.mp3", "1_Qn0yjAQSjw1LIfm-Ps9aLN_caQaNKWM"),
    ("100.07, Listen to a Conversation 4.mp3", "1ZLrFSkNxiOupOVcPxbJh72Or3mf3Qoez"),
    ("100.08, Listen to a Conversation 5.mp3", "1G6IvJmlrX3OTtU1doGHXlmW00RsOPID7"),
    ("100.09, Listen to a Conversation 6.mp3", "1VDJ8RHLDAV9TpCfnF7-DKISxKTttbPSB"),
    ("100.10, Listen to a Conversation 7.mp3", "1v2sRW1JwN0h4lYC1lT4Gn20Gffw567VM"),
    ("100.11, Listen to a Conversation 8.mp3", "1R88XEj8SS3lO5ryPJJ6gyCOBuVpok4jV"),
    ("100.12, Listen to a Conversation 9.mp3", "1Nz2g74vhtlMHFk8nNgX5CPjRZTtVu-DA"),
    ("100.13, Listen to a Conversation 10.mp3", "14Opr2cuX4qkD0_J0NL6xXjMF4LjShgHq"),
    ("100.14, Listen to a Conversation 11.mp3", "1QnUzc3a7N0BhHGfQSytCKXu24JUeVafK"),
    ("100.15, Listen to a Conversation 12.mp3", "1iC99A1RvD7ivfEfVCFoPvCYnt98Jc8AJ"),
    ("100.16, Listen to a Conversation 13.mp3", "1iz5Q8EYqWPso39V4iXtoD3UWZtxDTSTc"),
    ("100.17, Listen to a Conversation 14.mp3", "1V0JebdDmZ2tuZ7pKniyrAqTtOPz5T19l"),
    ("100.18, Listen to a Conversation 15.mp3", "1Xnu_zgi0LAgXsok3j1W5kAst-8LIp6o5"),
]

# Narrator file IDs (from previous work)
NARRATOR_FILES = {
    'daniel': '1o0cMffBzUnIMVZulhjzV7P7lgjJespbq',  # Daniel prefix (1.9s)
    'matilda': '19GayiAp7_eOLotNMNjvTNPCAtDZEnWjm',  # Matilda prefix (1.6s)
}


def download_file_curl(file_id: str, output_path: Path) -> bool:
    """Download a file from Google Drive using curl."""
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    cmd = ['curl', '-L', '-o', str(output_path), url]

    try:
        subprocess.run(cmd, capture_output=True, check=True)
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
        'ffprobe', '-v', 'error',
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
    concat_list = TEMP_DIR / 'concat_list.txt'

    with open(concat_list, 'w') as f:
        for file_path in input_files:
            f.write(f"file '{file_path.absolute()}'\n")

    cmd = [
        'ffmpeg', '-f', 'concat', '-safe', '0',
        '-i', str(concat_list),
        '-c', 'copy', '-y',
        str(output_path)
    ]

    try:
        subprocess.run(cmd, capture_output=True, check=True)
        if output_path.exists() and output_path.stat().st_size > 0:
            return True
        else:
            print(f"  ✗ Concatenation failed: output missing")
            return False
    except subprocess.CalledProcessError as e:
        print(f"  ✗ ffmpeg failed: {e}")
        return False
    finally:
        if concat_list.exists():
            concat_list.unlink()


def download_narrator_files() -> dict:
    """Download narrator prefix files if not already present."""
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
            size = output_path.stat().st_size
            print(f"✓ {narrator.capitalize()}: downloaded ({size:,} bytes)")
            narrator_paths[narrator] = output_path
        else:
            print(f"✗ {narrator.capitalize()}: FAILED")
            return None

    return narrator_paths


def process_conversations_from_downloads(narrator_paths: dict):
    """Process conversation files that are already in downloads/ directory."""
    print("\n" + "=" * 80)
    print(f"PROCESSING {len(CONVERSATION_FILES)} CONVERSATION FILES")
    print("=" * 80)

    # Sort filenames alphabetically for deterministic narrator assignment
    sorted_files = sorted(CONVERSATION_FILES, key=lambda x: x[0])

    results = []

    for idx, (filename, file_id) in enumerate(sorted_files):
        # Alternating narrator assignment
        narrator = 'daniel' if idx % 2 == 0 else 'matilda'

        print(f"\n[{idx+1}/{len(sorted_files)}] {filename} ({narrator.upper()})")

        conversation_path = DOWNLOADS_DIR / filename
        output_path = OUTPUT_DIR / filename

        # Check if conversation file exists in downloads
        if not conversation_path.exists():
            print(f"  ✗ File not found in downloads/: {filename}")
            results.append({
                'filename': filename,
                'narrator': narrator,
                'success': False,
                'message': 'File not found in downloads/'
            })
            continue

        try:
            # Get durations
            orig_dur = get_audio_duration(conversation_path)
            narr_dur = get_audio_duration(narrator_paths[narrator])
            print(f"  Original: {orig_dur:.1f}s, Narrator: {narr_dur:.1f}s")

            # Concatenate
            print(f"  Concatenating {narrator} narrator + conversation...")
            if not concatenate_audio_ffmpeg([narrator_paths[narrator], conversation_path], output_path):
                results.append({
                    'filename': filename,
                    'narrator': narrator,
                    'success': False,
                    'message': 'Concatenation failed'
                })
                continue

            # Validate output
            out_dur = get_audio_duration(output_path)
            expected_dur = orig_dur + narr_dur
            dur_diff = abs(out_dur - expected_dur)

            if dur_diff > 1.0:  # Allow 1 second tolerance
                print(f"  ⚠ Duration mismatch: expected {expected_dur:.1f}s, got {out_dur:.1f}s")

            print(f"  ✓ Output: {out_dur:.1f}s (expected ~{expected_dur:.1f}s)")

            results.append({
                'filename': filename,
                'file_id': file_id,
                'narrator': narrator,
                'success': True,
                'original_duration': orig_dur,
                'narrator_duration': narr_dur,
                'output_duration': out_dur,
                'message': 'Successfully processed'
            })

        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append({
                'filename': filename,
                'narrator': narrator,
                'success': False,
                'message': f'Unexpected error: {e}'
            })

    # Print summary
    successful = sum(1 for r in results if r['success'])
    failed = sum(1 for r in results if not r['success'])

    print("\n" + "=" * 80)
    print("PROCESSING SUMMARY")
    print("=" * 80)
    print(f"Total: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    if failed > 0:
        print("\nFailed files:")
        for r in results:
            if not r['success']:
                print(f"  ✗ {r['filename']}: {r['message']}")

    if successful > 0:
        print("\n" + "=" * 80)
        print("FILES READY FOR DRIVE UPLOAD")
        print("=" * 80)
        print("\nProcessed files are in: data/processed/")
        print("These files should be uploaded to Drive with version management (UPDATE method)")

        print("\nFile IDs for upload:")
        for r in results:
            if r['success']:
                print(f"  • {r['filename']}")
                print(f"    File ID: {r['file_id']}")

    return results


def main():
    print("\n" + "=" * 80)
    print("BATCH 100 CONVERSATION PROCESSING")
    print("=" * 80)

    # Download narrator files
    narrator_paths = download_narrator_files()
    if not narrator_paths:
        print("\n✗ Failed to download narrator files. Exiting.")
        return 1

    # Process conversations from downloads/ directory
    results = process_conversations_from_downloads(narrator_paths)

    successful = sum(1 for r in results if r['success'])
    print(f"\n{'='*80}")
    print(f"COMPLETE: {successful}/{len(results)} files processed successfully")
    print(f"{'='*80}\n")

    return 0 if successful == len(results) else 1


if __name__ == '__main__':
    exit(main())
