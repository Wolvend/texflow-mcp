# TeXFlow Current Architecture & Flow

## Tool Routing Status

### Tools Using Semantic Layer (Enhanced)
1. **document** → `semantic.execute("document", action, params)`
2. **output** → `semantic.execute("output", action, params)` 
3. **project** → `semantic.execute("project", action, params)`
4. **organizer** → `semantic.execute("organizer", action, params)`

### Tools Using Direct Call (No Enhancement)
1. **discover** → `texflow.discover()` (direct)
2. **printer** → `texflow.printer()` (direct)
3. **workflow** → `texflow.workflow()` (direct)
4. **templates** → `texflow.templates()` (direct)

## Current Flow for Semantic Tools

```
User Request
    ↓
texflow_unified.py (MCP interface)
    ↓
semantic.execute() [in texflow_semantic.py]
    ↓
SemanticRouter.route()
    ↓
Operation Handler (e.g., DocumentOperation)
    ↓ (sometimes)
texflow.py original function
```

## The Duplication Problem

### Case 1: Document Convert Action
- **Path 1**: `document_operation._convert_document()` → Implements pandoc conversion
- **Path 2**: `texflow.document()` → Also implements pandoc conversion
- **Result**: Same functionality in 2 places

### Case 2: Output Export Action  
- **Path 1**: `output_operation._export_document()` → Detects format, then calls texflow.output()
- **Path 2**: `texflow.output()` → Has all the conversion logic
- **Result**: Partial reimplementation + delegation

### Case 3: Format Detection
- **Implementation 1**: `document_operation._detect_format()`
- **Implementation 2**: `output_operation._detect_file_format()`
- **Implementation 3**: `format_detector.py` (exists but underused)
- **Result**: 3 similar implementations

## Why This Matters

1. **Bug fixes must be applied multiple times** (like the pandoc -s flag)
2. **Behavior can diverge** between entry points
3. **Confusion about which code path executes**
4. **Maintenance burden** increases with each duplication

## The Semantic Layer's Role

**Original Intent**: 
- Add workflow guidance and hints
- Provide intelligent routing
- Enhance operations with context

**Current Reality**:
- Sometimes reimplements core logic
- Sometimes delegates to original
- Inconsistent approach across operations

## Recommended Fix

The semantic layer should be a **thin enhancement layer** that:
1. Adds workflow context
2. Calls core services
3. Enhances results with hints
4. Never reimplements core functionality

All core logic should live in dedicated service modules that both the semantic layer and original texflow.py use.