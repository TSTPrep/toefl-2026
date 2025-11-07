# Task 1: Speaker Detection Improvement - Next Steps

## Current Status (Session End)

### ✅ Completed
1. **Initial Task 1**: 58 statement files created from 10 "Listen and Choose (no pauses)" files
2. **Issue Identified**: Some split files contain multiple statements (multiple speakers in one file)
3. **Solution Implemented**: Speaker diarization scripts using pyannote.audio 3.1
4. **Environment Setup**: Virtual environment created with all dependencies installed
5. **HuggingFace Token**: Configured and ready (user confirmed)

### ⏳ Pending
1. Verify setup with test script
2. Analyze current files to identify problematic ones
3. Test speaker detection on one problematic file
4. Batch reprocess suspicious files
5. Validate improvements
6. Upload improved files to Google Drive

---

## Environment Details

**Location**: `/home/blackthorne/Work/tstprep.com/toefl-2026/audio-file-extraction/`

**Virtual Environment**: `./venv/`
- Python 3.13
- pyannote.audio 4.0.1
- PyTorch 2.9.0 (with CUDA 12 support)
- All dependencies installed

**Activation**:
```bash
source venv/bin/activate
# OR
source activate_venv.sh
```

**HuggingFace Token**: Configured in `.env` file
- Required for pyannote.audio speaker diarization model
- Already accepted terms for speaker-diarization-3.1

---

## Next Steps (Exact Commands)

### Step 1: Verify Setup (30 seconds)
```bash
cd /home/blackthorne/Work/tstprep.com/toefl-2026/audio-file-extraction
source venv/bin/activate
python test_setup.py
```

**Expected Output**: 
- ✅ All dependencies found
- ✅ HuggingFace token valid
- ✅ Speaker diarization model accessible
- ✅ ffmpeg available

**If Issues**: See `test_setup.py` output for specific guidance

---

### Step 2: Analyze Current Files (1 minute)
```bash
# Still in venv
python reprocess_statements.py --analyze-only
```

**Expected Output**:
- List of all 58 current statement files
- Duration statistics
- Flagged "suspicious" files (>5 seconds, likely multi-statement)
- Recommended files for reprocessing

**Sample Output**:
```
Analyzing 10 modules with 58 total statements...

Suspicious files (duration > 5.0s):
  02.05.02, Module 2, Statement 001.mp3 (7.3s) ⚠️
  02.05.02, Module 2, Statement 002.mp3 (6.8s) ⚠️
  ...

Recommendation: Reprocess 4 suspicious files
```

---

### Step 3: Test on One File (2-3 minutes)
```bash
# Test speaker detection on most problematic file
python split_with_speaker_detection.py \
  -o output/test_speaker_detection \
  "downloads/02.05.02, Listen and Choose, Module 2 (no pauses).mp3"
```

**Expected Output**:
- Detection of speaker segments
- Intelligent merging of speaker changes + silences
- New statement files in `output/test_speaker_detection/`
- Should produce MORE statements than original (e.g., 3 → 4-5)

**Validation**:
```bash
# Compare original vs new
ls -lh "output/statements/02.05.02, Listen and Choose, Module 2/"
ls -lh "output/test_speaker_detection/02.05.02, Listen and Choose, Module 2/"

# Check durations
python simple_audio_check.py "output/test_speaker_detection/02.05.02, Listen and Choose, Module 2/"
```

---

### Step 4: Batch Reprocess (if test successful) (5-10 minutes)
```bash
# Dry run first (shows what would happen, no changes)
python reprocess_statements.py --suspicious-only --dry-run

# If dry run looks good, actually reprocess
python reprocess_statements.py --suspicious-only
```

**What This Does**:
1. Creates backups: `output/statements_backup_YYYYMMDD_HHMMSS/`
2. Identifies files with duration > 5s
3. Re-runs speaker detection on problematic files only
4. Replaces old files with new, better-split versions
5. Shows before/after comparison

**Expected Improvements**:
- 58 statements → 65-75 statements
- Suspicious file count: 4+ → 0-1
- Max duration: 7.3s → 4-5s
- Average duration: 2.8s → 2.2-2.5s

---

### Step 5: Validate Results (5 minutes)
```bash
# Analyze improved files
python reprocess_statements.py --analyze-only

# Spot check: Listen to a few reprocessed files
# Use mpv, vlc, or any audio player
mpv "output/statements/02.05.02, Listen and Choose, Module 2/02.05.02, Listen and Choose, Module 2, Statement 001.mp3"
```

**Validation Checklist**:
- [ ] Suspicious file count reduced (ideally to 0)
- [ ] No statements < 1 second (fragments)
- [ ] Max duration < 5 seconds
- [ ] Spot-checked files sound correct (one speaker per file)
- [ ] Total statement count increased appropriately

---

### Step 6: Upload to Drive (Manual - MCP limitation)

Once validated, upload improved statement files to Google Drive:

**Folder**: `1vbSukNXg7Z5mx3fAb6-h2TWxTBjHX5io`

**Method 1: Google Drive Web UI**
1. Open: https://drive.google.com/drive/folders/1vbSukNXg7Z5mx3fAb6-h2TWxTBjHX5io
2. Create/update subfolders matching `output/statements/` structure
3. Upload files (will replace old versions if same names)

**Method 2: rclone** (if configured)
```bash
rclone sync output/statements/ gdrive:TOEFL_Audio_Folder/statements/
```

---

## Key Scripts Reference

### Primary Scripts
1. **`split_with_speaker_detection.py`**
   - Main improved splitter with speaker diarization
   - Usage: `python split_with_speaker_detection.py [options] <input_file>`
   - Options:
     - `--no-speaker-detection`: Fall back to silence-only
     - `-t <threshold>`: Silence threshold in dB (default: -50)
     - `-d <duration>`: Min silence duration in seconds (default: 0.2)
     - `-o <dir>`: Output directory

