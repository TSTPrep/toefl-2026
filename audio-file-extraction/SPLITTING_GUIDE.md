# Audio Splitting Guide - Task 1

## Quick Start

### Step 1: Manual Download (Required)
Since Google Workspace MCP cannot download binary audio files, you need to manually download the sample file:

1. Open: https://drive.google.com/file/d/1G9oTrurIHDc3JFqbyWrRWRz_7w8Bsz0w/view
2. Click "Download"
3. Save to: `downloads/samples/02.03.02, Listen and Choose, Module 2 (no pauses).mp3`

### Step 2: Test with Sample File

Run the splitting script on the smallest file first:

```bash
python split_no_pauses.py \
  "downloads/samples/02.03.02, Listen and Choose, Module 2 (no pauses).mp3"
```

This will:
- Detect silences using `-50dB` threshold and `0.2s` minimum duration
- Split the audio at silence midpoints
- Create numbered statement files in `output/statements/02.03.02, Listen and Choose, Module 2/`
- Validate segment durations and sizes

### Step 3: Review Results

Check the output directory:
```bash
ls -lh "output/statements/02.03.02, Listen and Choose, Module 2/"
```

Expected output pattern:
```
02.03.02, Listen and Choose, Module 2, Statement 001.mp3
02.03.02, Listen and Choose, Module 2, Statement 002.mp3
02.03.02, Listen and Choose, Module 2, Statement 003.mp3
...
```

### Step 4: Adjust Parameters (If Needed)

If the automatic detection doesn't work well, you can adjust parameters:

**More sensitive** (detects shorter silences):
```bash
python split_no_pauses.py \
  -t -40 -d 0.15 \
  "downloads/samples/02.03.02, Listen and Choose, Module 2 (no pauses).mp3"
```

**Less sensitive** (only longer silences):
```bash
python split_no_pauses.py \
  -t -60 -d 0.3 \
  "downloads/samples/02.03.02, Listen and Choose, Module 2 (no pauses).mp3"
```

## Full File Processing

Once the sample file works correctly, process all 10 files:

### Download All Files

You'll need to manually download all 10 files from the Drive folder:

| File | Size | Download Link |
|------|------|--------------|
| 02.01.01 Module 1 | 261KB | [Download](https://drive.google.com/file/d/14xwzNbjmBlqzO1NSyNyPeUBZvz916bfv/view) |
| 02.01.02 Module 2 | 112KB | [Download](https://drive.google.com/file/d/1thXh6piCkHoxgjW8nWtAsXarFzyC-Fmm/view) |
| 02.02.01 Module 1 | 433KB | [Download](https://drive.google.com/file/d/1mJ6hElBZsYT2d329QyPD_fqmdTSSmuE_/view) |
| 02.02.02 Module 2 | 137KB | [Download](https://drive.google.com/file/d/16TrYPgS9WxoxZnuzXkClY9gBGOGCndO0/view) |
| 02.03.01 Module 1 | 315KB | [Download](https://drive.google.com/file/d/1KzR4jEHNtm7r179K8fbjH_bcjpsWvr7a/view) |
| 02.03.02 Module 2 | 105KB | [Download](https://drive.google.com/file/d/1G9oTrurIHDc3JFqbyWrRWRz_7w8Bsz0w/view) |
| 02.04.01 Module 1 | 333KB | [Download](https://drive.google.com/file/d/1juIanK2gjuWQePtHGmMOWUDBhxn7fKFI/view) |
| 02.04.02 Module 2 | 244KB | [Download](https://drive.google.com/file/d/1-C189_7nOS5zK-Db0i-8m_rbH4-Wu1Xt/view) |
| 02.05.01 Module 1 | 391KB | [Download](https://drive.google.com/file/d/1wyDvXKHioytCfzWZX2PKWQnUwZwK59gO/view) |
| 02.05.02 Module 2 | 250KB | [Download](https://drive.google.com/file/d/1BVSbzmwS243BqV7rhs2LfFGK-qMwOFYz/view) |

Save all files to: `downloads/samples/`

### Batch Processing Script

Create a batch processing script:

```bash
#!/bin/bash
# process_all.sh

FILES=(
  "02.01.01, Listen and Choose, Module 1 (no pauses).mp3"
  "02.01.02, Listen and Choose, Module 2 (no pauses).mp3"
  "02.02.01, Listen and Choose, Module 1 (no pauses).mp3"
  "02.02.02, Listen and Choose, Module 2 (no pauses).mp3"
  "02.03.01, Listen and Choose, Module 1 (no pauses).mp3"
  "02.03.02, Listen and Choose, Module 2 (no pauses).mp3"
  "02.04.01, Listen and Choose, Module 1 (no pauses).mp3"
  "02.04.02, Listen and Choose, Module 2 (no pauses).mp3"
  "02.05.01, Listen and Choose, Module 1 (no pauses).mp3"
  "02.05.02, Listen and Choose, Module 2 (no pauses).mp3"
)

for file in "${FILES[@]}"; do
  echo "Processing: $file"
  python split_no_pauses.py "downloads/samples/$file"
  echo "---"
done

echo "All files processed!"
```

Run it:
```bash
chmod +x process_all.sh
./process_all.sh
```

## Script Usage

### Basic Usage

```bash
python split_no_pauses.py <input_file>
```

### Advanced Options

```
Usage: split_no_pauses.py [-h] [-o OUTPUT_DIR] [-t THRESHOLD] [-d DURATION] input_file

Positional arguments:
  input_file            Input audio file path

Optional arguments:
  -h, --help            Show this help message
  -o OUTPUT_DIR         Output directory (default: auto-generated)
  -t THRESHOLD          Silence detection threshold in dB (default: -50)
  -d DURATION           Minimum silence duration in seconds (default: 0.2)
```

### Examples

**Custom output directory:**
```bash
python split_no_pauses.py \
  -o custom/output/path \
  "input.mp3"
```

**Adjust sensitivity:**
```bash
python split_no_pauses.py \
  -t -45 -d 0.25 \
  "input.mp3"
```

## Output Structure

```
output/
└── statements/
    ├── 02.01.01, Listen and Choose, Module 1/
    │   ├── 02.01.01, Listen and Choose, Module 1, Statement 001.mp3
    │   ├── 02.01.01, Listen and Choose, Module 1, Statement 002.mp3
    │   └── ...
    ├── 02.01.02, Listen and Choose, Module 2/
    │   └── ...
    └── [8 more directories]
```

## Validation

The script automatically validates:
1. ✅ Segment count
2. ✅ File sizes (warns if < 10KB)
3. ✅ Durations (warns if < 1s or > 30s)

### Manual Spot Check

Listen to a few statement files to verify quality:
```bash
# Play first 3 statements from sample
mpv "output/statements/02.03.02, Listen and Choose, Module 2/02.03.02, Listen and Choose, Module 2, Statement 001.mp3"
mpv "output/statements/02.03.02, Listen and Choose, Module 2/02.03.02, Listen and Choose, Module 2, Statement 002.mp3"
mpv "output/statements/02.03.02, Listen and Choose, Module 2/02.03.02, Listen and Choose, Module 2, Statement 003.mp3"
```

Check for:
- No cut-off speech
- Complete statements
- Appropriate silence removal

## Troubleshooting

### No silences detected
**Symptom**: `WARNING: No silences detected`
**Solution**: Lower the threshold (e.g., `-t -40`) or reduce minimum duration (e.g., `-d 0.1`)

### Too many segments
**Symptom**: Hundreds of tiny segments created
**Solution**: Increase threshold (e.g., `-t -60`) or increase minimum duration (e.g., `-d 0.3`)

### Statements cut off
**Symptom**: Speech is truncated in segments
**Solution**: The split points are at silence *midpoints*, so this should be rare. Try increasing minimum silence duration to ensure cleaner boundaries.

### Suspiciously small files
**Symptom**: Many files < 10KB
**Solution**: These might be artifacts. Check if they contain only silence or very brief sounds. Consider filtering them out or adjusting detection parameters.

## Next Steps After Splitting

1. **Count Results**: Verify expected number of statements per file
2. **Spot Check**: Listen to random samples for quality
3. **Upload to Drive**: Use MCP to upload the statement files back to Drive folder
4. **Documentation**: Update CLAUDE.md with final results

## Dependencies

Required tools:
- Python 3.7+
- ffmpeg (with ffprobe)

Install ffmpeg:
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Check installation
ffmpeg -version
ffprobe -version
```

## MCP Integration Notes

**Current Limitation**: Google Workspace MCP cannot:
- Download binary audio files
- Upload binary audio files directly

**Workaround**: Manual download required, but upload might be possible via Drive API or manual upload after processing.

## Files Created

- `TASK1_ANALYSIS.md` - Investigation results and file IDs
- `SPLITTING_GUIDE.md` - This file (usage instructions)
- `split_no_pauses.py` - The splitting script
- `downloads/` - Directory for downloaded source files
- `output/statements/` - Directory for processed statement files
