# Document Conversion and Export Code Duplication Analysis

## Summary

After analyzing the TeXFlow codebase, I found several instances of code duplication in document conversion and export functionality:

## 1. **Pandoc Usage for Markdown to LaTeX Conversion**

### Location 1: `src/features/document/document_operation.py` (lines 374-379)
```python
subprocess.run(
    ["pandoc", "-f", "markdown", "-t", "latex", "-s", "-o", str(output_file), str(source_path)], 
    check=True
)
```

### Location 2: `texflow.py` (lines 544-545)
```python
# Markdown to PDF via pandoc with XeLaTeX
subprocess.run(["pandoc", source_path, "-o", out_path, "--pdf-engine=xelatex"], check=True)
```

**Duplication**: Both locations use pandoc for conversion but with slightly different parameters. The document operation uses explicit format flags while texflow.py uses the pdf-engine parameter.

## 2. **XeLaTeX Usage for LaTeX to PDF Conversion**

### Location 1: `src/features/document/document_operation.py` (lines 593-598)
```python
# LaTeX validation via xelatex
result = subprocess.run(
    ["xelatex", "-interaction=nonstopmode", "-halt-on-error", str(temp_path)],
    cwd=temp_path.parent,
    capture_output=True,
    text=True
)
```

### Location 2: `texflow.py` (lines 547-549)
```python
# LaTeX to PDF via xelatex directly
result = subprocess.run(["xelatex", "-interaction=nonstopmode", source_path.name], 
                      cwd=source_path.parent, check=True)
```

**Duplication**: Both use xelatex with similar parameters but the document operation adds `-halt-on-error` and captures output for validation purposes.

## 3. **Format Detection Logic**

### Location 1: `src/features/document/document_operation.py` (lines 484-511)
- `_detect_format()`: Detects format from content using regex patterns
- `_detect_format_from_path()`: Detects format from file extension

### Location 2: `src/features/output/output_operation.py` (lines 268-302)
- `_detect_content_format()`: Nearly identical regex pattern matching
- `_detect_file_format()`: Similar file extension checking

**Duplication**: Both modules implement very similar format detection logic with overlapping regex patterns and file extension mappings.

## 4. **Document Action Handlers**

### Multiple Implementations:
1. **Document Operation** (`src/features/document/document_operation.py`): 
   - Handles convert action within the semantic layer
   - Validates LaTeX content
   
2. **Output Operation** (`src/features/output/output_operation.py`):
   - Handles export action 
   - Delegates to `texflow.output()` for actual conversion

3. **Original TeXFlow** (`texflow.py`):
   - `output()` function handles both print and export actions
   - Contains the actual conversion implementation

**Duplication**: The conversion/export functionality is split across three files with overlapping responsibilities.

## 5. **Error Handling Patterns**

Similar error handling patterns are repeated across all three files:
- FileNotFoundError for missing executables (pandoc, xelatex)
- subprocess.CalledProcessError for failed conversions
- Path validation and existence checks

## Recommendations

1. **Consolidate Conversion Logic**: Create a single conversion service/module that handles all document transformations
2. **Unified Format Detection**: Move all format detection to a single module (already partially done in `src/core/format_detector.py`)
3. **Centralize Process Execution**: Create a wrapper for subprocess calls to pandoc/xelatex with consistent error handling
4. **Single Source of Truth**: The semantic layer should fully replace the original implementation rather than delegating to it
5. **DRY Principle**: Extract common patterns like file validation, temporary file handling, and cleanup into utility functions

## Impact

This duplication leads to:
- Maintenance burden (fixing bugs in multiple places)
- Inconsistent behavior (different parameters to same tools)
- Confusion about which implementation to use
- Potential for diverging functionality over time