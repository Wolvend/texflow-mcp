# TeXFlow Unified Tool Reference

TeXFlow provides 8 semantic tools that understand your intent and guide you through document workflows.

## Core Concepts

Each tool:
- **Accepts an `action` parameter** to specify what you want to do
- **Provides inward hints** through clear parameter descriptions and examples
- **Returns outward hints** suggesting logical next steps
- **Auto-detects formats** when possible to reduce complexity
- **Remembers context** like current project and printer preferences

## The 7 Tools

### 1. `document` - Document Lifecycle Management

Manages creating, reading, editing, converting, and validating documents.

**Actions:**
- `create` - Create new document with auto-format detection
- `read` - Read document with line numbers
- `edit` - Make targeted edits with conflict detection
- `convert` - Transform between formats (e.g., Markdown→LaTeX)
- `validate` - Check syntax and structure
- `status` - Check for external modifications

**Key Parameters:**
- `content` - Document content (for create/validate)
- `path` - Document path (for read/edit/status)
- `source` - Source file (for convert - preferred over recreating!)
- `target_format` - Target format for conversion
- `intent` - Purpose like "research paper" or "quick note" (helps format selection)

**Examples:**
```python
# Create with smart format detection
document(action="create", content="# Quantum Theory\n\n$E = mc^2$", intent="research paper")
# → Creates LaTeX document due to math content and intent
# → Offers: read, edit, validate (for LaTeX), export

# Convert existing file (don't recreate!)
document(action="convert", source="notes.md", target_format="latex")
# → Creates notes.tex from notes.md
# → Suggests: edit the converted file

# Edit with multiple next steps
document(action="edit", path="paper.tex", old_string="draft", new_string="final")
# → Offers: edit more, review changes, validate, export

# Validate before export
document(action="validate", path="paper.tex")
# → If errors: suggests editing to fix
# → If warnings: suggests edit or export
# → If clean: suggests export to PDF

# Check before editing shared documents
document(action="status", path="shared.tex")
# → Shows modification time and size
# → Offers: read or edit
```

### 2. `output` - Print and Export

Handles all forms of output from the system.

**Actions:**
- `print` - Send to physical printer
- `export` - Generate PDF file
- `preview` - View rendered output (future)

**Key Parameters:**
- `source` - Path to existing file (PREFERRED - avoids regeneration)
- `content` - Direct content (use only if no file exists)
- `format` - Output format (auto-detected from file/content)
- `printer` - Printer name (remembered after first use)
- `output_path` - Where to save PDF

**Examples:**
```python
# Recommended: use existing files
output(action="export", source="thesis.tex", output_path="thesis.pdf")
# → Suggests: print the PDF or share it

# Print with smart conversion
output(action="print", source="notes.md")
# → Auto-converts to PDF and prints
```

### 3. `project` - Project Organization

Organizes work into structured projects.

**Actions:**
- `create` - Create project with AI-guided structure
- `switch` - Change active project
- `list` - Show all projects
- `info` - Get current project details
- `close` - Return to default Documents mode

**Key Parameters:**
- `name` - Project name
- `description` - Free-form description for AI structure generation

**Examples:**
```python
# Create with intelligent structure
project(action="create", name="quantum-paper", description="Research on quantum entanglement with experimental data")
# → Creates: content/, data/, figures/, output/ directories
# → Suggests: create introduction document

# Switch context
project(action="switch", name="thesis")
# → Subsequent operations use thesis project paths
```

### 4. `printer` - Hardware Management

Manages printing hardware configuration.

**Actions:**
- `list` - Show available printers
- `info` - Get printer details
- `set_default` - Change default printer
- `enable` - Allow job acceptance
- `disable` - Stop job acceptance
- `update` - Update metadata

**Examples:**
```python
printer(action="list")
# → Shows all printers with status
# → Suggests: set a default if none exists

printer(action="set_default", name="Office_Laser")
# → Sets default for all operations
```

### 5. `discover` - Resource Discovery

Finds documents, fonts, and system capabilities.

