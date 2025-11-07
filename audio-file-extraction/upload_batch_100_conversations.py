#!/usr/bin/env python3
"""
Upload batch 100.XX processed conversation files to Google Drive
Uses UPDATE to preserve file IDs and sharing links (version management)
"""

import sys
from pathlib import Path

# File ID mapping from Drive search results
CONVERSATION_FILE_IDS = {
    "100.04, Listen to a Conversation 1.mp3": "1TEmBiBvwYqJJwpjSN-7FZ7JZ2IgT4kDp",
    "100.05, Listen to a Conversation 2.mp3": "1YWQ7I4l8p8JiACCqYIivX4-pngNJT2kR",
    "100.06, Listen to a Conversation 3.mp3": "1_Qn0yjAQSjw1LIfm-Ps9aLN_caQaNKWM",
    "100.07, Listen to a Conversation 4.mp3": "1ZLrFSkNxiOupOVcPxbJh72Or3mf3Qoez",
    "100.08, Listen to a Conversation 5.mp3": "1G6IvJmlrX3OTtU1doGHXlmW00RsOPID7",
    "100.09, Listen to a Conversation 6.mp3": "1VDJ8RHLDAV9TpCfnF7-DKISxKTttbPSB",
    "100.10, Listen to a Conversation 7.mp3": "1v2sRW1JwN0h4lYC1lT4Gn20Gffw567VM",
    "100.11, Listen to a Conversation 8.mp3": "1R88XEj8SS3lO5ryPJJ6gyCOBuVpok4jV",
    "100.12, Listen to a Conversation 9.mp3": "1Nz2g74vhtlMHFk8nNgX5CPjRZTtVu-DA",
    "100.13, Listen to a Conversation 10.mp3": "14Opr2cuX4qkD0_J0NL6xXjMF4LjShgHq",
    "100.14, Listen to a Conversation 11.mp3": "1QnUzc3a7N0BhHGfQSytCKXu24JUeVafK",
    "100.15, Listen to a Conversation 12.mp3": "1iC99A1RvD7ivfEfVCFoPvCYnt98Jc8AJ",
    "100.16, Listen to a Conversation 13.mp3": "1iz5Q8EYqWPso39V4iXtoD3UWZtxDTSTc",
    "100.17, Listen to a Conversation 14.mp3": "1V0JebdDmZ2tuZ7pKniyrAqTtOPz5T19l",
    "100.18, Listen to a Conversation 15.mp3": "1Xnu_zgi0LAgXsok3j1W5kAst-8LIp6o5",
}

PROCESSED_DIR = Path("data/processed")

def main():
    """Generate file list for Claude to upload via MCP"""

    print("=" * 80)
    print("BATCH 100.XX CONVERSATION FILES - UPLOAD WITH VERSION MANAGEMENT")
    print("=" * 80)
    print()
    print("IMPORTANT: Use Google Workspace MCP to UPDATE files (not create new)")
    print("This preserves file IDs and sharing links.")
    print()
    print("Files to upload:")
    print()

    upload_list = []
    missing_files = []

    for filename, file_id in sorted(CONVERSATION_FILE_IDS.items()):
        local_path = PROCESSED_DIR / filename

        if not local_path.exists():
            missing_files.append(filename)
            print(f"  ✗ MISSING: {filename}")
            continue

        size = local_path.stat().st_size
        upload_list.append({
            "filename": filename,
            "file_id": file_id,
            "local_path": str(local_path.absolute()),
            "size": size
        })

        print(f"  [{len(upload_list):2d}] {filename}")
        print(f"       File ID: {file_id}")
        print(f"       Local:   {local_path.absolute()}")
        print(f"       Size:    {size:,} bytes")
        print()

    print("=" * 80)
    print(f"SUMMARY: {len(upload_list)} files ready to upload")

    if missing_files:
        print(f"WARNING: {len(missing_files)} files missing")
        for f in missing_files:
            print(f"  - {f}")

    print("=" * 80)
    print()
    print("MANUAL UPLOAD REQUIRED:")
    print("MCP Google Workspace cannot update binary files programmatically.")
    print()
    print("Please manually upload these 15 files via:")
    print("  1. Google Drive web interface")
    print("  2. Right-click existing file → 'Manage versions' → Upload new version")
    print("  3. Select corresponding file from data/processed/")
    print()
    print("This preserves file IDs and sharing links (version management).")
    print()

    return 0 if not missing_files else 1

if __name__ == "__main__":
    sys.exit(main())
