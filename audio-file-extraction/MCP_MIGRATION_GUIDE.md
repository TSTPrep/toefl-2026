# MCP Migration Guide

## Overview

The audio extraction scripts have been refactored to support **Google Workspace MCP** as an alternative to the direct Google Drive API. This provides better integration with Claude Code workflows and eliminates the need for managing OAuth credentials locally.

## Architecture

### Two Modes of Operation

1. **Legacy Mode** (USE_MCP=false)
   - Uses google-api-python-client directly
   - Requires credentials.json and token.json
   - Scripts execute Drive operations independently

2. **MCP Mode** (USE_MCP=true) - **Recommended**
   - Uses Google Workspace MCP tools
   - Requires Claude Code orchestration
   - No local credentials needed
   - User email: vlad@serenichron.com

### Current Status

- **.env**: `USE_MCP=true` (MCP mode enabled)
- **MCP User**: vlad@serenichron.com
- **Drive Folder**: 1vbSukNXg7Z5mx3fAb6-h2TWxTBjHX5io

## How MCP Mode Works

### Key Principle

**MCP tools can only be called by Claude, not by Python scripts directly.**

This means:
1. Python scripts detect MCP mode and raise helpful errors
2. Claude reads the error/log messages
3. Claude executes the appropriate MCP tool call
4. Results are passed back to the script context

### Drive Operation Flow

```
Python Script Request
        ↓
drive_manager.py detects USE_MCP=true
        ↓
Raises DriveManagerError with operation details
        ↓
Claude catches error and reads operation request
        ↓
Claude executes mcp__google_workspace__* tool
        ↓
Claude orchestrates next steps based on results
```

## MCP Tool Mapping

### List Files in Folder

**Python Request:**
```python
files = drive_manager.list_files(
    folder_id='1vbSukNXg7Z5mx3fAb6-h2TWxTBjHX5io',
    query="name contains 'conversation' and mimeType = 'audio/mpeg'",
    order_by='name'
)
```

**Claude Should Execute:**
```python
mcp__google_workspace__search_drive_files(
    user_google_email='vlad@serenichron.com',
    query="'1vbSukNXg7Z5mx3fAb6-h2TWxTBjHX5io' in parents and trashed=false and (name contains 'conversation' and mimeType = 'audio/mpeg')",
    page_size=100
)
```

### Search Files

**Python Request:**
```python
files = drive_manager.search_files(
    name_pattern='conversation',
    mime_type='audio/mpeg'
)
```

**Claude Should Execute:**
```python
mcp__google_workspace__search_drive_files(
    user_google_email='vlad@serenichron.com',
    query="'1vbSukNXg7Z5mx3fAb6-h2TWxTBjHX5io' in parents and trashed=false and name contains 'conversation' and mimeType = 'audio/mpeg'",
    page_size=100
)
```

### Download File

**Python Request:**
```python
drive_manager.download_file(
    file_id='1o0cMffBzUnIMVZulhjzV7P7lgjJespbq',
    output_path='data/temp/narrator_daniel.mp3'
)
```

**Claude Should Execute:**
```python
# Step 1: Get file content
content = mcp__google_workspace__get_drive_file_content(
    user_google_email='vlad@serenichron.com',
    file_id='1o0cMffBzUnIMVZulhjzV7P7lgjJespbq'
)

# Step 2: Write to local file
with open('data/temp/narrator_daniel.mp3', 'wb') as f:
    f.write(content)
```

### Upload File

**Python Request:**
```python
drive_manager.upload_file(
    file_path='data/processed/conversation.mp3',
    mime_type='audio/mpeg',
    update_existing=True
)
```

**Claude Should Execute:**
```python
# Step 1: Read local file
with open('data/processed/conversation.mp3', 'rb') as f:
    file_content = f.read()

# Step 2: Search for existing file (if update_existing=True)
existing = mcp__google_workspace__search_drive_files(
    user_google_email='vlad@serenichron.com',
    query="'1vbSukNXg7Z5mx3fAb6-h2TWxTBjHX5io' in parents and name = 'conversation.mp3' and trashed=false",
    page_size=1
)

# Step 3: Upload (or update if existing)
if existing and update_existing:
    # Update existing file (may need Drive API v3 update call)
    # Note: MCP may not have direct update capability
    # Consider delete + create instead
    pass
else:
    # Create new file
    mcp__google_workspace__create_drive_file(
        user_google_email='vlad@serenichron.com',
        file_name='conversation.mp3',
        folder_id='1vbSukNXg7Z5mx3fAb6-h2TWxTBjHX5io',
        mime_type='audio/mpeg',
        content=file_content  # Or fileUrl if uploaded elsewhere
    )
```

## Affected Scripts

### 1. scripts/utils/drive_manager.py

**Changes:**
- Added USE_MCP environment variable check
- Skip Google API imports when USE_MCP=true
- Raise informative errors when MCP operations are attempted
- Keep legacy API code for backward compatibility