**Actions:**
- `documents` - List documents in project/folder
- `fonts` - Browse available fonts
- `capabilities` - Check system dependencies

**Key Parameters:**
- `folder` - Subfolder to search
- `style` - Font style filter (serif/sans/mono)

**Examples:**
```python
discover(action="fonts")
# → Lists all available font families (e.g., Barlow, DejaVu Serif)
# → Shows: "📝 Available fonts (296 found)..."

discover(action="fonts", style="serif")
# → Filters to serif fonts only
# → Also supports: sans, mono, display

discover(action="capabilities")
# → Shows what's installed (pandoc, XeLaTeX, fontconfig, etc.)
```

**Font Usage Note**: After discovering fonts, use them in LaTeX with `\setmainfont{FontName}`. If a desired font isn't available, install it at the system level first.

### 6. `archive` - Version Management

Manages document history with soft delete functionality.

**Actions:**
- `archive` - Soft delete (preserve in .texflow_archive)
- `restore` - Recover archived document
- `list` - Show archived documents
- `versions` - Find all versions of a document
- `cleanup` - Bulk archive by pattern

**Key Parameters:**
- `path` - Document to archive
- `pattern` - File pattern for cleanup (e.g., "*_old*")
- `reason` - Why archiving (helps with later recovery)

**Examples:**
```python
# Find all versions
archive(action="versions", filename="thesis.tex")
# → Shows current + all archived versions
# → Suggests: restore an older version

# Clean workspace
archive(action="cleanup", pattern="*_draft*")
# → Archives all draft files
# → Suggests: list archived files
```

### 7. `workflow` - Intelligent Guidance

Provides context-aware help and automation.

**Actions:**
- `suggest` - Get workflow recommendations
- `guide` - Topic-specific help
- `next_steps` - Contextual next actions

**Examples:**
```python
workflow(action="suggest", task="write paper with citations")
# → Recommends: 1) Create project, 2) Create .bib file, 3) Use LaTeX template

workflow(action="guide", task="citations")
# → Shows citation workflow with examples
```

## 8. Templates Tool

Start quickly with pre-built document templates or create your own for reuse.

**Actions:**
- `list` - Show available templates (optionally filtered by category)
- `use` - Copy a template to current project or specified location
- `create` - Create a new template from content or existing document
- `copy` - Duplicate an existing template with a new name
- `edit` - Get location to modify an existing template
- `rename` - Rename a template
- `delete` - Remove a template
- `info` - Get details about a specific template

**Examples:**
```python
# List all templates
templates(action="list")
# → Shows: default/minimal, letter/formal, etc.

# Use a template in current project
templates(action="use", category="default", name="minimal")
# → Copies template to project with hints for next steps

# Create from existing document
templates(action="create", category="thesis", name="phd-format", 
         source="my-thesis.tex")
# → Saves document as reusable template

# Quick letter template
templates(action="use", category="letter", name="formal", 
         target="complaint.tex")
# → Ready-to-edit letter template
```

## Best Practices

1. **Use existing files** - Prefer `source` over `content` parameters
2. **Check status first** - Use `document(action="status")` before editing shared files
3. **Let format auto-detect** - The system chooses optimal format based on content
4. **Follow the hints** - Each operation suggests logical next steps
5. **Work in projects** - Organizes related documents together

## Common Workflows

### Research Paper
```python
1. project(action="create", name="my-paper", description="Research paper on AI")
2. document(action="create", content="# Introduction", intent="research paper")
3. document(action="convert", source="intro.md", target_format="latex")
4. document(action="edit", path="intro.tex", changes=[...])
5. output(action="export", source="intro.tex", output_path="intro.pdf")
```

### Quick Note to Print
```python
1. document(action="create", content="Meeting notes...", intent="quick note")
2. output(action="print", source="notes.md")
```

### Document Cleanup
```python
1. archive(action="versions", filename="report.tex")  # See what exists
2. archive(action="cleanup", pattern="*_old*")       # Archive old versions
3. discover(action="documents")                      # See cleaned workspace
```