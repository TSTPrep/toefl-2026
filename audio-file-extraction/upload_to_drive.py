#!/usr/bin/env python3
"""
Upload processed files to Google Drive with version management.

This script UPDATES existing files (preserving file IDs and sharing links)
rather than creating new files.

Requires: Google Drive API credentials (token.json or credentials.json)
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

# Scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Paths
PROCESSED_DIR = Path('data/processed')
REPORT_FILE = PROCESSED_DIR / 'task2_processing_report.json'
TOKEN_FILE = Path('token.json')
CREDENTIALS_FILE = Path('credentials.json')


def authenticate_drive() -> any:
    """Authenticate with Google Drive API."""
    creds = None

    # Check for existing token
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    # Refresh or create new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print(f"Error: {CREDENTIALS_FILE} not found!")
                print("Please download credentials.json from Google Cloud Console.")
                sys.exit(1)

            print("Starting OAuth flow...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save credentials
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
        print(f"Credentials saved to {TOKEN_FILE}")

    # Build service
    service = build('drive', 'v3', credentials=creds)
    print("✓ Google Drive API authenticated")
    return service


def upload_file_update(service: any, file_path: Path, file_id: str) -> Dict:
    """
    Update an existing file in Google Drive (version management).

    Args:
        service: Google Drive API service
        file_path: Local file path
        file_id: Existing Drive file ID to update

    Returns:
        Updated file metadata
    """
    media = MediaFileUpload(
        str(file_path),
        mimetype='audio/mpeg',
        resumable=True
    )

    try:
        updated_file = service.files().update(
            fileId=file_id,
            media_body=media,
            fields='id, name, size, modifiedTime, version, webViewLink'
        ).execute()

        return {
            'success': True,
            'file_id': updated_file['id'],
            'name': updated_file['name'],
            'size': updated_file.get('size'),
            'version': updated_file.get('version'),
            'modified': updated_file.get('modifiedTime'),
            'link': updated_file.get('webViewLink')
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Upload processed files to Google Drive')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be uploaded without actually uploading')

    args = parser.parse_args()

    # Load processing report
    if not REPORT_FILE.exists():
        print(f"Error: {REPORT_FILE} not found!")
        print("Please run task2_mcp_orchestrator.py first.")
        sys.exit(1)

    with open(REPORT_FILE, 'r') as f:
        report = json.load(f)

    successful_files = [r for r in report['results'] if r['success']]

    print("=" * 80)
    print(f"UPLOADING {len(successful_files)} FILES TO GOOGLE DRIVE")
    if args.dry_run:
        print("(DRY RUN - no actual uploads)")
    print("=" * 80)

    if args.dry_run:
        print("\nFiles that would be uploaded:")
        for result in successful_files:
            file_path = PROCESSED_DIR / result['filename']
            print(f"\n  • {result['filename']}")
            print(f"    File ID: {result['file_id']}")
            print(f"    Size: {file_path.stat().st_size:,} bytes")
            print(f"    Narrator: {result['narrator'].capitalize()}")
        print(f"\nTotal files: {len(successful_files)}")
        return

    # Authenticate
    print("\nAuthenticating with Google Drive...")
    service = authenticate_drive()

    # Upload files
    upload_results = []

    for idx, result in enumerate(successful_files, 1):
        file_path = PROCESSED_DIR / result['filename']
        file_id = result['file_id']

        print(f"\n[{idx}/{len(successful_files)}] Uploading: {result['filename']}")
        print(f"  File ID: {file_id}")
        print(f"  Size: {file_path.stat().st_size:,} bytes")

        upload_result = upload_file_update(service, file_path, file_id)

        if upload_result['success']:
            print(f"  ✓ SUCCESS")
            print(f"    Version: {upload_result.get('version')}")
            print(f"    Modified: {upload_result.get('modified')}")
            print(f"    Link: {upload_result.get('link')}")
        else:
            print(f"  ✗ FAILED: {upload_result.get('error')}")

        upload_results.append({
            'filename': result['filename'],
            'file_id': file_id,
            'narrator': result['narrator'],
            **upload_result
        })

    # Generate upload report
    upload_report = {
        'total': len(upload_results),
        'successful': sum(1 for r in upload_results if r['success']),
        'failed': sum(1 for r in upload_results if not r['success']),
        'results': upload_results
    }

    upload_report_file = PROCESSED_DIR / 'task2_upload_report.json'
    with open(upload_report_file, 'w') as f:
        json.dump(upload_report, f, indent=2)

    # Summary
    print("\n" + "=" * 80)
    print("UPLOAD SUMMARY")
    print("=" * 80)
    print(f"Total: {upload_report['total']}")
    print(f"Successful: {upload_report['successful']}")
    print(f"Failed: {upload_report['failed']}")
    print(f"\nUpload report saved: {upload_report_file}")

    if upload_report['failed'] > 0:
        print("\nFailed uploads:")
        for r in upload_results:
            if not r['success']:
                print(f"  ✗ {r['filename']}: {r.get('error')}")

    print("\n" + "=" * 80)
    print("TASK 2 COMPLETE!")
    print("=" * 80)
    print("\nAll conversation files now have narrator prefixes:")
    print(f"  • Daniel: {len([r for r in successful_files if r['narrator'] == 'daniel'])} files")
    print(f"  • Matilda: {len([r for r in successful_files if r['narrator'] == 'matilda'])} files")
    print("\nFiles have been updated in Google Drive (preserving file IDs and sharing links).")


if __name__ == '__main__':
    main()
