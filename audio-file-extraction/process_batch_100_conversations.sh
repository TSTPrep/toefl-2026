#!/usr/bin/env bash
# Process batch 100.XX conversation files with narrator prefixes
# Narrator assignment: alphabetical order with alternating Daniel/Matilda

set -euo pipefail

# Get absolute working directory
WORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Directories (absolute paths)
DOWNLOADS_DIR="$WORK_DIR/downloads"
TEMP_DIR="$WORK_DIR/data/temp"
PROCESSED_DIR="$WORK_DIR/data/processed"

# Narrator files (absolute paths)
NARRATOR_DANIEL="$TEMP_DIR/narrator_daniel.mp3"
NARRATOR_MATILDA="$TEMP_DIR/narrator_matilda.mp3"

# Verify narrator files exist
if [[ ! -f "$NARRATOR_DANIEL" ]] || [[ ! -f "$NARRATOR_MATILDA" ]]; then
    echo "ERROR: Narrator files not found in $TEMP_DIR"
    exit 1
fi

# Get conversation files in alphabetical order
mapfile -t CONVERSATIONS < <(ls -1 "$DOWNLOADS_DIR"/100.{04..18}*.mp3 2>/dev/null | sort)

if [[ ${#CONVERSATIONS[@]} -eq 0 ]]; then
    echo "ERROR: No conversation files found in $DOWNLOADS_DIR"
    exit 1
fi

echo "======================================================================"
echo "Processing ${#CONVERSATIONS[@]} conversation files with narrator prefixes"
echo "======================================================================"
echo ""

# Process each file with alternating narrator
for i in "${!CONVERSATIONS[@]}"; do
    input_file="${CONVERSATIONS[$i]}"
    basename_file=$(basename "$input_file")
    output_file="$PROCESSED_DIR/$basename_file"

    # Determine narrator (0-indexed, so even=Daniel, odd=Matilda)
    if (( i % 2 == 0 )); then
        narrator="Daniel"
        narrator_file="$NARRATOR_DANIEL"
    else
        narrator="Matilda"
        narrator_file="$NARRATOR_MATILDA"
    fi

    echo "[$((i+1))/${#CONVERSATIONS[@]}] Processing: $basename_file"
    echo "            Narrator: $narrator"

    # Create concat list with absolute paths
    concat_list="$TEMP_DIR/concat_$i.txt"
    cat > "$concat_list" <<EOF
file '$narrator_file'
file '$input_file'
EOF

    # Concatenate with ffmpeg (suppress verbose output)
    if ffmpeg -f concat -safe 0 -i "$concat_list" -c copy -y "$output_file" >/dev/null 2>&1; then
        # Verify output
        if [[ -f "$output_file" ]] && [[ -s "$output_file" ]]; then
            output_size=$(stat -c%s "$output_file" 2>/dev/null || stat -f%z "$output_file" 2>/dev/null)
            echo "            Output: $output_file (${output_size} bytes)"
        else
            echo "            ERROR: Output file creation failed"
            rm -f "$concat_list"
            exit 1
        fi
    else
        echo "            ERROR: ffmpeg concatenation failed"
        cat "$concat_list"
        rm -f "$concat_list"
        exit 1
    fi

    # Cleanup concat list
    rm -f "$concat_list"
    echo ""
done

echo "======================================================================"
echo "COMPLETE: All ${#CONVERSATIONS[@]} files processed successfully"
echo "======================================================================"
echo ""
echo "Output directory: $PROCESSED_DIR"
echo ""
