# Collaborative Editing Guide

## Overview

CUPS MCP Server includes advanced collaborative editing features that enable multiple agents (human or AI) to work on the same documents without conflicts. This guide explains how these features work and how to use them effectively.

## Core Concepts

### Change Detection
The server tracks documents using three key metrics:
- **Modification Time**: Filesystem timestamp of last change
- **File Size**: Quick check for content changes
- **Content Hash**: SHA256 hash for definitive change detection

### Conflict Prevention
When an edit is attempted on a file that has been modified externally:
1. The system detects the change
2. Shows a unified diff of what changed
3. Refuses the edit to prevent data loss
4. Advises re-reading the document

## Tools Overview

### `read_document`
Reads a document and establishes tracking metadata.

**Tracking Data Stored**:
- File path
- Modification time
- File size
- Content hash
- Full content (for diff generation)

### `edit_document`
Edits documents with automatic conflict detection.

**Workflow**:
1. Checks if file has been modified since last read
2. If modified: shows diff and refuses edit
3. If unchanged: performs edit and updates tracking

### `check_document_status`
Checks for external changes without attempting edits.

**Use Cases**:
- Periodic status checks
- Pre-edit verification
- Debugging collaboration issues

## Collaboration Patterns

### Human-AI Collaboration
```
1. Human creates/edits document in text editor
2. AI reads document (establishes baseline)
3. Human makes changes in editor
4. AI detects changes, shows diff
5. AI re-reads to sync
6. Both can continue editing safely
```

### AI-AI Collaboration
```
1. AI Agent A reads and edits document
2. AI Agent B attempts edit
3. Agent B sees Agent A's changes via diff
4. Agent B re-reads and proceeds
5. Process repeats with role reversal
```

## Best Practices

### For AI Agents
1. **Always read before editing** - Establishes tracking baseline
2. **Handle conflicts gracefully** - Re-read when changes detected
3. **Use check_document_status** - For non-intrusive monitoring
4. **Communicate changes** - Leave comments about modifications

### For Humans
1. **Save frequently** - Changes are detected on file save
2. **Avoid simultaneous edits** - Let AI complete its operation
3. **Use version control** - Git complements these features
4. **Review AI changes** - Diffs help understand AI modifications

## Technical Details

### Metadata Storage
- Stored in memory (dictionary) during server session
- Cleared on server restart
- No persistent storage between sessions

### Diff Generation
- Uses Python's `difflib.unified_diff`
- Shows 3 lines of context
- Standard unified diff format

### Hash Calculation
- SHA256 for reliability
- Computed on full file content
- Ensures accurate change detection

## Limitations

1. **Session-based tracking** - Metadata cleared on restart
2. **No merge capabilities** - Conflicts must be resolved manually
3. **File-level granularity** - Tracks whole files, not sections
4. **No lock mechanism** - Relies on detection, not prevention

## Future Enhancements

- Persistent metadata storage
- Section-level tracking
- Automatic merge for non-conflicting changes
- WebSocket notifications for real-time updates
- Integration with version control systems