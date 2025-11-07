#!/usr/bin/env python3
"""
Task 1: Timecode-Based Audio Splitting

Splits "Listen and Choose" audio files based on explicit timecodes from CSV files.
More accurate than silence detection (Task 1 original approach).

CSV Format:
    "Speaker Name","Start Time","End Time","Text"
    "Speaker 1","00:00:00:00","00:00:02:15","The deadline's coming up..."

Timecode Format: HH:MM:SS:FF (Hours:Minutes:Seconds:Frames at 30fps)
Output: Individual statement MP3 files using ffmpeg with no re-encoding

Usage:
    # Dry run (no file creation)
    python task1_split_by_timecode.py --dry-run

    # Process single file
    python task1_split_by_timecode.py --input "file.mp3" --csv "file.csv"

    # Process first 3 files (testing)
    python task1_split_by_timecode.py --limit 3

    # Process all valid CSV files
    python task1_split_by_timecode.py
"""

import argparse
import csv
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TimecodeEntry:
    """Represents a single timecode entry from CSV."""
    speaker: str
    start_time: str  # HH:MM:SS:FF format
    end_time: str    # HH:MM:SS:FF format
    text: str
    start_seconds: float
    end_seconds: float
    duration: float


class TimecodeProcessor:
    """Processes CSV timecode files and splits audio accordingly."""

    def __init__(self, fps: int = 30):
        """
        Initialize processor.

        Args:
            fps: Frames per second for timecode conversion (default: 30)
        """
        self.fps = fps

    def timecode_to_seconds(self, timecode: str) -> float:
        """
        Convert SMPTE timecode to seconds.

        Format: HH:MM:SS:FF (Hours:Minutes:Seconds:Frames)
        Example: 00:00:02:15 = 2 + (15/30) = 2.5 seconds

        Args:
            timecode: Timecode string in HH:MM:SS:FF format

        Returns:
            Total seconds as float

        Raises:
            ValueError: If timecode format is invalid
        """
        try:
            parts = timecode.split(':')
            if len(parts) != 4:
                raise ValueError(f"Invalid timecode format: {timecode}")

            hours, minutes, seconds, frames = map(int, parts)

            total_seconds = (
                hours * 3600 +
                minutes * 60 +
                seconds +
                frames / self.fps
            )

            return total_seconds

        except (ValueError, IndexError) as e:
            raise ValueError(f"Error parsing timecode '{timecode}': {e}")

    def seconds_to_ffmpeg_time(self, seconds: float) -> str:
        """
        Convert seconds to ffmpeg time format.

        Args:
            seconds: Time in seconds

        Returns:
            Time string in HH:MM:SS.mmm format
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60

        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

    def parse_csv(self, csv_path: Path) -> List[TimecodeEntry]:
        """
        Parse CSV file and extract timecode entries.

        Args:
            csv_path: Path to CSV file

        Returns:
            List of TimecodeEntry objects

        Raises:
            ValueError: If CSV format is invalid
            FileNotFoundError: If CSV file not found
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        entries = []

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                # Validate headers
                required_headers = {'Speaker Name', 'Start Time', 'End Time', 'Text'}
                if not required_headers.issubset(set(reader.fieldnames or [])):
                    raise ValueError(
                        f"CSV missing required headers. "
                        f"Expected: {required_headers}, "
                        f"Found: {reader.fieldnames}"
                    )

                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                    try:
                        start_sec = self.timecode_to_seconds(row['Start Time'])
                        end_sec = self.timecode_to_seconds(row['End Time'])
                        duration = end_sec - start_sec

                        if duration <= 0:
                            logger.warning(
                                f"Row {row_num}: Invalid duration ({duration:.3f}s). "
                                f"Start: {row['Start Time']}, End: {row['End Time']}"
                            )
                            continue

                        entry = TimecodeEntry(
                            speaker=row['Speaker Name'],
                            start_time=row['Start Time'],
                            end_time=row['End Time'],
                            text=row['Text'],
                            start_seconds=start_sec,
                            end_seconds=end_sec,
                            duration=duration
                        )

                        entries.append(entry)

                    except (ValueError, KeyError) as e:
                        logger.error(f"Row {row_num}: Error parsing entry: {e}")
                        continue

        except UnicodeDecodeError as e:
            raise ValueError(f"CSV file is corrupted or not valid UTF-8: {e}")

        if not entries:
            raise ValueError(f"No valid entries found in CSV: {csv_path}")

        logger.info(f"Parsed {len(entries)} entries from {csv_path.name}")
        return entries

    def split_audio(
        self,
        input_audio: Path,
        entries: List[TimecodeEntry],
        output_dir: Path,
        base_name: str,
        dry_run: bool = False
    ) -> List[Path]:
        """
        Split audio file based on timecode entries.

        Args:
            input_audio: Path to source audio file
            entries: List of timecode entries
            output_dir: Directory for output files
            base_name: Base name for output files (e.g., "02.01.01, Listen and Choose, Module 1")
            dry_run: If True, only log actions without creating files

        Returns:
            List of created output file paths

        Raises:
            FileNotFoundError: If input audio not found
            RuntimeError: If ffmpeg fails
        """
        if not input_audio.exists():
            raise FileNotFoundError(f"Input audio not found: {input_audio}")

        output_dir.mkdir(parents=True, exist_ok=True)
        output_files = []

        logger.info(f"Splitting {input_audio.name} into {len(entries)} statements")

        for idx, entry in enumerate(entries, start=1):
            output_filename = f"{base_name}, Statement {idx:03d}.mp3"
            output_path = output_dir / output_filename

            start_time = self.seconds_to_ffmpeg_time(entry.start_seconds)
            end_time = self.seconds_to_ffmpeg_time(entry.end_seconds)

            logger.debug(
                f"Statement {idx:03d}: {start_time} -> {end_time} "
                f"({entry.duration:.2f}s) | {entry.text[:50]}..."
            )

            if dry_run:
                logger.info(f"[DRY RUN] Would create: {output_filename}")
                output_files.append(output_path)
                continue

            # Use ffmpeg to extract segment
            cmd = [
                'ffmpeg',
                '-i', str(input_audio),
                '-ss', start_time,
                '-to', end_time,
                '-c', 'copy',  # No re-encoding (preserves quality)
                '-y',          # Overwrite if exists
                str(output_path)
            ]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode != 0:
                    logger.error(f"ffmpeg failed for statement {idx}: {result.stderr}")
                    continue

                # Validate output
                if not output_path.exists() or output_path.stat().st_size == 0:
                    logger.error(f"Output file invalid: {output_path}")
                    continue

                # Verify duration (±0.2s tolerance for encoding variations)
                actual_duration = self._get_duration(output_path)
                expected_duration = entry.duration
                duration_diff = abs(actual_duration - expected_duration)

                if duration_diff > 0.2:
                    logger.warning(
                        f"Statement {idx}: Duration mismatch. "
                        f"Expected: {expected_duration:.2f}s, "
                        f"Actual: {actual_duration:.2f}s, "
                        f"Diff: {duration_diff:.2f}s"
                    )

                logger.info(f"✓ Created: {output_filename} ({actual_duration:.2f}s)")
                output_files.append(output_path)

            except subprocess.TimeoutExpired:
                logger.error(f"ffmpeg timeout for statement {idx}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error for statement {idx}: {e}")
                continue

        success_count = len(output_files)
        logger.info(
            f"Completed: {success_count}/{len(entries)} statements created"
        )

        return output_files

    def _get_duration(self, audio_file: Path) -> float:
        """Get duration of audio file using ffprobe."""
        try:
            result = subprocess.run(
                [
                    'ffprobe',
                    '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    str(audio_file)
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return 0.0

            return float(result.stdout.strip())

        except (subprocess.TimeoutExpired, ValueError):
            return 0.0


def find_matching_files(downloads_dir: Path) -> List[Tuple[Path, Path]]:
    """
    Find matching MP3 and CSV file pairs.

    Args:
        downloads_dir: Directory containing downloads

    Returns:
        List of (mp3_path, csv_path) tuples
    """
    csv_files = sorted(downloads_dir.glob("*.csv"))
    pairs = []

    for csv_file in csv_files:
        # Derive MP3 filename from CSV filename
        mp3_file = csv_file.with_suffix('.mp3')

        if mp3_file.exists():
            pairs.append((mp3_file, csv_file))
        else:
            logger.warning(f"No matching MP3 for CSV: {csv_file.name}")

    return pairs


def extract_base_name(filename: str) -> str:
    """
    Extract base name from audio filename.

    Example:
        "02.01.01, Listen and Choose, Module 1 (no pauses).mp3"
        -> "02.01.01, Listen and Choose, Module 1"

    Args:
        filename: Original filename

    Returns:
        Base name without " (no pauses)" and extension
    """
    # Remove extension
    name = Path(filename).stem

    # Remove " (no pauses)" suffix
    if name.endswith(" (no pauses)"):
        name = name[:-len(" (no pauses)")]

    return name


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Split audio files based on CSV timecodes"
    )
    parser.add_argument(
        '--input',
        type=Path,
        help='Specific input audio file to process'
    )
    parser.add_argument(
        '--csv',
        type=Path,
        help='Specific CSV file to use (required if --input specified)'
    )
    parser.add_argument(
        '--downloads-dir',
        type=Path,
        default=Path('downloads'),
        help='Directory containing source files (default: downloads)'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('output/statements_timecode'),
        help='Output directory (default: output/statements_timecode)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit processing to first N files (for testing)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Parse and validate without creating files'
    )
    parser.add_argument(
        '--fps',
        type=int,
        default=30,
        help='Frames per second for timecode conversion (default: 30)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logger.setLevel('DEBUG')

    # Check ffmpeg availability
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("ffmpeg not found. Please install ffmpeg.")
        return 1

    processor = TimecodeProcessor(fps=args.fps)

    # Determine files to process
    if args.input:
        if not args.csv:
            logger.error("--csv required when --input is specified")
            return 1

        if not args.input.exists():
            logger.error(f"Input file not found: {args.input}")
            return 1

        if not args.csv.exists():
            logger.error(f"CSV file not found: {args.csv}")
            return 1

        file_pairs = [(args.input, args.csv)]

    else:
        if not args.downloads_dir.exists():
            logger.error(f"Downloads directory not found: {args.downloads_dir}")
            return 1

        file_pairs = find_matching_files(args.downloads_dir)

        if not file_pairs:
            logger.error(f"No matching MP3/CSV pairs found in {args.downloads_dir}")
            return 1

        logger.info(f"Found {len(file_pairs)} MP3/CSV pairs")

        if args.limit:
            file_pairs = file_pairs[:args.limit]
            logger.info(f"Limited to first {args.limit} files")

    # Process each file pair
    total_statements = 0
    total_files = len(file_pairs)
    successful_files = 0

    for idx, (mp3_file, csv_file) in enumerate(file_pairs, start=1):
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing {idx}/{total_files}: {mp3_file.name}")
        logger.info(f"{'='*80}")

        try:
            # Parse CSV
            entries = processor.parse_csv(csv_file)

            # Extract base name for output
            base_name = extract_base_name(mp3_file.name)

            # Create output subdirectory
            output_subdir = args.output_dir / base_name

            # Split audio
            output_files = processor.split_audio(
                input_audio=mp3_file,
                entries=entries,
                output_dir=output_subdir,
                base_name=base_name,
                dry_run=args.dry_run
            )

            if output_files:
                successful_files += 1
                total_statements += len(output_files)

        except (ValueError, FileNotFoundError) as e:
            logger.error(f"Error processing {csv_file.name}: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error processing {mp3_file.name}: {e}")
            continue

    # Summary report
    logger.info(f"\n{'='*80}")
    logger.info("PROCESSING SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"Files processed: {successful_files}/{total_files}")
    logger.info(f"Total statements: {total_statements}")
    logger.info(f"Output directory: {args.output_dir}")

    if args.dry_run:
        logger.info("\n[DRY RUN] No files were created")

    return 0


if __name__ == '__main__':
    sys.exit(main())
