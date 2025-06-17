# TeXFlow Validation Parameter Fix

## Issues Found

1. **Validation Parameter Mismatch**
   - The `document(action='validate')` expects `content_or_path` parameter
   - But the MCP tool signature only provides `path` parameter
   - This causes validation to fail with "content_or_path parameter is required"

2. **XeLaTeX Compilation Failures**
   - When LaTeX documents use XeLaTeX-specific features (fontspec, custom fonts)
   - The compilation fails with non-zero exit status
   - Common causes: missing fonts, missing packages, Unicode issues

## Fix Applied

### 1. Parameter Mapping Fix (texflow_unified.py)

Added parameter mapping for the validate action:

```python
# Document operation expects 'content_or_path' for validate action
if action == "validate" and path is not None:
    params["content_or_path"] = params.pop("path", None)
```

This fix is at line 203-205 in texflow_unified.py.

## To Test After Restarting Claude Code

1. Restart Claude Code to pick up the changes
2. Test validation:
   ```
   mcp__texflow__document(action="validate", path="content/test-document.tex")
   ```

3. For XeLaTeX issues, the agent should:
   - Try simpler LaTeX first (without fontspec)
   - Check system dependencies with `discover(action='capabilities')`
   - Use pandoc for conversion if XeLaTeX fails

## Common XeLaTeX Failure Causes

1. **Missing Fonts**: Using `\setmainfont{Arial}` when Arial isn't available
2. **Missing Packages**: `fontspec`, `unicode-math` not installed
3. **Encoding Issues**: Special characters without proper Unicode support
4. **Package Conflicts**: Incompatible package combinations

## Recommendation

After restarting, the validation parameter issue should be fixed. For XeLaTeX failures, the agent should fall back to simpler LaTeX or use pandoc for conversion.