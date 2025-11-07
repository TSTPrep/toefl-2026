#!/usr/bin/env python3
"""
Improved Audio Splitting Script with Speaker Diarization
Splits audio files using speaker detection + silence analysis for better statement separation
"""

import subprocess
import re
import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional
import argparse
import json

# Check for speaker diarization libraries
try:
    from pyannote.audio import Pipeline
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False
    print("WARNING: pyannote.audio not available. Install with:")
    print("  pip install pyannote.audio")
    print("  Also requires HuggingFace authentication token")

# Check for audio processing libraries
try:
    import numpy as np
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("WARNING: torch/numpy not available for advanced processing")


class SpeakerAwareSplitter:
    """
    Audio splitter that combines speaker diarization with silence detection
    for improved statement boundary detection.
    """

    def __init__(
        self,
        silence_threshold_db=-50,
        silence_min_duration=0.2,
        min_segment_duration=1.5,
        use_speaker_detection=True,
        hf_token=None
    ):
        """
        Initialize the splitter.

        Args:
            silence_threshold_db: Noise threshold in dB for silence detection
            silence_min_duration: Minimum silence duration in seconds
            min_segment_duration: Minimum duration for output segments
            use_speaker_detection: Whether to use speaker diarization
            hf_token: HuggingFace token for pyannote.audio (or set HF_TOKEN env var)
        """
        self.silence_threshold_db = silence_threshold_db
        self.silence_min_duration = silence_min_duration
        self.min_segment_duration = min_segment_duration
        self.use_speaker_detection = use_speaker_detection and PYANNOTE_AVAILABLE

        self.pipeline = None
        if self.use_speaker_detection:
            token = hf_token or os.environ.get('HF_TOKEN')
            if not token:
                print("WARNING: No HuggingFace token provided. Speaker detection disabled.")
                print("Set HF_TOKEN environment variable or pass --hf-token")
                print("Get token at: https://huggingface.co/settings/tokens")
                self.use_speaker_detection = False
            else:
                try:
                    self.pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1",
                        token=token
                    )
                    print("✓ Speaker diarization loaded successfully")
                except Exception as e:
                    print(f"WARNING: Failed to load speaker diarization: {e}")
                    print("Falling back to silence detection only")
                    self.use_speaker_detection = False

    def detect_silences(self, input_file: str) -> List[Tuple[float, float]]:
        """
        Run ffmpeg silencedetect to find silence periods.

        Args:
            input_file: Path to the input audio file

        Returns:
            List of (silence_start, silence_end) tuples in seconds
        """
        print(f"Detecting silences...")
        print(f"  Parameters: threshold={self.silence_threshold_db}dB, min_duration={self.silence_min_duration}s")

        cmd = [
            'ffmpeg', '-i', input_file,
            '-af', f'silencedetect=noise={self.silence_threshold_db}dB:d={self.silence_min_duration}',
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

        print(f"  Found {len(silence_periods)} silence periods")
        return silence_periods

    def detect_speaker_changes(self, input_file: str) -> List[Tuple[float, str]]:
        """
        Use pyannote.audio to detect speaker changes.

        Args:
            input_file: Path to the input audio file

        Returns:
            List of (timestamp, speaker_label) tuples indicating speaker segments
        """
        if not self.use_speaker_detection:
            return []

        print("Running speaker diarization...")

        try:
            # Run diarization
            diarization = self.pipeline(input_file)

            # Extract speaker change points
            speaker_segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                speaker_segments.append((turn.start, speaker))

            print(f"  Found {len(speaker_segments)} speaker segments")

            # Log speaker distribution
            speakers = set(seg[1] for seg in speaker_segments)
            print(f"  Detected {len(speakers)} unique speakers")

            return speaker_segments

        except Exception as e:
            print(f"ERROR in speaker diarization: {e}")
            return []

    def merge_split_signals(
        self,
        speaker_segments: List[Tuple[float, str]],
        silence_periods: List[Tuple[float, float]],
        audio_duration: float
    ) -> List[float]:
        """
        Combine speaker changes and silence detection to determine optimal split points.

        Strategy:
        1. Speaker changes are primary split points
        2. Look for nearby silence to make clean cuts
        3. Add silence-only splits for long single-speaker segments
        4. Merge segments shorter than minimum duration

        Args:
            speaker_segments: List of (timestamp, speaker_label) from diarization
            silence_periods: List of (start, end) silence periods
            audio_duration: Total audio duration in seconds

        Returns:
            List of split timestamps
        """
        print("Merging speaker and silence signals...")

        split_points = []

        if not speaker_segments:
            # Fallback to silence-only detection
            print("  No speaker segments - using silence only")
            for silence_start, silence_end in silence_periods:
                midpoint = (silence_start + silence_end) / 2.0
                split_points.append(midpoint)

        else:
            # Process speaker boundaries
            for i in range(1, len(speaker_segments)):
                speaker_change_time = speaker_segments[i][0]
                prev_speaker = speaker_segments[i-1][1]
                curr_speaker = speaker_segments[i][1]

                # Only split on actual speaker changes
                if prev_speaker != curr_speaker:
                    # Look for nearby silence within ±0.5 seconds
                    nearby_silence = self._find_nearest_silence(
                        speaker_change_time,
                        silence_periods,
                        window=0.5
                    )

                    if nearby_silence:
                        # Use silence midpoint for clean cut
                        split_time = (nearby_silence[0] + nearby_silence[1]) / 2.0
                    else:
                        # Use speaker boundary directly
                        split_time = speaker_change_time

                    split_points.append(split_time)

            # Add silence-only splits for long single-speaker segments
            segments = self._segments_from_splits(split_points, audio_duration)

            additional_splits = []
            for seg_start, seg_end in segments:
                seg_duration = seg_end - seg_start

                # If segment is suspiciously long, check for internal silences
                if seg_duration > 6.0:  # Threshold for "too long"
                    internal_silences = [
                        (s_start, s_end) for s_start, s_end in silence_periods
                        if seg_start < s_start < seg_end
                    ]

                    if internal_silences:
                        # Add strongest silence as split
                        longest_silence = max(internal_silences, key=lambda x: x[1] - x[0])
                        split_time = (longest_silence[0] + longest_silence[1]) / 2.0
                        additional_splits.append(split_time)
                        print(f"  Adding silence split in long segment ({seg_duration:.1f}s) at {split_time:.2f}s")

            split_points.extend(additional_splits)

        # Sort and deduplicate
        split_points = sorted(set(split_points))

        # Merge segments that are too short
        split_points = self._merge_short_segments(split_points, audio_duration)

        print(f"  Final split points: {len(split_points)}")
        return split_points

    def _find_nearest_silence(
        self,
        timestamp: float,
        silence_periods: List[Tuple[float, float]],
        window: float = 0.5
    ) -> Optional[Tuple[float, float]]:
        """Find silence period closest to given timestamp within window."""
        candidates = [
            (s_start, s_end) for s_start, s_end in silence_periods
            if abs((s_start + s_end) / 2.0 - timestamp) <= window
        ]

        if not candidates:
            return None

        # Return closest silence
        return min(candidates, key=lambda x: abs((x[0] + x[1]) / 2.0 - timestamp))

    def _segments_from_splits(
        self,
        split_points: List[float],
        audio_duration: float
    ) -> List[Tuple[float, float]]:
        """Convert split points to (start, end) segments."""
        if not split_points:
            return [(0, audio_duration)]

        segments = []
        prev_time = 0

        for split_time in split_points:
            segments.append((prev_time, split_time))
            prev_time = split_time

        # Add final segment
        segments.append((prev_time, audio_duration))

        return segments

    def _merge_short_segments(
        self,
        split_points: List[float],
        audio_duration: float
    ) -> List[float]:
        """Remove split points that create segments shorter than minimum duration."""
        if not split_points:
            return split_points

        segments = self._segments_from_splits(split_points, audio_duration)
        merged_splits = []

        prev_end = 0
        for i, (seg_start, seg_end) in enumerate(segments):
            seg_duration = seg_end - seg_start

            # If segment is too short and not the last segment, skip this split
            if seg_duration < self.min_segment_duration and i < len(segments) - 1:
                print(f"  Merging short segment ({seg_duration:.1f}s) at {seg_start:.2f}s")
                continue

            # Keep this split point
            if seg_end < audio_duration:  # Don't add split at the very end
                merged_splits.append(seg_end)

        return merged_splits

    def get_audio_duration(self, file_path: str) -> float:
        """Get duration of audio file using ffprobe."""
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
            print("WARNING: No split points found.")
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
        """Rename segments to proper naming scheme."""
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

    def validate_segments(self, segment_files: List[str]) -> dict:
        """Validate segment characteristics."""
        print("\nValidating segments...")

        durations = []
        issues = []

        for file_path in segment_files:
            if not os.path.exists(file_path):
                issues.append(f"Missing: {file_path}")
                continue

            size = os.path.getsize(file_path)
            if size < 10000:
                issues.append(f"Suspiciously small ({size} bytes): {os.path.basename(file_path)}")

            duration = self.get_audio_duration(file_path)
            if duration > 0:
                durations.append(duration)

                if duration < 1.0:
                    issues.append(f"Very short ({duration:.1f}s): {os.path.basename(file_path)}")
                elif duration > 30.0:
                    issues.append(f"Very long ({duration:.1f}s): {os.path.basename(file_path)}")

        stats = {
            'count': len(segment_files),
            'avg_duration': sum(durations) / len(durations) if durations else 0,
            'min_duration': min(durations) if durations else 0,
            'max_duration': max(durations) if durations else 0,
            'issues': issues
        }

        print(f"  Total segments: {stats['count']}")
        if durations:
            print(f"  Average duration: {stats['avg_duration']:.1f}s")
            print(f"  Duration range: {stats['min_duration']:.1f}s - {stats['max_duration']:.1f}s")

        if issues:
            print(f"\n  WARNING: {len(issues)} potential issues:")
            for issue in issues[:5]:
                print(f"    - {issue}")
            if len(issues) > 5:
                print(f"    ... and {len(issues) - 5} more")

        return stats

    def process_file(self, input_file: str, output_dir: str = None) -> Tuple[List[str], dict]:
        """
        Complete processing pipeline for a single audio file.

        Args:
            input_file: Path to input audio file
            output_dir: Optional output directory

        Returns:
            Tuple of (list of output files, validation statistics)
        """
        input_path = Path(input_file)

        if not input_path.exists():
            print(f"ERROR: Input file not found: {input_file}")
            return [], {}

        if output_dir is None:
            base_name = input_path.stem.replace(' (no pauses)', '')
            output_dir = os.path.join('output', 'statements_improved', base_name)

        print(f"\n{'='*80}")
        print(f"Processing: {input_path.name}")
        print(f"Output dir: {output_dir}")
        print(f"Method: {'Speaker Detection + Silence' if self.use_speaker_detection else 'Silence Only'}")
        print(f"{'='*80}\n")

        # Get audio duration
        audio_duration = self.get_audio_duration(str(input_path))
        print(f"Audio duration: {audio_duration:.2f}s\n")

        # Step 1: Detect silences
        silence_periods = self.detect_silences(str(input_path))

        # Step 2: Detect speaker changes (if enabled)
        speaker_segments = []
        if self.use_speaker_detection:
            speaker_segments = self.detect_speaker_changes(str(input_path))

        # Step 3: Merge signals and determine split points
        split_points = self.merge_split_signals(
            speaker_segments,
            silence_periods,
            audio_duration
        )

        if not split_points:
            print("WARNING: No split points determined")
            return [], {}

        # Step 4: Split audio
        segment_files = self.split_audio(str(input_path), split_points, output_dir)

        if not segment_files:
            print("ERROR: No segments created")
            return [], {}

        # Step 5: Rename
        print(f"\nRenaming {len(segment_files)} segments...")
        renamed_files = self.rename_outputs(segment_files, input_path.name)

        # Step 6: Validate
        stats = self.validate_segments(renamed_files)

        print(f"\n{'='*80}")
        print(f"COMPLETE: {len(renamed_files)} statements created")
        print(f"{'='*80}\n")

        return renamed_files, stats


def main():
    parser = argparse.ArgumentParser(
        description='Split audio files using speaker detection and silence analysis'
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
        '--no-speaker-detection',
        action='store_true',
        help='Disable speaker detection (silence only)'
    )
    parser.add_argument(
        '--hf-token',
        help='HuggingFace token for pyannote.audio (or set HF_TOKEN env var)',
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
    parser.add_argument(
        '--min-segment',
        type=float,
        default=1.5,
        help='Minimum segment duration in seconds (default: 1.5)'
    )

    args = parser.parse_args()

    # Create splitter
    splitter = SpeakerAwareSplitter(
        silence_threshold_db=args.threshold,
        silence_min_duration=args.duration,
        min_segment_duration=args.min_segment,
        use_speaker_detection=not args.no_speaker_detection,
        hf_token=args.hf_token
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
            print(f"\nNote: {len(stats['issues'])} potential issues detected.")
            sys.exit(1)
    else:
        print("\nFailed to create statement files.")
        sys.exit(1)


if __name__ == '__main__':
    main()
