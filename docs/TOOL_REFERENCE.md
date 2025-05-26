# CUPS MCP Tool Reference

Quick reference for all 19 tools provided by the CUPS MCP Server.

## Printer Management Tools

### `list_printers`
List all available CUPS printers.
```json
{"name": "list_printers"}
```

### `get_printer_info`
Get detailed information about a specific printer.
```json
{
  "name": "get_printer_info",
  "arguments": {"printer_name": "HP_LaserJet"}
}
```

### `set_default_printer`
Set a printer as the system default.
```json
{
  "name": "set_default_printer",
  "arguments": {"printer_name": "HP_LaserJet"}
}
```

### `enable_printer` / `disable_printer`
Enable or disable a printer.
```json
{
  "name": "enable_printer",
  "arguments": {"printer_name": "HP_LaserJet"}
}
```

### `update_printer_info`
Update printer description and location.
```json
{
  "name": "update_printer_info",
  "arguments": {
    "printer_name": "HP_LaserJet",
    "description": "Office Printer",
    "location": "Room 101"
  }
}
```

## Printing Tools

### `print_text`
Print plain text content.
```json
{
  "name": "print_text",
  "arguments": {
    "content": "Hello, World!",
    "printer": "HP_LaserJet"  // optional
  }
}
```

### `print_markdown`
Print Markdown (rendered to PDF).
```json
{
  "name": "print_markdown",
  "arguments": {
    "content": "# Title\n\nContent with **formatting**",
    "printer": "HP_LaserJet",  // optional
    "title": "My Document"     // optional
  }
}
```

### `print_latex`
Print LaTeX documents.
```json
{
  "name": "print_latex",
  "arguments": {
    "content": "\\documentclass{article}\\begin{document}Hello\\end{document}",
    "printer": "HP_LaserJet",  // optional
    "title": "My Document"     // optional
  }
}
```

### `print_file`
Print any file from the filesystem.
```json
{
  "name": "print_file",
  "arguments": {
    "path": "/home/user/document.pdf",
    "printer": "HP_LaserJet"  // optional
  }
}
```

### `print_from_documents`
Print files from Documents folder.
```json
{
  "name": "print_from_documents",
  "arguments": {
    "filename": "report.pdf",
    "folder": "projects",      // optional subfolder
    "printer": "HP_LaserJet"   // optional
  }
}
```

## Document Creation Tools

### `markdown_to_pdf`
Convert Markdown to PDF (save without printing).
```json
{
  "name": "markdown_to_pdf",
  "arguments": {
    "content": "# Document\n\nContent",
    "output_path": "report.pdf",
    "title": "My Report"  // optional
  }
}
```

### `save_markdown`
Save Markdown content to file.
```json
{
  "name": "save_markdown",
  "arguments": {
    "content": "# My Document\n\nContent",
    "filename": "notes.md"
  }
}
```

### `save_latex`
Save LaTeX content to file.
```json
{
  "name": "save_latex",
  "arguments": {
    "content": "\\documentclass{article}...",
    "filename": "paper.tex"
  }
}
```

### `validate_latex`
Check LaTeX syntax before compilation.
```json
{
  "name": "validate_latex",
  "arguments": {
    "content": "\\documentclass{article}..."
  }
}
```

## Document Management Tools

### `list_documents`
List files in Documents folder.
```json
{
  "name": "list_documents",
  "arguments": {
    "folder": "projects"  // optional subfolder
  }
}
```

## Collaborative Editing Tools

### `read_document`
Read document with line numbers (establishes tracking).
```json
{
  "name": "read_document",
  "arguments": {
    "file_path": "proposal.tex",
    "offset": 1,   // optional, default: 1
    "limit": 50    // optional, default: 50
  }
}
```

### `edit_document`
Edit document with conflict detection.
```json
{
  "name": "edit_document",
  "arguments": {
    "file_path": "proposal.tex",
    "old_string": "old text",
    "new_string": "new text",
    "expected_replacements": 1  // optional
  }
}
```

### `check_document_status`
Check if document was modified externally.
```json
{
  "name": "check_document_status",
  "arguments": {
    "file_path": "proposal.tex"
  }
}
```

## Path Handling

### Default Locations
- Simple filename → `~/Documents/`
- Relative path → `~/Documents/subfolder/`
- Absolute path → Uses exact path
- Path with `~` → Expands to home

### Examples
- `"report.pdf"` → `/home/user/Documents/report.pdf`
- `"projects/report.pdf"` → `/home/user/Documents/projects/report.pdf`
- `"/tmp/report.pdf"` → `/tmp/report.pdf`
- `"~/Downloads/report.pdf"` → `/home/user/Downloads/report.pdf`

## Best Practices

### For AI Agents
1. Check for default printer before printing
2. Remember user's printer choice for session
3. Read documents before editing
4. Handle external changes gracefully
5. Use simple filenames for user convenience

### For Humans
1. Save files to Documents folder for easy access
2. Use the validation tool for complex LaTeX
3. Check document status if editing externally
4. Let AI complete operations before editing

## Error Handling

### Common Errors
- **File not found**: Check path and use `list_documents`
- **Printer not found**: Use `list_printers` first
- **External changes detected**: Re-read the document
- **Permission denied**: Check file permissions
- **Missing dependencies**: Install required tools

### Dependency Errors
Tools will not be registered if dependencies are missing:
- `print_markdown` requires `pandoc`
- `print_latex` requires `xelatex`
- HTML printing requires `weasyprint`
- SVG printing requires `rsvg-convert`