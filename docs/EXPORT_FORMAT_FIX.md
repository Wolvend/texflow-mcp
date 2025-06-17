# TeXFlow Export Format Parameter Issue & Solution

## Problem Summary

Agents are incorrectly using the `format` parameter when exporting documents. They're setting `format: "pdf"` thinking it specifies the target format, but it actually specifies the **source** format.

## Error Reproduction

```python
# ❌ INCORRECT - This causes the error
texflow:output(
    action: "export",
    source: "content/document.tex",
    format: "pdf",  # Wrong! This means source is PDF
    output_path: "output/document.pdf"
)

# ✅ CORRECT - Omit format or specify source format
texflow:output(
    action: "export", 
    source: "content/document.tex",
    format: "latex",  # Or omit entirely for auto-detection
    output_path: "output/document.pdf"
)
```

## Root Cause

1. The `format` parameter is ambiguous - it refers to the source format, not target
2. Export can produce multiple formats (PDF, DOCX, ODT, RTF, HTML, EPUB) but PDF is default
3. The error message is confusing: "Cannot export from format 'pdf' to PDF"
4. Missing semantic hints after LaTeX document creation

## Proposed Fixes

### Fix 1: Improve Error Message
Change line 225-229 in `output_operation.py`:

```python
return {
    "error": f"Invalid source format '{format_hint}'. The 'format' parameter specifies the source document format, not the target.",
    "supported_source_formats": ["markdown", "latex"],
    "hint": "For .tex files use format='latex', for .md files use format='markdown', or omit format for auto-detection",
    "note": "Target format is determined by file extension in output_path (default: .pdf)"
}
```

### Fix 2: Add Semantic Hints for LaTeX Workflow
Add workflow hints in semantic router after LaTeX document operations:

```python
# In semantic router after document creation/edit
if format == "latex":
    hints = [
        "✓ LaTeX document saved",
        "💡 Recommended workflow:",
        "  1. document(action='validate') - Check LaTeX syntax",
        "  2. output(action='export', source='path/to/file.tex') - Generate PDF",
        "     • Don't set format='pdf' - that's the source format",
        "     • Default output is PDF, use .docx extension for Word"
    ]
```

### Fix 3: Support Multiple Output Formats
The output_path extension should determine the target format:

```python
# Examples of proper usage:
texflow:output(
    action: "export",
    source: "content/document.tex",
    output_path: "output/document.pdf"    # → PDF (default)
)

texflow:output(
    action: "export",
    source: "content/document.tex",
    output_path: "output/document.docx"   # → Word document
)

texflow:output(
    action: "export",
    source: "content/document.tex",
    output_path: "output/document.html"   # → HTML
)
```

## Implementation Plan

1. **Immediate**: Fix error message to clarify format parameter
2. **High Priority**: Add semantic hints after LaTeX document operations
3. **Clarify**: Document that output format is determined by file extension

## Usage Examples

### Correct Export Usage

```python
# LaTeX to PDF (most common)
texflow:output(
    action: "export",
    source: "content/report.tex",
    output_path: "output/report.pdf"
)

# LaTeX to Word (for collaboration)
texflow:output(
    action: "export",
    source: "content/report.tex",
    output_path: "output/report.docx"
)

# Markdown to PDF
texflow:output(
    action: "export",
    source: "content/notes.md",
    format: "markdown",  # Optional, auto-detected from .md
    output_path: "output/notes.pdf"
)
```

### Testing

Run `test_agent_scenario.py` to verify the fix handles all cases correctly.