# Timecode-Based Audio Splitting - Analysis Report

**Date**: 2025-11-02
**Project**: TOEFL 2026 Audio File Extraction
**Task**: Timecode-based splitting analysis vs. Task 1 (silence detection)

---

## Executive Summary

**Finding**: CSV timecode files provide **explicit split points** but have **significant discrepancies** with Task 1 silence detection results. **Recommendation**: Use timecodes as **primary source of truth** and create new output directory to avoid conflicts.

**Key Statistics**:
- **Valid CSV files**: 9 out of 10 (90%)
- **Corrupted CSV**: 1 file (`02.05.01`) - binary data instead of CSV
- **Total statements in CSVs**: 42 statements (vs. 58 from Task 1 silence detection)
- **Files with perfect match**: 3 out of 9 (33%)
- **Files with discrepancies**: 6 out of 9 (67%)

---

## 1. Timecode File Analysis

### 1.1 CSV File Structure

**Format**: Standard CSV with 4 columns
```csv
"Speaker Name","Start Time","End Time","Text"
"Speaker 1","00:00:00:00","00:00:02:15","The deadline's coming up sooner than I expected."
```

**Columns**:
- `Speaker Name`: Speaker identifier (e.g., "Speaker 1", "Speaker 2")
- `Start Time`: Timecode in format `HH:MM:SS:FF` (Hours:Minutes:Seconds:Frames)
- `End Time`: Timecode in format `HH:MM:SS:FF`
- `Text`: Transcript of the statement

### 1.2 Timecode Format Details

**Format**: `HH:MM:SS:FF` (SMPTE timecode)
- **HH**: Hours (00)
- **MM**: Minutes (00)
- **SS**: Seconds (00-59)
- **FF**: Frames (00-29, assuming 30 fps)

**Example**: `00:00:02:15`
- 0 hours, 0 minutes, 2 seconds, 15 frames
- Total: 2 + (15/30) = **2.5 seconds**

**Conversion to ffmpeg format**: `HH:MM:SS.mmm`
```
00:00:02:15 → 00:00:02.500
00:00:04:09 → 00:00:04.300
```

Formula: `seconds = SS + (FF / 30.0)`

### 1.3 File Status Summary

| File | Status | Statements | Notes |
|------|--------|-----------|-------|
| `02.01.01, Module 1.csv` | ✅ Valid | 7 | -2 vs Task 1 |
| `02.01.02, Module 2.csv` | ✅ Valid | 3 | -1 vs Task 1 |
| `02.02.01, Module 1.csv` | ✅ Valid | 8 | +4 vs Task 1 |
| `02.02.02, Module 2.csv` | ✅ Valid | 2 | +1 vs Task 1 |
| `02.03.01, Module 1.csv` | ✅ Valid | 6 | ✓ Perfect match |
| `02.03.02, Module 2.csv` | ✅ Valid | 3 | ✓ Perfect match |
| `02.04.01, Module 1.csv` | ✅ Valid | 3 | +6 vs Task 1 (!) |
| `02.04.02, Module 2.csv` | ✅ Valid | 5 | ✓ Perfect match |
| `02.05.01, Module 1.csv` | ❌ **CORRUPTED** | N/A | Binary PSX image data |
| `02.05.02, Module 2.csv` | ✅ Valid | 5 | -2 vs Task 1 |

**Total Valid**: 9 files, 42 statements
**Total Corrupted**: 1 file (needs manual reconstruction or use Task 1 results)

---

## 2. Comparison with Task 1 (Silence Detection)

### 2.1 Detailed Discrepancy Analysis

| File | Task 1 (Silence) | CSV (Timecode) | Difference | Analysis |
|------|-----------------|----------------|------------|----------|
| 02.01.01, Module 1 | 5 | 7 | **-2** | CSV has MORE statements (silence detection missed 2) |
| 02.01.02, Module 2 | 2 | 3 | **-1** | CSV has MORE statements |
| 02.02.01, Module 1 | 12 | 8 | **+4** | Task 1 has MORE (silence detection over-split) |
| 02.02.02, Module 2 | 3 | 2 | **+1** | Task 1 has MORE |
| 02.03.01, Module 1 | 6 | 6 | ✓ | **Perfect match** |
| 02.03.02, Module 2 | 3 | 3 | ✓ | **Perfect match** |
| 02.04.01, Module 1 | 9 | 3 | **+6** | **Significant over-split** by silence detection |
| 02.04.02, Module 2 | 5 | 5 | ✓ | **Perfect match** |
| 02.05.01, Module 1 | 10 | N/A | N/A | CSV corrupted |
| 02.05.02, Module 2 | 3 | 5 | **-2** | CSV has MORE statements |

### 2.2 Key Findings

**Silence Detection Issues**:
1. **Over-splitting** (Task 1 > CSV): 3 files
   - `02.02.01`: 12 vs 8 (+4 false positives)
   - `02.04.01`: 9 vs 3 (**+6 false positives - most significant**)
   - `02.02.02`: 3 vs 2 (+1 false positive)

