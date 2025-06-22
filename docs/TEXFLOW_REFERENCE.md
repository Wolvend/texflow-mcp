# TeXFlow Reference Guide

## Overview

TeXFlow is a semantic document authoring system that provides intelligent workflow guidance for creating LaTeX and Markdown documents. It transforms document creation from a series of technical commands into natural, intent-based operations.

## Architecture

### Semantic Layer Design

```
User Intent → Semantic Router → Operation Handler → Core Implementation
     ↓              ↓                   ↓                    ↓
"Write paper"  Detect context    Execute action      Generate output
                Add hints         Track state         Return guidance
```

The semantic layer:
- **Understands intent** rather than requiring technical format knowledge
- **Provides workflow guidance** suggesting logical next steps
- **Auto-detects formats** based on content and purpose
- **Maintains context** across operations

### Implementation Structure

- `texflow_unified.py` - MCP server entry point with semantic tools
- `src/texflow_semantic.py` - Semantic layer orchestration
- `src/core/semantic_router.py` - Intelligent routing with workflow hints
- `src/features/*/` - Operation implementations
- `texflow.py` - Core implementation (original functionality)

## The 9 Semantic Tools

### 1. `document` - Document Lifecycle Management

**Purpose**: Create, read, edit, convert, and validate documents with intelligent format handling.

**Actions:**
- `create` - Create new document with auto-format detection
- `read` - Read document with line numbers
- `edit` - Make targeted edits
- `convert` - Transform between formats
- `validate` - Check syntax and structure
- `status` - Check for external modifications
- `inspect` - View PDF pages as images

**Examples:**
```python
# Create with smart format detection
document(action="create", content="# Title\n\n$E = mc^2$", intent="research paper")
# → Creates LaTeX due to math content

# Convert existing file (preferred over recreating!)
document(action="convert", source="notes.md", target_format="latex")

# Edit specific content
document(action="edit", path="paper.tex", old_string="draft", new_string="final")
```

### 2. `output` - Document Output Generation

**Purpose**: Export documents to various formats and print.

**Actions:**
- `export` - Generate PDF, DOCX, HTML, etc.
- `print` - Send to physical printer

**Examples:**
```python
# Export to PDF (auto-compiles LaTeX)
output(action="export", source="paper.tex", output_path="paper.pdf")

# Print with automatic format handling
output(action="print", source="document.md")
```

### 3. `project` - Project Management

**Purpose**: Organize documents in structured projects.

**Actions:**
- `create` - Create new project with organized structure
- `switch` - Change active project
- `list` - Show all projects
- `info` - Get current project details
- `import` - Import existing directory as project
- `close` - Work without project context

**Examples:**
```python
# Create project with AI-generated structure
project(action="create", name="thesis", description="PhD thesis on quantum computing")

# Import existing work
project(action="import", name="existing-papers")
```

### 4. `discover` - Content Discovery

**Purpose**: Find documents, fonts, system capabilities, and packages.

**Actions:**
- `documents` - List documents in project
- `recent` - Show recently modified documents
- `fonts` - Browse available fonts
- `capabilities` - Check system dependencies
- `packages` - List installed LaTeX packages

**Examples:**
```python
discover(action="documents")  # Lists all documents in current project
discover(action="capabilities")  # Shows system readiness
```

### 5. `organizer` - Document Organization

**Purpose**: Move, archive, and clean up documents and auxiliary files.

**Actions:**
- `move` - Move or rename documents
- `archive` - Soft delete to hidden archive
- `restore` - Restore archived documents
- `clean_aux` - Remove LaTeX auxiliary files
- `batch` - Execute multiple operations

**Examples:**
```python
# Clean LaTeX build files
organizer(action="clean_aux", path="paper.tex")

# Archive old versions
organizer(action="archive", path="draft-v1.tex", reason="Superseded by v2")
```

### 6. `printer` - Printer Management

**Purpose**: Configure and manage printers.

**Actions:**
- `list` - Show available printers
- `info` - Get printer details
- `set_default` - Change default printer
- `enable`/`disable` - Control printer availability

### 7. `workflow` - Workflow Guidance

**Purpose**: Get intelligent suggestions for document tasks.

**Actions:**
- `suggest` - Get workflow recommendations
- `guide` - Get comprehensive guidance
- `next_steps` - See contextual next actions

