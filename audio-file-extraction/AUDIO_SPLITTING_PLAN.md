# TOEFL Audio File Extraction - Implementation Plan

## Executive Summary

This document provides a comprehensive plan for splitting the TOEFL Listening master audio file into individual segments based on the Sequence.csv timing data.

**Project**: TOEFL 2026 Audio Segment Extraction
**Date**: 2025-10-30
**Status**: Design Complete - Ready for Implementation

---

## 1. File Analysis

### 1.1 Input Files Located

**Location**: `/home/blackthorne/Work/tstprep.com/toefl-2026/audio-file-extraction/`

#### Master Audio File
- **Filename**: `Listening - Audio File - Master.mp3`
- **Size**: 71.2 MB (71,191,735 bytes)
- **Duration**: 2222.319063 seconds (~37 minutes, 2 seconds)
- **Format**: MP3
- **Sample Rate**: 44100 Hz
- **Channels**: Stereo (2)
- **Bit Rate**: 256 kbps
- **Codec**: MP3 (MPEG audio layer 3)

#### Sequence CSV File
- **Filename**: `Sequence.csv`
- **Size**: 47 KB
- **Rows**: 257 (256 segments + 1 header)
- **Encoding**: UTF-8

### 1.2 CSV Schema Documentation

```csv
Column 1: "Speaker Name" - Identifies the speaker (e.g., "Speaker 1", "Speaker 2")
Column 2: "Start Time"   - SMPTE timecode format (HH:MM:SS:FF)
Column 3: "End Time"     - SMPTE timecode format (HH:MM:SS:FF)
Column 4: "Text"         - Transcript or description of the segment
```

**Example Rows**:
```csv
"Speaker Name","Start Time","End Time","Text"
"Speaker 1","00:00:00:00","00:00:02:15","The deadline's coming up sooner than I expected."
"Speaker 2","00:00:02:17","00:00:04:05","Looks like the meeting's running late."
```

### 1.3 Timestamp Format Analysis

**Format**: SMPTE Timecode - `HH:MM:SS:FF`
- **HH**: Hours (00-23)
- **MM**: Minutes (00-59)
- **SS**: Seconds (00-59)
- **FF**: Frames (00-24, assuming 25 fps)

**Frame Rate**: 25 fps (confirmed by analyzing frame values in CSV)

**Conversion Formula**:
```python
total_seconds = (hours * 3600) + (minutes * 60) + seconds + (frames / 25.0)
```

**Example Conversions**:
| Timecode      | Calculation                    | Seconds   |
|---------------|--------------------------------|-----------|
| 00:00:00:00   | 0 + 0 + 0 + (0/25)            | 0.000     |
| 00:00:02:15   | 0 + 0 + 2 + (15/25)           | 2.600     |
| 00:00:04:09   | 0 + 0 + 4 + (9/25)            | 4.360     |
| 00:01:06:04   | 0 + 60 + 6 + (4/25)           | 66.160    |

---

## 2. Architecture Design

### 2.1 Directory Structure

```
audio-file-extraction/
├── Listening - Audio File - Master.mp3    # Input master file
├── Sequence.csv                            # Input timing data
├── output/
│   ├── segments/                          # Extracted audio segments
│   │   ├── segment_0001_speaker1_00-00-00-00_to_00-00-02-15.mp3
│   │   ├── segment_0002_speaker2_00-00-02-17_to_00-00-04-05.mp3
│   │   ├── segment_0003_speaker3_00-00-04-09_to_00-00-06-18.mp3
│   │   └── ... (256 total segments)
│   └── metadata/                          # Validation and logging
│       ├── extraction_log.json            # Detailed extraction log
│       ├── segment_manifest.csv           # Complete segment metadata
│       └── validation_report.json         # Validation results
├── scripts/
│   └── split_audio.py                     # Main extraction script
└── AUDIO_SPLITTING_PLAN.md                # This document
```

### 2.2 File Naming Convention

**Pattern**: `segment_{row:04d}_{speaker}_{start_tc}_to_{end_tc}.mp3`