2. **Under-splitting** (Task 1 < CSV): 3 files
   - `02.01.01`: 5 vs 7 (-2 missed splits)
   - `02.01.02`: 2 vs 3 (-1 missed split)
   - `02.05.02`: 3 vs 5 (-2 missed splits)

3. **Perfect matches**: 3 files (33%)
   - `02.03.01`, `02.03.02`, `02.04.02`

**Total Statements**:
- Task 1 (silence detection): **58 statements**
- CSV (timecodes): **42 statements** (9 files only)
- Net difference: **+16 statements** from Task 1

**Accuracy Assessment**:
- Silence detection is **unreliable** for consistent splitting
- Timecodes provide **ground truth** with explicit boundaries
- **Recommendation**: Use timecodes as primary method

---

## 3. Strategic Recommendations

### 3.1 Primary Recommendation: **Replace Task 1 with Timecode-Based Splitting**

**Rationale**:
1. **Explicit boundaries**: Timecodes define exact split points (no guesswork)
2. **Consistency**: Same input = same output (deterministic)
3. **Quality**: No false positives/negatives from silence detection
4. **Transcript alignment**: CSV provides text for validation

**Implementation Approach**:
- Create **NEW output directory**: `output/statements_timecode/`
- Preserve existing Task 1 results in `output/statements/` (backup)
- Process 9 valid CSV files → create 42 statement files
- Handle `02.05.01` separately (corrupted CSV):
  - Option A: Use existing Task 1 results (10 statements)
  - Option B: Manually reconstruct CSV from audio analysis
  - Option C: Skip this file for now

### 3.2 Output Directory Structure

**Proposed Structure**:
```
output/
├── statements/              # Task 1 results (PRESERVED)
│   ├── 02.01.01, Listen and Choose, Module 1/
│   │   ├── Statement 001.mp3  (5 files)
│   │   └── ...
│   └── ... (10 folders, 58 total files)
│
└── statements_timecode/     # NEW: Timecode-based results
    ├── 02.01.01, Listen and Choose, Module 1/
    │   ├── Statement 001.mp3  (7 files from CSV)
    │   └── ...
    └── ... (9 folders, 42 total files)
```

### 3.3 File Naming Convention

**Pattern**: `02.TT.PP, Listen and Choose, Module X, Statement NNN.mp3`

**Example**:
- Input: `downloads/02.01.01, Listen and Choose, Module 1 (no pauses).mp3`
- CSV: `downloads/02.01.01, Listen and Choose, Module 1 (no pauses).csv` (7 entries)
- Output:
  - `output/statements_timecode/02.01.01, Listen and Choose, Module 1/`
    - `02.01.01, Listen and Choose, Module 1, Statement 001.mp3`
    - `02.01.01, Listen and Choose, Module 1, Statement 002.mp3`
    - ... (7 files total)

**Consistent with Task 1 naming** → Easy comparison and validation

---

## 4. Technical Implementation Plan

### 4.1 Script Design

**Script Name**: `scripts/task1_split_by_timecode.py`

**Core Functions**:
1. **CSV Parsing**:
   - Read CSV with `csv.DictReader`
   - Validate columns: `Speaker Name, Start Time, End Time, Text`
   - Convert timecode `HH:MM:SS:FF` → `HH:MM:SS.mmm` for ffmpeg

2. **Timecode Conversion**:
   ```python
   def timecode_to_ffmpeg(tc: str, fps: int = 30) -> str:
       """Convert HH:MM:SS:FF to HH:MM:SS.mmm"""
       h, m, s, f = tc.split(':')
       total_seconds = int(h)*3600 + int(m)*60 + int(s) + int(f)/fps
       hours = int(total_seconds // 3600)
       minutes = int((total_seconds % 3600) // 60)
       seconds = total_seconds % 60
       return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
   ```

3. **Audio Splitting**:
   ```bash
   ffmpeg -i input.mp3 \
          -ss START_TIME \
          -to END_TIME \
          -c copy \
          output.mp3
   ```
   - Use `-c copy` (no re-encoding, preserves quality)
   - `-ss` and `-to` accept `HH:MM:SS.mmm` format

4. **Validation**:
   - Check output file size > 0
   - Verify duration matches CSV (±0.1 second tolerance)
   - Log any discrepancies

### 4.2 Error Handling

**Corrupted CSV (`02.05.01`)**:
```python
try:
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
except UnicodeDecodeError:
    logger.warning(f"Corrupted CSV: {csv_file.name}")
    logger.info(f"Using Task 1 results as fallback")
    # Skip or use existing Task 1 output
```

**Missing/Invalid Timecodes**:
- Validate timecode format with regex: `^\d{2}:\d{2}:\d{2}:\d{2}$`
- Skip malformed entries with warning

**ffmpeg Errors**:
- Capture stderr output
- Retry with adjusted parameters if needed
- Log all errors for debugging

