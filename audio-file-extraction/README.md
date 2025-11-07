# TOEFL Audio File Extraction

Automated system for processing TOEFL audio files stored in Google Drive. Handles conversation prefix addition and file splitting tasks.

## Overview

This project provides tools to:

1. **Task 2**: Add narrator prefixes to conversation files with deterministic 50/50 rotation
2. **Task 1**: Investigate and split "Listen and Choose" files (investigation-first approach)

## Architecture

```
audio-file-extraction/
├── scripts/
│   ├── utils/
│   │   ├── audio_processor.py    # ffmpeg wrapper for audio operations
│   │   ├── drive_manager.py      # Google Drive API wrapper
│   │   ├── file_parser.py        # Filename parsing/validation
│   │   └── logger.py             # Logging configuration
│   ├── task2_add_prefix.py       # Main Task 2 script
│   └── investigate_task1.py      # Task 1 investigation framework
├── config/                        # Configuration files
├── data/
│   ├── raw/                      # Downloaded files
│   ├── processed/                # Processed output files
│   └── temp/                     # Temporary processing files
├── tests/                        # Comprehensive test suite
├── logs/                         # Application logs
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment configuration template
└── README.md                     # This file
```

## Features

### Core Utilities

#### AudioProcessor
- **Concatenation**: ffmpeg concat demuxer method (no re-encoding, preserves quality)
- **Splitting**: Split audio files at specified time points
- **Validation**: Verify audio file integrity
- **Duration extraction**: Get accurate audio durations

#### DriveManager
- **Authentication**: OAuth 2.0 with token persistence
- **Listing**: Paginated file listing with query support
- **Download**: Efficient file downloads with progress tracking
- **Upload**: Version management (updates existing files instead of creating new)
- **Search**: Pattern-based file searching

#### FileParser
- **Validation**: Parse and validate TOEFL filename patterns
- **Filtering**: Filter by conversation, Listen and Choose, etc.
- **Grouping**: Group files by base name for related file operations

### Task 2: Add Narrator Prefix

**Purpose**: Add narrator introduction to conversation files with deterministic narrator rotation.

**Features**:
- Lists all conversation files from Google Drive
- Downloads narrator files (Daniel/Matilda)
- Assigns narrators using alphabetical sorting (50/50 rotation)
- Concatenates narrator prefix with conversation using ffmpeg concat demuxer
- Uploads to Drive with version management (updates existing files)
- Generates comprehensive processing report

**Usage**:
```bash
# Full processing
python scripts/task2_add_prefix.py

# Dry run (no uploads)
python scripts/task2_add_prefix.py --dry-run

# Process limited files (testing)
python scripts/task2_add_prefix.py --limit 10
```

### Task 1: Investigation Framework

**Purpose**: Discover and analyze "Listen and Choose" files to inform splitting implementation.

**Features**:
- Searches Drive for all Listen and Choose files
- Analyzes naming patterns
- Downloads and analyzes audio samples
- Generates investigation report with recommendations

**Usage**:
```bash
# Full investigation
python scripts/investigate_task1.py

# Analyze more samples
python scripts/investigate_task1.py --download-samples 10
```

## Installation

### Prerequisites

1. **Python 3.8+**
2. **ffmpeg**: Required for audio processing
   ```bash
   # Ubuntu/Debian
   sudo apt-get install ffmpeg

   # macOS
   brew install ffmpeg

   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

3. **Google Cloud Project** with Drive API enabled
   - Create project at https://console.cloud.google.com
   - Enable Google Drive API
   - Create OAuth 2.0 credentials
   - Download `credentials.json`

### Setup

1. **Clone and navigate to project**:
   ```bash
   cd audio-file-extraction
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your values:
   ```env
   DRIVE_FOLDER_ID=your_folder_id_here
   NARRATOR_DANIEL_FILE_ID=your_daniel_file_id
   NARRATOR_MATILDA_FILE_ID=your_matilda_file_id
   LOG_LEVEL=INFO
   ```

5. **Add Google credentials**:
   - Place `credentials.json` in project root
   - First run will initiate OAuth flow and create `token.json`

