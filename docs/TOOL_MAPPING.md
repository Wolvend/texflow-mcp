# TeXFlow Tool Mapping Guide

This document maps the existing 27+ tools to the new semantic operations.

## Document Operation

The `document` operation handles all document creation, editing, and format management.

### Mapping

| Old Tool | New Operation | Action | Example |
|----------|---------------|---------|---------|
| `save_markdown` | `document` | `create` | `document(action="create", content="...", format="markdown")` |
| `save_latex` | `document` | `create` | `document(action="create", content="...", format="latex")` |
| `read_document` | `document` | `read` | `document(action="read", path="intro.md")` |
| `edit_document` | `document` | `edit` | `document(action="edit", path="...", changes=[...])` |
| `check_document_status` | `document` | `status` | `document(action="status", path="...")` |
| `validate_latex` | `document` | `validate` | `document(action="validate", content="...")` |
| `markdown_to_latex` | `document` | `convert` | `document(action="convert", source="...", target_format="latex")` |

### Key Improvements
- Format auto-detection when not specified
- Unified interface for all document types
- Intelligent path resolution (project-aware)

## Output Operation

The `output` operation handles all forms of document output (print, PDF, preview).

### Mapping

| Old Tool | New Operation | Action | Example |
|----------|---------------|---------|---------|
| `print_text` | `output` | `print` | `output(action="print", content="...", format="text")` |
| `print_markdown` | `output` | `print` | `output(action="print", source="doc.md")` |
| `print_latex` | `output` | `print` | `output(action="print", source="doc.tex")` |
| `print_file` | `output` | `print` | `output(action="print", path="...")` |
| `print_from_documents` | `output` | `print` | `output(action="print", document="...")` |
| `markdown_to_pdf` | `output` | `export` | `output(action="export", source="...", format="pdf")` |
| `latex_to_pdf` | `output` | `export` | `output(action="export", source="...", format="pdf")` |

### Key Improvements
- Single operation for all output needs
- Automatic format detection
- Printer selection handled intelligently

## Project Operation

The `project` operation manages document projects.

### Mapping

| Old Tool | New Operation | Action | Example |
|----------|---------------|---------|---------|
| `create_project` | `project` | `create` | `project(action="create", name="...", description="...")` |
| `use_project` | `project` | `switch` | `project(action="switch", name="...")` |
| `list_projects` | `project` | `list` | `project(action="list")` |
| `project_info` | `project` | `info` | `project(action="info")` |

### Key Improvements
- Free-form project descriptions
- AI-guided directory structure
- Workflow hints after project creation

## Printer Operation

The `printer` operation manages all printer-related tasks.

### Mapping

| Old Tool | New Operation | Action | Example |
|----------|---------------|---------|---------|
| `list_printers` | `printer` | `list` | `printer(action="list")` |
| `get_printer_info` | `printer` | `info` | `printer(action="info", name="...")` |
| `set_default_printer` | `printer` | `set_default` | `printer(action="set_default", name="...")` |
| `enable_printer` | `printer` | `enable` | `printer(action="enable", name="...")` |
| `disable_printer` | `printer` | `disable` | `printer(action="disable", name="...")` |
| `update_printer_info` | `printer` | `update` | `printer(action="update", name="...", info={...})` |

### Key Improvements
- Grouped configuration actions
- Clearer action names
- Consistent parameter naming

## Discover Operation

The `discover` operation helps users find documents, fonts, and system capabilities.

### Mapping

| Old Tool | New Operation | Action | Example |
|----------|---------------|---------|---------|
| `list_documents` | `discover` | `documents` | `discover(action="documents", folder="...")` |
| `list_available_fonts` | `discover` | `fonts` | `discover(action="fonts", style="serif")` |
| System checks | `discover` | `capabilities` | `discover(action="capabilities")` |

### Key Improvements
- Unified discovery interface
- Richer filtering options
- System capability reporting

## Workflow Operation

The `workflow` operation provides guidance and suggestions.

### Mapping

| Old Tool | New Operation | Action | Example |
|----------|---------------|---------|---------|
| `suggest_document_workflow` | `workflow` | `suggest` | `workflow(action="suggest", task="write a paper")` |
| (new) | `workflow` | `guide` | `workflow(action="guide", topic="citations")` |
| (new) | `workflow` | `next_steps` | `workflow(action="next_steps")` |

### Key Improvements
- Context-aware suggestions
- Learning resources
- Dynamic next step recommendations

## Migration Examples

### Example 1: Creating and Printing a Document

**Old way:**
```python
save_markdown("# My Document", "doc.md")
markdown_to_pdf(file_path="doc.md", output_path="doc.pdf")
print_file("doc.pdf", printer="default")
```

**New way:**
```python
result = document(action="create", content="# My Document", intent="quick note")
output(action="print", source=result["path"])
# System handles format detection and conversion automatically
```

### Example 2: Working with Projects

**Old way:**
```python
create_project("my-thesis", "thesis")
use_project("my-thesis")
save_latex("\\documentclass{article}...", "chapter1.tex")
latex_to_pdf(file_path="chapter1.tex", output_path="chapter1.pdf")
```

**New way:**
```python
project(action="create", name="my-thesis", description="PhD thesis on quantum computing")
document(action="create", content="\\documentclass{article}...", name="chapter1")
output(action="export", document="chapter1", format="pdf")
# System handles project context and paths automatically
```

## Backward Compatibility

During the transition period:

1. All original tools remain available
2. Semantic operations use the original tools internally
3. Both APIs can be used interchangeably
4. Deprecation warnings guide users to new patterns
5. Migration helper available: `workflow(action="migrate", old_command="save_latex(...)")`