**Components**:
- `segment`: Prefix for easy identification
- `{row:04d}`: Zero-padded row number (0001-0256)
- `{speaker}`: Sanitized speaker name (lowercase, no spaces)
- `{start_tc}`: Start timecode with dashes (HH-MM-SS-FF)
- `{end_tc}`: End timecode with dashes (HH-MM-SS-FF)
- `.mp3`: File extension

**Examples**:
```
segment_0001_speaker1_00-00-00-00_to_00-00-02-15.mp3
segment_0002_speaker2_00-00-02-17_to_00-00-04-05.mp3
segment_0032_speaker1_00-02-20-08_to_00-02-40-05.mp3
```

**Rationale**:
- Row number ensures unique sorting and traceability
- Speaker name allows filtering by speaker
- Timecodes provide temporal context
- Human-readable and filesystem-safe

---

## 3. Technical Implementation

### 3.1 Python Script Architecture

```python
# Class Structure

class AudioSegmentExtractor:
    """Main class for extracting audio segments from master file."""

    def __init__(self, csv_path: str, master_audio_path: str,
                 output_dir: str, fps: int = 25):
        """Initialize with file paths and frame rate."""

    def parse_csv(self) -> List[SegmentInfo]:
        """Parse CSV and create segment metadata."""

    def validate_timestamps(self, segments: List[SegmentInfo]) -> ValidationResult:
        """Validate timestamp ordering and ranges."""

    def convert_timecode(self, timecode_str: str) -> float:
        """Convert SMPTE timecode to seconds."""

    def extract_segment(self, segment: SegmentInfo) -> bool:
        """Extract a single audio segment using ffmpeg."""

    def validate_output(self, segment: SegmentInfo, output_path: str) -> bool:
        """Validate extracted segment."""

    def generate_manifest(self, segments: List[SegmentInfo]) -> pd.DataFrame:
        """Generate segment manifest CSV."""

    def run(self) -> ExtractionReport:
        """Execute the full extraction pipeline."""


@dataclass
class SegmentInfo:
    """Data structure for segment metadata."""
    row_number: int
    speaker_name: str
    start_timecode: str
    end_timecode: str
    start_seconds: float
    end_seconds: float
    duration: float
    text: str
    output_filename: str
    output_path: str
```

### 3.2 Dependencies

```python
# requirements.txt additions
pandas>=2.0.0        # CSV parsing and data manipulation
tqdm>=4.65.0         # Progress bars
```

**Standard Library**:
- `subprocess` - ffmpeg execution
- `pathlib` - File path operations
- `dataclasses` - Data structures
- `logging` - Logging framework
- `json` - JSON serialization
- `re` - Regular expressions for validation

### 3.3 Core Algorithms

#### Timecode Conversion

```python
def convert_timecode(self, timecode_str: str) -> float:
    """
    Convert SMPTE timecode to seconds.

    Args:
        timecode_str: Format "HH:MM:SS:FF"

    Returns:
        Total seconds as float

    Example:
        "00:00:02:15" -> 2.6 seconds
    """
    # Validate format
    pattern = r'^(\d{2}):(\d{2}):(\d{2}):(\d{2})$'
    match = re.match(pattern, timecode_str)

    if not match:
        raise ValueError(f"Invalid timecode format: {timecode_str}")

    hours, minutes, seconds, frames = map(int, match.groups())

    # Validate frame number
    if frames >= self.fps:
        raise ValueError(f"Frame {frames} exceeds fps {self.fps}")

    # Convert to seconds
    total_seconds = (hours * 3600) + (minutes * 60) + seconds + (frames / self.fps)

    return total_seconds
```

#### Timestamp Validation

