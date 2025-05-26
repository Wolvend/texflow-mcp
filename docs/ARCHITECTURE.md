# CUPS MCP Server Architecture

## Overview

The CUPS MCP Server follows a modular handler-based architecture for processing different document types and managing print operations.

## Core Components

### 1. MCP Server Foundation
- Built on `fastmcp` framework
- Provides tool registration and communication
- Handles JSON-RPC protocol

### 2. Document Processing Pipeline
```
Input Document → Type Detection → Handler Selection → Processing → Output
```

### 3. Handler System

#### Base Handler Pattern
Each document type has a dedicated handler responsible for:
- Validation
- Conversion to printable format
- Error handling
- Dependency checking

#### Current Handlers

**Plain Text Handler**
- Direct pass-through to CUPS
- No conversion needed
- Handles encoding properly

**Markdown Handler**
- Uses `pandoc` for conversion
- Pandoc → XeLaTeX → PDF pipeline
- Supports math expressions and formatting

**LaTeX Handler**
- Direct XeLaTeX compilation
- Full LaTeX package support
- Multi-pass compilation for references

**PDF Handler**
- Direct printing without conversion
- Validates PDF integrity
- Preserves formatting

**HTML Handler**
- Uses `weasyprint` for rendering
- CSS support
- Modern web standards

**SVG Handler**
- Uses `rsvg-convert`
- Vector graphics preservation
- Scalable output

### 4. CUPS Integration Layer

**Printer Management**
- List printers
- Get printer info
- Set defaults
- Enable/disable printers

**Job Management**
- Submit print jobs
- Track job status
- Handle errors

### 5. File System Layer

**Path Resolution**
- Smart path expansion
- Documents folder defaults
- Home directory handling

**File Operations**
- Read with line numbers
- Safe writes with validation
- Atomic operations

### 6. Collaborative Editing System

**Change Tracking**
- Metadata storage (mtime, size, hash)
- Diff generation
- Conflict detection

**Safety Mechanisms**
- Pre-edit validation
- External change detection
- Data loss prevention

## Design Principles

### 1. Fail-Safe Operation
- Check dependencies before registration
- Graceful degradation
- Clear error messages

### 2. User-Friendly Defaults
- Documents folder as default location
- Automatic file naming
- Smart path handling

### 3. Extensibility
- Easy to add new handlers
- Modular design
- Clear interfaces

### 4. Performance
- Lazy loading of dependencies
- Efficient file operations
- Minimal memory footprint

## Data Flow

### Print Operation Flow
```
1. User Request → MCP Tool
2. Tool → Validation
3. Validation → Handler Selection
4. Handler → Document Processing
5. Processing → Temporary File
6. Temporary File → CUPS
7. CUPS → Physical Printer
```

### Edit Operation Flow
```
1. Read Request → File System
2. File System → Content + Metadata
3. Edit Request → Change Detection
4. If Changed → Show Diff + Abort
5. If Unchanged → Apply Edit
6. Update Metadata → Storage
```

## Security Considerations

### Input Validation
- Path traversal prevention
- Command injection protection
- File type verification

### Process Isolation
- Subprocess for external commands
- Timeout mechanisms
- Resource limits

### File System Safety
- Permission checks
- Atomic operations
- Backup considerations

## Performance Optimizations

### Caching
- Document metadata in memory
- Dependency check results
- Printer information

### Lazy Operations
- On-demand dependency loading
- Deferred file reads
- Streaming where possible

## Error Handling Strategy

### User-Facing Errors
- Clear, actionable messages
- Suggest solutions
- Preserve user data

### System Errors
- Log for debugging
- Graceful degradation
- State recovery

## Testing Approach

### Unit Tests
- Individual handler testing
- Utility function validation
- Edge case coverage

### Integration Tests
- Full pipeline testing
- CUPS interaction
- File system operations

### Manual Testing
- Real printer verification
- Multi-user scenarios
- Performance validation