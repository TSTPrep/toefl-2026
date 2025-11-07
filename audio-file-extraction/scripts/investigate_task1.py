#!/usr/bin/env python3
"""
Task 1: Investigate "Listen and Choose" Files

This script searches for and analyzes "Listen and Choose" files to determine:
1. How many such files exist
2. Their naming patterns
3. Audio characteristics (duration, format)
4. Whether they need splitting and how

Usage:
    python investigate_task1.py [--download-samples N]
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
import argparse
from dotenv import load_dotenv
from tqdm import tqdm
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.drive_manager import GoogleDriveManager, DriveManagerError
from utils.audio_processor import AudioProcessor, AudioProcessingError
from utils.file_parser import TOEFLFileParser, TOEFLFileInfo
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

logger = setup_logger(__name__, level=os.getenv('LOG_LEVEL', 'INFO'))


class Task1Investigator:
    """Investigates Listen and Choose files for Task 1 implementation."""

    def __init__(self):
        """Initialize Task 1 investigator."""
        self.temp_dir = Path(os.getenv('TEMP_DIR', 'data/temp'))
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Initialize managers
        self.drive_manager = GoogleDriveManager()
        self.audio_processor = AudioProcessor()

        # Check ffmpeg
        if not self.audio_processor.check_ffmpeg_installed():
            raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

        self.findings = {
            'total_files': 0,
            'files': [],
            'naming_patterns': {},
            'audio_analysis': []
        }

    def search_listen_and_choose_files(self) -> List[Dict]:
        """
        Search for all "Listen and Choose" files.

        Returns:
            List of file metadata dictionaries
        """
        logger.info("Searching for 'Listen and Choose' files...")

        # Search for files containing "Listen" or "Choose"
        search_terms = ['Listen', 'Choose', 'listen', 'choose']
        all_files = []

        for term in search_terms:
            query = f"name contains '{term}' and mimeType = 'audio/mpeg'"

            for file in self.drive_manager.list_files(query=query, order_by='name'):
                # Avoid duplicates
                if not any(f['id'] == file['id'] for f in all_files):
                    all_files.append(file)

        # Filter to only valid Listen and Choose files
        listen_choose_files = []

        for file in all_files:
            file_info = TOEFLFileParser.parse(file['name'])
            if file_info and file_info.is_listen_and_choose:
                listen_choose_files.append(file)
            else:
                # Log files that contain search terms but don't match pattern
                if any(term.lower() in file['name'].lower() for term in search_terms):
                    logger.debug(f"Found file with search term but not Listen-and-Choose pattern: {file['name']}")

        logger.info(f"Found {len(listen_choose_files)} valid 'Listen and Choose' files")

        self.findings['total_files'] = len(listen_choose_files)
        self.findings['files'] = listen_choose_files

        return listen_choose_files

    def analyze_naming_patterns(self, files: List[Dict]) -> None:
        """
        Analyze naming patterns in files.

        Args:
            files: List of file metadata
        """
        logger.info("Analyzing naming patterns...")

        patterns = {}

        for file in files:
            file_info = TOEFLFileParser.parse(file['name'])
            if file_info:
                # Track task types
                task_type = file_info.task_type
                if task_type not in patterns:
                    patterns[task_type] = {
                        'count': 0,
                        'examples': [],
                        'has_suffix': 0,
                        'no_suffix': 0
                    }

                patterns[task_type]['count'] += 1

                if len(patterns[task_type]['examples']) < 5:
                    patterns[task_type]['examples'].append(file['name'])

                if file_info.suffix:
                    patterns[task_type]['has_suffix'] += 1
                else:
                    patterns[task_type]['no_suffix'] += 1

        self.findings['naming_patterns'] = patterns

        logger.info(f"Found {len(patterns)} distinct naming patterns")
        for pattern, data in patterns.items():
            logger.info(f"  {pattern}: {data['count']} files "
                       f"(suffix: {data['has_suffix']}, no suffix: {data['no_suffix']})")

    def analyze_audio_samples(
        self,
        files: List[Dict],
        sample_count: int = 5
    ) -> None:
        """
        Download and analyze audio samples.

        Args:
            files: List of file metadata
            sample_count: Number of samples to download and analyze
        """
        logger.info(f"Analyzing {sample_count} audio samples...")

        # Select samples (evenly distributed)
        if len(files) <= sample_count:
            samples = files
        else:
            step = len(files) // sample_count
            samples = [files[i * step] for i in range(sample_count)]

        audio_analysis = []

        for file in tqdm(samples, desc="Analyzing samples"):
            file_name = file['name']
            file_id = file['id']

            try:
                # Download file
                sample_path = self.temp_dir / f"sample_{file_name}"

                self.drive_manager.download_file(
                    file_id=file_id,
                    output_path=str(sample_path),
                    show_progress=False
                )

                # Get audio properties
                duration = self.audio_processor.get_audio_duration(str(sample_path))
                is_valid, error = self.audio_processor.validate_audio_file(str(sample_path))

                file_size = sample_path.stat().st_size

                analysis = {
                    'file_name': file_name,
                    'file_id': file_id,
                    'duration_seconds': round(duration, 2),
                    'file_size_mb': round(file_size / (1024 * 1024), 2),
                    'is_valid': is_valid,
                    'error': error
                }

                audio_analysis.append(analysis)

                logger.debug(f"{file_name}: {duration:.1f}s, {file_size / (1024 * 1024):.1f}MB")

                # Clean up sample
                sample_path.unlink()

            except (DriveManagerError, AudioProcessingError) as e:
                logger.error(f"Error analyzing {file_name}: {e}")
                audio_analysis.append({
                    'file_name': file_name,
                    'file_id': file_id,
                    'error': str(e)
                })

        self.findings['audio_analysis'] = audio_analysis

    def generate_report(self) -> None:
        """Generate investigation report."""
        report_path = self.temp_dir.parent / 'task1_investigation_report.txt'
        json_path = self.temp_dir.parent / 'task1_investigation_report.json'

        logger.info("\n" + "="*80)
        logger.info("TASK 1 INVESTIGATION REPORT")
        logger.info("="*80)

        # Text report
        with open(report_path, 'w') as f:
            report = f"""