```python
def validate_timestamps(self, segments: List[SegmentInfo]) -> ValidationResult:
    """
    Validate all timestamps for consistency.

    Checks:
    1. Start < End for each segment
    2. Sequential ordering (end[n] <= start[n+1])
    3. All times within master file duration
    4. No negative durations
    """
    errors = []
    warnings = []

    master_duration = 2222.319063  # From audio metadata

    for i, seg in enumerate(segments):
        # Check 1: Start < End
        if seg.start_seconds >= seg.end_seconds:
            errors.append(f"Row {seg.row_number}: Start >= End")

        # Check 2: Duration is positive
        if seg.duration <= 0:
            errors.append(f"Row {seg.row_number}: Non-positive duration")

        # Check 3: Within master duration
        if seg.end_seconds > master_duration:
            errors.append(f"Row {seg.row_number}: Exceeds master duration")

        # Check 4: Sequential ordering
        if i > 0:
            prev_seg = segments[i-1]
            gap = seg.start_seconds - prev_seg.end_seconds

            if gap < 0:
                errors.append(f"Row {seg.row_number}: Overlaps with previous segment")
            elif gap > 0.5:  # Warning for large gaps
                warnings.append(f"Row {seg.row_number}: Gap of {gap:.2f}s from previous")

    return ValidationResult(
        is_valid=(len(errors) == 0),
        errors=errors,
        warnings=warnings
    )
```

---

## 4. ffmpeg Commands

### 4.1 Primary Extraction Command

**Precise Encoding Method** (Recommended):

```bash
ffmpeg -i "Listening - Audio File - Master.mp3" \
       -ss {start_seconds} \
       -t {duration_seconds} \
       -acodec libmp3lame \
       -b:a 256k \
       -ar 44100 \
       -ac 2 \
       -y \
       "output/segments/segment_0001.mp3"
```

**Parameters Explained**:
- `-i`: Input file path
- `-ss {start_seconds}`: Start time in seconds (e.g., 2.6)
- `-t {duration_seconds}`: Duration to extract (e.g., 1.4)
- `-acodec libmp3lame`: Use LAME MP3 encoder for precise cuts
- `-b:a 256k`: Match original bitrate (256 kbps)
- `-ar 44100`: Match original sample rate (44.1 kHz)
- `-ac 2`: Match stereo channels
- `-y`: Overwrite existing files without prompting

**Example**:
```bash
# Extract segment from 2.6s to 4.2s (duration 1.6s)
ffmpeg -i "Listening - Audio File - Master.mp3" \
       -ss 2.6 -t 1.6 \
       -acodec libmp3lame -b:a 256k -ar 44100 -ac 2 \
       -y "segment_0002.mp3"
```

### 4.2 Fast Extraction Method (Alternative)

**Stream Copy Method** (Faster but less precise):

```bash
ffmpeg -ss {start_seconds} \
       -i "Listening - Audio File - Master.mp3" \
       -t {duration_seconds} \
       -c copy \
       -y \
       "output.mp3"
```

**Trade-offs**:
- **Pros**: 10-20x faster (no re-encoding)
- **Cons**: May not cut at exact timestamps (seeks to nearest keyframe)
- **Use Case**: If frame-level precision is not critical

**Recommendation**: Use precise encoding method for TOEFL test content where exact timing is essential.

### 4.3 Validation Command

**Check Output File Metadata**:

```bash
ffprobe -v quiet \
        -print_format json \
        -show_format \
        -show_streams \
        "output.mp3"
```

**Extract Duration**:
```bash
ffprobe -v error \
        -show_entries format=duration \
        -of default=noprint_wrappers=1:nokey=1 \
        "output.mp3"
```

---

## 5. Validation Strategy

### 5.1 Three-Tier Validation

#### Tier 1: Pre-Extraction Validation

**Purpose**: Catch errors before processing begins

**Checks**:
1. ✓ CSV file exists and is readable
2. ✓ Master audio file exists and is readable
3. ✓ CSV has required columns
4. ✓ All timecodes are valid SMPTE format
5. ✓ All timestamps are sequential
6. ✓ No overlapping segments
7. ✓ All timestamps within master file duration
8. ✓ Output directory is writable
9. ✓ Sufficient disk space (estimated 80 MB needed)

**Implementation**:
```python
def pre_extraction_validation(self) -> bool:
    """Run all pre-extraction checks."""
    logger.info("Running pre-extraction validation...")

    checks = [
        self.check_input_files(),
        self.check_csv_structure(),
        self.check_timestamps(),
        self.check_output_directory(),
        self.check_disk_space()
    ]

    return all(checks)
```

#### Tier 2: During-Extraction Validation

**Purpose**: Validate each segment as it's extracted

