"""
Mock tests for drive_manager module.

These tests use mocking to avoid actual Google Drive API calls.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
from pathlib import Path
import sys
import io

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from utils.drive_manager import GoogleDriveManager, DriveManagerError


@pytest.fixture
def mock_credentials():
    """Mock Google credentials."""
    with patch('utils.drive_manager.Credentials') as mock_creds:
        creds = Mock()
        creds.valid = True
        creds.expired = False
        mock_creds.return_value = creds
        yield creds


@pytest.fixture
def mock_drive_service():
    """Mock Google Drive service."""
    with patch('utils.drive_manager.build') as mock_build:
        service = Mock()
        mock_build.return_value = service
        yield service


@pytest.fixture
def drive_manager(mock_credentials, mock_drive_service):
    """Create DriveManager with mocked dependencies."""
    with patch('utils.drive_manager.Path.exists', return_value=True), \
         patch('builtins.open', mock_open()), \
         patch('pickle.load', return_value=mock_credentials):

        manager = GoogleDriveManager(
            credentials_file='credentials.json',
            token_file='token.json',
            folder_id='test_folder_id'
        )
        manager.service = mock_drive_service

        return manager


class TestGoogleDriveManager:
    """Tests for GoogleDriveManager."""

    def test_initialization(self, drive_manager):
        """Test successful initialization."""
        assert drive_manager.default_folder_id == 'test_folder_id'
        assert drive_manager.service is not None

    def test_list_files(self, drive_manager, mock_drive_service):
        """Test listing files."""
        # Mock API response
        mock_response = {
            'files': [
                {'id': 'file1', 'name': 'test1.mp3'},
                {'id': 'file2', 'name': 'test2.mp3'}
            ],
            'nextPageToken': None
        }

        mock_drive_service.files().list().execute.return_value = mock_response

        # List files
        files = list(drive_manager.list_files())

        assert len(files) == 2
        assert files[0]['name'] == 'test1.mp3'
        assert files[1]['name'] == 'test2.mp3'

    def test_list_files_pagination(self, drive_manager, mock_drive_service):
        """Test listing files with pagination."""
        # Mock API responses for two pages
        mock_response_page1 = {
            'files': [{'id': 'file1', 'name': 'test1.mp3'}],
            'nextPageToken': 'token123'
        }
        mock_response_page2 = {
            'files': [{'id': 'file2', 'name': 'test2.mp3'}],
            'nextPageToken': None
        }

        mock_list = mock_drive_service.files().list
        mock_list().execute.side_effect = [mock_response_page1, mock_response_page2]

        # List files
        files = list(drive_manager.list_files())

        assert len(files) == 2
        assert mock_list().execute.call_count == 2

    def test_list_files_no_folder_id(self):
        """Test listing files without folder_id raises error."""
        with patch('utils.drive_manager.Path.exists', return_value=True), \
             patch('builtins.open', mock_open()), \
             patch('pickle.load'):

            manager = GoogleDriveManager(
                credentials_file='credentials.json',
                token_file='token.json'
            )

            with pytest.raises(DriveManagerError, match="No folder_id"):
                list(manager.list_files())

    def test_search_files(self, drive_manager, mock_drive_service):
        """Test searching files."""
        mock_response = {
            'files': [{'id': 'file1', 'name': 'conversation.mp3'}],
            'nextPageToken': None
        }

        mock_drive_service.files().list().execute.return_value = mock_response

        # Search files
        files = drive_manager.search_files(name_pattern='conversation')

        assert len(files) == 1
        assert files[0]['name'] == 'conversation.mp3'

    def test_download_file(self, drive_manager, mock_drive_service, tmp_path):
        """Test downloading a file."""
        # Mock file metadata
        mock_metadata = {'name': 'test.mp3', 'size': '1024'}
        mock_drive_service.files().get().execute.return_value = mock_metadata

        # Mock download
        mock_request = Mock()
        mock_drive_service.files().get_media.return_value = mock_request

        output_path = tmp_path / "downloaded.mp3"

        with patch('utils.drive_manager.MediaIoBaseDownload') as mock_download:
            # Mock download progress
            mock_downloader = Mock()
            mock_downloader.next_chunk.return_value = (None, True)
            mock_download.return_value = mock_downloader

            with patch('io.FileIO'):
                drive_manager.download_file(
                    file_id='test_file_id',
                    output_path=str(output_path)
                )

            # Verify download was attempted
            mock_drive_service.files().get_media.assert_called_once_with(fileId='test_file_id')

    def test_upload_file_new(self, drive_manager, mock_drive_service, tmp_path):
        """Test uploading a new file."""
        # Create a test file
        test_file = tmp_path / "test.mp3"
        test_file.write_text("test audio data")

        # Mock search returns no existing file
        mock_drive_service.files().list().execute.return_value = {
            'files': [],
            'nextPageToken': None
        }

        # Mock upload response
        mock_upload_response = {
            'id': 'new_file_id',
            'name': 'test.mp3',
            'version': 1
        }
        mock_drive_service.files().create().execute.return_value = mock_upload_response

        with patch('utils.drive_manager.MediaFileUpload'):
            result = drive_manager.upload_file(
                file_path=str(test_file),
                mime_type='audio/mpeg'
            )

        assert result['id'] == 'new_file_id'
        mock_drive_service.files().create.assert_called_once()

    def test_upload_file_update_existing(self, drive_manager, mock_drive_service, tmp_path):
        """Test uploading updates existing file."""
        # Create a test file
        test_file = tmp_path / "test.mp3"
        test_file.write_text("test audio data")

        # Mock search returns existing file
        mock_drive_service.files().list().execute.return_value = {
            'files': [{'id': 'existing_file_id', 'name': 'test.mp3'}],
            'nextPageToken': None
        }

        # Mock update response
        mock_update_response = {
            'id': 'existing_file_id',
            'name': 'test.mp3',
            'version': 2
        }
        mock_drive_service.files().update().execute.return_value = mock_update_response

        with patch('utils.drive_manager.MediaFileUpload'):
            result = drive_manager.upload_file(
                file_path=str(test_file),
                mime_type='audio/mpeg',
                update_existing=True
            )

        assert result['id'] == 'existing_file_id'
        assert result['version'] == 2
        mock_drive_service.files().update.assert_called_once()

    def test_upload_file_nonexistent(self, drive_manager):
        """Test uploading nonexistent file raises error."""
        with pytest.raises(DriveManagerError, match="not found"):
            drive_manager.upload_file(
                file_path="/nonexistent/file.mp3"
            )

    def test_get_file_metadata(self, drive_manager, mock_drive_service):
        """Test getting file metadata."""
        mock_metadata = {
            'id': 'test_file_id',
            'name': 'test.mp3',
            'size': '1024'
        }
        mock_drive_service.files().get().execute.return_value = mock_metadata

        result = drive_manager.get_file_metadata('test_file_id')

        assert result['id'] == 'test_file_id'
        assert result['name'] == 'test.mp3'
        mock_drive_service.files().get.assert_called_once()

    def test_delete_file(self, drive_manager, mock_drive_service):
        """Test deleting a file."""
        mock_drive_service.files().delete().execute.return_value = None

        drive_manager.delete_file('test_file_id')

        mock_drive_service.files().delete.assert_called_once_with(fileId='test_file_id')

    @patch('utils.drive_manager.InstalledAppFlow')
    @patch('utils.drive_manager.Path.exists')
    def test_authentication_new_credentials(self, mock_exists, mock_flow):
        """Test authentication with new credentials."""
        # Token file doesn't exist, credentials file exists
        mock_exists.side_effect = lambda path: 'credentials.json' in str(path)

        # Mock OAuth flow
        mock_creds = Mock()
        mock_creds.valid = True
        mock_flow_instance = Mock()
        mock_flow_instance.run_local_server.return_value = mock_creds
        mock_flow.from_client_secrets_file.return_value = mock_flow_instance

        with patch('builtins.open', mock_open()), \
             patch('pickle.dump'), \
             patch('utils.drive_manager.build'):

            manager = GoogleDriveManager(
                credentials_file='credentials.json',
                token_file='token.json'
            )

            assert manager.service is not None
            mock_flow_instance.run_local_server.assert_called_once()

    def test_authentication_missing_credentials(self):
        """Test authentication without credentials file raises error."""
        with patch('utils.drive_manager.Path.exists', return_value=False):
            with pytest.raises(DriveManagerError, match="Credentials file not found"):
                GoogleDriveManager(
                    credentials_file='nonexistent.json',
                    token_file='token.json'
                )


class TestDriveManagerErrorHandling:
    """Tests for error handling in DriveManager."""

    def test_list_files_http_error(self, drive_manager, mock_drive_service):
        """Test handling of HTTP error during list_files."""
        from googleapiclient.errors import HttpError

        mock_error = HttpError(Mock(status=403), b'Forbidden')
        mock_drive_service.files().list().execute.side_effect = mock_error

        with pytest.raises(DriveManagerError, match="Failed to list files"):
            list(drive_manager.list_files())

    def test_download_file_http_error(self, drive_manager, mock_drive_service):
        """Test handling of HTTP error during download."""
        from googleapiclient.errors import HttpError

        mock_error = HttpError(Mock(status=404), b'Not Found')
        mock_drive_service.files().get().execute.side_effect = mock_error

        with pytest.raises(DriveManagerError, match="Failed to download"):
            drive_manager.download_file(
                file_id='nonexistent_id',
                output_path='/tmp/test.mp3'
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
