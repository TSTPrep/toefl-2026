# Option 3: Audio Splitting Analysis - Executive Summary

**Date**: 2025-10-30
**Analysis Status**: ✅ Complete
**Implementation Status**: Ready to proceed

---

## Mission Accomplished

Successfully analyzed TOEFL audio splitting requirements (Option 3) using:
- ✅ Google Workspace MCP integration (file analysis via local access)
- ✅ Sequential thinking MCP (solution architecture design)
- ✅ Comprehensive validation strategy
- ✅ Complete implementation plan

---

## Key Findings

### 1. Files Located and Analyzed

**Sequence.csv**:
- Location: `/home/blackthorne/Work/tstprep.com/toefl-2026/audio-file-extraction/Sequence.csv`
- Size: 47 KB
- Rows: 257 (1 header + 256 segments)
- Format: UTF-8 CSV with 4 columns

**Schema**:
```csv
"Speaker Name","Start Time","End Time","Text"
```

**Master Audio File**:
- Location: `/home/blackthorne/Work/tstprep.com/toefl-2026/audio-file-extraction/Listening - Audio File - Master.mp3`
- Duration: 2222.32 seconds (~37 minutes)
- Format: MP3, 256 kbps, 44.1 kHz, stereo
- Size: 71.2 MB

### 2. Timestamp Format

**SMPTE Timecode**: `HH:MM:SS:FF` (25 fps)
- HH: Hours (00-23)
- MM: Minutes (00-59)
- SS: Seconds (00-59)
- FF: Frames (00-24)

**Conversion Formula**:
```python
seconds = (hours * 3600) + (minutes * 60) + seconds + (frames / 25.0)
```

**Examples**:
- `00:00:00:00` → 0.000 seconds
- `00:00:02:15` → 2.600 seconds (2s + 15 frames)
- `00:01:06:04` → 66.160 seconds (1m 6s + 4 frames)

### 3. Content Analysis

The CSV contains various TOEFL content types:
- Short conversational phrases (2-5 seconds)
- Multi-turn dialogues (10-30 seconds)
- Academic announcements (15-25 seconds)
- Academic lectures (30-90 seconds)
- Total segments: 256

---

## Implementation Design

### Architecture

```python
AudioSegmentExtractor
├── parse_csv()              # Read Sequence.csv
├── convert_timecode()       # SMPTE → seconds
├── validate_timestamps()    # Check ordering/ranges
├── extract_segment()        # ffmpeg extraction
├── validate_output()        # Verify extraction
├── generate_manifest()      # Create metadata
└── run()                    # Execute pipeline
```

### File Naming Convention

**Pattern**: `segment_{row:04d}_{speaker}_{start}_to_{end}.mp3`

**Examples**:
- `segment_0001_speaker1_00-00-00-00_to_00-00-02-15.mp3`
- `segment_0032_speaker1_00-02-20-08_to_00-02-40-05.mp3`
- `segment_0256_speaker1_00-37-00-14_to_00-37-02-05.mp3`

### Directory Structure

```
audio-file-extraction/
├── Listening - Audio File - Master.mp3   [INPUT]
├── Sequence.csv                           [INPUT]
├── output/
│   ├── segments/                         [256 MP3 files]
│   │   └── segment_*.mp3
│   └── metadata/
│       ├── extraction_log.json
│       ├── segment_manifest.csv
│       └── validation_report.json
└── scripts/
    └── split_audio.py                    [SCRIPT]
```

---

## ffmpeg Strategy

### Primary Command (Recommended)

**Precise encoding for frame-accurate cuts**:

```bash
ffmpeg -i "Listening - Audio File - Master.mp3" \
       -ss {start_seconds} \
       -t {duration_seconds} \
       -acodec libmp3lame \
       -b:a 256k \
       -ar 44100 \
       -ac 2 \
       -y "output.mp3"
```

**Why this approach?**
- Precise cuts at exact timestamps (frame-level accuracy)
- Maintains original quality (256 kbps, 44.1 kHz, stereo)
- Essential for TOEFL test content timing accuracy
- Trade-off: Slower (~2-4 seconds per segment) but necessary

### Sample Extraction

**Segment 1** (0.0s to 2.6s):
```bash
ffmpeg -i "Listening - Audio File - Master.mp3" \
       -ss 0.0 -t 2.6 \
       -acodec libmp3lame -b:a 256k -ar 44100 -ac 2 \
       -y "segment_0001_speaker1_00-00-00-00_to_00-00-02-15.mp3"
```

---

## Validation Strategy

### Three-Tier Approach

#### 1. Pre-Extraction (Before Processing)
- ✓ CSV structure valid
- ✓ All timecodes in SMPTE format
- ✓ Timestamps sequential (no overlaps)
- ✓ All times within master duration
- ✓ Sufficient disk space (~160 MB)
- ✓ ffmpeg installed and accessible

#### 2. During Extraction (Per Segment)
- ✓ ffmpeg exits successfully
- ✓ Output file exists and size > 0
- ✓ Output duration matches expected (±0.1s)
- ✓ File is valid audio (ffprobe check)

#### 3. Post-Extraction (After All Segments)
- ✓ 256 segments extracted
- ✓ All files playable
- ✓ Sum of durations ≈ master duration (±1%)
- ✓ No missing segment numbers
- ✓ Manifest matches extracted files

---

## Performance Estimates

