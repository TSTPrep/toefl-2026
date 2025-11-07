# Speaker Detection - Quick Start

Get speaker-aware audio splitting working in 5 minutes.

---

## 1. Install Dependencies (2 min)

```bash
pip install -r requirements_speaker_detection.txt
```

---

## 2. Configure Token (1 min)

```bash
# Get token: https://huggingface.co/settings/tokens
# Accept terms: https://huggingface.co/pyannote/speaker-diarization-3.1

export HF_TOKEN="your_token_here"
```

---

## 3. Test Setup (30 sec)

```bash
python3 test_setup.py
```

---

## 4. Analyze Current Files (30 sec)

```bash
python3 reprocess_statements.py --analyze-only
```

---

## 5. Reprocess Suspicious Files (1 min)

```bash
# Dry run first
python3 reprocess_statements.py --suspicious-only --dry-run

# Actually reprocess
python3 reprocess_statements.py --suspicious-only
```

---

## Common Commands

```bash
# Analyze (no changes)
python3 reprocess_statements.py --analyze-only

# Test single file
python3 split_with_speaker_detection.py "input/file.mp3"

# Reprocess suspicious only
python3 reprocess_statements.py --suspicious-only

# Reprocess specific module
python3 reprocess_statements.py --dir "02.05.02, Listen and Choose, Module 2"

# Reprocess all
python3 reprocess_statements.py

# Without speaker detection (faster)
python3 split_with_speaker_detection.py --no-speaker-detection "input/file.mp3"
```

---

## Troubleshooting

**Token issues?**
```bash
echo $HF_TOKEN  # Check if set
export HF_TOKEN="your_token"
```

**Missing packages?**
```bash
pip install -r requirements_speaker_detection.txt
```

**Too slow?**
```bash
# Use silence only
python3 split_with_speaker_detection.py --no-speaker-detection input.mp3
```

---

## Full Documentation

- **ANALYSIS_SUMMARY.md** - Overview and results
- **SPEAKER_DETECTION_GUIDE.md** - Complete guide
- Run `--help` on any script

---

## Expected Improvements

- 58 → 65-75 statements (+12-29%)
- Better speaker separation
- More uniform durations
- Each file = one statement

---

**Time**: 5 minutes
**Difficulty**: Easy
**Dependencies**: Python 3.8+, ffmpeg, HuggingFace account