6. **Verify installation**:
   ```bash
   python -c "from scripts.utils.audio_processor import AudioProcessor; print('ffmpeg:', AudioProcessor.check_ffmpeg_installed())"
   ```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DRIVE_FOLDER_ID` | Google Drive folder ID | Required |
| `CREDENTIALS_FILE` | Path to credentials.json | `credentials.json` |
| `TOKEN_FILE` | Path to token file | `token.json` |
| `NARRATOR_DANIEL_FILE_ID` | Daniel narrator file ID | Required |
| `NARRATOR_MATILDA_FILE_ID` | Matilda narrator file ID | Required |
| `TEMP_DIR` | Temporary files directory | `data/temp` |
| `PROCESSED_DIR` | Processed files directory | `data/processed` |
| `RAW_DIR` | Raw files directory | `data/raw` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FILE` | Log file path | `logs/processing.log` |

### Google Drive Authentication

First run will open browser for OAuth authentication:

1. Select Google account
2. Grant Drive API permissions
3. Token saved to `token.json` for future use

Token refreshes automatically when expired.

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Suites

```bash
# File parser tests (fast)
pytest tests/test_file_parser.py -v

# Audio processor tests (requires ffmpeg)
pytest tests/test_audio_processor.py -v

# Drive manager tests (mocked, no API calls)
pytest tests/test_drive_manager.py -v
```

### Test Coverage

```bash
pytest tests/ --cov=scripts/utils --cov-report=html
```

Coverage report generated in `htmlcov/index.html`.

### Test Categories

- **Unit tests**: `test_file_parser.py` - Pure logic, no external dependencies
- **Integration tests**: `test_audio_processor.py` - Requires ffmpeg, creates test audio files
- **Mock tests**: `test_drive_manager.py` - Mocked Drive API calls

## Usage Examples

### Task 2: Process Conversation Files

**Basic usage**:
```bash
python scripts/task2_add_prefix.py
```

**Dry run (preview without uploading)**:
```bash
python scripts/task2_add_prefix.py --dry-run
```

**Process limited files for testing**:
```bash
python scripts/task2_add_prefix.py --limit 5
```

**Output**:
- Processed files uploaded to Drive (version management)
- Processing report: `data/processed/task2_processing_report.txt`
- Logs: `logs/processing.log`

### Task 1: Investigate Files

**Basic usage**:
```bash
python scripts/investigate_task1.py
```

**Analyze more samples**:
```bash
python scripts/investigate_task1.py --download-samples 10
```

**Output**:
- Text report: `data/task1_investigation_report.txt`
- JSON report: `data/task1_investigation_report.json`
- Logs: `logs/processing.log`

## Technical Details

### Audio Processing

**Concatenation Method**: ffmpeg concat demuxer
- **Advantages**: No re-encoding, preserves quality, very fast
- **Requirements**: All files must have same codec/format/parameters
- **Implementation**: Creates temporary concat list file, uses `-c copy`

**Example concat list**:
```
file '/path/to/narrator.mp3'
file '/path/to/conversation.mp3'
```

**ffmpeg command**:
```bash
ffmpeg -f concat -safe 0 -i concat_list.txt -c copy output.mp3
```

### Drive Version Management

**Update Existing Files**:
- Searches for file by exact name match
- If found: Updates existing file (preserves file ID, increments version)
- If not found: Creates new file

**Benefits**:
- Preserves sharing links
- Maintains file history
- Prevents duplicate files

### Narrator Rotation

**Deterministic Algorithm**:
1. Sort files alphabetically by name
2. Assign narrators alternating: Daniel (even index), Matilda (odd index)
3. Result: Consistent 50/50 distribution

**Example**:
```
Files (sorted):          Narrator:
conversation-Q1-v1  ->   Daniel
conversation-Q2-v1  ->   Matilda
conversation-Q3-v1  ->   Daniel
conversation-Q4-v1  ->   Matilda
```

### Filename Patterns

**Valid patterns**:
```
TOEFL-{TestType}-{TaskType}-Q{N}-v{N}[-{suffix}].mp3

Examples:
- TOEFL-Speaking-Conversation-Q1-v1-conversation.mp3
- TOEFL-Speaking-Listen-and-Choose-Q1-v1.mp3
- TOEFL-Reading-Passage-Q5-v2.mp3
```

**Components**:
- `TOEFL`: Fixed prefix
- `{TestType}`: Speaking, Reading, Writing, Listening
- `{TaskType}`: Conversation, Listen-and-Choose, Passage, etc.
- `Q{N}`: Question number
- `v{N}`: Version number
- `[-{suffix}]`: Optional suffix (conversation, response, etc.)
- `.mp3`: File extension

## Logging