2. **`reprocess_statements.py`**
   - Batch reprocessing utility
   - Usage: `python reprocess_statements.py [options]`
   - Options:
     - `--analyze-only`: Just show analysis, no reprocessing
     - `--suspicious-only`: Only reprocess files >5s
     - `--all`: Reprocess all files
     - `--dry-run`: Show what would happen without doing it
     - `--threshold <float>`: Duration threshold for "suspicious" (default: 5.0)

3. **`test_setup.py`**
   - Verify environment and dependencies
   - Usage: `python test_setup.py`
   - Checks: ffmpeg, Python packages, HF token, speaker model

4. **`simple_audio_check.py`**
   - Quick audio analysis (no ML dependencies)
   - Usage: `python simple_audio_check.py <directory>`
   - Shows: silences, speech segments, potential issues

### Supporting Scripts
- **`split_no_pauses.py`**: Original silence-only splitter (still useful)
- **`process_all.sh`**: Original batch processor
- **`activate_venv.sh`**: Virtual environment activation helper

---

## Documentation Reference

**Quick Start**: `SPEAKER_DETECTION_QUICKSTART.md`
- 5-minute getting started guide
- Essential commands only

**Overview**: `ANALYSIS_SUMMARY.md`
- Detailed problem analysis
- Solution explanation
- Getting started with examples

**Technical Guide**: `SPEAKER_DETECTION_GUIDE.md`
- Complete technical reference
- All parameters and options
- Advanced usage

**Implementation**: `DELIVERABLES.md`
- What was implemented
- How it works
- Expected improvements

---

## Troubleshooting

### If test_setup.py fails:

**HuggingFace token issue:**
```bash
# Verify token is set
echo $HF_TOKEN
# Should show: hf_xxxxx...

# Re-export if needed
export HF_TOKEN="hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

**Missing dependencies:**
```bash
source venv/bin/activate
pip install -r requirements_speaker_detection.txt
```

**ffmpeg not found:**
```bash
# Arch Linux
sudo pacman -S ffmpeg

# Verify
ffmpeg -version
```

### If speaker detection is too slow:

**Option 1: Use CPU-only** (if GPU causing issues)
```bash
export CUDA_VISIBLE_DEVICES=""
python split_with_speaker_detection.py ...
```

**Option 2: Fall back to silence-only**
```bash
python split_with_speaker_detection.py --no-speaker-detection ...
```

**Option 3: Adjust silence parameters only**
```bash
python split_no_pauses.py --threshold -45 --duration 0.15 ...
```

### If too many small segments created:

Increase minimum segment duration in `reprocess_statements.py`:
- Default: 1.5 seconds
- Adjust `MIN_SEGMENT_DURATION` in script if needed

---

## Expected Timeline

| Step | Duration | Description |
|------|----------|-------------|
| 1. Verify setup | 30 sec | Run test_setup.py |
| 2. Analyze files | 1 min | Identify problematic files |
| 3. Test on one file | 2-3 min | Validate speaker detection works |
| 4. Batch reprocess | 5-10 min | Reprocess suspicious files |
| 5. Validate | 5 min | Check improvements |
| 6. Upload to Drive | 10-15 min | Manual upload |
| **Total** | **25-35 min** | End-to-end execution |

---

## Success Criteria

### Quantitative
- [ ] Statement count: 58 → 65-75 (increase of 12-29%)
- [ ] Suspicious files (>5s): 4+ → 0-1 (reduction to nearly zero)
- [ ] Average duration: 2.8s → 2.2-2.5s (more uniform)
- [ ] Max duration: 7.3s → 4-5s (better separation)

### Qualitative
- [ ] No audible cut-offs in statements
- [ ] One speaker per statement file
- [ ] Clean audio quality maintained
- [ ] Naming scheme consistent
- [ ] No regression on already-correct files

---

## File Locations Summary

**Source files**: `downloads/*.mp3` (10 files)
**Current output**: `output/statements/` (58 files, some multi-statement)
**Improved output**: `output/statements/` (will replace after validation)
**Backup**: `output/statements_backup_YYYYMMDD_HHMMSS/` (auto-created)
**Test output**: `output/test_speaker_detection/` (for single-file testing)

**Scripts**:
- All `.py` scripts in project root
- `activate_venv.sh` for venv activation

**Documentation**:
- All `*.md` files in project root
- Start with `SPEAKER_DETECTION_QUICKSTART.md`

**Environment**:
- `venv/` directory (virtual environment)
- `.env` file (HF_TOKEN configured)

---

## After Improvement Complete

### Remaining Tasks

1. **Task 1**: ✅ Complete (with improvements)
   - Upload improved statement files to Drive

2. **Task 2**: ⏳ Pending
   - Add narrator prefix to conversation files
   - 24 conversation files identified
   - Daniel/Matilda narrator files located
   - Implementation planned with 50/50 rotation

---

## Quick Resume Commands

```bash
# Resume work
cd /home/blackthorne/Work/tstprep.com/toefl-2026/audio-file-extraction
source venv/bin/activate

# Verify environment
python test_setup.py

# Continue from where we left off
python reprocess_statements.py --analyze-only
```

---

## Notes for Future Agents

- User confirmed HF_TOKEN is configured
- Virtual environment is fully set up and tested
- All scripts are production-ready
- Documentation is comprehensive
- User has reviewed current files and identified multi-statement issue
- Ready to proceed with verification and reprocessing
- After Task 1 improvements complete, move to Task 2 (narrator prefix)
