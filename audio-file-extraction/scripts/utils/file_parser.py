"""
File Parser Module

Parses and validates TOEFL audio filenames according to naming conventions.
Supports patterns like:
- TOEFL-Speaking-Conversation-Q1-v1-conversation.mp3
- TOEFL-Speaking-Listen-and-Choose-Q1-v1.mp3
"""

import re
from dataclasses import dataclass
from typing import Optional, Tuple
from pathlib import Path


@dataclass
class TOEFLFileInfo:
    """Structured information extracted from TOEFL audio filename."""

    test_type: str  # e.g., "Speaking"
    task_type: str  # e.g., "Conversation", "Listen-and-Choose"
    question_num: int  # e.g., 1
    version: int  # e.g., 1
    suffix: Optional[str]  # e.g., "conversation", None
    original_filename: str

    @property
    def is_conversation(self) -> bool:
        """Check if this is a conversation file."""
        return self.task_type.lower() == "conversation"

    @property
    def is_listen_and_choose(self) -> bool:
        """Check if this is a Listen and Choose file."""
        return "listen" in self.task_type.lower() and "choose" in self.task_type.lower()

    @property
    def base_name(self) -> str:
        """Get base name without suffix."""
        parts = [
            "TOEFL",
            self.test_type,
            self.task_type,
            f"Q{self.question_num}",
            f"v{self.version}"
        ]
        return "-".join(parts)

    def __str__(self) -> str:
        return f"{self.base_name} (suffix: {self.suffix})"


class TOEFLFileParser:
    """Parser for TOEFL audio filenames."""

    # Pattern: TOEFL-{TestType}-{TaskType}-Q{N}-v{N}[-{suffix}].mp3
    FILENAME_PATTERN = re.compile(
        r'^TOEFL-'
        r'(?P<test_type>[A-Za-z]+)-'
        r'(?P<task_type>[A-Za-z\-]+?)-'
        r'Q(?P<question>\d+)-'
        r'v(?P<version>\d+)'
        r'(?:-(?P<suffix>[a-z]+))?'
        r'\.mp3$',
        re.IGNORECASE
    )

    @classmethod
    def parse(cls, filename: str) -> Optional[TOEFLFileInfo]:
        """
        Parse a TOEFL audio filename.

        Args:
            filename: Filename to parse (with or without path)

        Returns:
            TOEFLFileInfo if valid, None if invalid
        """
        # Extract filename from path if needed
        filename = Path(filename).name

        match = cls.FILENAME_PATTERN.match(filename)
        if not match:
            return None

        groups = match.groupdict()

        return TOEFLFileInfo(
            test_type=groups['test_type'],
            task_type=groups['task_type'],
            question_num=int(groups['question']),
            version=int(groups['version']),
            suffix=groups.get('suffix'),
            original_filename=filename
        )

    @classmethod
    def is_valid(cls, filename: str) -> bool:
        """
        Check if filename matches TOEFL naming pattern.

        Args:
            filename: Filename to validate

        Returns:
            True if valid, False otherwise
        """
        return cls.parse(filename) is not None

    @classmethod
    def extract_components(cls, filename: str) -> Optional[Tuple[str, str, int, int, Optional[str]]]:
        """
        Extract components from filename as tuple.

        Args:
            filename: Filename to parse

        Returns:
            Tuple of (test_type, task_type, question_num, version, suffix) or None
        """
        info = cls.parse(filename)
        if info is None:
            return None

        return (
            info.test_type,
            info.task_type,
            info.question_num,
            info.version,
            info.suffix
        )

    @classmethod
    def filter_conversation_files(cls, filenames: list[str]) -> list[str]:
        """
        Filter list to only conversation files.

        Args:
            filenames: List of filenames to filter

        Returns:
            List of conversation filenames
        """
        result = []
        for filename in filenames:
            info = cls.parse(filename)
            if info and info.is_conversation:
                result.append(filename)
        return result

    @classmethod
    def filter_listen_and_choose_files(cls, filenames: list[str]) -> list[str]:
        """
        Filter list to only Listen and Choose files.

        Args:
            filenames: List of filenames to filter

        Returns:
            List of Listen and Choose filenames
        """
        result = []
        for filename in filenames:
            info = cls.parse(filename)
            if info and info.is_listen_and_choose:
                result.append(filename)
        return result

    @classmethod
    def group_by_base_name(cls, filenames: list[str]) -> dict[str, list[str]]:
        """
        Group files by their base name (without suffix).

        Args:
            filenames: List of filenames to group

        Returns:
            Dictionary mapping base names to lists of filenames
        """
        groups = {}
        for filename in filenames:
            info = cls.parse(filename)
            if info:
                base = info.base_name
                if base not in groups:
                    groups[base] = []
                groups[base].append(filename)
        return groups