**Checks** (per segment):
1. ✓ ffmpeg exits successfully (return code 0)
2. ✓ Output file exists
3. ✓ Output file size > 0 bytes
4. ✓ Output file is valid audio (ffprobe succeeds)
5. ✓ Output duration matches expected duration (±0.1s tolerance)

**Implementation**:
```python
def extract_and_validate_segment(self, segment: SegmentInfo) -> bool:
    """Extract segment and validate immediately."""

    # Extract
    success = self.extract_segment(segment)
    if not success:
        logger.error(f"Extraction failed for {segment.row_number}")
        return False

    # Validate
    if not self.validate_output(segment):
        logger.error(f"Validation failed for {segment.row_number}")
        return False

    return True
```

#### Tier 3: Post-Extraction Validation

**Purpose**: Verify overall extraction quality

**Checks**:
1. ✓ Total segments extracted = CSV rows (256)
2. ✓ All output files are playable
3. ✓ Sum of segment durations ≈ master duration (±1% tolerance)
4. ✓ No missing segment numbers
5. ✓ No duplicate output files
6. ✓ Manifest CSV matches extracted files

**Implementation**:
```python
def post_extraction_validation(self) -> ValidationReport:
    """Comprehensive post-extraction validation."""

    report = {
        "total_expected": len(self.segments),
        "total_extracted": len(list(self.output_dir.glob("*.mp3"))),
        "total_duration": sum(seg.duration for seg in self.segments),
        "master_duration": 2222.319063,
        "missing_segments": [],
        "failed_segments": [],
        "validation_passed": True
    }

    # Check each segment exists and is valid
    for seg in self.segments:
        if not seg.output_path.exists():
            report["missing_segments"].append(seg.row_number)
            report["validation_passed"] = False

    return report
```

### 5.2 Error Handling

**Error Categories and Responses**:

| Error Type | Example | Handling Strategy |
|------------|---------|-------------------|
| Invalid Timecode | "00:00:02:99" (invalid frame) | Halt with clear error message |
| Overlapping Segments | End[n] > Start[n+1] | Halt with conflict details |
| ffmpeg Failure | Non-zero exit code | Log error, continue with next segment |
| File I/O Error | Permission denied | Halt with permission instructions |
| Disk Space | Insufficient space | Halt before extraction begins |
| Validation Failure | Duration mismatch | Log warning, flag segment for review |

**Implementation**:
```python
class ExtractionError(Exception):
    """Base exception for extraction errors."""
    pass

class TimecodeError(ExtractionError):
    """Raised for invalid timecode format."""
    pass

class ValidationError(ExtractionError):
    """Raised for validation failures."""
    pass

# Usage
try:
    extractor = AudioSegmentExtractor(csv_path, master_path, output_dir)
    report = extractor.run()
except TimecodeError as e:
    logger.error(f"Timecode error: {e}")
    sys.exit(1)
except ValidationError as e:
    logger.error(f"Validation error: {e}")
    sys.exit(1)
```

---

## 6. Output Specifications

### 6.1 Segment Audio Files

**Format**: MP3
**Codec**: MPEG Audio Layer 3 (MP3)
**Sample Rate**: 44100 Hz
**Bit Rate**: 256 kbps (CBR)
**Channels**: Stereo (2)
**Total Files**: 256 segments
**Estimated Total Size**: ~75-80 MB

### 6.2 Metadata Files

#### extraction_log.json

```json
{
  "extraction_date": "2025-10-30T15:30:00Z",
  "master_file": "Listening - Audio File - Master.mp3",
  "csv_file": "Sequence.csv",
  "total_segments": 256,
  "successful_extractions": 256,
  "failed_extractions": 0,
  "total_duration": 2222.32,
  "execution_time_seconds": 847.3,
  "validation_passed": true,
  "segments": [
    {
      "row": 1,
      "speaker": "Speaker 1",
      "start": "00:00:00:00",
      "end": "00:00:02:15",
      "duration": 2.6,
      "filename": "segment_0001_speaker1_00-00-00-00_to_00-00-02-15.mp3",
      "extraction_success": true,
      "validation_success": true
    }
  ]
}
```

#### segment_manifest.csv