**Examples:**
```python
workflow(action="suggest", task="write research paper")
# → Returns step-by-step guidance
```

### 8. `templates` - Template Management

**Purpose**: Use and manage document templates.

**Actions:**
- `list` - Show available templates
- `use` - Instantiate a template
- `create` - Create new template
- `activate` - Convert project to template

**Examples:**
```python
templates(action="use", name="ieee-paper", target="my-paper.tex")
```

### 9. `reference` - LaTeX Documentation Search

**Purpose**: Search LaTeX commands, packages, symbols, and get error help.

**Actions:**
- `search` - Search commands and topics
- `symbol` - Find symbols by description
- `package` - Get package information
- `check_style` - Analyze document style
- `error_help` - Decode error messages
- `example` - Get working examples

**Examples:**
```python
# Find what package provides a command
reference(action="search", query="rowcolor")
# → Returns: colortbl package required

# Find symbols
reference(action="symbol", description="approximately equal")
# → Returns: ≈ (\\approx)

# Get error help
reference(action="error_help", error="Undefined control sequence")
```

## Workflow Philosophy

### 1. Project-First Approach
Always work within a project for better organization:
```python
project(action="create", name="my-paper")
document(action="create", content="...")  # Automatically in project
```

### 2. Edit Over Recreate
Modify existing documents instead of regenerating:
```python
# Good: Edit existing
document(action="edit", path="paper.tex", changes=[...])

# Avoid: Recreating entire document
document(action="create", content="[entire document]")
```

### 3. Convert Over Rewrite
Transform formats instead of manual conversion:
```python
# Good: Use conversion
document(action="convert", source="notes.md", target_format="latex")

# Avoid: Manual rewriting
```

### 4. Validate Before Export
Check LaTeX syntax before generating PDFs:
```python
document(action="validate", path="paper.tex")
output(action="export", source="paper.tex")
```

## System Requirements

### Essential (Required)
- **pandoc** - Document conversion engine
- **XeLaTeX** or **pdfLaTeX** - LaTeX compilation
- **CUPS** - Printing system (Linux/macOS)

### Optional (Enhanced Features)
- **poppler-utils** - PDF inspection
- **ghostscript** - PDF optimization
- **chktex** - LaTeX linting

Check system status:
```python
discover(action="capabilities")
```

## MCP Resources

TeXFlow provides several MCP resources for system monitoring:

- `system-dependencies://status` - Complete dependency status
- `system-dependencies://summary` - Human-readable summary
- `texflow://projects` - List all projects
- `texflow://templates` - Browse templates
- `texflow://workflow-guide` - Context-aware guidance
- `texflow://latex-reference` - Reference tool statistics

## Common Workflows

### Research Paper
```python
# 1. Create project
project(action="create", name="quantum-paper", description="Research on quantum entanglement")

# 2. Start from template
templates(action="use", name="ieee-paper")

# 3. Write content
document(action="edit", path="paper.tex", ...)

# 4. Add references
document(action="create", path="references.bib", content="@article{...}")

# 5. Validate and export
document(action="validate", path="paper.tex")
output(action="export", source="paper.tex", output_path="final.pdf")
```

### Quick Note to PDF
```python
# Direct creation and export
document(action="create", content="# Meeting Notes\n\n- Item 1\n- Item 2")
output(action="export", source="meeting-notes.md", output_path="notes.pdf")
```

## Tips and Best Practices

1. **Let TeXFlow detect formats** - It's smart about choosing LaTeX vs Markdown
2. **Use templates** - Start from templates to save time
3. **Trust the workflow hints** - They guide you to the next logical step
4. **Check capabilities first** - Run `discover(action="capabilities")` on new systems
5. **Use the reference tool** - Get instant help without leaving your workflow

## Troubleshooting

### Common Issues

**"Undefined control sequence" error**
```python
reference(action="error_help", error="Undefined control sequence \\somecommand")
```

**Package not found**
```python
reference(action="package", name="missing-package")
discover(action="packages")  # Check what's installed
```

**PDF generation fails**
```python
document(action="validate", path="document.tex")  # Check for errors first
discover(action="capabilities")  # Ensure XeLaTeX is installed
```

For more examples and detailed workflows, see the example documents in the `docs/` directory.