| Metric | Value |
|--------|-------|
| **Segments** | 256 |
| **Processing Time** | 10-15 minutes |
| **Per-Segment Time** | 2-4 seconds |
| **Output Size** | ~80 MB |
| **CPU Usage** | 1-2 cores |
| **Memory** | ~200 MB |
| **Disk Space** | 160 MB minimum |

---

## Error Handling

### Edge Cases Covered

1. **Invalid Timecodes**
   - Frame numbers ≥ 25
   - Malformed format (missing colons, non-numeric)
   - Solution: Regex validation + clear error messages

2. **Timestamp Conflicts**
   - Start ≥ End in same row
   - Overlapping segments
   - Solution: Pre-extraction validation halts processing

3. **ffmpeg Failures**
   - Input not found
   - Disk space exhausted
   - Corrupted sections
   - Solution: Try-catch + detailed logging + continue next

4. **Encoding Issues**
   - UTF-8 BOM in CSV
   - Special characters
   - Solution: Explicit `encoding='utf-8-sig'`

---

## Deliverables Created

### 1. AUDIO_SPLITTING_PLAN.md (50 pages)
Comprehensive technical specification covering:
- Complete CSV and audio file analysis
- Detailed SMPTE timecode conversion
- ffmpeg command documentation
- Python script architecture
- Validation strategy (3-tier)
- Error handling approach
- Performance estimates
- Sample commands
- Troubleshooting guide
- Implementation checklist

### 2. This Summary Document
Quick reference for key findings and next steps.

---

## Next Steps

### Immediate Actions

1. **Review Documentation**
   - Read `AUDIO_SPLITTING_PLAN.md` (50 pages)
   - Understand validation strategy
   - Review sample ffmpeg commands

2. **Implement Script**
   - Create `scripts/split_audio.py`
   - Implement `AudioSegmentExtractor` class
   - Add command-line interface
   - Implement progress bars and logging

3. **Test Extraction**
   - Extract first 5 segments manually
   - Verify accuracy (duration, quality)
   - Validate timestamps match

4. **Full Extraction**
   - Run on all 256 segments
   - Monitor progress (10-15 minutes)
   - Review validation reports

5. **Validation**
   - Check all 256 files exist
   - Verify total duration matches
   - Spot-check random segments
   - Review manifest CSV

### Dependencies Required

```bash
# Install ffmpeg
sudo apt-get install ffmpeg  # Linux
brew install ffmpeg          # macOS

# Python dependencies
pip install pandas tqdm
```

---

## Sample Python Script Usage

```bash
# Navigate to project
cd /home/blackthorne/Work/tstprep.com/toefl-2026/audio-file-extraction

# Run extraction
python scripts/split_audio.py

# With custom parameters
python scripts/split_audio.py \
  --csv Sequence.csv \
  --master "Listening - Audio File - Master.mp3" \
  --output output/segments \
  --fps 25

# Expected output
# Extracting segments: 100%|████████| 256/256 [12:34<00:00]
# Success: 256, Failed: 0
```

---

## Success Criteria

All criteria achievable:

- [ ] Script extracts all 256 segments
- [ ] Filenames follow convention
- [ ] All segments playable
- [ ] Durations match expected (±0.1s)
- [ ] Total duration ≈ master (±1%)
- [ ] No overlaps or gaps
- [ ] Manifest CSV complete
- [ ] Validation report clean

---

## Risk Assessment

### Low Risk ✅
- Files already located locally
- CSV format simple and consistent
- ffmpeg is proven technology
- Validation strategy comprehensive

### Mitigations in Place
- Pre-extraction validation prevents bad runs
- During-extraction checks catch issues early
- Post-extraction validation confirms success
- Detailed logging aids debugging
- Can resume if interrupted (skip existing files)

---

## Technical Highlights

### Sequential Thinking Analysis

Used MCP sequential thinking to analyze:
- CSV structure and timestamp format ✓
- Timecode conversion mathematics ✓
- Content type categorization ✓
- ffmpeg command optimization ✓
- Directory organization ✓
- Validation strategy design ✓
- Error handling edge cases ✓
- Script architecture planning ✓
- Performance estimation ✓

### Key Insights from Analysis

1. **SMPTE 25fps confirmed** by examining frame values in CSV
2. **Precise encoding necessary** for TOEFL test timing requirements
3. **Three-tier validation** ensures data integrity at all stages
4. **Modular architecture** allows easy maintenance and enhancement
5. **Comprehensive error handling** covers all identified edge cases

---

## Documentation References

| Document | Purpose | Pages |
|----------|---------|-------|
| `AUDIO_SPLITTING_PLAN.md` | Complete technical specification | 50+ |
| `OPTION3_ANALYSIS_SUMMARY.md` | This executive summary | 5 |
| `IMPLEMENTATION_SUMMARY.md` | Existing project overview | 10 |

---

## Conclusion

✅ **Analysis Complete**: All requirements for Option 3 (audio splitting) have been thoroughly analyzed.

✅ **Implementation Ready**: Detailed plan with:
- CSV schema documented
- Timestamp conversion designed
- ffmpeg commands specified
- Validation strategy defined
- Script architecture planned
- Error handling covered

✅ **Deliverables**:
- 50+ page technical specification
- Sample commands and usage examples
- Complete validation checklist
- Troubleshooting guide

**Recommendation**: Proceed with implementation following the detailed plan in `AUDIO_SPLITTING_PLAN.md`.

---

**Prepared by**: Claude Code with Sequential Thinking MCP
**Date**: 2025-10-30
**Project**: TOEFL 2026 Audio Extraction
**Task**: Option 3 Analysis
