"""
MCP Drive Wrapper Module

This module provides a wrapper around Google Workspace MCP tools
that mimics the interface of GoogleDriveManager but uses MCP calls.

NOTE: This module is designed to be used BY CLAUDE, not by Python scripts directly.
The actual MCP tool calls (mcp__google_workspace__*) can only be executed by Claude.

Usage Pattern:
    Claude reads the Python script, identifies Drive operations needed,
    executes MCP tools directly, then passes results back to the script.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from .logger import get_logger

logger = get_logger(__name__)

MCP_USER_EMAIL = os.getenv('MCP_USER_EMAIL', 'vlad@serenichron.com')


class MCPDriveOperationRequest:
    """
    Represents a Drive operation request that Claude should execute via MCP.

    This class documents the operation needed so Claude can execute
    the appropriate MCP tool call and return results.
    """

    def __init__(self, operation: str, params: Dict[str, Any]):
        """
        Initialize operation request.

        Args:
            operation: Type of operation ('list', 'search', 'download', 'upload', etc.)
            params: Parameters for the operation
        """
        self.operation = operation
        self.params = params
        self.user_email = MCP_USER_EMAIL

    def to_mcp_call_guide(self) -> str:
        """
        Generate a guide for Claude on which MCP tool to call.

        Returns:
            String describing the MCP tool call needed
        """
        if self.operation == 'list_files':
            return self._list_files_guide()
        elif self.operation == 'search_files':
            return self._search_files_guide()
        elif self.operation == 'download_file':
            return self._download_file_guide()
        elif self.operation == 'upload_file':
            return self._upload_file_guide()
        elif self.operation == 'get_metadata':
            return self._get_metadata_guide()
        else:
            return f"Unknown operation: {self.operation}"

    def _list_files_guide(self) -> str:
        """Guide for listing files."""
        folder_id = self.params.get('folder_id')
        query = self.params.get('query', '')

        # Build Google Drive query format
        drive_query = f"'{folder_id}' in parents and trashed=false"
        if query:
            drive_query = f"{drive_query} and ({query})"

        return f"""
MCP Tool: mcp__google_workspace__search_drive_files

Parameters:
- user_google_email: {self.user_email}
- query: "{drive_query}"
- page_size: {self.params.get('page_size', 100)}

This will return file metadata in format:
{{
  'id': 'file_id',
  'name': 'filename.mp3',
  'mimeType': 'audio/mpeg',
  'size': '12345',
  'modifiedTime': '2024-01-01T00:00:00Z'
}}
"""

    def _search_files_guide(self) -> str:
        """Guide for searching files."""
        name_pattern = self.params.get('name_pattern', '')
        mime_type = self.params.get('mime_type', '')
        folder_id = self.params.get('folder_id')

        query_parts = []
        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")
        query_parts.append("trashed=false")

        if name_pattern:
            query_parts.append(f"name contains '{name_pattern}'")
        if mime_type:
            query_parts.append(f"mimeType = '{mime_type}'")

        drive_query = " and ".join(query_parts)

        return f"""
MCP Tool: mcp__google_workspace__search_drive_files

Parameters:
- user_google_email: {self.user_email}
- query: "{drive_query}"
- page_size: {self.params.get('page_size', 100)}
"""

    def _download_file_guide(self) -> str:
        """Guide for downloading a file."""
        return f"""
MCP Tool: mcp__google_workspace__get_drive_file_content

Parameters:
- user_google_email: {self.user_email}
- file_id: {self.params.get('file_id')}

Note: This returns file content as text/binary data.
Save to: {self.params.get('output_path')}
"""

    def _upload_file_guide(self) -> str:
        """Guide for uploading a file."""
        return f"""
MCP Tool: mcp__google_workspace__create_drive_file

Parameters:
- user_google_email: {self.user_email}
- file_name: {Path(self.params.get('file_path')).name}
- folder_id: {self.params.get('folder_id')}
- mime_type: {self.params.get('mime_type', 'audio/mpeg')}
- content: [Read from {self.params.get('file_path')}]

Note: If update_existing=True, first search for existing file and update if found.
"""

    def _get_metadata_guide(self) -> str:
        """Guide for getting file metadata."""
        return f"""
MCP Tool: mcp__google_workspace__search_drive_files
(Can use file_id in query)

Or use the get_drive_file_content tool which also returns metadata.

Parameters:
- user_google_email: {self.user_email}
- file_id: {self.params.get('file_id')}
"""


def log_mcp_operation_needed(operation: str, params: Dict[str, Any]) -> None:
    """
    Log that an MCP operation is needed.

    This function is called when Python code needs a Drive operation
    but USE_MCP=true. It logs the operation details so Claude can
    see what needs to be done.

    Args:
        operation: Type of operation needed
        params: Parameters for the operation
    """
    request = MCPDriveOperationRequest(operation, params)

    logger.warning("="*80)
    logger.warning("MCP OPERATION NEEDED")
    logger.warning("="*80)
    logger.warning(f"Operation: {operation}")
    logger.warning(f"Parameters: {params}")
    logger.warning("")
    logger.warning("Claude should execute:")
    logger.warning(request.to_mcp_call_guide())
    logger.warning("="*80)


# Mapping of Drive operations to MCP tools
MCP_TOOL_MAPPING = {
    'list_files': {
        'tool': 'mcp__google_workspace__search_drive_files',
        'description': 'List files in a folder',
        'required_params': ['user_google_email', 'query']
    },
    'search_files': {
        'tool': 'mcp__google_workspace__search_drive_files',
        'description': 'Search for files by name/type',
        'required_params': ['user_google_email', 'query']
    },
    'download_file': {
        'tool': 'mcp__google_workspace__get_drive_file_content',
        'description': 'Download file content',
        'required_params': ['user_google_email', 'file_id']
    },
    'upload_file': {
        'tool': 'mcp__google_workspace__create_drive_file',
        'description': 'Upload or update a file',
        'required_params': ['user_google_email', 'file_name', 'folder_id']
    },
    'get_metadata': {
        'tool': 'mcp__google_workspace__search_drive_files',
        'description': 'Get file metadata',
        'required_params': ['user_google_email', 'query']
    },
    'list_in_folder': {
        'tool': 'mcp__google_workspace__list_drive_items',
        'description': 'List items in a folder',
        'required_params': ['user_google_email', 'folder_id']
    }
}