```csv
row_number,speaker_name,start_timecode,end_timecode,start_seconds,end_seconds,duration,filename,file_size_bytes,validated
1,Speaker 1,00:00:00:00,00:00:02:15,0.0,2.6,2.6,segment_0001_speaker1_00-00-00-00_to_00-00-02-15.mp3,84352,true
2,Speaker 2,00:00:02:17,00:00:04:05,2.68,4.2,1.52,segment_0002_speaker2_00-00-02-17_to_00-00-04-05.mp3,49216,true
```

#### validation_report.json

```json
{
  "validation_date": "2025-10-30T15:45:00Z",
  "total_segments": 256,
  "validated_segments": 256,
  "failed_validations": 0,
  "pre_extraction": {
    "passed": true,
    "checks": {
      "input_files": "pass",
      "csv_structure": "pass",
      "timestamps": "pass",
      "disk_space": "pass"
    }
  },
  "post_extraction": {
    "passed": true,
    "total_duration_match": true,
    "all_segments_present": true,
    "all_segments_playable": true
  },
  "warnings": [
    "Row 128: Gap of 0.52s from previous segment"
  ],
  "errors": []
}
```

---

## 7. Performance Estimates

### 7.1 Execution Time

**Serial Processing**:
- Per segment extraction: ~2-4 seconds (with re-encoding)
- Total segments: 256
- **Estimated total time**: 10-15 minutes

**Factors affecting speed**:
- CPU performance (encoding is CPU-intensive)
- Disk I/O speed (SSD vs HDD)
- System load

### 7.2 Resource Requirements

**CPU**: 1-2 cores utilized (ffmpeg is single-threaded per process)
**Memory**: ~100-200 MB RAM
**Disk Space**:
- Input: 71.2 MB
- Output: ~80 MB
- Temp: ~10 MB
- **Total**: ~160 MB minimum

**Disk I/O**:
- Read: 71.2 MB (master file)
- Write: ~80 MB (256 segments)
- Sequential reads, random writes

---

## 8. Usage Instructions

### 8.1 Prerequisites

```bash
# Install ffmpeg
sudo apt-get install ffmpeg  # Linux
brew install ffmpeg          # macOS

# Verify installation
ffmpeg -version
ffprobe -version

# Install Python dependencies
cd /home/blackthorne/Work/tstprep.com/toefl-2026/audio-file-extraction
pip install pandas tqdm
```

### 8.2 Basic Usage

```bash
# Navigate to project directory
cd /home/blackthorne/Work/tstprep.com/toefl-2026/audio-file-extraction

# Run extraction script
python scripts/split_audio.py

# With custom parameters
python scripts/split_audio.py \
  --csv Sequence.csv \
  --master "Listening - Audio File - Master.mp3" \
  --output output/segments \
  --fps 25
```

### 8.3 Expected Output

```
Audio Segment Extraction
========================
CSV: Sequence.csv (256 segments)
Master: Listening - Audio File - Master.mp3 (2222.32s)
Output: output/segments/

Pre-extraction validation: PASSED
  ✓ Input files exist
  ✓ CSV structure valid
  ✓ Timestamps sequential
  ✓ Disk space sufficient

Extracting segments: 100%|████████████████| 256/256 [12:34<00:00,  2.95s/segment]

Post-extraction validation: PASSED
  ✓ All 256 segments extracted
  ✓ Total duration matches (2222.31s / 2222.32s)
  ✓ All segments playable

Results:
  Success: 256
  Failed: 0
  Total time: 12m 34s

Manifest saved: output/metadata/segment_manifest.csv
Log saved: output/metadata/extraction_log.json
```

---

## 9. Sample ffmpeg Commands

### 9.1 Example Extractions

**Segment 1** (Speaker 1, 0.0s to 2.6s):
```bash
ffmpeg -i "Listening - Audio File - Master.mp3" \
       -ss 0.0 -t 2.6 \
       -acodec libmp3lame -b:a 256k -ar 44100 -ac 2 \
       -y "output/segments/segment_0001_speaker1_00-00-00-00_to_00-00-02-15.mp3"
```

