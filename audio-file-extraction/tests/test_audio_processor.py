"""
Integration tests for audio_processor module.

Note: These tests require ffmpeg to be installed.
Some tests use actual audio file operations.
"""

import pytest
import tempfile
import subprocess
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from utils.audio_processor import AudioProcessor, AudioProcessingError


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_audio_file(temp_dir):
    """Create a sample audio file for testing using ffmpeg."""
    output_file = temp_dir / "sample.mp3"

    # Generate 1 second of silence
    subprocess.run([
        'ffmpeg',
        '-f', 'lavfi',
        '-i', 'anullsrc=r=44100:cl=stereo',
        '-t', '1',
        '-q:a', '9',
        '-acodec', 'libmp3lame',
        str(output_file)
    ], capture_output=True, check=True)

    return output_file


@pytest.fixture
def multiple_audio_files(temp_dir):
    """Create multiple sample audio files for concatenation testing."""
    files = []

    for i in range(3):
        output_file = temp_dir / f"sample_{i}.mp3"

        # Generate 0.5 second of silence
        subprocess.run([
            'ffmpeg',
            '-f', 'lavfi',
            '-i', 'anullsrc=r=44100:cl=stereo',
            '-t', '0.5',
            '-q:a', '9',
            '-acodec', 'libmp3lame',
            str(output_file)
        ], capture_output=True, check=True)

        files.append(str(output_file))

    return files


