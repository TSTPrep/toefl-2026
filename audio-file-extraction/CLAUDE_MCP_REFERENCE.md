# Claude MCP Reference Card

Quick reference for orchestrating TOEFL audio scripts with Google Workspace MCP.

## Environment

```bash
USE_MCP=true
MCP_USER_EMAIL=vlad@serenichron.com
DRIVE_FOLDER_ID=1vbSukNXg7Z5mx3fAb6-h2TWxTBjHX5io
NARRATOR_DANIEL_FILE_ID=1o0cMffBzUnIMVZulhjzV7P7lgjJespbq
NARRATOR_MATILDA_FILE_ID=19GayiAp7_eOLotNMNjvTNPCAtDZEnWjm
```

## Common MCP Operations

### 1. List All Files in Folder

```python
mcp__google_workspace__search_drive_files(
    user_google_email='vlad@serenichron.com',
    query="'1vbSukNXg7Z5mx3fAb6-h2TWxTBjHX5io' in parents and trashed=false",
    page_size=100
)
```

### 2. Search for Conversation Files

```python
mcp__google_workspace__search_drive_files(
    user_google_email='vlad@serenichron.com',
    query="'1vbSukNXg7Z5mx3fAb6-h2TWxTBjHX5io' in parents and trashed=false and name contains 'conversation' and mimeType = 'audio/mpeg'",
    page_size=100
)
```

### 3. Search for Listen-and-Choose Files

```python
mcp__google_workspace__search_drive_files(
    user_google_email='vlad@serenichron.com',
    query="'1vbSukNXg7Z5mx3fAb6-h2TWxTBjHX5io' in parents and trashed=false and (name contains 'Listen' or name contains 'Choose') and mimeType = 'audio/mpeg'",
    page_size=100
)
```

### 4. Download File by ID

```python
# Returns file content (binary for audio files)
content = mcp__google_workspace__get_drive_file_content(
    user_google_email='vlad@serenichron.com',
    file_id='FILE_ID_HERE'
)

# Save to local file
with open('path/to/output.mp3', 'wb') as f:
    f.write(content)
```

### 5. Upload File to Drive

```python
# Read local file
with open('path/to/file.mp3', 'rb') as f:
    file_content = f.read()

# Create in Drive
mcp__google_workspace__create_drive_file(
    user_google_email='vlad@serenichron.com',
    file_name='filename.mp3',
    folder_id='1vbSukNXg7Z5mx3fAb6-h2TWxTBjHX5io',
    mime_type='audio/mpeg',
    content=file_content  # or fileUrl if uploaded elsewhere
)
```

### 6. Download Narrator Files

```python
# Daniel narrator
daniel_content = mcp__google_workspace__get_drive_file_content(
    user_google_email='vlad@serenichron.com',
    file_id='1o0cMffBzUnIMVZulhjzV7P7lgjJespbq'
)
with open('data/temp/narrator_daniel.mp3', 'wb') as f:
    f.write(daniel_content)

# Matilda narrator
matilda_content = mcp__google_workspace__get_drive_file_content(
    user_google_email='vlad@serenichron.com',
    file_id='19GayiAp7_eOLotNMNjvTNPCAtDZEnWjm'
)
with open('data/temp/narrator_matilda.mp3', 'wb') as f:
    f.write(matilda_content)
```

## Script Orchestration Patterns

### Pattern 1: task2_add_prefix.py

**Workflow:**
1. Download narrator files (Daniel + Matilda)
2. List all conversation files
3. For each conversation file:
   - Download conversation file
   - Concatenate narrator + conversation (using ffmpeg)
   - Upload result back to Drive

**MCP Calls Needed:**
- 2× `get_drive_file_content` (narrators)
- 1× `search_drive_files` (list conversations)
- N× `get_drive_file_content` (download each conversation)
- N× `create_drive_file` (upload each processed file)

### Pattern 2: investigate_task1.py

**Workflow:**
1. Search for Listen-and-Choose files
2. Download sample files for analysis
3. Analyze audio properties (duration, format)
4. Generate investigation report

**MCP Calls Needed:**
- 1× `search_drive_files` (find Listen-and-Choose files)
- N× `get_drive_file_content` (download samples)

## Query Builder Helper

### Generic Query Template

