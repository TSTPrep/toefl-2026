"""
Google Drive Manager Module

Handles Google Drive operations including:
- Authentication (via Google API or MCP)
- Listing files with pagination
- Downloading files
- Uploading files with version management (update existing files)
- File metadata management

Supports two modes:
1. Direct Google Drive API (legacy)
2. Google Workspace MCP (new, enabled via USE_MCP=true)
"""

import os
import io
from pathlib import Path
from typing import Optional, List, Dict, Any, Generator
from .logger import get_logger

# Only import Google API libraries if not using MCP
USE_MCP = os.getenv('USE_MCP', 'false').lower() == 'true'

if not USE_MCP:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
    from googleapiclient.errors import HttpError
    import pickle

logger = get_logger(__name__)


# Scopes for Google Drive API (legacy mode only)
SCOPES = ['https://www.googleapis.com/auth/drive']

# User email for MCP operations
MCP_USER_EMAIL = os.getenv('MCP_USER_EMAIL', 'vlad@serenichron.com')


class DriveManagerError(Exception):
    """Exception raised for Drive Manager errors."""
    pass


class GoogleDriveManager:
    """Manages Google Drive operations via API or MCP."""

    def __init__(
        self,
        credentials_file: Optional[str] = None,
        token_file: Optional[str] = None,
        folder_id: Optional[str] = None
    ):
        """
        Initialize Google Drive Manager.

        Args:
            credentials_file: Path to credentials.json (ignored if USE_MCP=true)
            token_file: Path to token file (ignored if USE_MCP=true)
            folder_id: Default folder ID for operations (defaults to env var)
        """
        self.use_mcp = USE_MCP
        self.default_folder_id = folder_id or os.getenv('DRIVE_FOLDER_ID')

        if self.use_mcp:
            logger.info("Using Google Workspace MCP for Drive operations")
            self.user_email = MCP_USER_EMAIL
            self.service = None  # Not needed for MCP
        else:
            logger.info("Using direct Google Drive API")
            self.credentials_file = credentials_file or os.getenv('CREDENTIALS_FILE', 'credentials.json')
            self.token_file = token_file or os.getenv('TOKEN_FILE', 'token.json')
            self.service = None
            self._authenticate()

    def _authenticate(self) -> None:
        """
        Authenticate with Google Drive API (legacy mode only).

        Uses existing token if available, otherwise initiates OAuth flow.
        """
        if self.use_mcp:
            # MCP handles authentication automatically
            return

        creds = None

        # Load existing token
        if Path(self.token_file).exists():
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)

        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials")
                creds.refresh(Request())
            else:
                if not Path(self.credentials_file).exists():
                    raise DriveManagerError(
                        f"Credentials file not found: {self.credentials_file}. "
                        "Please download credentials.json from Google Cloud Console."
                    )

                logger.info("Starting OAuth flow")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save credentials for next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
            logger.info(f"Credentials saved to {self.token_file}")

        # Build service
        self.service = build('drive', 'v3', credentials=creds)
        logger.info("Google Drive API authenticated successfully")

    def _mcp_list_files(
        self,
        folder_id: str,
        query: Optional[str] = None,
        page_size: int = 100,
        order_by: Optional[str] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        List files using MCP tools.

        Note: This is a stub that shows how to integrate MCP calls.
        The actual MCP calls must be made from the main Claude context,
        not from within a Python script.
        """
        raise NotImplementedError(
            "MCP operations must be called from the main Claude context. "
            "This method is a placeholder showing the intended interface."
        )

    def list_files(
        self,
        folder_id: Optional[str] = None,
        query: Optional[str] = None,
        page_size: int = 100,
        order_by: Optional[str] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        List files in a folder with pagination support.

        Args:
            folder_id: Folder ID to list (defaults to self.default_folder_id)
            query: Additional query filters (optional)
            page_size: Number of files per page (max 1000)
            order_by: Sort order (e.g., 'name', 'createdTime', 'modifiedTime')

        Yields:
            File metadata dictionaries

        Raises:
            DriveManagerError: If listing fails
        """
        folder_id = folder_id or self.default_folder_id
        if not folder_id:
            raise DriveManagerError("No folder_id provided")

        if self.use_mcp:
            raise DriveManagerError(
                "MCP mode is enabled but requires external orchestration. "
                "Please use the MCP-compatible wrapper class instead."
            )

        # Legacy API implementation
        # Build query
        base_query = f"'{folder_id}' in parents and trashed=false"
        if query:
            full_query = f"{base_query} and ({query})"
        else:
            full_query = base_query

        try:
            page_token = None
            file_count = 0

            while True:
                # Request files
                results = self.service.files().list(
                    q=full_query,
                    pageSize=min(page_size, 1000),
                    fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, version)",
                    pageToken=page_token,
                    orderBy=order_by
                ).execute()

                files = results.get('files', [])

                for file in files:
                    file_count += 1
                    yield file

                page_token = results.get('nextPageToken')
                if not page_token:
                    break

            logger.info(f"Listed {file_count} files from folder {folder_id}")

        except HttpError as e:
            raise DriveManagerError(f"Failed to list files: {e}")

    def search_files(
        self,
        name_pattern: Optional[str] = None,
        mime_type: Optional[str] = None,
        folder_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for files by name pattern and/or mime type.

        Args:
            name_pattern: Filename pattern (e.g., "conversation")
            mime_type: MIME type filter (e.g., "audio/mpeg")
            folder_id: Folder to search in (defaults to self.default_folder_id)

        Returns:
            List of matching file metadata

        Raises:
            DriveManagerError: If search fails
        """
        if self.use_mcp:
            raise DriveManagerError(
                "MCP mode is enabled but requires external orchestration. "
                "Please use the MCP-compatible wrapper class instead."
            )

        query_parts = []

        if name_pattern:
            query_parts.append(f"name contains '{name_pattern}'")

        if mime_type:
            query_parts.append(f"mimeType = '{mime_type}'")

        query = " and ".join(query_parts) if query_parts else None

        return list(self.list_files(folder_id=folder_id, query=query))

    def download_file(
        self,
        file_id: str,
        output_path: str,
        show_progress: bool = True
    ) -> None:
        """
        Download a file from Google Drive.

        Args:
            file_id: Google Drive file ID
            output_path: Local path to save file
            show_progress: Whether to log download progress

        Raises:
            DriveManagerError: If download fails
        """
        if self.use_mcp:
            raise DriveManagerError(
                "MCP mode is enabled but requires external orchestration. "
                "Please use the MCP-compatible wrapper class instead."
            )

        try:
            # Get file metadata
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields='name, size'
            ).execute()

            file_name = file_metadata.get('name', 'unknown')
            file_size = int(file_metadata.get('size', 0))

            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # Download file
            request = self.service.files().get_media(fileId=file_id)
            fh = io.FileIO(output_path, 'wb')

            downloader = MediaIoBaseDownload(fh, request)

            done = False
            downloaded_bytes = 0

            while not done:
                status, done = downloader.next_chunk()
                if status and show_progress:
                    downloaded_bytes = int(status.resumable_progress)
                    percent = int(status.progress() * 100)
                    logger.debug(f"Download progress: {percent}% ({downloaded_bytes}/{file_size} bytes)")

            fh.close()
            logger.info(f"Downloaded {file_name} to {output_path}")

        except HttpError as e:
            raise DriveManagerError(f"Failed to download file {file_id}: {e}")
        except Exception as e:
            raise DriveManagerError(f"Unexpected error downloading file: {e}")

    def upload_file(
        self,
        file_path: str,
        folder_id: Optional[str] = None,
        mime_type: str = 'audio/mpeg',
        update_existing: bool = True
    ) -> Dict[str, Any]:
        """
        Upload a file to Google Drive.

        Args:
            file_path: Local path to file to upload
            folder_id: Destination folder ID (defaults to self.default_folder_id)
            mime_type: MIME type of file
            update_existing: If True, update existing file instead of creating new version

        Returns:
            File metadata dictionary

        Raises:
            DriveManagerError: If upload fails
        """
        folder_id = folder_id or self.default_folder_id
        if not folder_id:
            raise DriveManagerError("No folder_id provided")

        if not Path(file_path).exists():
            raise DriveManagerError(f"File not found: {file_path}")

        if self.use_mcp:
            raise DriveManagerError(
                "MCP mode is enabled but requires external orchestration. "
                "Please use the MCP-compatible wrapper class instead."
            )

        file_name = Path(file_path).name

        try:
            # Check if file already exists
            existing_file = None
            if update_existing:
                search_results = self.search_files(
                    name_pattern=file_name,
                    folder_id=folder_id
                )
                # Find exact name match
                for result in search_results:
                    if result['name'] == file_name:
                        existing_file = result
                        break

            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)

            if existing_file:
                # Update existing file (version management)
                logger.info(f"Updating existing file: {file_name} (ID: {existing_file['id']})")

                file = self.service.files().update(
                    fileId=existing_file['id'],
                    media_body=media,
                    fields='id, name, mimeType, size, version, modifiedTime'
                ).execute()

                logger.info(f"Updated file {file_name} (version {file.get('version')})")

            else:
                # Create new file
                logger.info(f"Creating new file: {file_name}")

                file_metadata = {
                    'name': file_name,
                    'parents': [folder_id]
                }

                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, name, mimeType, size, version, modifiedTime'
                ).execute()

                logger.info(f"Created file {file_name} (ID: {file['id']})")

            return file

        except HttpError as e:
            raise DriveManagerError(f"Failed to upload file {file_name}: {e}")
        except Exception as e:
            raise DriveManagerError(f"Unexpected error uploading file: {e}")

    def get_file_metadata(self, file_id: str, fields: Optional[str] = None) -> Dict[str, Any]:
        """
        Get metadata for a file.

        Args:
            file_id: Google Drive file ID
            fields: Comma-separated fields to retrieve (defaults to common fields)

        Returns:
            File metadata dictionary

        Raises:
            DriveManagerError: If retrieval fails
        """
        if self.use_mcp:
            raise DriveManagerError(
                "MCP mode is enabled but requires external orchestration. "
                "Please use the MCP-compatible wrapper class instead."
            )

        if fields is None:
            fields = 'id, name, mimeType, size, createdTime, modifiedTime, version, parents'

        try:
            file = self.service.files().get(
                fileId=file_id,
                fields=fields
            ).execute()

            return file

        except HttpError as e:
            raise DriveManagerError(f"Failed to get metadata for file {file_id}: {e}")

    def delete_file(self, file_id: str) -> None:
        """
        Delete a file from Google Drive.

        Args:
            file_id: Google Drive file ID

        Raises:
            DriveManagerError: If deletion fails
        """
        if self.use_mcp:
            raise DriveManagerError(
                "MCP mode is enabled but requires external orchestration. "
                "Please use the MCP-compatible wrapper class instead."
            )

        try:
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"Deleted file {file_id}")

        except HttpError as e:
            raise DriveManagerError(f"Failed to delete file {file_id}: {e}")
