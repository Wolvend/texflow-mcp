# TeXFlow Export Error Summary

## The Problem

The agent is using `format: "pdf"` when trying to export a `.tex` file to PDF, causing this error:
```
❌ Error: Cannot export from format 'pdf' to PDF. Auto-detected format may be unsupported.
```

## Why This Happens

1. **Parameter Confusion**: The `format` parameter specifies the **source** format (latex/markdown), not the target format
2. **Assumption**: Agents assume `format: "pdf"` means "export to PDF" 
3. **Auto-detection Issue**: When the agent specifies `format: "pdf"`, it overrides the auto-detection that would correctly identify `.tex` as LaTeX

## The Solution

### For Agents Using TeXFlow

```python
# ✅ CORRECT - Let auto-detection work or specify source format
texflow:output(
    action: "export",
    source: "content/document.tex",  # Auto-detects as LaTeX
    output_path: "output/document.pdf"
)

# ✅ ALSO CORRECT - Explicitly specify source format
texflow:output(
    action: "export", 
    source: "content/document.tex",
    format: "latex",  # Source format, not target!
    output_path: "output/document.pdf"
)

# ❌ WRONG - Don't do this!
texflow:output(
    action: "export",
    source: "content/document.tex",
    format: "pdf",  # This says the source is already PDF!
    output_path: "output/document.pdf"
)
```

### Target Format Selection

The target format is determined by the file extension in `output_path`:
- `.pdf` → PDF (default)
- `.docx` → Word document
- `.html` → HTML
- `.epub` → EPUB
- `.odt` → OpenDocument
- `.rtf` → Rich Text Format

## Recommended Fixes

1. **Update Error Message**: Make it clear that `format` is for source format
2. **Add Workflow Hints**: After creating/editing LaTeX documents, suggest the correct export syntax
3. **Documentation**: Clarify parameter usage in tool descriptions

## Quick Test

To reproduce and verify the fix:
```bash
python test_agent_scenario.py
```

This shows:
- Scenario 1: Wrong file extension (.pdf instead of .tex)
- Scenario 2: Correct usage
- Scenario 3: The actual bug - setting format='pdf'