**Segment 32** (Speaker 1, 140.32s to 160.2s):
```bash
ffmpeg -i "Listening - Audio File - Master.mp3" \
       -ss 140.32 -t 19.88 \
       -acodec libmp3lame -b:a 256k -ar 44100 -ac 2 \
       -y "output/segments/segment_0032_speaker1_00-02-20-08_to_00-02-40-05.mp3"
```

**Segment 256** (Last segment):
```bash
ffmpeg -i "Listening - Audio File - Master.mp3" \
       -ss 2220.56 -t 1.76 \
       -acodec libmp3lame -b:a 256k -ar 44100 -ac 2 \
       -y "output/segments/segment_0256_speaker1_00-37-00-14_to_00-37-02-05.mp3"
```

### 9.2 Validation Examples

**Check segment duration**:
```bash
ffprobe -v error -show_entries format=duration \
        -of default=noprint_wrappers=1:nokey=1 \
        "output/segments/segment_0001_speaker1_00-00-00-00_to_00-00-02-15.mp3"
# Expected output: 2.600000
```

**Check segment metadata**:
```bash
ffprobe -v quiet -print_format json -show_format -show_streams \
        "output/segments/segment_0001_speaker1_00-00-00-00_to_00-00-02-15.mp3"
```

---

## 10. Validation Checklist

### 10.1 Pre-Implementation Checklist

- [x] CSV file analyzed and schema documented
- [x] Master audio file analyzed and metadata recorded
- [x] Timestamp format understood (SMPTE, 25 fps)
- [x] File naming convention designed
- [x] Directory structure planned
- [x] Validation strategy defined
- [x] Error handling approach documented
- [x] ffmpeg commands finalized
- [x] Python script architecture designed
- [ ] Implementation plan reviewed

### 10.2 Post-Implementation Checklist

- [ ] Script extracts all 256 segments
- [ ] All segments have correct filenames
- [ ] All segments are playable
- [ ] Segment durations match expected values (±0.1s)
- [ ] Total duration matches master file (±1%)
- [ ] No overlapping or missing segments
- [ ] Manifest CSV generated correctly
- [ ] Extraction log contains complete information
- [ ] Validation report shows all checks passed
- [ ] No errors or warnings (except acceptable gaps)

---

## 11. Troubleshooting Guide

### 11.1 Common Issues

**Issue**: "Invalid timecode format"
- **Cause**: Malformed timestamp in CSV
- **Solution**: Check CSV for non-numeric characters or missing colons
- **Fix**: Validate CSV format with regex before processing

**Issue**: ffmpeg fails with "Invalid data found"
- **Cause**: Corrupted master audio file
- **Solution**: Re-download master file, verify with ffprobe

**Issue**: "Insufficient disk space"
- **Cause**: Less than 160 MB available
- **Solution**: Free up disk space or specify different output directory

**Issue**: Segment duration mismatch
- **Cause**: Frame rate assumption incorrect
- **Solution**: Verify actual frame rate in CSV, adjust fps parameter

**Issue**: Permission denied writing to output
- **Cause**: Insufficient write permissions
- **Solution**: Create output directory with proper permissions:
  ```bash
  mkdir -p output/segments output/metadata
  chmod 755 output output/segments output/metadata
  ```

---

## 12. Next Steps

### 12.1 Implementation Phase

1. **Create Python script** (`scripts/split_audio.py`)
   - Implement `AudioSegmentExtractor` class
   - Add command-line argument parsing
   - Implement logging and progress bars

2. **Test with sample segments**
   - Extract first 5 segments manually
   - Verify accuracy and quality
   - Adjust parameters if needed

3. **Full extraction**
   - Run script on all 256 segments
   - Monitor progress and logs
   - Handle any errors that arise

4. **Validation**
   - Run post-extraction validation
   - Verify manifest and logs
   - Spot-check random segments

### 12.2 Optional Enhancements

- **Parallel processing**: Extract multiple segments concurrently (2-4 workers)
- **Resume capability**: Skip already-extracted segments on restart
- **Quality presets**: Fast/balanced/precise extraction modes
- **Metadata tagging**: Embed speaker and timecode in MP3 ID3 tags
- **Audio normalization**: Normalize volume across all segments
- **Format conversion**: Also export as WAV or FLAC

---

## 13. References

### 13.1 Documentation

