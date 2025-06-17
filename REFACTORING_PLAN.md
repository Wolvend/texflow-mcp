# TeXFlow Refactoring Plan: Eliminating Code Duplication

## Current State Analysis

### Architecture Overview
- **texflow_unified.py**: MCP entry point, routes to semantic layer
- **Semantic Layer**: Provides workflow guidance and enhanced operations
- **Original texflow.py**: Contains core implementation logic
- **Problem**: Partial reimplementation in semantic layer causes duplication

### Key Duplication Areas
1. Document conversion (pandoc usage)
2. PDF export (XeLaTeX usage)
3. Format detection logic
4. Error handling patterns

## Refactoring Strategy

### Principle: Semantic Enhancement, Not Reimplementation
The semantic layer should **enhance** the original implementation with workflow guidance, not duplicate its functionality.

## Proposed Architecture

```
┌─────────────────────┐
│  texflow_unified.py │ (MCP Interface)
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Semantic Router    │ (Workflow guidance & hints)
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│ Operation Handlers  │ (Thin wrappers)
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   Core Services     │ (Single implementation)
└─────────────────────┘
```

## Implementation Plan

### Phase 1: Create Core Services
Create dedicated service modules for each capability:

#### 1. `src/core/conversion_service.py`
```python
class ConversionService:
    """Centralized document conversion logic"""
    
    def convert_markdown_to_latex(self, source_path: Path, output_path: Path) -> Dict:
        """Single implementation of markdown to latex conversion"""
        # Move pandoc logic here
        
    def convert_latex_to_pdf(self, source_path: Path, output_path: Path) -> Dict:
        """Single implementation of latex to pdf conversion"""
        # Move XeLaTeX logic here
        
    def convert_to_format(self, source: Path, target_format: str) -> Dict:
        """Generic conversion dispatcher"""
        # Route to appropriate converter
```

#### 2. `src/core/validation_service.py`
```python
class ValidationService:
    """Centralized validation logic"""
    
    def validate_latex(self, content_or_path: str) -> Dict:
        """Single implementation of LaTeX validation"""
        # Move chktex and XeLaTeX validation here
```

#### 3. Enhance existing `src/core/format_detector.py`
- Consolidate all format detection logic
- Remove duplicate implementations

### Phase 2: Refactor Operation Handlers
Make operation handlers thin wrappers that:
1. Add semantic context
2. Call core services
3. Add workflow hints to results

#### Example: `document_operation.py`
```python
def _convert_document(self, params, context):
    """Thin wrapper around conversion service"""
    # 1. Extract parameters
    source = params.get("source")
    target_format = params.get("target_format")
    
    # 2. Call core service
    result = self.conversion_service.convert_to_format(source, target_format)
    
    # 3. Add semantic enhancements
    if result["success"]:
        result["workflow"] = self._get_conversion_workflow_hints(source, target_format)
    
    return result
```

### Phase 3: Update texflow.py
Refactor to use core services instead of inline implementations:

```python
def output(action, **kwargs):
    """Original output function using core services"""
    if action == "export":
        # Use conversion_service instead of inline subprocess calls
        return conversion_service.convert_to_format(...)
```

### Phase 4: Eliminate Delegation Confusion
Current issue: Some operations delegate to texflow.py, others reimplement.

Solution:
1. **All semantic operations** should use core services
2. **texflow.py** should also use the same core services
3. This ensures single implementation, multiple entry points

## Migration Steps

### Step 1: Create Core Services (No Breaking Changes)
1. Create new service modules
2. Extract logic without removing from current locations
3. Add comprehensive tests

### Step 2: Update Semantic Layer
1. Replace inline implementations with service calls
2. Maintain exact same API
3. Add deprecation notices in old code

### Step 3: Update Original Implementation
1. Replace texflow.py inline logic with service calls
2. Ensure backward compatibility

### Step 4: Clean Up
1. Remove deprecated code
2. Update documentation
3. Add integration tests

## Benefits

1. **Single Source of Truth**: Each operation has one implementation
2. **Consistent Behavior**: Same logic regardless of entry point
3. **Easier Maintenance**: Fix bugs in one place
4. **Clear Responsibilities**: 
   - Core services: Implementation
   - Semantic layer: Workflow guidance
   - texflow.py: Legacy compatibility

## Testing Strategy

1. **Unit Tests**: For each core service
2. **Integration Tests**: Ensure semantic layer enhances correctly
3. **Regression Tests**: Verify no breaking changes
4. **End-to-End Tests**: Test full workflows

## Timeline

- Week 1: Create core services with tests
- Week 2: Refactor semantic layer
- Week 3: Update original implementation
- Week 4: Testing and documentation

## Success Criteria

1. No code duplication for conversion/validation logic
2. All tests pass
3. Semantic routing preserved
4. Workflow hints still provided
5. No breaking changes to API