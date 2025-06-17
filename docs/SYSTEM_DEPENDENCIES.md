# TeXFlow System Dependencies

TeXFlow includes a dynamic system dependency checker that monitors external tools required for full functionality. This system automatically detects available tools, their versions, and provides installation guidance for missing dependencies.

## Architecture

The system consists of three main components:

1. **Manifest File** (`config/system_dependencies.json`) - Defines all dependencies with platform-specific installation info
2. **Checker Module** (`src/core/system_checker.py`) - Performs dependency detection and version checking
3. **MCP Resources** - Exposes dependency status through three MCP resources

## MCP Resources

The TeXFlow MCP server exposes three resources for dependency information:

### `system-dependencies://status`
Returns complete dependency status as JSON, including:
- Detailed status for each dependency
- Version information where available
- Platform compatibility
- Installation options for missing tools

### `system-dependencies://summary`
Returns a human-readable summary with:
- Overall system status (fully_operational, operational, degraded)
- Essential vs optional dependency counts
- Category-wise breakdowns with status icons

### `system-dependencies://missing`
Returns installation guidance for missing dependencies:
- Categorized by essential vs optional
- Platform-specific installation commands
- Package manager recommendations

## Dependency Categories

Dependencies are organized into logical categories:

### Essential (Required for Core Functionality)
- **document_processing**: pandoc for format conversion
- **latex_engine**: XeLaTeX for LaTeX compilation
- **font_management**: fontconfig for font discovery

### Optional (Enhanced Functionality)
- **printing**: CUPS for physical printing (Linux/macOS)
- **pdf_processing**: poppler-utils, ghostscript for PDF manipulation
- **latex_tools**: chktex for LaTeX syntax checking

## Platform Support

The system supports cross-platform detection for:
- **Linux**: apt, pacman, dnf package managers
- **macOS**: Homebrew, system tools
- **Windows**: chocolatey, scoop (limited support)

## Status Levels

The checker reports four overall status levels:

- **fully_operational**: All essential and optional dependencies available
- **operational**: All essential dependencies available, some optional missing
- **degraded**: Some essential dependencies missing
- **unknown**: Unable to determine status

## Adding New Dependencies

To add a new dependency to the manifest:

1. **Define the dependency** in `config/system_dependencies.json`:
```json
{
  "new_tool": {
    "name": "new_tool",
    "description": "Description of the tool",
    "commands": ["command1", "command2"],
    "version_command": "command1 --version",
    "version_pattern": "version\\s+([\\d\\.]+)",
    "required_for": ["feature1", "feature2"],
    "category": "category_name",
    "platforms": {
      "linux": {
        "package_managers": {
          "apt": "package-name",
          "pacman": "package-name"
        }
      }
    }
  }
}
```

2. **Add category** if needed:
```json
{
  "categories": {
    "new_category": {
      "description": "Category description",
      "essential": false
    }
  }
}
```

3. **Test the dependency**:
```bash
python test_system_checker.py
```

## Version Detection

The system attempts to detect versions using:
1. **Specified version command** and regex pattern
2. **Fallback parsing** for common version formats
3. **"unknown" status** if version cannot be determined

## Caching

The checker caches results during a single session to avoid repeated subprocess calls. Cache is cleared automatically between MCP server restarts.

## Error Handling

The system gracefully handles:
- Missing manifest files
- Invalid JSON syntax
- Command execution failures
- Platform incompatibilities
- Version detection failures

## Testing

Two test scripts are provided:

- `test_system_checker.py` - Tests core dependency checking functionality
- `test_mcp_resources.py` - Tests MCP resource functions

## Examples

### Check if all essential dependencies are available:
```python
from src.core.system_checker import SystemDependencyChecker

checker = SystemDependencyChecker()
missing = checker.get_missing_essential_dependencies()
if not missing:
    print("✅ All essential dependencies available")
else:
    print(f"❌ Missing: {', '.join(missing)}")
```

### Get installation suggestions:
```python
suggestions = checker.get_installation_suggestions()
for dep in suggestions["missing_essential"]:
    print(f"Install {dep['name']}: {dep['installation_options']}")
```

### Access via MCP resource:
The resources are automatically available when the TeXFlow MCP server starts. Client applications can access them using the MCP protocol to display dependency status and provide user guidance.

## Integration with TeXFlow Tools

The dependency checker integrates with TeXFlow's workflow guidance system:
- Tools automatically check for required dependencies before execution
- Missing dependencies trigger helpful error messages with installation hints
- Workflow suggestions adapt based on available tools

This ensures users get clear guidance on what needs to be installed for full TeXFlow functionality.