**Interface:** Unchanged (same methods, same signatures)

### 2. scripts/task2_add_prefix.py

**Changes:** None required (uses drive_manager interface)

**Claude Orchestration Needed:**
- Read script to understand workflow
- Execute MCP calls when script hits Drive operations
- Pass results back to script logic
- Continue script execution with results

### 3. scripts/investigate_task1.py

**Changes:** None required (uses drive_manager interface)

**Claude Orchestration Needed:**
- Same pattern as task2_add_prefix.py

## Running Scripts with MCP

### Manual Orchestration (Current Approach)

Since the scripts can't call MCP directly, Claude must orchestrate:

1. **Read the script** to understand what it does
2. **Execute step-by-step**, calling MCP tools when Drive operations are needed
3. **Track state** between MCP calls
4. **Process results** and continue script logic

### Example: Running task2_add_prefix.py

```python
# Claude reads: scripts/task2_add_prefix.py
# Understands the workflow:
# 1. Download narrator files
# 2. List conversation files
# 3. Process each file (download → concatenate → upload)

# Step 1: Download narrator files
narrator_daniel = mcp__google_workspace__get_drive_file_content(
    user_google_email='vlad@serenichron.com',
    file_id='1o0cMffBzUnIMVZulhjzV7P7lgjJespbq'
)
# Save to data/temp/narrator_daniel.mp3

narrator_matilda = mcp__google_workspace__get_drive_file_content(
    user_google_email='vlad@serenichron.com',
    file_id='19GayiAp7_eOLotNMNjvTNPCAtDZEnWjm'
)
# Save to data/temp/narrator_matilda.mp3

# Step 2: List conversation files
conversation_files = mcp__google_workspace__search_drive_files(
    user_google_email='vlad@serenichron.com',
    query="'1vbSukNXg7Z5mx3fAb6-h2TWxTBjHX5io' in parents and name contains 'conversation' and mimeType = 'audio/mpeg' and trashed=false",
    page_size=100
)

# Step 3: For each conversation file...
# (Process, concatenate, upload back)
```

## Future Improvements

### Option 1: MCP Bridge Service

Create a local service that:
- Accepts Drive operation requests from Python scripts
- Forwards to Claude's MCP interface
- Returns results to Python scripts
- Enables scripts to run "normally" with MCP backend

### Option 2: Direct MCP Client Library

If Google Workspace MCP protocol becomes available as a library:
- Python scripts could call MCP directly
- No orchestration needed
- Seamless migration from API to MCP

### Option 3: Hybrid Approach

Keep both modes:
- USE_MCP=false for automated/CI execution (with credentials)
- USE_MCP=true for interactive Claude-assisted execution
- Scripts work in both modes

## Troubleshooting

### Error: "MCP mode is enabled but requires external orchestration"

**Cause:** Script tried to execute Drive operation while USE_MCP=true

**Solution:**
1. Claude should read the error message
2. Identify which Drive operation is needed
3. Execute the appropriate MCP tool
4. Continue orchestrating the script

### Error: "No folder_id provided"

**Cause:** DRIVE_FOLDER_ID not set in .env

**Solution:** Ensure .env has:
```
DRIVE_FOLDER_ID=1vbSukNXg7Z5mx3fAb6-h2TWxTBjHX5io
```

### Missing MCP Authentication

**Cause:** Claude hasn't authenticated with Google Workspace MCP

**Solution:**
```python
# Claude should call first:
mcp__google_workspace__start_google_auth(
    service_name='drive',
    user_google_email='vlad@serenichron.com'
)
```

## Testing

### Test MCP Integration

1. **List files:**
```python
result = mcp__google_workspace__search_drive_files(
    user_google_email='vlad@serenichron.com',
    query="'1vbSukNXg7Z5mx3fAb6-h2TWxTBjHX5io' in parents and trashed=false",
    page_size=10
)
```

2. **Download narrator file:**
```python
content = mcp__google_workspace__get_drive_file_content(
    user_google_email='vlad@serenichron.com',
    file_id='1o0cMffBzUnIMVZulhjzV7P7lgjJespbq'
)
```

3. **Verify folder access:**
```python
items = mcp__google_workspace__list_drive_items(
    user_google_email='vlad@serenichron.com',
    folder_id='1vbSukNXg7Z5mx3fAb6-h2TWxTBjHX5io',
    page_size=10
)
```

## Summary

The refactoring maintains **full backward compatibility** while enabling **MCP-based operation** when Claude orchestrates the workflows. The key insight is that MCP tools are Claude-native, so the architecture embraces this by having Claude orchestrate Drive operations based on script needs rather than trying to make Python call MCP directly.

**Benefits:**
- No credential management for MCP mode
- Better integration with Claude Code workflows
- Flexible: can still use legacy mode when needed
- Scripts remain unchanged (same interface)

**Trade-off:**
- MCP mode requires Claude orchestration
- Can't run scripts fully autonomously with MCP
- Recommended for interactive/Claude-assisted execution
