#!/bin/bash

# Process files from smallest to largest
FILES=(
  "downloads/02.03.02, Listen and Choose, Module 2 (no pauses).mp3"
  "downloads/02.01.02, Listen and Choose, Module 2 (no pauses).mp3"
  "downloads/02.02.02, Listen and Choose, Module 2 (no pauses).mp3"
  "downloads/02.04.02, Listen and Choose, Module 2 (no pauses).mp3"
  "downloads/02.05.02, Listen and Choose, Module 2 (no pauses).mp3"
  "downloads/02.01.01, Listen and Choose, Module 1 (no pauses).mp3"
  "downloads/02.03.01, Listen and Choose, Module 1 (no pauses).mp3"
  "downloads/02.04.01, Listen and Choose, Module 1 (no pauses).mp3"
  "downloads/02.05.01, Listen and Choose, Module 1 (no pauses).mp3"
  "downloads/02.02.01, Listen and Choose, Module 1 (no pauses).mp3"
)

echo "Processing 10 'Listen and Choose (no pauses)' files..."
echo "======================================================="
echo ""

total=0
for i in "${!FILES[@]}"; do
  file="${FILES[$i]}"
  num=$((i + 1))
  
  echo "[$num/10] Processing: $(basename "$file")"
  
  python split_no_pauses.py "$file" 2>&1 | grep -E "^(Processing|Found|Created|COMPLETE|WARNING|ERROR|  Total)"
  
  if [ $? -eq 0 ]; then
    echo "  ✓ Success"
  else
    echo "  ✗ Failed"
  fi
  echo ""
done

echo "======================================================="
echo "Batch processing complete!"
echo ""
echo "Summary of output directories:"
ls -d output/statements/*/