class TestAudioProcessor:
    """Tests for AudioProcessor."""

    def test_check_ffmpeg_installed(self):
        """Test ffmpeg installation check."""
        result = AudioProcessor.check_ffmpeg_installed()
        assert result is True, "ffmpeg must be installed for these tests"

    def test_get_audio_duration(self, sample_audio_file):
        """Test getting audio duration."""
        duration = AudioProcessor.get_audio_duration(str(sample_audio_file))

        # Should be approximately 1 second (allow 0.1s tolerance)
        assert 0.9 <= duration <= 1.1

    def test_get_audio_duration_nonexistent_file(self):
        """Test getting duration of nonexistent file raises error."""
        with pytest.raises(AudioProcessingError, match="not found"):
            AudioProcessor.get_audio_duration("/nonexistent/file.mp3")

    def test_concatenate_audio_files_demuxer(self, multiple_audio_files, temp_dir):
        """Test audio concatenation using concat demuxer."""
        output_file = temp_dir / "concatenated.mp3"

        AudioProcessor.concatenate_audio_files(
            input_files=multiple_audio_files,
            output_file=str(output_file),
            use_concat_demuxer=True
        )

        assert output_file.exists()

        # Check duration is approximately sum of inputs (3 * 0.5 = 1.5s)
        duration = AudioProcessor.get_audio_duration(str(output_file))
        assert 1.4 <= duration <= 1.6

    def test_concatenate_audio_files_filter(self, multiple_audio_files, temp_dir):
        """Test audio concatenation using concat filter."""
        output_file = temp_dir / "concatenated_filter.mp3"

        AudioProcessor.concatenate_audio_files(
            input_files=multiple_audio_files,
            output_file=str(output_file),
            use_concat_demuxer=False
        )

        assert output_file.exists()

        # Check duration is approximately sum of inputs
        duration = AudioProcessor.get_audio_duration(str(output_file))
        assert 1.4 <= duration <= 1.6

    def test_concatenate_empty_input_list(self, temp_dir):
        """Test concatenation with empty input list raises error."""
        with pytest.raises(AudioProcessingError, match="No input files"):
            AudioProcessor.concatenate_audio_files(
                input_files=[],
                output_file=str(temp_dir / "output.mp3")
            )

    def test_concatenate_nonexistent_input(self, temp_dir):
        """Test concatenation with nonexistent input raises error."""
        with pytest.raises(AudioProcessingError, match="not found"):
            AudioProcessor.concatenate_audio_files(
                input_files=["/nonexistent/file.mp3"],
                output_file=str(temp_dir / "output.mp3")
            )

    def test_split_audio_file(self, temp_dir):
        """Test audio splitting."""
        # Create a 3-second audio file
        input_file = temp_dir / "long_sample.mp3"
        subprocess.run([
            'ffmpeg',
            '-f', 'lavfi',
            '-i', 'anullsrc=r=44100:cl=stereo',
            '-t', '3',
            '-q:a', '9',
            '-acodec', 'libmp3lame',
            str(input_file)
        ], capture_output=True, check=True)

        # Split at 1s and 2s (creates 3 segments)
        output_prefix = temp_dir / "split"
        output_files = AudioProcessor.split_audio_file(
            input_file=str(input_file),
            output_prefix=str(output_prefix),
            split_times=[1.0, 2.0]
        )

        assert len(output_files) == 3

        # Check all segments exist
        for file_path in output_files:
            assert Path(file_path).exists()

        # Check durations (approximately 1s each, allow tolerance)
        for file_path in output_files:
            duration = AudioProcessor.get_audio_duration(file_path)
            assert 0.9 <= duration <= 1.1

    def test_split_audio_file_nonexistent(self, temp_dir):
        """Test splitting nonexistent file raises error."""
        with pytest.raises(AudioProcessingError, match="not found"):
            AudioProcessor.split_audio_file(
                input_file="/nonexistent/file.mp3",
                output_prefix=str(temp_dir / "split"),
                split_times=[1.0]
            )

    def test_split_audio_file_empty_times(self, sample_audio_file, temp_dir):
        """Test splitting with empty times raises error."""
        with pytest.raises(AudioProcessingError, match="No split times"):
            AudioProcessor.split_audio_file(
                input_file=str(sample_audio_file),
                output_prefix=str(temp_dir / "split"),
                split_times=[]
            )

    def test_split_audio_file_unsorted_times(self, sample_audio_file, temp_dir):
        """Test splitting with unsorted times raises error."""
        with pytest.raises(AudioProcessingError, match="ascending order"):
            AudioProcessor.split_audio_file(
                input_file=str(sample_audio_file),
                output_prefix=str(temp_dir / "split"),
                split_times=[2.0, 1.0]
            )

    def test_validate_audio_file_valid(self, sample_audio_file):
        """Test validation of valid audio file."""
        is_valid, error = AudioProcessor.validate_audio_file(str(sample_audio_file))

        assert is_valid is True
        assert error is None

    def test_validate_audio_file_nonexistent(self):
        """Test validation of nonexistent file."""
        is_valid, error = AudioProcessor.validate_audio_file("/nonexistent/file.mp3")

        assert is_valid is False
        assert "not found" in error

    def test_validate_audio_file_invalid(self, temp_dir):
        """Test validation of invalid audio file."""
        # Create a non-audio file
        invalid_file = temp_dir / "invalid.mp3"
        invalid_file.write_text("This is not audio data")

        is_valid, error = AudioProcessor.validate_audio_file(str(invalid_file))

        assert is_valid is False
        assert error is not None

    def test_concatenate_creates_output_directory(self, multiple_audio_files, temp_dir):
        """Test that concatenation creates output directory if needed."""
        output_dir = temp_dir / "nested" / "output"
        output_file = output_dir / "concatenated.mp3"

        AudioProcessor.concatenate_audio_files(
            input_files=multiple_audio_files,
            output_file=str(output_file),
            use_concat_demuxer=True
        )

        assert output_file.exists()
        assert output_dir.exists()


@pytest.mark.slow
class TestAudioProcessorPerformance:
    """Performance tests for AudioProcessor (marked slow)."""

    def test_concatenate_many_files(self, temp_dir):
        """Test concatenating many files."""
        # Create 10 short audio files
        files = []
        for i in range(10):
            output_file = temp_dir / f"sample_{i}.mp3"
            subprocess.run([
                'ffmpeg',
                '-f', 'lavfi',
                '-i', 'anullsrc=r=44100:cl=stereo',
                '-t', '0.1',
                '-q:a', '9',
                '-acodec', 'libmp3lame',
                str(output_file)
            ], capture_output=True, check=True)
            files.append(str(output_file))

        output_file = temp_dir / "many_concatenated.mp3"

        # Should complete without error
        AudioProcessor.concatenate_audio_files(
            input_files=files,
            output_file=str(output_file),
            use_concat_demuxer=True
        )

        assert output_file.exists()

        # Check duration is approximately sum of inputs (10 * 0.1 = 1s)
        duration = AudioProcessor.get_audio_duration(str(output_file))
        assert 0.9 <= duration <= 1.1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
