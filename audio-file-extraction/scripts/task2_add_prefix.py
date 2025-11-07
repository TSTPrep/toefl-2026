#!/usr/bin/env python3
"""
Task 2: Add Narrator Prefix to Conversation Files

This script:
1. Lists all conversation files from Google Drive
2. Downloads narrator files (Daniel/Matilda)
3. Applies alphabetical sorting for deterministic 50/50 narrator rotation
4. Concatenates narrator prefix with conversation file using ffmpeg concat demuxer
5. Uploads updated files to Drive (version management - updates existing files)
6. Generates processing report

Usage:
    python task2_add_prefix.py [--dry-run] [--limit N]
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import argparse
from dotenv import load_dotenv
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.drive_manager import GoogleDriveManager, DriveManagerError
from utils.audio_processor import AudioProcessor, AudioProcessingError
from utils.file_parser import TOEFLFileParser, TOEFLFileInfo
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

logger = setup_logger(__name__, level=os.getenv('LOG_LEVEL', 'INFO'))


class Task2Processor:
    """Processes conversation files by adding narrator prefixes."""

    def __init__(self, dry_run: bool = False):
        """
        Initialize Task 2 processor.

        Args:
            dry_run: If True, simulate processing without uploading
        """
        self.dry_run = dry_run
        self.temp_dir = Path(os.getenv('TEMP_DIR', 'data/temp'))
        self.processed_dir = Path(os.getenv('PROCESSED_DIR', 'data/processed'))

        # Create directories
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        # Initialize managers
        self.drive_manager = GoogleDriveManager()
        self.audio_processor = AudioProcessor()

        # Check ffmpeg
        if not self.audio_processor.check_ffmpeg_installed():
            raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

        # Narrator file IDs
        self.narrator_files = {
            'daniel': os.getenv('NARRATOR_DANIEL_FILE_ID'),
            'matilda': os.getenv('NARRATOR_MATILDA_FILE_ID')
        }

        if not all(self.narrator_files.values()):
            raise ValueError("Narrator file IDs not set in environment variables")

        self.narrator_paths = {}
        self.processing_stats = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0
        }

    def download_narrator_files(self) -> None:
        """Download narrator prefix files to temp directory."""
        logger.info("Downloading narrator files...")

        for narrator, file_id in self.narrator_files.items():
            output_path = self.temp_dir / f"narrator_{narrator}.mp3"

            if output_path.exists():
                logger.info(f"Narrator file already exists: {output_path}")
            else:
                try:
                    self.drive_manager.download_file(
                        file_id=file_id,
                        output_path=str(output_path),
                        show_progress=True
                    )
                except DriveManagerError as e:
                    logger.error(f"Failed to download {narrator} narrator file: {e}")
                    raise

            self.narrator_paths[narrator] = output_path

        logger.info(f"Narrator files ready: {list(self.narrator_paths.keys())}")

    def get_conversation_files(self) -> List[Dict]:
        """
        Get all conversation files from Drive.

        Returns:
            List of file metadata dictionaries
        """
        logger.info("Listing conversation files from Drive...")

        # Query for audio files containing "conversation"
        query = "name contains 'conversation' and mimeType = 'audio/mpeg'"

        files = []
        for file in self.drive_manager.list_files(query=query, order_by='name'):
            # Validate filename format
            file_info = TOEFLFileParser.parse(file['name'])
            if file_info and file_info.is_conversation:
                files.append(file)
            else:
                logger.warning(f"Skipping invalid conversation filename: {file['name']}")

        logger.info(f"Found {len(files)} valid conversation files")
        return files

    def assign_narrators(self, files: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Assign narrators to files using alphabetical sorting for 50/50 rotation.

        Args:
            files: List of file metadata

        Returns:
            Dictionary mapping narrator to list of files
        """
        # Sort files alphabetically by name
        sorted_files = sorted(files, key=lambda f: f['name'])

        # Assign alternating narrators
        assignments = {'daniel': [], 'matilda': []}
        narrators = ['daniel', 'matilda']

        for i, file in enumerate(sorted_files):
            narrator = narrators[i % 2]
            assignments[narrator].append(file)

        logger.info(f"Narrator assignments: Daniel={len(assignments['daniel'])}, "
                   f"Matilda={len(assignments['matilda'])}")

        return assignments

    def process_file(
        self,
        file: Dict,
        narrator: str
    ) -> Tuple[bool, str]:
        """
        Process a single conversation file.

        Args:
            file: File metadata from Drive
            narrator: Narrator to use ('daniel' or 'matilda')

        Returns:
            Tuple of (success, message)
        """
        file_name = file['name']
        file_id = file['id']

        try:
            # Download conversation file
            conversation_path = self.temp_dir / file_name
            logger.info(f"Downloading {file_name}...")

            self.drive_manager.download_file(
                file_id=file_id,
                output_path=str(conversation_path),
                show_progress=False
            )

            # Prepare output path
            output_path = self.processed_dir / file_name

            # Concatenate narrator + conversation
            narrator_path = self.narrator_paths[narrator]
            logger.info(f"Concatenating {narrator} narrator + {file_name}...")

            self.audio_processor.concatenate_audio_files(
                input_files=[str(narrator_path), str(conversation_path)],
                output_file=str(output_path),
                use_concat_demuxer=True
            )

            # Validate output
            is_valid, error = self.audio_processor.validate_audio_file(str(output_path))
            if not is_valid:
                return False, f"Output validation failed: {error}"

            # Upload to Drive (update existing file)
            if not self.dry_run:
                logger.info(f"Uploading {file_name} to Drive...")
                self.drive_manager.upload_file(
                    file_path=str(output_path),
                    mime_type='audio/mpeg',
                    update_existing=True
                )

            # Clean up temp files
            conversation_path.unlink()
            output_path.unlink()

            return True, f"Successfully processed with {narrator} narrator"

        except (DriveManagerError, AudioProcessingError) as e:
            logger.error(f"Error processing {file_name}: {e}")
            return False, str(e)

        except Exception as e:
            logger.error(f"Unexpected error processing {file_name}: {e}")
            return False, f"Unexpected error: {e}"

    def process_all_files(self, limit: Optional[int] = None) -> None:
        """
        Process all conversation files.

        Args:
            limit: Optional limit on number of files to process (for testing)
        """
        # Download narrator files
        self.download_narrator_files()

        # Get conversation files
        files = self.get_conversation_files()

        if limit:
            files = files[:limit]
            logger.info(f"Limited to {limit} files for processing")

        self.processing_stats['total'] = len(files)

        # Assign narrators
        assignments = self.assign_narrators(files)

        # Process files
        logger.info(f"Processing {len(files)} files...")

        results = []

        for narrator, narrator_files in assignments.items():
            logger.info(f"\nProcessing {len(narrator_files)} files with {narrator} narrator")

            for file in tqdm(narrator_files, desc=f"Processing ({narrator})"):
                success, message = self.process_file(file, narrator)

                if success:
                    self.processing_stats['successful'] += 1
                else:
                    self.processing_stats['failed'] += 1

                results.append({
                    'file': file['name'],
                    'narrator': narrator,
                    'success': success,
                    'message': message
                })

        # Generate report
        self.generate_report(results)

    def generate_report(self, results: List[Dict]) -> None:
        """
        Generate processing report.

        Args:
            results: List of processing results
        """
        report_path = self.processed_dir / 'task2_processing_report.txt'

        logger.info("\n" + "="*80)
        logger.info("PROCESSING REPORT")
        logger.info("="*80)

        with open(report_path, 'w') as f:
            # Summary
            summary = f"""
Task 2: Add Narrator Prefix to Conversation Files
===================================================

Total files: {self.processing_stats['total']}
Successful: {self.processing_stats['successful']}
Failed: {self.processing_stats['failed']}
Skipped: {self.processing_stats['skipped']}

Mode: {'DRY RUN' if self.dry_run else 'LIVE'}

Detailed Results:
-----------------
"""
            print(summary)
            f.write(summary)

            # Detailed results
            for result in results:
                status = "✓" if result['success'] else "✗"
                line = f"{status} {result['file']} ({result['narrator']}): {result['message']}\n"
                print(line, end='')
                f.write(line)

        logger.info(f"\nReport saved to: {report_path}")
        logger.info("="*80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Task 2: Add narrator prefix to conversation files'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate processing without uploading to Drive'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of files to process (for testing)'
    )

    args = parser.parse_args()

    try:
        processor = Task2Processor(dry_run=args.dry_run)
        processor.process_all_files(limit=args.limit)

        logger.info("\nTask 2 completed successfully!")

    except Exception as e:
        logger.error(f"Task 2 failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