- **ffmpeg Documentation**: https://ffmpeg.org/documentation.html
- **ffmpeg Audio Encoding**: https://trac.ffmpeg.org/wiki/Encode/MP3
- **SMPTE Timecode**: https://en.wikipedia.org/wiki/SMPTE_timecode
- **Python subprocess**: https://docs.python.org/3/library/subprocess.html
- **pandas CSV**: https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html

### 13.2 Tools Used

- **ffmpeg**: 6.0+ (audio extraction and encoding)
- **ffprobe**: 6.0+ (audio metadata inspection)
- **Python**: 3.8+ (scripting and automation)
- **pandas**: 2.0+ (CSV processing)
- **tqdm**: 4.65+ (progress bars)

---

## Appendix A: Complete Python Script Structure

```python
#!/usr/bin/env python3
"""
TOEFL Audio Segment Extractor

Splits master audio file into individual segments based on CSV timecode data.
"""

import subprocess
import logging
import json
import re
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional
import pandas as pd
from tqdm import tqdm


@dataclass
class SegmentInfo:
    """Metadata for a single audio segment."""
    row_number: int
    speaker_name: str
    start_timecode: str
    end_timecode: str
    start_seconds: float
    end_seconds: float
    duration: float
    text: str
    output_filename: str
    output_path: Optional[Path] = None


class AudioSegmentExtractor:
    """Extract audio segments from master file based on CSV timestamps."""

    def __init__(self, csv_path: str, master_audio_path: str,
                 output_dir: str, fps: int = 25):
        """
        Initialize extractor.

        Args:
            csv_path: Path to Sequence.csv
            master_audio_path: Path to master audio file
            output_dir: Directory for output segments
            fps: Frame rate for timecode conversion (default 25)
        """
        self.csv_path = Path(csv_path)
        self.master_path = Path(master_audio_path)
        self.output_dir = Path(output_dir)
        self.fps = fps
        self.segments: List[SegmentInfo] = []

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def convert_timecode(self, timecode_str: str) -> float:
        """Convert SMPTE timecode to seconds."""
        # Implementation as documented above
        pass

    def parse_csv(self) -> List[SegmentInfo]:
        """Parse CSV and create segment metadata."""
        # Implementation details
        pass

    def validate_timestamps(self, segments: List[SegmentInfo]) -> Tuple[bool, List[str]]:
        """Validate timestamp consistency."""
        # Implementation details
        pass

    def extract_segment(self, segment: SegmentInfo) -> bool:
        """Extract single audio segment using ffmpeg."""
        # Implementation details
        pass

    def validate_output(self, segment: SegmentInfo) -> bool:
        """Validate extracted segment."""
        # Implementation details
        pass

    def generate_manifest(self) -> pd.DataFrame:
        """Generate segment manifest CSV."""
        # Implementation details
        pass

    def run(self) -> dict:
        """Execute full extraction pipeline."""
        # Implementation details
        pass


if __name__ == "__main__":
    # Command-line interface
    import argparse

    parser = argparse.ArgumentParser(description="Extract audio segments from master file")
    parser.add_argument("--csv", default="Sequence.csv", help="Path to CSV file")
    parser.add_argument("--master", default="Listening - Audio File - Master.mp3",
                        help="Path to master audio file")
    parser.add_argument("--output", default="output/segments",
                        help="Output directory")
    parser.add_argument("--fps", type=int, default=25,
                        help="Frame rate (default: 25)")

    args = parser.parse_args()

    # Run extraction
    extractor = AudioSegmentExtractor(
        csv_path=args.csv,
        master_audio_path=args.master,
        output_dir=args.output,
        fps=args.fps
    )

    report = extractor.run()

    print("\n" + "="*50)
    print("Extraction Complete")
    print("="*50)
    print(f"Total segments: {report['total_segments']}")
    print(f"Successful: {report['successful']}")
    print(f"Failed: {report['failed']}")
    print(f"Execution time: {report['execution_time']:.1f}s")
```

---

## Document History

| Version | Date       | Author | Changes |
|---------|------------|--------|---------|
| 1.0     | 2025-10-30 | System | Initial comprehensive plan created |

---

**End of Document**
