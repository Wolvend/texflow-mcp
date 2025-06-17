# TeXFlow MCP Server Project Memory

## Project Overview

TeXFlow is a semantic document authoring MCP server that provides intelligent workflow guidance for creating LaTeX and Markdown documents. It emphasizes efficiency through smart hints and project-based organization.

## Architecture

### Unified Semantic Server (`texflow_unified.py`)
- Single entry point that routes all operations through the semantic layer
- Currently exposes 4 core tools:
  - **document**: Create, read, edit, convert, validate documents
  - **output**: Export to various formats (PDF, DOCX, etc.) and print
  - **project**: Manage document projects with organized structure
  - **organizer**: Archive, move, clean documents and auxiliary files

### Semantic Layer (`src/`)
- **Core Components**:
  - `semantic_router.py`: Routes operations with workflow awareness
  - `operation_registry.py`: Manages operation handlers
  - `format_detector.py`: Auto-detects optimal document format
  
- **Features**: Modular operations for document, output, project, organizer, and archive

### Workflow Philosophy
1. **Projects First**: Always work within a project context for organization
2. **Edit Don't Recreate**: Use edit operations on existing documents to save tokens
3. **Convert Don't Rewrite**: Transform between formats instead of regenerating
4. **Validate Before Export**: Check LaTeX syntax before generating PDFs

## Development Workflow

1. **Test locally**: `uv run python texflow_unified.py`
2. **Update MCP**: After changes, restart Claude Desktop to test
3. **Use MCP Inspector**: For interactive testing of individual tools

## System Dependencies

- **pandoc**: Document conversion (Markdown ↔ LaTeX ↔ PDF)
- **XeLaTeX**: LaTeX compilation with Unicode support
- **CUPS**: Linux printing system
- **fontconfig**: Font discovery (fc-list)

## Claude Desktop Configuration

```json
{
  "mcpServers": {
    "texflow": {
      "command": "uv",
      "args": ["--directory", "/path/to/texflow-mcp", "run", "texflow", "/home/aaron/Documents/TeXFlow"]
    }
  }
}
```

The last argument is the workspace root where all TeXFlow projects will be stored. You can also use the `TEXFLOW_WORKSPACE` environment variable instead.

## Pending Implementation

Tools from original texflow.py that need semantic layer integration:
- **printer**: Manage CUPS printers
- **discover**: Find documents, fonts, system capabilities
- **workflow**: Get task-specific guidance
- **templates**: Manage document templates

## Key Design Decisions

1. **Semantic Routing**: All operations go through semantic layer for consistent workflow guidance
2. **Project Context**: Operations are project-aware to maintain organization
3. **Format Detection**: Automatic detection of optimal format (LaTeX vs Markdown) based on content
4. **Efficiency Hints**: Proactive guidance to prevent token waste (e.g., edit vs recreate)