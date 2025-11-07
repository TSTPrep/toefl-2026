#!/bin/bash
# TOEFL Audio Extraction - Ready-to-Run Script
# Run this after obtaining HuggingFace model access for pyannote/segmentation-3.0

set -e  # Exit on error

echo "================================================================================"
echo "TOEFL Audio Extraction - Speaker Detection Enhancement"
echo "================================================================================"
echo ""

# Configuration
PROJECT_DIR="/home/blackthorne/Work/tstprep.com/toefl-2026/audio-file-extraction"
# Load HF_TOKEN from .env file (contains: HF_TOKEN=your_token_here)
source .env 2>/dev/null || { echo "Error: .env file not found. Create it with HF_TOKEN=your_token"; exit 1; }

cd "$PROJECT_DIR"

echo "Step 1: Activate virtual environment"
echo "--------------------------------------------------------------------------------"
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

echo "Step 2: Set HuggingFace token"
echo "--------------------------------------------------------------------------------"
export HF_TOKEN="$HF_TOKEN"
echo "✓ HF_TOKEN configured"
echo ""

echo "Step 3: Verify setup (including model access)"
echo "--------------------------------------------------------------------------------"
python test_setup.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Setup verification failed!"
    echo ""
    echo "Possible reasons:"
    echo "  1. You haven't accepted terms at https://huggingface.co/pyannote/segmentation-3.0"
    echo "  2. Access approval is still pending (wait a few minutes)"
    echo "  3. Your HF_TOKEN has expired or been revoked"
    echo ""
    echo "Please resolve the issue and run this script again."
    exit 1
fi

echo ""
echo "✓ All checks passed! Ready to proceed."
echo ""

echo "Step 4: Test speaker detection on one file"
echo "--------------------------------------------------------------------------------"
echo "Testing on: 02.05.02, Listen and Choose, Module 2 (longest file at 7.25s)"
echo ""

TEST_FILE="input/02.05.02, Listen and Choose, Module 2 (no pauses).mp3"
TEST_OUTPUT="output/test_speaker_detection"

# Clean up old test output if exists
if [ -d "$TEST_OUTPUT" ]; then
    echo "Removing old test output..."
    rm -rf "$TEST_OUTPUT"
fi

python split_with_speaker_detection.py "$TEST_FILE" "$TEST_OUTPUT"

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Test successful!"
    echo ""
    echo "Test results:"
    ls -lh "$TEST_OUTPUT"/*.mp3
    echo ""
else
    echo ""
    echo "❌ Test failed! Check error messages above."
    exit 1
fi

echo ""
read -p "Test looks good? Press Enter to continue with full reprocessing, or Ctrl+C to stop..."
echo ""

echo "Step 5: Reprocess suspicious files"
echo "--------------------------------------------------------------------------------"
echo "This will reprocess 3 files that exceed 5 seconds duration."
echo "Backups will be created automatically before modification."
echo ""

python reprocess_statements.py --suspicious-only --hf-token "$HF_TOKEN"

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Reprocessing complete!"
    echo ""
else
    echo ""
    echo "❌ Reprocessing failed! Backups have been restored."
    exit 1
fi

echo "Step 6: Generate final metrics"
echo "--------------------------------------------------------------------------------"
python << 'PYTHON_SCRIPT'
import os
from pathlib import Path
from pydub import AudioSegment

statements_dir = Path("output/statements")
statements = sorted(statements_dir.rglob("*.mp3"))

durations = []
for statement in statements:
    audio = AudioSegment.from_mp3(statement)
    duration_sec = len(audio) / 1000.0
    durations.append(duration_sec)

print(f"Final Statistics:")
print(f"  Total statements: {len(statements)}")
print(f"  Min duration: {min(durations):.2f}s")
print(f"  Max duration: {max(durations):.2f}s")
print(f"  Average duration: {sum(durations)/len(durations):.2f}s")
print(f"  Median duration: {sorted(durations)[len(durations)//2]:.2f}s")
print(f"  Files >5s: {sum(1 for d in durations if d > 5.0)}")
print(f"  Files >7s: {sum(1 for d in durations if d > 7.0)}")
PYTHON_SCRIPT

echo ""
echo "================================================================================"
echo "COMPLETE! ✅"
echo "================================================================================"
echo ""
echo "Summary:"
echo "  - All suspicious files reprocessed with speaker detection"
echo "  - Backups preserved in *.backup directories"
echo "  - Original files untouched in input/"
echo "  - Enhanced statements ready in output/statements/"
echo ""
echo "Next steps:"
echo "  - Review the enhanced statement files"
echo "  - If satisfied, you can remove .backup directories"
echo "  - If issues, backups can be restored"
echo ""
echo "Documentation:"
echo "  - SUMMARY.md - Quick overview"
echo "  - PROGRESS_REPORT.md - Detailed progress"
echo "  - HUGGINGFACE_ACCESS_GUIDE.md - Model access help"
echo ""
