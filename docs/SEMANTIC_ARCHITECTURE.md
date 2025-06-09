# TeXFlow Semantic Architecture

## Overview

TeXFlow's semantic architecture transforms 27+ individual MCP tools into 6 intelligent operations that understand user intent rather than requiring technical knowledge of document formats and workflows.

## Core Principles

1. **Intent-Based Operations**: Users express what they want to achieve, not how to achieve it
2. **Workflow Awareness**: Each operation knows what commonly comes next
3. **Format Agnosticism**: The system chooses appropriate formats based on document requirements
4. **Progressive Disclosure**: Simple tasks stay simple, complex features reveal themselves when needed

## Architecture Components

### 1. Semantic Operations

The system provides 6 high-level operations that bundle related functionality:

```
┌─────────────────────────────────────────────────────────────┐
│                    Semantic Operations                       │
├──────────────┬────────────────────────┬────────────────────┤
│  Operation   │  Actions               │  Maps From         │
├──────────────┼────────────────────────┼────────────────────┤
│  document    │  create, edit,         │  save_*, read_*,   │
│              │  convert, validate     │  edit_*, check_*   │
├──────────────┼────────────────────────┼────────────────────┤
│  output      │  print, export,        │  print_*, *_to_pdf │
│              │  preview               │                    │
├──────────────┼────────────────────────┼────────────────────┤
│  project     │  create, switch,       │  create_project,   │
│              │  list, info            │  use_project, etc  │
├──────────────┼────────────────────────┼────────────────────┤
│  printer     │  list, configure,      │  *_printer tools   │
│              │  set_default           │                    │
├──────────────┼────────────────────────┼────────────────────┤
│  discover    │  documents, fonts,     │  list_documents,   │
│              │  capabilities          │  list_fonts        │
├──────────────┼────────────────────────┼────────────────────┤
│  workflow    │  suggest, guide,       │  suggest_document_ │
│              │  next_steps            │  workflow          │
└──────────────┴────────────────────────┴────────────────────┘
```

### 2. Semantic Router

The router interprets user intent and routes to appropriate handlers:

```python
# User says: "I need to write a paper with equations"
router.route("document", "create", {
    "content": "My paper content",
    "intent": "academic paper with math"
})
# Router detects: needs equations → uses LaTeX
# Returns: document created + suggests next steps
```

### 3. Workflow Engine

Each operation returns contextual next steps:

```json
{
  "result": "Document created: introduction.md",
  "suggested_next": [
    {
      "operation": "document",
      "action": "edit",
      "hint": "Continue writing"
    },
    {
      "operation": "output",
      "action": "export",
      "hint": "Generate PDF when ready"
    }
  ]
}
```

### 4. Format Detection

The system automatically detects optimal format:

- Simple text/lists → Markdown
- Mathematical content → LaTeX
- Citations/bibliography → LaTeX
- Complex layouts → LaTeX

### 5. Personality System

Currently one comprehensive role:

```json
{
  "document-author": {
    "operations": ["document", "output", "project", "printer", "discover", "workflow"],
    "context": {
      "default_format": "auto",
      "workflow_hints": true
    }
  }
}
```

## Implementation Structure

```
texflow/
├── config/
│   ├── personalities.json      # Role definitions
│   └── workflows.json          # Workflow hints and transitions
├── src/
│   ├── core/
│   │   ├── semantic_router.py  # Routes operations to handlers
│   │   ├── format_detector.py  # Auto-detects document format needs
│   │   ├── workflow_engine.py  # Manages workflow suggestions
│   │   └── operation_registry.py # Registers and manages operations
│   ├── features/
│   │   ├── document/          # Document operations
│   │   ├── output/            # Print/export operations
│   │   ├── project/           # Project management
│   │   └── system/            # Printer/discovery operations
│   └── texflow_semantic.py    # Main entry point
```

## Benefits

1. **Reduced Complexity**: 6 operations vs 27+ tools
2. **Natural Language**: "Create a document" vs choosing between save_markdown/save_latex
3. **Guided Workflows**: System suggests next steps
4. **Format Transparency**: Users don't need to know Markdown vs LaTeX
5. **Extensible**: Easy to add new formats or workflows

## Example Usage

### Before (Direct Tools):
```python
# User must know:
# 1. Which format to use
# 2. Which tool saves that format
# 3. How to convert to PDF
# 4. Which print function to use

save_latex(content, "paper.tex")
latex_to_pdf(file_path="paper.tex", output_path="paper.pdf")
print_file("paper.pdf", printer="default")
```

### After (Semantic Operations):
```python
# User just describes intent
document(action="create", content=content, intent="academic paper")
# System handles format selection, suggests next steps
output(action="print", document="paper")
# System knows the format and handles conversion
```

## Migration Path

1. Semantic layer built on top of existing tools
2. Backward compatibility maintained
3. Existing tools remain accessible
4. Gradual deprecation based on usage patterns