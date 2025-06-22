# TeXFlow MCP Server Project Memory

## Project Overview

TeXFlow is a semantic document authoring MCP server that provides intelligent workflow guidance for creating LaTeX and Markdown documents. It emphasizes efficiency through smart hints and project-based organization.

## Architecture

### Unified Semantic Server (`texflow_unified.py`)
- Single entry point that routes all operations through the semantic layer
- Exposes all 9 semantic tools:
  - **document**: Create, read, edit, convert, validate documents
  - **output**: Export to various formats (PDF, DOCX, etc.) and print
  - **project**: Manage document projects with organized structure
  - **discover**: Find documents, fonts, system capabilities, and installed packages
  - **organizer**: Archive, move, clean documents and auxiliary files
  - **printer**: Manage CUPS printers and settings
  - **workflow**: Get task-specific guidance
  - **templates**: Manage document templates
  - **reference**: LaTeX documentation search and help (commands, symbols, errors)
- Exposes 9 MCP resources:
  - **System Monitoring**:
    - **system-dependencies://status**: Complete dependency status as JSON (includes discovered packages)
    - **system-dependencies://summary**: Human-readable dependency summary
    - **system-dependencies://missing**: Installation guidance for missing tools
    - **system-dependencies://packages**: Discovered LaTeX packages from system package manager (Linux only)
  - **Content Discovery**:
    - **texflow://projects**: List all TeXFlow projects with commands
    - **texflow://templates**: Browse available document templates
    - **texflow://recent-documents**: Recent documents across projects
    - **texflow://workflow-guide**: Context-aware workflow guidance
    - **texflow://latex-reference**: LaTeX reference database statistics and search tips

### Semantic Layer (`src/`)
- **Core Components**:
  - `semantic_router.py`: Routes operations with workflow awareness
  - `operation_registry.py`: Manages operation handlers
  - `format_detector.py`: Auto-detects optimal document format
  - `system_checker.py`: Dynamic system dependency monitoring and status reporting
  - `package_discovery.py`: Discovers installed LaTeX packages via system package managers (Linux only)
  
- **Features**: Modular operations for document, output, project, organizer, and archive

### Workflow Philosophy
1. **Projects First**: Always work within a project context for organization
2. **Edit Don't Recreate**: Use edit operations on existing documents to save tokens
3. **Convert Don't Rewrite**: Transform between formats instead of regenerating
4. **Validate Before Export**: Check LaTeX syntax before generating PDFs

## Development Workflow

1. **Test locally**: `uv run python texflow_unified.py`
2. **Test dependencies**: `python test_system_checker.py`
3. **Test MCP resources**: `python test_mcp_resources.py`
4. **Test package discovery**: `python test_package_discovery.py` (Linux only)
5. **Update MCP**: After changes, restart Claude Desktop to test
6. **Use MCP Inspector**: For interactive testing of individual tools

## Documentation

- **[TEXFLOW_REFERENCE.md](docs/TEXFLOW_REFERENCE.md)**: Complete reference guide for all 9 semantic tools
- **[SYSTEM_DEPENDENCIES.md](docs/SYSTEM_DEPENDENCIES.md)**: System requirements and dependency management
- **[LATEX_REFERENCE_DESIGN.md](docs/LATEX_REFERENCE_DESIGN.md)**: Design doc for the LaTeX reference tool
- **[COMPLETE_WORKFLOW_EXAMPLE.md](docs/COMPLETE_WORKFLOW_EXAMPLE.md)**: End-to-end workflow examples
- **[RECIPE_BOOK_EXAMPLE.md](docs/RECIPE_BOOK_EXAMPLE.md)**: Practical example creating a recipe book

## System Dependencies

TeXFlow includes dynamic dependency checking with automatic status reporting via MCP resources. Dependencies are categorized as:

**Essential (Required for Core Functionality):**
- **pandoc**: Document conversion (Markdown ↔ LaTeX ↔ PDF)
- **XeLaTeX**: LaTeX compilation with Unicode support
- **CUPS**: Linux printing system
- **fontconfig**: Font discovery (fc-list)

**Optional (Enhanced Functionality):**
- **poppler-utils**: PDF page inspection and rendering
- **chktex**: LaTeX syntax checking
- **ghostscript**: PDF optimization

The system automatically detects available tools, reports versions, and provides platform-specific installation guidance. See `docs/SYSTEM_DEPENDENCIES.md` for complete details.

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

## Recent Enhancements

- **LaTeX Reference Tool**: New `reference` tool provides instant access to LaTeX documentation:
  - Search 5900+ commands and symbols
  - Get package documentation and examples
  - Decode error messages with solutions
  - Check documents for style best practices
  - Find symbols by description (e.g., "approximately equal" → \approx)
- **Flexible Conversion**: The document conversion tool now works without requiring an active project
- **Any-to-Any Format Support**: Expanded conversion capabilities using pandoc
- **Atomic Operations**: Clear hints when performing conversions outside of projects
- **Extended Format Support**: Input formats include markdown, latex, html, docx, odt, rtf, epub, mediawiki, rst

## Pending Enhancements

All 9 semantic tools are now exposed. Future enhancements:
- **Expanded reference data**: Add more LaTeX packages, symbols, and examples
- **Build-time data generation**: Automated extraction from latex2e-help-texinfo and symbol lists
- **Context-aware help**: Auto-suggest relevant documentation during editing
- **Visual symbol search**: Render symbols as images for easier identification

## Key Design Decisions

1. **Semantic Routing**: All operations go through semantic layer for consistent workflow guidance
2. **Project Context**: Operations are project-aware to maintain organization
3. **Format Detection**: Automatic detection of optimal format (LaTeX vs Markdown) based on content
4. **Efficiency Hints**: Proactive guidance to prevent token waste (e.g., edit vs recreate)