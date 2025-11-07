# Speaker Detection Feature

## Overview

Enhanced audio splitting using speaker diarization to better separate statements in "Listen and Choose (no pauses)" files.

## Quick Start

```bash
# 1. Install
pip install -r requirements_speaker_detection.txt

# 2. Configure
export HF_TOKEN="your_huggingface_token"

# 3. Test
python3 test_setup.py

# 4. Use
python3 split_with_speaker_detection.py "input/file.mp3"
```

## Key Files

- **SPEAKER_DETECTION_QUICKSTART.md** - 5-minute start guide
- **ANALYSIS_SUMMARY.md** - Overview and getting started
- **SPEAKER_DETECTION_GUIDE.md** - Complete documentation
- **DELIVERABLES.md** - Implementation summary

## Scripts

- `split_with_speaker_detection.py` - Improved splitting with speaker detection
- `reprocess_statements.py` - Batch reprocessing utility
- `test_setup.py` - Setup verification
- `simple_audio_check.py` - Audio analysis tool

## Expected Results

- 12-29% more statements detected
- Better speaker separation
- More uniform durations
- Each file = one statement

## Get Help

```bash
python3 test_setup.py                              # Check setup
python3 reprocess_statements.py --analyze-only    # Analyze files
python3 split_with_speaker_detection.py --help    # Usage info
```

See **SPEAKER_DETECTION_QUICKSTART.md** for complete instructions.