### 4.3 Execution Strategy

**Phase 1: Dry Run**
```bash
python scripts/task1_split_by_timecode.py --dry-run
```
- Parse all CSV files
- Validate timecodes
- Report statistics (no file creation)

**Phase 2: Limited Test**
```bash
python scripts/task1_split_by_timecode.py --limit 3
```
- Process first 3 files (02.01.01, 02.01.02, 02.02.01)
- Validate output quality manually
- Compare with Task 1 results

**Phase 3: Full Processing**
```bash
python scripts/task1_split_by_timecode.py
```
- Process all 9 valid CSV files
- Generate processing report
- Create upload manifest for Google Drive

---

## 5. Quality Validation Checklist

### 5.1 Pre-Processing Validation
- [ ] All 9 valid CSV files accessible
- [ ] CSV format validated (4 columns, proper structure)
- [ ] Timecodes parsed correctly (no format errors)
- [ ] Source MP3 files exist in `downloads/`
- [ ] Output directory created: `output/statements_timecode/`

### 5.2 Post-Processing Validation
- [ ] All 42 output files created
- [ ] File sizes > 0 bytes
- [ ] Durations match CSV timecodes (±0.1s tolerance)
- [ ] No audio artifacts or corruption
- [ ] File naming consistent with convention
- [ ] Spot-check 5 random files (listen to quality)

### 5.3 Comparison with Task 1
- [ ] Compare durations for matching files
- [ ] Verify discrepancies match analysis (e.g., 02.04.01: 3 vs 9)
- [ ] Document differences in report

---

## 6. Handling Corrupted File: `02.05.01`

**Problem**: CSV file is binary data (Sony PlayStation PSX image), not valid CSV.

**Options**:

### Option A: Use Task 1 Results (RECOMMENDED)
- **Pros**: Already processed, 10 statements created, working files
- **Cons**: May have false positives from silence detection
- **Action**: Copy Task 1 results to timecode directory
  ```bash
  cp -r output/statements/'02.05.01, Listen and Choose, Module 1'/ \
        output/statements_timecode/
  ```

### Option B: Manual CSV Reconstruction
- **Pros**: Most accurate, aligned with timecodes
- **Cons**: Time-consuming, requires manual audio analysis
- **Action**:
  1. Listen to source MP3
  2. Identify statement boundaries manually
  3. Create CSV with proper timecodes
  4. Process with script

### Option C: Request Fixed CSV
- **Pros**: Authoritative source
- **Cons**: Delays processing, may not be available
- **Action**: Contact file source, request corrected CSV

**Decision**: Use **Option A** (Task 1 results) for continuity, document in report.

---

## 7. Next Steps

### Immediate Actions
1. ✅ **Analysis Complete** - This report
2. ⏳ **Script Development** - Create `task1_split_by_timecode.py`
3. ⏳ **Dry Run** - Validate parsing and logic
4. ⏳ **Limited Test** - Process 3 files, validate quality
5. ⏳ **Full Processing** - Process all 9 valid CSV files
6. ⏳ **Quality Check** - Spot-check random samples
7. ⏳ **Upload to Drive** - Use existing upload workflow

### Testing Strategy
```bash
# 1. Dry run (no file creation)
python scripts/task1_split_by_timecode.py --dry-run

# 2. Test single file
python scripts/task1_split_by_timecode.py \
    --input "downloads/02.03.01, Listen and Choose, Module 1 (no pauses).mp3" \
    --csv "downloads/02.03.01, Listen and Choose, Module 1 (no pauses).csv"

# 3. Test batch (3 files)
python scripts/task1_split_by_timecode.py --limit 3

# 4. Full processing (9 files)
python scripts/task1_split_by_timecode.py
```

### Documentation Updates
- [ ] Update `CLAUDE.md` with timecode approach
- [ ] Add timecode section to `audio_workflows` memory
- [ ] Create `TIMECODE_RESULTS.md` after processing
- [ ] Update project README

---

## 8. Conclusion

**Summary**:
- **CSV timecodes available**: 9 out of 10 files (42 statements)
- **Corrupted CSV**: `02.05.01` (use Task 1 results as fallback)
- **Recommendation**: Use timecodes as **primary method** (more accurate than silence detection)
- **Strategy**: Create separate output directory, preserve Task 1 results
- **Next**: Implement `task1_split_by_timecode.py` script

**Benefits of Timecode Approach**:
1. **Accuracy**: Explicit boundaries, no false positives/negatives
2. **Consistency**: Deterministic, repeatable results
3. **Validation**: Transcript text for quality checks
4. **Efficiency**: Single pass, no iterative tuning of silence parameters

**Risk Mitigation**:
- Preserve Task 1 results (backup)
- Dry run validation before full processing
- Limited test on 3 files before batch
- Comprehensive error handling for corrupted CSV

---

**Report Generated**: 2025-11-02
**Analyst**: Claude (Tactical Coordinator)
**Status**: ✅ Analysis Complete → Ready for Implementation
