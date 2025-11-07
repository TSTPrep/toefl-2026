# Task 2: Quick Start Guide

## Current Status

✅ **Processing Complete**: All 19 conversation files processed with narrator prefixes
⏳ **Upload Pending**: Files ready for Google Drive upload

## Quick Commands

### View Processing Results
```bash
cd /home/blackthorne/Work/tstprep.com/toefl-2026/audio-file-extraction
ls -lh data/processed/*.mp3
cat data/processed/task2_processing_report.json | python3 -m json.tool
```

### Upload to Google Drive (One-Time Setup)

**Step 1**: Download Google Drive API credentials
- Go to: https://console.cloud.google.com/
- Enable: Google Drive API
- Create: OAuth 2.0 Client ID (Desktop app)
- Download: credentials.json
- Place in: `/home/blackthorne/Work/tstprep.com/toefl-2026/audio-file-extraction/`

**Step 2**: Run upload script
```bash
cd /home/blackthorne/Work/tstprep.com/toefl-2026/audio-file-extraction
source venv/bin/activate
python3 upload_to_drive.py --dry-run  # Test first
python3 upload_to_drive.py             # Actual upload
```

Browser will open for authorization. After granting access, token.json will be saved for future use.

### Re-run Processing (if needed)
```bash
cd /home/blackthorne/Work/tstprep.com/toefl-2026/audio-file-extraction
source venv/bin/activate

# Clean previous outputs
rm -rf data/processed/*.mp3

# Re-process all files
python3 task2_mcp_orchestrator.py

# Or test with limited files
python3 task2_mcp_orchestrator.py --limit 3 --dry-run
```

## Files & Locations

**Processed Files**: `/home/blackthorne/Work/tstprep.com/toefl-2026/audio-file-extraction/data/processed/`
- 19 MP3 files with narrator prefixes
- task2_processing_report.json

**Scripts**:
- `task2_mcp_orchestrator.py` - Main processing script
- `upload_to_drive.py` - Drive upload with version management

**Documentation**:
- `TASK2_COMPLETION_REPORT.md` - Complete technical report
- `QUICK_START.md` - This file (quick reference)

**Memory**: `audio_workflows` updated with Task 2 completion status

## Narrator Assignments

**Daniel (10 files)**:
- 02.01.04, 02.02.04, 02.02.06, 02.03.03, 02.03.05
- 02.04.03, 02.04.05, 02.04.07, 02.05.04, 02.05.06

**Matilda (9 files)**:
- 02.02.03, 02.02.05, 02.02.07, 02.03.04, 02.03.06
- 02.04.04, 02.04.06, 02.05.03, 02.05.05

## Troubleshooting

### Missing credentials.json
Download from Google Cloud Console → APIs & Services → Credentials

### Upload fails with 403 Forbidden
Delete token.json and re-authenticate: `rm token.json && python3 upload_to_drive.py`

### ffmpeg not found
Install: `sudo apt-get install ffmpeg` (Ubuntu) or `brew install ffmpeg` (macOS)

## Next Action

**To complete Task 2**: Set up Google Drive API credentials and run `upload_to_drive.py`

---

For detailed technical documentation, see: `TASK2_COMPLETION_REPORT.md`