**Log levels**:
- `DEBUG`: Detailed diagnostic information
- `INFO`: Confirmation of expected operations (default)
- `WARNING`: Unexpected but handled situations
- `ERROR`: Errors preventing specific operations
- `CRITICAL`: Errors preventing program execution

**Log locations**:
- Console: Real-time feedback
- File: `logs/processing.log` (persistent record)

**Change log level**:
```bash
# In .env
LOG_LEVEL=DEBUG

# Or at runtime
export LOG_LEVEL=DEBUG
python scripts/task2_add_prefix.py
```

## Error Handling

**Common errors and solutions**:

1. **ffmpeg not found**
   - Install ffmpeg (see Prerequisites)
   - Verify: `ffmpeg -version`

2. **Credentials file not found**
   - Download `credentials.json` from Google Cloud Console
   - Place in project root

3. **Permission denied (Drive API)**
   - Delete `token.json`
   - Re-authenticate with correct account

4. **Audio file not found**
   - Check `DRIVE_FOLDER_ID` in `.env`
   - Verify file exists in Drive
   - Check filename matches pattern

5. **Concatenation failed**
   - Verify audio files have same format/codec
   - Check ffmpeg error in logs
   - Try with `use_concat_demuxer=False` (slower, re-encodes)

## Development

### Code Style

**Format code**:
```bash
black scripts/ tests/
```

**Lint code**:
```bash
flake8 scripts/ tests/
```

**Type checking**:
```bash
mypy scripts/
```

### Project Structure Conventions

- **Utilities**: Reusable components in `scripts/utils/`
- **Main scripts**: Task-specific scripts in `scripts/`
- **Tests**: Mirror source structure in `tests/`
- **Data**: Gitignored, organized by processing stage

### Adding New Tasks

1. Create script in `scripts/`
2. Use existing utilities from `scripts/utils/`
3. Add tests in `tests/`
4. Document in README
5. Update requirements.txt if new dependencies

## Performance Considerations

**Optimization strategies**:

1. **ffmpeg concat demuxer**: No re-encoding (~10x faster than filter method)
2. **Pagination**: Process files in batches to handle large datasets
3. **Temp file cleanup**: Remove temporary files after processing
4. **Version management**: Update existing files instead of creating new
5. **Parallel processing**: Can be added for independent file operations

**Bottlenecks**:
- Network I/O: Download/upload to Drive (most significant)
- Disk I/O: Reading/writing large audio files
- Audio processing: Minimal due to concat demuxer (no encoding)

## Troubleshooting

### Enable Debug Logging

```bash
export LOG_LEVEL=DEBUG
python scripts/task2_add_prefix.py
```

### Test Drive Connection

```python
from scripts.utils.drive_manager import GoogleDriveManager

manager = GoogleDriveManager()
files = list(manager.list_files())
print(f"Found {len(files)} files")
```

### Test Audio Processing

```bash
# Create test audio
ffmpeg -f lavfi -i anullsrc=r=44100:cl=stereo -t 1 test.mp3

# Test validation
python -c "from scripts.utils.audio_processor import AudioProcessor; print(AudioProcessor.validate_audio_file('test.mp3'))"
```

### Verify File Parser

```python
from scripts.utils.file_parser import TOEFLFileParser

filename = "TOEFL-Speaking-Conversation-Q1-v1-conversation.mp3"
info = TOEFLFileParser.parse(filename)
print(info)
```

## Contributing

1. Fork repository
2. Create feature branch
3. Make changes with tests
4. Run test suite
5. Submit pull request

## License

Copyright 2024 TSTPrep. All rights reserved.

## Support

For issues or questions:
1. Check logs in `logs/processing.log`
2. Review error messages
3. Consult Troubleshooting section
4. Contact development team

## Project Status

- ✅ **Task 2**: Fully implemented and ready for execution
- 🔍 **Task 1**: Investigation framework ready (implementation pending investigation results)
- ✅ **Core utilities**: Complete with comprehensive tests
- ✅ **Documentation**: Complete with usage examples

## Next Steps

1. **Configure environment**: Set up `.env` with actual Drive IDs
2. **Authenticate**: Run any script to complete OAuth flow
3. **Test Task 2**: Run with `--dry-run` and `--limit 5` to verify
4. **Execute Task 2**: Run full processing
5. **Investigate Task 1**: Run investigation script
6. **Implement Task 1**: Based on investigation findings