Task 1: Listen and Choose Files Investigation
==============================================

SUMMARY
-------
Total files found: {self.findings['total_files']}

NAMING PATTERNS
---------------
"""
            print(report)
            f.write(report)

            for pattern, data in self.findings['naming_patterns'].items():
                section = f"""
Pattern: {pattern}
  Count: {data['count']}
  With suffix: {data['has_suffix']}
  Without suffix: {data['no_suffix']}
  Examples:
"""
                print(section)
                f.write(section)

                for example in data['examples']:
                    line = f"    - {example}\n"
                    print(line, end='')
                    f.write(line)

            # Audio analysis
            if self.findings['audio_analysis']:
                audio_section = "\nAUDIO ANALYSIS\n--------------\n"
                print(audio_section)
                f.write(audio_section)

                durations = [a['duration_seconds'] for a in self.findings['audio_analysis']
                           if 'duration_seconds' in a]

                if durations:
                    avg_duration = sum(durations) / len(durations)
                    min_duration = min(durations)
                    max_duration = max(durations)

                    stats = f"""
Sample count: {len(self.findings['audio_analysis'])}
Average duration: {avg_duration:.1f}s
Min duration: {min_duration:.1f}s
Max duration: {max_duration:.1f}s

Individual samples:
"""
                    print(stats)
                    f.write(stats)

                    for analysis in self.findings['audio_analysis']:
                        if 'duration_seconds' in analysis:
                            line = (f"  {analysis['file_name']}: "
                                  f"{analysis['duration_seconds']}s, "
                                  f"{analysis['file_size_mb']}MB\n")
                            print(line, end='')
                            f.write(line)

            # Recommendations
            recommendations = """

RECOMMENDATIONS FOR TASK 1 IMPLEMENTATION
-----------------------------------------
"""
            print(recommendations)
            f.write(recommendations)

            if self.findings['total_files'] == 0:
                rec = "No 'Listen and Choose' files found. Task 1 may not be applicable.\n"
            else:
                rec = f"""
1. Review the {self.findings['total_files']} files found
2. Determine if files need splitting based on audio analysis
3. If splitting is needed, analyze audio content to identify split points
4. Consider whether suffixes indicate separate segments
5. Implement splitting logic based on findings

Next steps:
- Listen to sample files manually to understand content structure
- Determine if split points are at fixed intervals or need detection
- Design splitting strategy (fixed time intervals vs content-based)
"""
            print(rec)
            f.write(rec)

        # JSON report (for programmatic access)
        with open(json_path, 'w') as f:
            json.dump(self.findings, f, indent=2)

        logger.info(f"\nText report saved to: {report_path}")
        logger.info(f"JSON report saved to: {json_path}")
        logger.info("="*80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Task 1: Investigate Listen and Choose files'
    )
    parser.add_argument(
        '--download-samples',
        type=int,
        default=5,
        help='Number of sample files to download and analyze (default: 5)'
    )

    args = parser.parse_args()

    try:
        investigator = Task1Investigator()

        # Search for files
        files = investigator.search_listen_and_choose_files()

        if not files:
            logger.warning("No 'Listen and Choose' files found. Exiting.")
            investigator.generate_report()
            return

        # Analyze patterns
        investigator.analyze_naming_patterns(files)

        # Analyze audio samples
        if args.download_samples > 0:
            investigator.analyze_audio_samples(files, args.download_samples)

        # Generate report
        investigator.generate_report()

        logger.info("\nTask 1 investigation completed successfully!")

    except Exception as e:
        logger.error(f"Task 1 investigation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