```python
query = f"'{folder_id}' in parents and trashed=false"

# Add name filter
if name_contains:
    query += f" and name contains '{name_contains}'"

# Add MIME type filter
if mime_type:
    query += f" and mimeType = '{mime_type}'"

# Example result:
# "'1vbSukNXg7Z5mx3fAb6-h2TWxTBjHX5io' in parents and trashed=false and name contains 'conversation' and mimeType = 'audio/mpeg'"
```

### Exact Name Match

```python
query = f"'{folder_id}' in parents and trashed=false and name = 'exact_filename.mp3'"
```

### Multiple Conditions (OR)

```python
query = f"'{folder_id}' in parents and trashed=false and (name contains 'Listen' or name contains 'Choose')"
```

## File Update Pattern

MCP may not have direct file update capability. Use this pattern:

```python
# Step 1: Search for existing file
existing = mcp__google_workspace__search_drive_files(
    user_google_email='vlad@serenichron.com',
    query="'1vbSukNXg7Z5mx3fAb6-h2TWxTBjHX5io' in parents and name = 'filename.mp3' and trashed=false",
    page_size=1
)

# Step 2: If found, note the file_id for potential deletion
# (MCP may not support in-place update)

# Step 3: Create new file (overwrites if Drive supports it)
mcp__google_workspace__create_drive_file(
    user_google_email='vlad@serenichron.com',
    file_name='filename.mp3',
    folder_id='1vbSukNXg7Z5mx3fAb6-h2TWxTBjHX5io',
    mime_type='audio/mpeg',
    content=new_content
)
```

## Response Format Examples

### search_drive_files Response

```python
{
    'files': [
        {
            'id': '1abc123...',
            'name': 'TOEFL-Speaking-Conversation-Q1-v1-conversation.mp3',
            'mimeType': 'audio/mpeg',
            'size': '1234567',
            'modifiedTime': '2024-01-01T00:00:00Z',
            'createdTime': '2024-01-01T00:00:00Z'
        },
        # ... more files
    ]
}
```

### get_drive_file_content Response

```python
# Binary content for audio files
# Text content for text files
# Can be written directly to file with 'wb' mode
```

## Error Handling

### Authentication Error

```python
# If authentication fails, call:
mcp__google_workspace__start_google_auth(
    service_name='drive',
    user_google_email='vlad@serenichron.com'
)
```

### Folder Access Error

```python
# Verify folder exists and is accessible:
items = mcp__google_workspace__list_drive_items(
    user_google_email='vlad@serenichron.com',
    folder_id='1vbSukNXg7Z5mx3fAb6-h2TWxTBjHX5io'
)
```

## Orchestration Checklist

When running a script with MCP:

- [ ] Verify USE_MCP=true in .env
- [ ] Confirm MCP_USER_EMAIL is set
- [ ] Check DRIVE_FOLDER_ID is correct
- [ ] Read script to understand workflow
- [ ] Identify all Drive operations needed
- [ ] Execute MCP tools in correct order
- [ ] Save downloaded files to correct paths
- [ ] Pass results to next step
- [ ] Handle errors gracefully
- [ ] Log operations for debugging

## Quick Test

Verify MCP access:

```python
# Test 1: List files
files = mcp__google_workspace__search_drive_files(
    user_google_email='vlad@serenichron.com',
    query="'1vbSukNXg7Z5mx3fAb6-h2TWxTBjHX5io' in parents and trashed=false",
    page_size=5
)
print(f"Found {len(files.get('files', []))} files")

# Test 2: Download narrator
content = mcp__google_workspace__get_drive_file_content(
    user_google_email='vlad@serenichron.com',
    file_id='1o0cMffBzUnIMVZulhjzV7P7lgjJespbq'
)
print(f"Downloaded {len(content)} bytes")
```

## Common Pitfalls

1. **Forgot to add folder_id to query**
   - Always include: `'FOLDER_ID' in parents`

2. **Not filtering trashed files**
   - Always include: `and trashed=false`

3. **Binary vs text mode**
   - Audio files: use `'wb'` mode when writing
   - Text files: use `'w'` mode

4. **Query syntax errors**
   - Use single quotes around string values in query
   - Use proper boolean operators: `and`, `or`, `not`

5. **File paths**
   - Use absolute paths when possible
   - Ensure directories exist before writing files

## Tips

- **Pagination:** Default page_size=100, increase for large folders
- **Sorting:** MCP search may not support orderBy, sort results in Python
- **Progress:** Log operations for long-running tasks
- **Validation:** Use TOEFLFileParser to validate filenames
- **Audio:** Use AudioProcessor for audio operations (ffmpeg)
