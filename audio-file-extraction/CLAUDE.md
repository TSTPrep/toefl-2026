# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project processes TOEFL audio files from Google Drive with two main tasks:
1. **Task 1**: Split "Listen and Choose" combined audio files into individual statements (10 files)
2. **Task 2**: Prepend narrator introduction to conversation audio files (~19+ files) with 50/50 Daniel/Matilda rotation

Source files are in Google Drive folder: `1vbSukNXg7Z5mx3fAb6-h2TWxTBjHX5io`

## Required Tools

```bash
# System dependencies
ffmpeg >= 4.0
python3 >= 3.8

# Python dependencies (install with pip install -r requirements.txt)
google-api-python-client>=2.0.0
google-auth-httplib2>=0.1.0
google-auth-oauthlib>=0.5.0
```

## Project Structure

```
scripts/
  ├── task1_split_listen_choose.py   # Split "Listen and Choose" files
  ├── task2_add_prefix.py            # Add conversation prefixes
  └── utils/
      ├── audio_processor.py         # ffmpeg operations
      ├── drive_manager.py           # Google Drive API wrapper
      ├── file_parser.py             # Filename parsing/validation
      └── logger.py                  # Logging configuration

data/                                # Gitignored
  ├── input/                         # Downloaded source files
  ├── output/                        # Processed files before upload
  └── temp/                          # Temporary processing files

config/
  ├── drive_config.json              # Drive folder IDs
  └── timestamps_task1.json          # Manual timestamps (if needed for Task 1)
```

## Core Workflows

### Task 2: Adding Narrator Prefix (Primary Task)

**Process Flow**:
1. List all files in Google Drive folder with pagination
2. Filter conversation files matching pattern: `02.TT.PP, Listen to a Conversation, Module X.mp3`
3. Download narrator files (Daniel/Matilda) and conversation files
4. Apply alphabetical sorting for deterministic narrator assignment (alternating 50/50)
5. Concatenate using ffmpeg concat demuxer (preserves audio quality)
6. Upload back to Drive using **version management** (update existing file, don't create new)

**Critical ffmpeg Command**:
```bash
# Use concat demuxer method (recommended for identical formats)
echo "file '/path/to/narrator_prefix.mp3'" > concat_list.txt
echo "file '/path/to/conversation.mp3'" >> concat_list.txt
ffmpeg -f concat -safe 0 -i concat_list.txt -c copy output.mp3
```

**Narrator Assignment**:
```python
# Deterministic alphabetical sorting with alternating assignment
conversation_files.sort()
narrator = "Daniel" if idx % 2 == 0 else "Matilda"
```

### Task 1: Splitting "Listen and Choose" Files ✅ COMPLETED

**Status**: Successfully processed all 10 files → **58 total statement files created**

**Files Processed**: Pattern `02.TT.PP, Listen and Choose, Module X (no pauses).mp3`
- 2 files per test × 5 tests = 10 total files
- All files processed using automated silence detection

**Implementation**:
- **Script**: `split_no_pauses.py` (fully automated)
- **Method**: ffmpeg silence detection + midpoint splitting
- **Parameters**: `-50dB` threshold, `0.2s` minimum silence duration
- **Output**: Sequential statement files with proper naming

**Results by File**:
| File | Statements Created |
|------|-------------------|
| 02.01.01, Module 1 | 5 statements |
| 02.01.02, Module 2 | 2 statements |
| 02.02.01, Module 1 | 12 statements |
| 02.02.02, Module 2 | 3 statements |
| 02.03.01, Module 1 | 6 statements |
| 02.03.02, Module 2 | 3 statements |
| 02.04.01, Module 1 | 9 statements |
| 02.04.02, Module 2 | 5 statements |
| 02.05.01, Module 1 | 10 statements |
| 02.05.02, Module 2 | 3 statements |

**Output Naming**: `02.TT.PP, Listen and Choose, Module X, Statement NNN.mp3`

**Key Commands**:
```bash
# Process single file
python split_no_pauses.py "downloads/input.mp3"

# Process all files
./process_all.sh

# Custom parameters
python split_no_pauses.py -t -45 -d 0.25 "input.mp3"
```

**Output Location**: `output/statements/{file_base}/`

See `TASK1_RESULTS.md` for complete details.

## Google Drive Integration

### Authentication
- Use Google Workspace MCP with `vlad@serenichron.com` credentials
- API scopes needed: `drive.readonly` (download), `drive.file` (upload)

### Version Management (Critical for Task 2)
Must use Drive API `update()` method to preserve file history:
```python
from googleapiclient.http import MediaFileUpload

media = MediaFileUpload(local_file_path, mimetype='audio/mpeg')
drive_service.files().update(
    fileId=existing_file_id,  # Same file ID, not create new
    media_body=media
).execute()
```

## File Naming Conventions

**Pattern**: `02.TT.PP, Description, Module X.mp3`
- `02` = Listening section
- `TT` = Test number (01-05)
- `PP` = Passage number within test
- Examples:
  - `02.01.04, Listen to a Conversation, Module 1.mp3`
  - `02.02.03, Listen and Choose, Module 1 (no pauses).mp3`

**Known Inconsistencies**:
- "COnversation" (typo in some files)
- Extra parentheses in module names
- Parser should handle gracefully with flexible regex

## Quality Validation

**Pre-concatenation checks**:
```bash
ffprobe -v error -show_entries stream=codec_name,sample_rate,channels,bit_rate input.mp3
```

**Post-processing validation**:
- Verify output file size > 0
- Check duration = narrator duration + conversation duration (±1 second tolerance)
- Confirm no audio artifacts at concatenation point
- Spot-check random samples manually

## Error Handling

**Drive API**:
- Implement exponential backoff for rate limits
- Retry logic for network failures (max 3 retries)
- Comprehensive logging for debugging

**Audio Processing**:
- Validate file integrity before processing
- Check matching audio formats (sample rate, channels)
- Log ffmpeg stderr output for debugging

## Development Commands

```bash
# Setup environment
pip install -r requirements.txt

# Run Task 2 (conversation prefix)
python scripts/task2_add_prefix.py

# Run Task 1 (split audio - after investigation)
python scripts/task1_split_listen_choose.py

# Test utilities
python -m pytest tests/

# Check audio file properties
ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1:nokey=1 file.mp3
```

## Performance Considerations

- Estimated disk space: ~75MB for Task 2 processing
- Use parallel processing for multiple files (respect Drive API rate limits)
- Clean up temp files after successful upload
- Progress tracking for long-running operations

## Implementation Priority

1. ✅ **Task 1 COMPLETED** - All 58 statement files created from 10 source files
2. ⏳ **Task 1 Upload** - Upload statement files to Google Drive (manual upload required due to MCP binary file limitation)
3. ⏳ **Task 2** - Add narrator prefix to conversation files (~24 files identified)

## Key Technical Decisions

- **Audio concatenation**: ffmpeg concat demuxer (no re-encoding, preserves quality)
- **Narrator rotation**: Alphabetical sorting ensures deterministic, repeatable assignment
- **File management**: Drive version management (not new files)
- **Error recovery**: Comprehensive logging + retry logic for resilience