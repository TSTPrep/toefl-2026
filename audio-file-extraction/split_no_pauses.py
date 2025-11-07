#!/usr/bin/env python3
"""
Audio Splitting Script for "Listen and Choose (no pauses)" files
Splits audio files at silence boundaries into individual statement files
"""

import subprocess
import re
import os
import sys
from pathlib import Path
from typing import List, Tuple
import argparse


class AudioSplitter:
    def __init__(self, threshold_db=-50, min_duration=0.2):
        """
        Initialize the audio splitter with silence detection parameters.

        Args:
            threshold_db: Noise threshold in dB for silence detection (default: -50)
            min_duration: Minimum silence duration in seconds (default: 0.2)
        """
        self.threshold_db = threshold_db
        self.min_duration = min_duration

    def detect_silences(self, input_file: str) -> List[Tuple[float, float]]:
        """
        Run ffmpeg silencedetect and parse output to find silence periods.

        Args:
            input_file: Path to the input audio file

        Returns:
            List of (silence_start, silence_end) tuples in seconds
        """
        print(f"Detecting silences in: {input_file}")
        print(f"Parameters: threshold={self.threshold_db}dB, min_duration={self.min_duration}s")

        cmd = [
            'ffmpeg', '-i', input_file,
            '-af', f'silencedetect=noise={self.threshold_db}dB:d={self.min_duration}',
            '-f', 'null', '-'
        ]

        try:
            result = subprocess.run(
                cmd,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                check=False
            )
        except FileNotFoundError:
            print("ERROR: ffmpeg not found. Please install ffmpeg.")
            sys.exit(1)

        # Parse silence_start and silence_end from output
        silence_periods = []
        silence_start = None

        for line in result.stderr.split('\n'):
            if 'silence_start' in line:
                match = re.search(r'silence_start: ([\d.]+)', line)
                if match:
                    silence_start = float(match.group(1))

            elif 'silence_end' in line and silence_start is not None:
                match = re.search(r'silence_end: ([\d.]+)', line)
                if match:
                    silence_end = float(match.group(1))
                    silence_periods.append((silence_start, silence_end))
                    silence_start = None

        print(f"Found {len(silence_periods)} silence periods")
        return silence_periods

    def calculate_split_points(self, silence_periods: List[Tuple[float, float]]) -> List[float]:
        """
        Calculate midpoints of silence periods as split points.

        Args:
            silence_periods: List of (silence_start, silence_end) tuples

        Returns:
            List of timestamps in seconds where audio should be split
        """
        split_points = []
        for start, end in silence_periods:
            midpoint = (start + end) / 2.0
            split_points.append(midpoint)

        print(f"Calculated {len(split_points)} split points")
        return split_points

    def split_audio(self, input_file: str, split_points: List[float], output_dir: str) -> List[str]:
        """
        Split audio at given timestamps using ffmpeg segment muxer.

        Args:
            input_file: Path to input audio file
            split_points: List of timestamps in seconds
            output_dir: Directory for output files

        Returns:
            List of output file paths
        """
        if not split_points:
            print("WARNING: No split points found. File may not contain silences.")
            return []

        os.makedirs(output_dir, exist_ok=True)

        # Create segment times string
        segment_times = ','.join([f'{t:.3f}' for t in split_points])

        # Temporary output pattern
        temp_pattern = os.path.join(output_dir, 'segment_%03d.mp3')

        print(f"Splitting audio into {len(split_points) + 1} segments...")

        cmd = [
            'ffmpeg', '-i', input_file,
            '-f', 'segment',
            '-segment_times', segment_times,
            '-c', 'copy',  # Copy codec (no re-encoding)
            temp_pattern
        ]

        result = subprocess.run(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            check=False
        )

        if result.returncode != 0:
            print(f"ERROR: ffmpeg split failed:\n{result.stderr}")
            return []

        # Find all created segments
        output_files = sorted([
            os.path.join(output_dir, f)
            for f in os.listdir(output_dir)
            if f.startswith('segment_') and f.endswith('.mp3')
        ])

        print(f"Created {len(output_files)} audio segments")
        return output_files

    def rename_outputs(self, segment_files: List[str], base_name: str) -> List[str]:
        """
        Rename segments to proper naming scheme.

        Format: "{base}, Listen and Choose, Module X, Statement NNN.mp3"

        Args:
            segment_files: List of temporary segment file paths
            base_name: Original filename (e.g., "02.03.02, Listen and Choose, Module 2 (no pauses).mp3")

        Returns:
            List of renamed file paths
        """
        # Extract base prefix and module number from filename
        # Pattern: "02.03.02, Listen and Choose, Module 2 (no pauses).mp3"
        # Result: "02.03.02, Listen and Choose, Module 2"
        base = base_name.replace(' (no pauses).mp3', '').replace('.mp3', '')

        renamed_files = []
        output_dir = os.path.dirname(segment_files[0]) if segment_files else '.'

        for i, old_path in enumerate(segment_files, start=1):
            new_name = f"{base}, Statement {i:03d}.mp3"
            new_path = os.path.join(output_dir, new_name)

            try:
                os.rename(old_path, new_path)
                renamed_files.append(new_path)
                print(f"  [{i:3d}] {new_name}")
            except OSError as e:
                print(f"ERROR renaming {old_path} to {new_path}: {e}")
                renamed_files.append(old_path)

        return renamed_files

    def get_audio_duration(self, file_path: str) -> float:
        """
        Get duration of audio file using ffprobe.

        Args:
            file_path: Path to audio file

        Returns:
            Duration in seconds, or 0 if failed
        """
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            file_path
        ]

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            return float(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
            return 0.0

    def validate_segments(self, segment_files: List[str]) -> dict:
        """
        Validate that segments have reasonable characteristics.

        Args:
            segment_files: List of segment file paths

        Returns:
            Dictionary with validation statistics
        """
        print("\nValidating segments...")

        durations = []
        sizes = []
        issues = []

        for file_path in segment_files:
            # Check file exists and has size
            if not os.path.exists(file_path):
                issues.append(f"Missing: {file_path}")
                continue

            size = os.path.getsize(file_path)
            sizes.append(size)

            # Warn about suspiciously small files
            if size < 10000:  # Less than 10KB
                issues.append(f"Suspiciously small ({size} bytes): {os.path.basename(file_path)}")

            # Get duration
            duration = self.get_audio_duration(file_path)
            if duration > 0:
                durations.append(duration)

                # Warn about very short or very long segments
                if duration < 1.0:
                    issues.append(f"Very short ({duration:.1f}s): {os.path.basename(file_path)}")
                elif duration > 30.0:
                    issues.append(f"Very long ({duration:.1f}s): {os.path.basename(file_path)}")

        stats = {
            'count': len(segment_files),
            'total_size': sum(sizes),
            'avg_size': sum(sizes) / len(sizes) if sizes else 0,
            'avg_duration': sum(durations) / len(durations) if durations else 0,
            'min_duration': min(durations) if durations else 0,
            'max_duration': max(durations) if durations else 0,
            'issues': issues
        }

        print(f"  Total segments: {stats['count']}")
        print(f"  Average size: {stats['avg_size']/1024:.1f} KB")
        if durations:
            print(f"  Average duration: {stats['avg_duration']:.1f}s")
            print(f"  Duration range: {stats['min_duration']:.1f}s - {stats['max_duration']:.1f}s")

        if issues:
            print(f"\n  WARNING: {len(issues)} potential issues found:")
            for issue in issues[:10]:  # Show first 10
                print(f"    - {issue}")
            if len(issues) > 10:
                print(f"    ... and {len(issues) - 10} more")

        return stats

    def process_file(self, input_file: str, output_dir: str = None) -> Tuple[List[str], dict]:
        """
        Complete processing pipeline for a single audio file.

        Args:
            input_file: Path to input audio file
            output_dir: Optional output directory (defaults to auto-generated)

        Returns:
            Tuple of (list of output files, validation statistics)
        """
        input_path = Path(input_file)

        if not input_path.exists():
            print(f"ERROR: Input file not found: {input_file}")
            return [], {}

        # Auto-generate output directory if not provided
        if output_dir is None:
            base_name = input_path.stem.replace(' (no pauses)', '')
            output_dir = os.path.join('output', 'statements', base_name)

        print(f"\n{'='*80}")
        print(f"Processing: {input_path.name}")
        print(f"Output dir: {output_dir}")
        print(f"{'='*80}\n")

        # Step 1: Detect silences
        silence_periods = self.detect_silences(str(input_path))

        if not silence_periods:
            print("WARNING: No silences detected. Check threshold parameters.")
            return [], {}

        # Step 2: Calculate split points
        split_points = self.calculate_split_points(silence_periods)

        # Step 3: Split audio
        segment_files = self.split_audio(str(input_path), split_points, output_dir)

        if not segment_files:
            print("ERROR: No segments created")
            return [], {}

        # Step 4: Rename to proper naming scheme
        print(f"\nRenaming {len(segment_files)} segments...")
        renamed_files = self.rename_outputs(segment_files, input_path.name)

        # Step 5: Validate
        stats = self.validate_segments(renamed_files)

        print(f"\n{'='*80}")
        print(f"COMPLETE: {len(renamed_files)} statements created")
        print(f"{'='*80}\n")

        return renamed_files, stats


def main():
    parser = argparse.ArgumentParser(
        description='Split "Listen and Choose (no pauses)" audio files into individual statements'
    )
    parser.add_argument(
        'input_file',
        help='Input audio file path'
    )
    parser.add_argument(
        '-o', '--output-dir',
        help='Output directory (default: auto-generated)',
        default=None
    )
    parser.add_argument(
        '-t', '--threshold',
        type=int,
        default=-50,
        help='Silence detection threshold in dB (default: -50)'
    )
    parser.add_argument(
        '-d', '--duration',
        type=float,
        default=0.2,
        help='Minimum silence duration in seconds (default: 0.2)'
    )

    args = parser.parse_args()

    # Create splitter with specified parameters
    splitter = AudioSplitter(
        threshold_db=args.threshold,
        min_duration=args.duration
    )

    # Process file
    output_files, stats = splitter.process_file(
        args.input_file,
        args.output_dir
    )

    if output_files:
        print(f"\nSuccess! Created {len(output_files)} statement files.")
        print(f"Output directory: {os.path.dirname(output_files[0])}")

        if stats.get('issues'):
            print(f"\nNote: {len(stats['issues'])} potential issues detected. Review validation output above.")
            sys.exit(1)
    else:
        print("\nFailed to create statement files.")
        sys.exit(1)


if __name__ == '__main__':
    main()
