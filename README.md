# TeXFlow MCP Server

A comprehensive LaTeX document processing server implementing the Model Context Protocol (MCP). TeXFlow provides advanced features for creating, editing, compiling, and managing LaTeX documents with built-in error handling, bibliography management, and multi-format export capabilities.

## 🚀 Key Features

### Enhanced Document Processing (100MB Support)
- **Large Document Support**: Handle PDFs and LaTeX documents up to 100MB
- **Book-Length Projects**: Create extremely long stories or intricate mathematical equations
- **Incremental Writing**: Append and insert content for continuous document development

### Advanced LaTeX Features
- **Smart Error Diagnosis**: Automatic detection and fixing of compilation errors
- **Bibliography Management**: Import from DOI, arXiv, ISBN; manage BibTeX databases
- **Version Control**: Built-in git-like versioning with branching and rollback
- **Smart Search**: LaTeX-aware search and replace with regex support
- **Project Analytics**: Word count, writing velocity, structure analysis
- **Multi-format Export**: PDF, DOCX, EPUB, HTML, Markdown, RTF
- **Performance Optimization**: Compilation caching and profiling

## Installation

```bash
# Clone the repository
git clone https://github.com/Wolvend/texflow-mcp.git
cd texflow-mcp

# Install dependencies
pip install -r requirements.txt

# Install LaTeX (required for compilation)
# Ubuntu/Debian:
sudo apt-get install texlive-full

# macOS:
brew install --cask mactex

# Windows:
# Download and install MiKTeX from https://miktex.org/
```

## Configuration

Add TeXFlow to your MCP settings:

```json
{
  "mcpServers": {
    "texflow": {
      "command": "python",
      "args": ["/path/to/texflow-mcp/texflow_server_fixed.py"],
      "env": {
        "TEXFLOW_WORKSPACE": "/path/to/your/latex/workspace"
      }
    }
  }
}
```

## Usage Examples

### Basic Document Operations

```python
# Create a new LaTeX document
{
  "tool": "document",
  "arguments": {
    "action": "create",
    "path": "paper.tex",
    "format": "latex",
    "content": "\\documentclass{article}\n\\begin{document}\nHello World\n\\end{document}"
  }
}

# Compile to PDF
{
  "tool": "compile",
  "arguments": {
    "path": "paper.tex"
  }
}
```

### Advanced Features

#### Bibliography Management
```python
# Import reference from DOI
{
  "tool": "bibliography",
  "arguments": {
    "action": "import",
    "source": "10.1038/nature12373",
    "file": "references.bib"
  }
}
```

#### Smart Editing
```python
# Find all unused citations
{
  "tool": "smart_edit",
  "arguments": {
    "action": "find_unused",
    "path": "paper.tex",
    "scope": "citations"
  }
}
```

#### Version Control
```python
# Commit changes
{
  "tool": "version",
  "arguments": {
    "action": "commit",
    "path": "paper.tex",
    "message": "Added introduction section"
  }
}
```

## Tool Overview

TeXFlow provides 11 advanced tools for comprehensive document management:

1. **document** - Create, read, edit, append, and insert content into documents
2. **output** - Export documents to various formats (PDF, DOCX, EPUB, etc.)
3. **project** - Create and manage document projects with templates
4. **compile** - Compile LaTeX documents with error handling
5. **diagnose** - Automatically diagnose and fix LaTeX compilation errors
6. **bibliography** - Import and manage BibTeX references from DOI, arXiv, ISBN
7. **version** - Git-like version control for documents
8. **smart_edit** - LaTeX-aware search and replace with regex support
9. **analytics** - Track word count, writing velocity, and document structure
10. **export** - Export to multiple formats beyond PDF
11. **performance** - Monitor and optimize compilation performance

## Project Templates

TeXFlow includes templates for:
- **book**: Multi-chapter book projects
- **thesis**: Academic thesis with proper formatting
- **article**: Journal articles
- **report**: Technical reports
- **math-heavy**: Documents with extensive mathematical content
- **novel**: Fiction writing with proper formatting

