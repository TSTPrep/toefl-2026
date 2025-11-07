"""
Audio Processor Module

Wrapper for ffmpeg operations including concatenation and splitting.
Uses ffmpeg concat demuxer method (no re-encoding) for high-quality, fast processing.
"""

import subprocess
import os
from pathlib import Path
from typing import List, Optional, Tuple
from .logger import get_logger

logger = get_logger(__name__)


class AudioProcessingError(Exception):
    """Exception raised for audio processing errors."""
    pass


class AudioProcessor:
    """Handles audio file operations using ffmpeg."""

    @staticmethod
    def check_ffmpeg_installed() -> bool:
        """
        Check if ffmpeg is installed and accessible.

        Returns:
            True if ffmpeg is available, False otherwise
        """
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    @staticmethod
    def get_audio_duration(file_path: str) -> float:
        """
        Get duration of audio file in seconds.

        Args:
            file_path: Path to audio file

        Returns:
            Duration in seconds

        Raises:
            AudioProcessingError: If unable to get duration
        """
        if not Path(file_path).exists():
            raise AudioProcessingError(f"Audio file not found: {file_path}")

        try:
            result = subprocess.run(
                [
                    'ffprobe',
                    '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    file_path
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                raise AudioProcessingError(f"ffprobe error: {result.stderr}")

            return float(result.stdout.strip())

        except subprocess.TimeoutExpired:
            raise AudioProcessingError(f"Timeout getting duration for {file_path}")
        except ValueError as e:
            raise AudioProcessingError(f"Invalid duration value: {e}")

    @staticmethod
    def concatenate_audio_files(
        input_files: List[str],
        output_file: str,
        use_concat_demuxer: bool = True
    ) -> None:
        """
        Concatenate multiple audio files into one.

        Uses ffmpeg concat demuxer method (recommended) which:
        - Does not re-encode (preserves quality)
        - Is very fast
        - Requires all files to have same codec/format

        Args:
            input_files: List of input file paths
            output_file: Path for output file
            use_concat_demuxer: Use concat demuxer (True) or filter (False)

        Raises:
            AudioProcessingError: If concatenation fails
        """
        if not input_files:
            raise AudioProcessingError("No input files provided")

        for file_path in input_files:
            if not Path(file_path).exists():
                raise AudioProcessingError(f"Input file not found: {file_path}")

        # Ensure output directory exists
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Concatenating {len(input_files)} files to {output_file}")

        if use_concat_demuxer:
            # Create temporary concat list file
            concat_list_path = Path(output_file).parent / "concat_list.txt"

            try:
                with open(concat_list_path, 'w') as f:
                    for file_path in input_files:
                        # ffmpeg concat demuxer requires absolute paths or relative with 'file' prefix
                        abs_path = Path(file_path).resolve()
                        # Escape single quotes in path
                        escaped_path = str(abs_path).replace("'", "'\\''")
                        f.write(f"file '{escaped_path}'\n")

                # Run ffmpeg concat demuxer
                result = subprocess.run(
                    [
                        'ffmpeg',
                        '-f', 'concat',
                        '-safe', '0',
                        '-i', str(concat_list_path),
                        '-c', 'copy',  # Copy codec (no re-encoding)
                        '-y',  # Overwrite output file
                        output_file
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode != 0:
                    raise AudioProcessingError(f"ffmpeg concatenation failed: {result.stderr}")

                logger.info(f"Successfully concatenated to {output_file}")

            finally:
                # Clean up concat list file
                if concat_list_path.exists():
                    concat_list_path.unlink()

        else:
            # Alternative: concat filter (re-encodes, slower but more flexible)
            filter_complex = ''.join([f'[{i}:a]' for i in range(len(input_files))])
            filter_complex += f'concat=n={len(input_files)}:v=0:a=1[out]'

            cmd = ['ffmpeg']
            for file_path in input_files:
                cmd.extend(['-i', file_path])

            cmd.extend([
                '-filter_complex', filter_complex,
                '-map', '[out]',
                '-y',
                output_file
            ])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                raise AudioProcessingError(f"ffmpeg filter concatenation failed: {result.stderr}")

            logger.info(f"Successfully concatenated to {output_file}")

    @staticmethod
    def split_audio_file(
        input_file: str,
        output_prefix: str,
        split_times: List[float]
    ) -> List[str]:
        """
        Split audio file at specified times.

        Args:
            input_file: Path to input audio file
            output_prefix: Prefix for output files (e.g., "output" -> "output_1.mp3", "output_2.mp3")
            split_times: List of split points in seconds (e.g., [10.0, 20.0] creates 3 segments)

        Returns:
            List of output file paths

        Raises:
            AudioProcessingError: If splitting fails
        """
        if not Path(input_file).exists():
            raise AudioProcessingError(f"Input file not found: {input_file}")

        if not split_times:
            raise AudioProcessingError("No split times provided")

        # Validate split times are sorted
        if split_times != sorted(split_times):
            raise AudioProcessingError("Split times must be in ascending order")

        logger.info(f"Splitting {input_file} at {len(split_times)} points")

        # Get total duration
        total_duration = AudioProcessor.get_audio_duration(input_file)

        # Create segments: [0 to split_times[0], split_times[0] to split_times[1], ..., split_times[-1] to end]
        segments = []
        output_files = []

        start = 0
        for i, end in enumerate(split_times, 1):
            segments.append((start, end - start, i))
            start = end

        # Add final segment
        segments.append((start, total_duration - start, len(split_times) + 1))

        # Process each segment
        output_dir = Path(output_prefix).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        for start_time, duration, segment_num in segments:
            output_file = f"{output_prefix}_{segment_num}.mp3"

            result = subprocess.run(
                [
                    'ffmpeg',
                    '-i', input_file,
                    '-ss', str(start_time),
                    '-t', str(duration),
                    '-c', 'copy',  # Copy codec (no re-encoding)
                    '-y',
                    output_file
                ],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                raise AudioProcessingError(f"ffmpeg split failed for segment {segment_num}: {result.stderr}")

            output_files.append(output_file)
            logger.debug(f"Created segment {segment_num}: {output_file}")

        logger.info(f"Successfully split into {len(output_files)} segments")
        return output_files

    @staticmethod
    def validate_audio_file(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that a file is a valid audio file.

        Args:
            file_path: Path to audio file

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not Path(file_path).exists():
            return False, f"File not found: {file_path}"

        try:
            result = subprocess.run(
                [
                    'ffprobe',
                    '-v', 'error',
                    '-show_entries', 'format=format_name,duration',
                    '-of', 'default=noprint_wrappers=1',
                    file_path
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return False, f"Invalid audio file: {result.stderr}"

            # Check that we got valid output
            output = result.stdout.strip()
            if not output or 'duration=' not in output:
                return False, "File does not contain valid audio stream"

            return True, None

        except subprocess.TimeoutExpired:
            return False, "Validation timeout"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
