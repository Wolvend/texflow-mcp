# TeXFlow Semantic Layer Migration Guide

This guide explains how to integrate the semantic layer with the existing texflow.py MCP server.

## Overview

The semantic layer reduces TeXFlow's 27+ individual tools to 4-6 semantic operations, making the system more intuitive while maintaining all functionality.

## Migration Steps

### 1. Import Semantic Components

In `texflow.py`, add the semantic imports:

```python
from src.texflow_semantic import TeXFlowSemantic, create_semantic_tools
```

### 2. Initialize Semantic Layer

After creating the TeXFlow server instance, initialize the semantic layer:

```python
class TeXFlow:
    def __init__(self):
        # ... existing initialization ...
        
        # Initialize semantic layer
        self.semantic = TeXFlowSemantic(self)
```

### 3. Register Semantic Tools

Replace the individual tool registrations with semantic tools:

```python
# Instead of registering 27+ individual tools...
# server.add_tool("save_markdown", ...)
# server.add_tool("save_latex", ...)
# etc...

# Register semantic tools
semantic_tools = create_semantic_tools(server)
for tool in semantic_tools:
    server.add_tool(
        tool["name"],
        tool["handler"],
        tool["description"],
        tool["input_schema"]
    )
```

### 4. Maintain Backward Compatibility (Optional)

If needed, you can keep some original tools for compatibility:

```python
# Keep a few essential direct tools for backward compatibility
legacy_tools = [
    "list_printers",  # System management
    "check_document_status",  # Specific functionality
]

for tool_name in legacy_tools:
    # Register original tool alongside semantic ones
```

## Tool Mapping

### Before (27+ tools):
```
save_markdown → document(action='create', format='markdown')
save_latex → document(action='create', format='latex')
read_document → document(action='read')
edit_document → document(action='edit')
validate_latex → document(action='validate')
markdown_to_latex → document(action='convert')

print_text → output(action='print', format='text')
print_markdown → output(action='print', format='markdown')
print_latex → output(action='print', format='latex')
print_file → output(action='print')
markdown_to_pdf → output(action='export', format='pdf')
latex_to_pdf → output(action='export', format='pdf')

create_project → project(action='create')
list_projects → project(action='list')
use_project → project(action='switch')
project_info → project(action='info')
```

### After (4 semantic tools):
```
document - Manage all document operations
output - Handle printing and PDF export
project - Organize work in projects
texflow_help - Get workflow suggestions and help
```

## Example Integration

Here's a minimal example of integrating the semantic layer:

```python
# texflow.py modifications

from mcp import MCPServer
from src.texflow_semantic import create_semantic_tools

class TeXFlow:
    def __init__(self):
        # Existing initialization
        self.current_project = None
        self.project_base = Path.home() / "Documents" / "TeXFlow"
        
    # Keep all existing methods - they're used by semantic layer
    
async def main():
    server = MCPServer("texflow")
    texflow = TeXFlow()
    
    # Register semantic tools
    semantic_tools = create_semantic_tools(texflow)
    
    for tool in semantic_tools:
        @server.tool(
            name=tool["name"],
            description=tool["description"],
            input_schema=tool["input_schema"]
        )
        async def handle_tool(arguments):
            return tool["handler"](arguments)
    
    # Optional: Register system management tools directly
    @server.tool(name="list_printers")
    async def list_printers(arguments):
        return texflow.list_printers()
    
    await server.run()
```

## Benefits of Migration

1. **Simpler API**: 4 operations instead of 27+ tools
2. **Auto-detection**: Format and printer selection handled automatically
3. **Workflow guidance**: Built-in suggestions for next steps
4. **Flexible input**: Multiple ways to specify documents
5. **Intent-based**: System understands user intent

## Testing the Migration

1. Test document creation with auto-detection:
```python
# Old way
save_markdown(content="# Title", filename="doc.md")

# New way
document(action='create', content="# Title", intent="quick note")
```

2. Test printing with smart routing:
```python
# Old way (need to know format)
print_markdown(file_path="doc.md", printer="HP_Printer")

# New way (auto-detects format)
output(action='print', source="doc.md")
```

3. Test project management:
```python
# Old way
create_project(name="thesis", description="PhD thesis")

# New way (same but through semantic layer)
project(action='create', name="thesis", description="PhD thesis")
```

## Rollback Plan

If issues arise, the semantic layer can be disabled by:
1. Commenting out semantic tool registration
2. Re-enabling original tool registration
3. No data migration needed - all original functions remain

## Next Steps

1. Test semantic layer with existing workflows
2. Update documentation for end users
3. Consider deprecation timeline for direct tools
4. Add telemetry to track usage patterns

## Notes

- The semantic layer is additive - no existing functionality is removed
- All original tool functions must remain in texflow.py
- The semantic layer adds intelligence on top of existing tools
- System requirements checking happens automatically