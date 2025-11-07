"""
Unit tests for file_parser module.
"""

import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from utils.file_parser import TOEFLFileParser, TOEFLFileInfo


class TestTOEFLFileParser:
    """Tests for TOEFL file parser."""

    # Valid filenames
    valid_conversation = "TOEFL-Speaking-Conversation-Q1-v1-conversation.mp3"
    valid_listen_choose = "TOEFL-Speaking-Listen-and-Choose-Q1-v1.mp3"
    valid_no_suffix = "TOEFL-Reading-Passage-Q5-v2.mp3"

    # Invalid filenames
    invalid_no_prefix = "Speaking-Conversation-Q1-v1.mp3"
    invalid_no_question = "TOEFL-Speaking-Conversation-v1.mp3"
    invalid_no_version = "TOEFL-Speaking-Conversation-Q1.mp3"
    invalid_extension = "TOEFL-Speaking-Conversation-Q1-v1.wav"

    def test_parse_valid_conversation(self):
        """Test parsing valid conversation filename."""
        result = TOEFLFileParser.parse(self.valid_conversation)

        assert result is not None
        assert result.test_type == "Speaking"
        assert result.task_type == "Conversation"
        assert result.question_num == 1
        assert result.version == 1
        assert result.suffix == "conversation"
        assert result.original_filename == self.valid_conversation

    def test_parse_valid_listen_choose(self):
        """Test parsing valid Listen and Choose filename."""
        result = TOEFLFileParser.parse(self.valid_listen_choose)

        assert result is not None
        assert result.test_type == "Speaking"
        assert result.task_type == "Listen-and-Choose"
        assert result.question_num == 1
        assert result.version == 1
        assert result.suffix is None

    def test_parse_valid_no_suffix(self):
        """Test parsing valid filename without suffix."""
        result = TOEFLFileParser.parse(self.valid_no_suffix)

        assert result is not None
        assert result.test_type == "Reading"
        assert result.task_type == "Passage"
        assert result.question_num == 5
        assert result.version == 2
        assert result.suffix is None

    def test_parse_invalid_filenames(self):
        """Test parsing invalid filenames returns None."""
        assert TOEFLFileParser.parse(self.invalid_no_prefix) is None
        assert TOEFLFileParser.parse(self.invalid_no_question) is None
        assert TOEFLFileParser.parse(self.invalid_no_version) is None
        assert TOEFLFileParser.parse(self.invalid_extension) is None

    def test_parse_with_path(self):
        """Test parsing filename with path."""
        path = "/path/to/" + self.valid_conversation
        result = TOEFLFileParser.parse(path)

        assert result is not None
        assert result.original_filename == self.valid_conversation

    def test_is_valid(self):
        """Test is_valid method."""
        assert TOEFLFileParser.is_valid(self.valid_conversation) is True
        assert TOEFLFileParser.is_valid(self.valid_listen_choose) is True
        assert TOEFLFileParser.is_valid(self.invalid_no_prefix) is False

    def test_is_conversation_property(self):
        """Test is_conversation property."""
        conv_info = TOEFLFileParser.parse(self.valid_conversation)
        listen_info = TOEFLFileParser.parse(self.valid_listen_choose)

        assert conv_info.is_conversation is True
        assert listen_info.is_conversation is False

    def test_is_listen_and_choose_property(self):
        """Test is_listen_and_choose property."""
        conv_info = TOEFLFileParser.parse(self.valid_conversation)
        listen_info = TOEFLFileParser.parse(self.valid_listen_choose)

        assert conv_info.is_listen_and_choose is False
        assert listen_info.is_listen_and_choose is True

    def test_base_name_property(self):
        """Test base_name property."""
        result = TOEFLFileParser.parse(self.valid_conversation)
        expected = "TOEFL-Speaking-Conversation-Q1-v1"

        assert result.base_name == expected

    def test_extract_components(self):
        """Test extract_components method."""
        components = TOEFLFileParser.extract_components(self.valid_conversation)

        assert components is not None
        assert components[0] == "Speaking"
        assert components[1] == "Conversation"
        assert components[2] == 1
        assert components[3] == 1
        assert components[4] == "conversation"

    def test_filter_conversation_files(self):
        """Test filter_conversation_files method."""
        filenames = [
            self.valid_conversation,
            self.valid_listen_choose,
            self.valid_no_suffix,
            "TOEFL-Speaking-Conversation-Q2-v1-conversation.mp3",
        ]

        result = TOEFLFileParser.filter_conversation_files(filenames)

        assert len(result) == 2
        assert self.valid_conversation in result
        assert self.valid_listen_choose not in result

    def test_filter_listen_and_choose_files(self):
        """Test filter_listen_and_choose_files method."""
        filenames = [
            self.valid_conversation,
            self.valid_listen_choose,
            "TOEFL-Speaking-Listen-and-Choose-Q2-v1.mp3",
        ]

        result = TOEFLFileParser.filter_listen_and_choose_files(filenames)

        assert len(result) == 2
        assert self.valid_listen_choose in result
        assert self.valid_conversation not in result

    def test_group_by_base_name(self):
        """Test group_by_base_name method."""
        filenames = [
            "TOEFL-Speaking-Conversation-Q1-v1-conversation.mp3",
            "TOEFL-Speaking-Conversation-Q1-v1-response.mp3",
            "TOEFL-Speaking-Conversation-Q2-v1-conversation.mp3",
        ]

        result = TOEFLFileParser.group_by_base_name(filenames)

        assert len(result) == 2
        assert "TOEFL-Speaking-Conversation-Q1-v1" in result
        assert len(result["TOEFL-Speaking-Conversation-Q1-v1"]) == 2

    def test_case_insensitivity(self):
        """Test that parsing is case-insensitive."""
        lowercase = "toefl-speaking-conversation-q1-v1-conversation.mp3"
        uppercase = "TOEFL-SPEAKING-CONVERSATION-Q1-V1-CONVERSATION.MP3"

        result_lower = TOEFLFileParser.parse(lowercase)
        result_upper = TOEFLFileParser.parse(uppercase)

        assert result_lower is not None
        assert result_upper is not None
        assert result_lower.test_type.lower() == result_upper.test_type.lower()

    def test_various_question_numbers(self):
        """Test parsing with various question numbers."""
        for q_num in [1, 5, 10, 99]:
            filename = f"TOEFL-Speaking-Conversation-Q{q_num}-v1.mp3"
            result = TOEFLFileParser.parse(filename)

            assert result is not None
            assert result.question_num == q_num

    def test_various_version_numbers(self):
        """Test parsing with various version numbers."""
        for version in [1, 5, 10, 99]:
            filename = f"TOEFL-Speaking-Conversation-Q1-v{version}.mp3"
            result = TOEFLFileParser.parse(filename)

            assert result is not None
            assert result.version == version


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