Create a project with a template:
```python
{
  "tool": "project",
  "arguments": {
    "action": "create",
    "name": "my-thesis",
    "template": "thesis"
  }
}
```

## Security Features

- **File Size Limits**: 100MB maximum file size (optimized for large documents)
- **Path Validation**: Prevents directory traversal attacks
- **Resource Limits**: CPU and memory usage controls
- **Workspace Isolation**: All operations confined to designated workspace

## Integration with Other MCP Servers

TeXFlow integrates seamlessly with:
- **ArXiv LaTeX MCP**: Import and process papers from ArXiv
- **Manim MCP**: Generate animations from LaTeX equations
- **Obsidian MCP**: Sync documentation and notes
- **GitHub MCP**: Version control and collaboration

## Error Handling

TeXFlow includes intelligent error diagnosis:
- Missing package detection and installation suggestions
- Encoding issue resolution
- Syntax error fixes
- Citation and reference validation

## Performance

- Incremental compilation support
- Smart caching for repeated builds
- Parallel processing for multi-file projects
- Optimized for large documents (tested with 500+ page documents)

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues and feature requests, please use the [GitHub issue tracker](https://github.com/Wolvend/texflow-mcp/issues).

## Acknowledgments

Built on the Model Context Protocol (MCP) by Anthropic.

## Installation

```bash
# Install system dependencies (choose your distribution)

# Debian/Ubuntu - Full installation with all features
sudo apt-get install cups pandoc texlive-xetex texlive-fonts-recommended \
                     texlive-latex-recommended texlive-pictures chktex \
                     weasyprint librsvg2-bin

# Fedora - Full installation with all features  
sudo dnf install cups pandoc texlive-xetex texlive-collection-fontsrecommended \
                 texlive-collection-pictures texlive-chktex \
                 weasyprint librsvg2-tools

# Arch - Full installation with all features
sudo pacman -S cups pandoc texlive-xetex texlive-fontsrecommended \
               texlive-pictures texlive-binextra \
               python-weasyprint librsvg

# Clone and install
git clone https://github.com/aaronsb/texflow-mcp
cd texflow-mcp
uv sync
```

## Quick Start

### Option 1: Run directly from GitHub (Recommended)

No installation needed! Just ensure you have `uv` installed and run:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run TeXFlow directly from GitHub
uvx --from git+https://github.com/aaronsb/texflow-mcp.git texflow
```

### Option 2: Clone and run locally

```bash
# Clone the repository
git clone https://github.com/aaronsb/texflow-mcp
cd texflow-mcp

# Run the server
uv run texflow
```

## Usage

### Quick Start - 9 Unified Tools

TeXFlow provides 9 semantic tools that intelligently guide your document workflow:

#### 1. `document` - Create, edit, and transform documents
```python
# Create with auto-format detection
document(action="create", content="# My Paper", intent="research")

# Convert existing files (don't recreate!)
document(action="convert", source="notes.md", target_format="latex")

# Edit with conflict detection
document(action="edit", path="paper.tex", old_string="draft", new_string="final")
```

#### 2. `output` - Print or export documents
```python
# Print existing file (preferred)
output(action="print", source="report.pdf")

# Export to PDF
output(action="export", source="notes.md", output_path="notes.pdf")
```

#### 3. `project` - Organize your work
```python
# Create project with AI-guided structure
project(action="create", name="thesis", description="PhD thesis on quantum computing")

# Switch projects
project(action="switch", name="thesis")
```

#### 4. `printer` - Manage printing hardware
```python
printer(action="list")  # Show all printers
printer(action="set_default", name="Office_Laser")
```

#### 5. `discover` - Find resources
```python
discover(action="documents", folder="drafts")  # Find documents
discover(action="fonts", style="serif")  # Browse fonts
```

#### 6. `archive` - Manage versions
```python
archive(action="versions", filename="paper.tex")  # Find all versions
archive(action="cleanup", pattern="*_old*")  # Clean old files
```

#### 7. `workflow` - Get intelligent guidance
```python
workflow(action="suggest", task="write paper with citations")
workflow(action="next_steps")  # What to do next
```

Each tool provides hints for next steps, guiding you through complex workflows.

### Complete Tool Reference

For detailed documentation of all 9 tools, see [Tool Reference](docs/TEXFLOW_REFERENCE.md).

### Legacy Tool Documentation

For users still using individual tools, the original tool documentation follows below. Note that the unified semantic tools above are the recommended approach.

#### `print_text`
Prints plain text content.

```json
{
  "name": "print_text",
  "arguments": {
    "content": "Hello, World!",
    "printer": "Brother_HL_L2350DW"  // optional
  }
}
```

#### `print_markdown`
Prints Markdown content rendered as PDF via pandoc and XeLaTeX.

**Supports:**
- Standard markdown formatting (headers, lists, tables, code blocks)
- LaTeX math expressions (inline with `$`, display with `$$`)
- Latin scripts including European languages
- Greek and Cyrillic alphabets
- Basic symbols and punctuation

**Limited support for:**
- Complex Unicode (emoji, box drawing characters)
- Right-to-left scripts (Arabic, Hebrew)
- CJK characters (Chinese, Japanese, Korean)

```json
{
  "name": "print_markdown",
  "arguments": {
    "content": "# My Document\n\nThis is **bold** text.\n\nMath: $E = mc^2$",
    "printer": "HP_LaserJet",  // optional
    "title": "My Document"     // optional
  }
}
```

#### `print_file`
Prints a file from the filesystem.

```json
{
  "name": "print_file",
  "arguments": {
    "path": "/path/to/document.pdf",
    "printer": "Canon_PIXMA"  // optional
  }
}
```

#### `get_printer_info`
Get detailed information about a specific printer including status, make/model, location, and URI.

```json
{
  "name": "get_printer_info",
  "arguments": {
    "printer_name": "My_Printer"
  }
}
```

#### `set_default_printer`
Change the default printer.

```json
{
  "name": "set_default_printer",
  "arguments": {
    "printer_name": "CanonG3260"
  }
}
```

#### `enable_printer` / `disable_printer`
Control printer availability for accepting jobs.

```json
{
  "name": "enable_printer",
  "arguments": {
    "printer_name": "My_Printer"
  }
}
```

#### `update_printer_info`
Update printer description and/or location.

```json
{
  "name": "update_printer_info",
  "arguments": {
    "printer_name": "My_Printer",
    "description": "Office Color Laser",
    "location": "Room 201"
  }
}
```

#### `markdown_to_pdf`
Convert markdown to PDF and save to a file (without printing).

**Supports:**
- Same markdown features as `print_markdown`
- Saves PDF to specified path instead of printing

```json
{
  "name": "markdown_to_pdf",
  "arguments": {
    "content": "# My Document\n\nSave this as PDF.",
    "output_path": "report.pdf",  // Saves to ~/Documents/report.pdf by default
    "title": "My Document"
  }
}
```

#### `print_latex`
Print LaTeX content (compiled to PDF via XeLaTeX).

**Supports:**
- Full LaTeX syntax and packages
- Mathematical formulas and equations
- TikZ diagrams and graphics
- Bibliography and citations
- Custom document classes

```json
{
  "name": "print_latex",
  "arguments": {
    "content": "\\documentclass{article}\n\\begin{document}\nHello LaTeX!\n\\end{document}",
    "printer": "My_Printer",  // optional
    "title": "My LaTeX Doc"  // optional
  }
}
```

#### `save_markdown`
Save markdown content to a .md file.

```json
{
  "name": "save_markdown",
  "arguments": {
    "content": "# My Document\n\nThis is my markdown content.",
    "filename": "notes.md"  // Saves to ~/Documents/notes.md by default
  }
}
```

#### `save_latex`
Save LaTeX content to a .tex file.

```json
{
  "name": "save_latex",
  "arguments": {
    "content": "\\documentclass{article}\n\\begin{document}\nHello LaTeX!\n\\end{document}",
    "filename": "document.tex"  // Saves to ~/Documents/document.tex by default
  }
}
```

#### `list_documents`
List PDF and Markdown files in the Documents folder.

```json
{
  "name": "list_documents",
  "arguments": {
    "folder": "reports"  // Optional: list files in ~/Documents/reports
  }
}
```

#### `print_from_documents`
Print a PDF or Markdown file from the Documents folder.

```json
{
  "name": "print_from_documents",
  "arguments": {
    "filename": "report.pdf",     // or just "report" - will find .pdf or .md
    "printer": "My_Printer",  // optional
    "folder": "reports"           // optional subfolder
  }
}
```

**Features:**
- Automatically finds .pdf or .md extension if not specified
- Converts Markdown files to PDF before printing
- Works with subfolders in Documents

#### `markdown_to_latex`
Convert a Markdown file to LaTeX format for further customization.

```json
{
  "name": "markdown_to_latex",
  "arguments": {
    "file_path": "research_notes.md",  // Path to markdown file
    "output_path": "research_paper.tex",  // Optional: output path
    "title": "My Research Paper",  // Optional: document title
    "standalone": true  // Optional: create complete document (default: true)
  }
}
```

**Features:**
- Converts Markdown to editable LaTeX format
- Preserves math expressions, tables, and formatting
- Adds conversion metadata as comments
- Allows fine-tuning before final PDF compilation
- Part of the markdown → LaTeX → PDF workflow

**Workflow example:**
```bash
1. save_markdown(content="...", filename="notes.md")
2. markdown_to_latex(file_path="notes.md")  # Creates notes.tex
3. edit_document(file_path="notes.tex", ...)  # Optional: customize
4. latex_to_pdf(file_path="notes.tex", output_path="final.pdf")
```

#### `list_available_fonts`
List fonts available for use with XeLaTeX documents.

```json
{
  "name": "list_available_fonts",
  "arguments": {
    "style": "serif"  // Optional: filter by 'serif', 'sans', 'mono', or None for all
  }
}
```

**Features:**
- Lists all system fonts compatible with XeLaTeX
- Filter by font style (serif, sans-serif, monospace)
- Groups fonts alphabetically for easy browsing
- Provides usage examples for LaTeX documents
- Shows popular font recommendations

#### `validate_latex`
Validate LaTeX content for syntax errors before compilation.

```json
{
  "name": "validate_latex",
  "arguments": {
    "content": "\\documentclass{article}\n\\begin{document}\nHello!\n\\end{document}"
  }
}
```

**Features:**
- Uses `lacheck` and `chktex` for syntax checking (if available)
- Performs test compilation with XeLaTeX
- Returns detailed error reports and warnings
- Helps catch errors before printing

#### `read_document`
Read a document file with line numbers for editing.

```json
{
  "name": "read_document",
  "arguments": {
    "file_path": "proposal.tex",  // or full path
    "offset": 1,                  // starting line (optional, default: 1)
    "limit": 50                   // number of lines (optional, default: 50)
  }
}
```

**Features:**
- Returns content with line numbers in `cat -n` format
- Works with any text file in Documents folder
- Smart path handling (defaults to ~/Documents/)
- Supports reading portions of large files

#### `edit_document`
Edit a document file by replacing exact string matches.

```json
{
  "name": "edit_document",
  "arguments": {
    "file_path": "proposal.tex",
    "old_string": "Hello World",
    "new_string": "Hello CUPS MCP",
    "expected_replacements": 1    // optional, default: 1
  }
}
```

**Features:**
- Exact string replacement with occurrence validation
- Returns context snippet showing changes
- Prevents accidental replacements with count validation
- Same smart path handling as read_document
- **Collaborative editing support:** Detects external file changes and shows diffs
- Prevents overwrites when user has edited file externally
- Automatically tracks file modifications for safe concurrent editing

#### `check_document_status`
Check if a document has been modified externally and show changes.

```json
{
  "name": "check_document_status",
  "arguments": {
    "file_path": "proposal.tex"  // or full path
  }
}
```

**Features:**
- Tracks document modification times and content hashes
- Detects external changes made by users or other programs
- Shows unified diff of what changed since last read
- Helps coordinate collaborative editing between AI and users
- Essential for preventing conflicting edits in shared documents

**Path handling for save tools:**
- Simple filename (e.g., `report.pdf`) → Saves to `~/Documents/`
- Full path (e.g., `/home/user/Documents/report.pdf`) → Uses exact path
- Path with `~` (e.g., `~/Downloads/report.pdf`) → Expands to home directory

**Automatic features:**
- Creates Documents directory if it doesn't exist
- Generates unique filename if file already exists (adds _1, _2, etc.)
- Returns clear error messages for permission issues or other failures

### AI Agent Guidelines

#### Printer Selection Logic

When using the printing tools, AI agents should follow this logic:

1. **First print request:**
   - If user doesn't specify, ask: "Would you like to print or save as PDF?"
   - If printing and no default printer exists, ask which printer to use
   - Remember the chosen printer for the session

2. **Subsequent requests:**
   - Use the remembered printer from the first request
   - Only change if user explicitly specifies a different printer

#### File Paths

When saving PDFs with `markdown_to_pdf`:
- Use simple filenames (e.g., `report.pdf`) which save to `~/Documents/`
- Don't assume the user's home directory path
- Let the tool handle path expansion

This ensures users aren't repeatedly asked about printer selection and files are saved to predictable locations.

## Configuration for Claude Desktop and Claude Code

### Important: Workspace Path

TeXFlow requires a workspace path where all your document projects will be stored. This is passed as the last argument to the `texflow` command.

### For Claude Desktop

Claude Desktop uses a JSON configuration file to manage MCP servers. The location depends on your operating system:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

#### Method 1: Run from GitHub (Recommended)

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "texflow": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/aaronsb/texflow-mcp.git", "texflow", "/home/aaron/Documents/TeXFlow"]
    }
  }
}
```

**Note**: Replace `/home/aaron/Documents/TeXFlow` with your desired workspace path.

#### Method 2: Run from local directory

If you've cloned the repository locally:

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

**Note**: Replace `/path/to/texflow-mcp` with the actual path to your cloned repository.

After editing the config file, restart Claude Desktop for the changes to take effect.

### For Claude Code

Claude Code provides a CLI command to add MCP servers. You can choose between different scopes:

- `--scope user`: Available across all your projects (recommended)
- `--scope project`: Only available in the current project
- `--scope local`: Available only on this machine

#### Method 1: Run from GitHub (Recommended)

```bash
# Add with user scope (available in all projects)
claude mcp add --scope user texflow uvx -- --from git+https://github.com/aaronsb/texflow-mcp.git texflow ~/Documents/TeXFlow

# Or with project scope (current project only)
claude mcp add --scope project texflow uvx -- --from git+https://github.com/aaronsb/texflow-mcp.git texflow ~/Documents/TeXFlow
```

#### Method 2: Run from local directory

If you've cloned the repository:

```bash
# Add with user scope
claude mcp add --scope user texflow uv -- --directory /path/to/texflow-mcp run texflow ~/Documents/TeXFlow

# Or with project scope
claude mcp add --scope project texflow uv -- --directory /path/to/texflow-mcp run texflow ~/Documents/TeXFlow
```

**Note**: The `--` after the scope is required to separate Claude Code options from the command arguments.

### Workspace Path Options

You can specify the workspace path in three ways:

1. **Command line argument**: `~/Documents/TeXFlow` as shown in the examples above
2. **Environment variable**: Set `TEXFLOW_WORKSPACE=~/Documents/TeXFlow` in your shell or system environment
3. **Default**: If neither is provided, defaults to `~/Documents/TeXFlow`

All TeXFlow projects and documents will be created within this workspace directory.

### Verifying Installation

After installation, you can verify TeXFlow is working by asking Claude to:

1. List available TeXFlow projects: "Use texflow to list my projects"
2. Check system dependencies: "Check texflow system dependencies"
3. Create a test project: "Create a new texflow project called 'test'"

## AI-to-AI Collaboration 🤖🤝🤖

The collaborative editing features enable fascinating multi-agent workflows:

### Use Cases
- **Parallel Document Development**: Multiple AI agents can work on different sections simultaneously
- **Review Workflows**: One AI drafts, another reviews and edits
- **Specialized Collaboration**: Domain-specific AIs (e.g., technical writer + code reviewer) working together
- **Iterative Refinement**: AIs can build upon each other's contributions with full visibility

### How It Works
1. **Agent A** reads and edits a document, establishing a baseline
2. **Agent B** detects Agent A's changes through the diff system
3. **Agent B** reviews the changes before making its own contributions
4. Each agent maintains awareness of others' modifications through the tracking system

### Example Workflow
```bash
# Agent 1 (Technical Writer AI)
- Creates initial documentation structure
- Writes API reference sections

# Agent 2 (Code Examples AI)  
- Detects Agent 1's additions
- Adds code examples to each API section
- Preserves Agent 1's documentation

# Agent 3 (Review AI)
- Sees combined work from both agents
- Fixes inconsistencies
- Adds cross-references
```

This opens up entirely new possibilities for AI collaboration on complex documentation and content creation tasks.

## Examples

### Common Workflows

#### Academic Paper with Citations
```python
# Create project structure
project(action="create", name="ml-paper", description="Machine learning research paper")

# Create bibliography
document(action="create", content="@article{smith2023,...}", path="refs.bib")

# Create main document
document(action="create", content="\\documentclass{article}...", path="paper.tex")

# Export to PDF
output(action="export", source="paper.tex", output_path="paper.pdf")
```

#### Convert and Edit Workflow
```python
# Convert existing Markdown notes to LaTeX
document(action="convert", source="notes.md", target_format="latex")

# Edit the converted file
document(action="edit", path="notes.tex", old_string="TODO", new_string="Introduction")

# Generate PDF
output(action="export", source="notes.tex")
```

### Workflow Features

The system prevents common AI workflow issues:

1. **Smart Content Detection**: The server detects when LaTeX content has already been saved and warns against regenerating it
2. **Clear Tool Guidance**: Tool descriptions guide the preferred workflow (save → use file path)
3. **Better Error Handling**: LaTeX error parser provides specific package installation instructions

Example of the improved workflow:
```python
# Step 1: Save LaTeX content
save_latex(content="...", filename="paper.tex")
# Returns: "LaTeX saved successfully to: /home/user/Documents/paper.tex"

# Step 2: Convert to PDF using file path (not content!)
latex_to_pdf(file_path="/home/user/Documents/paper.tex", output_path="paper.pdf")
# Efficient: Uses saved file instead of regenerating content
```

## Documentation

- 📖 [Tool Reference](docs/TEXFLOW_REFERENCE.md) - Complete guide to all 9 semantic tools
- 🤝 [Collaborative Editing Guide](docs/COLLABORATIVE_EDITING.md) - Deep dive into collaboration features
- 🎯 [LaTeX Reference Design](docs/LATEX_REFERENCE_DESIGN.md) - Design of the LaTeX documentation tool
- 📄 [System Dependencies](docs/SYSTEM_DEPENDENCIES.md) - System requirements and dependency management
- 👨‍🍳 [Recipe Book Example](docs/RECIPE_BOOK_EXAMPLE.md) - Practical example creating a recipe book
- 🚀 [Complete Workflow Example](docs/COMPLETE_WORKFLOW_EXAMPLE.md) - End-to-end workflow examples

## Future Enhancements

- [ ] HTML to PDF printing (via weasyprint)
- [ ] SVG to PDF printing (via rsvg-convert)
- [ ] Image format handling and scaling
- [ ] Print job status tracking
- [ ] Print job cancellation
- [ ] Printer options (paper size, orientation, etc.)
- [ ] Base64 encoded content support

## License

MIT