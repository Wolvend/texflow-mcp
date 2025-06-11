# Tool Grouping for TeXFlow

This document describes the semantic grouping of TeXFlow's 30+ MCP tools into 7 coherent operations, with considerations for future expansion.

## Current Semantic Operations (7 Groups)

### 1. Document Operation 📄
**Purpose:** Manage the entire document lifecycle
**Actions:**
- `create` - Create new documents with auto-format detection
- `read` - Read documents with line numbers
- `edit` - Edit with change tracking and conflict prevention
- `convert` - Transform between formats (Markdown ↔ LaTeX)
- `validate` - Check syntax and structure
- `status` - Check for external modifications

**Tools Mapped:**
- save_markdown, save_latex → create
- read_document → read
- edit_document → edit
- markdown_to_latex → convert
- validate_latex → validate
- check_document_status → status

### 2. Output Operation 🖨️
**Purpose:** Export documents from the system
**Actions:**
- `print` - Send to physical printers
- `export` - Generate PDF files
- `preview` - View rendered output (future)

**Tools Mapped:**
- print_text, print_markdown, print_latex, print_file, print_from_documents → print
- markdown_to_pdf, latex_to_pdf → export

### 3. Project Operation 📁
**Purpose:** Organize work into logical units
**Actions:**
- `create` - Create project with AI-guided structure
- `switch` - Change active project
- `list` - Show all projects
- `info` - Get current project details
- `close` - Close current project

**Tools Mapped:**
- create_project → create
- use_project → switch
- list_projects → list
- project_info → info
- close_project → close

### 4. Printer Operation 🖨️
**Purpose:** Manage printing hardware
**Actions:**
- `list` - Show available printers
- `info` - Get printer details
- `set_default` - Change default printer
- `enable` - Enable printer
- `disable` - Disable printer
- `update` - Update printer metadata

**Tools Mapped:**
- list_printers → list
- get_printer_info → info
- set_default_printer → set_default
- enable_printer → enable
- disable_printer → disable
- update_printer_info → update

### 5. Discover Operation 🔍
**Purpose:** Find resources and capabilities
**Actions:**
- `documents` - List available documents
- `fonts` - Browse system fonts
- `capabilities` - Check system requirements

**Tools Mapped:**
- list_documents → documents
- list_available_fonts → fonts
- (new) system capability checks → capabilities

### 6. Archive Operation 📦
**Purpose:** Manage document versions and history
**Actions:**
- `archive` - Soft delete documents
- `restore` - Recover archived documents
- `list` - Show archived documents
- `versions` - Find all versions of a document
- `cleanup` - Bulk archive by pattern

**Tools Mapped:**
- archive_document → archive
- restore_archived_document → restore
- list_archived_documents → list
- find_document_versions → versions
- clean_workspace → cleanup

### 7. Workflow Operation 💡
**Purpose:** Provide guidance and automation
**Actions:**
- `suggest` - Recommend workflows for tasks
- `guide` - Provide topic-specific help
- `next_steps` - Show contextual next actions

**Tools Mapped:**
- suggest_document_workflow → suggest
- (new) contextual guidance → guide
- (new) next step suggestions → next_steps

## Benefits of This Grouping

1. **Clear Mental Model**
   - Each operation has a single, well-defined purpose
   - Users think in terms of goals, not tools

2. **Reduced Complexity**
   - 7 operations vs 30+ individual tools
   - Logical grouping makes discovery easier

3. **Progressive Disclosure**
   - Start with basic actions
   - Advanced features reveal themselves contextually

4. **Better Discoverability**
   - Related functions are grouped together
   - Consistent naming patterns

5. **Extensibility**
   - New features fit naturally into existing groups
   - Clear pattern for adding new operations

## Future Considerations

### Potential New Operations

1. **Collaborate Operation** 🤝
   - Track active editors
   - Merge conflicts
   - Show live changes
   - Lock/unlock documents

2. **Template Operation** 📋
   - Browse templates
   - Create from template
   - Save as template
   - Share templates

3. **Review Operation** 📝
   - Track changes
   - Add comments
   - Compare versions
   - Accept/reject changes

### Enhancement Opportunities

1. **Discover Operation**
   - Add template discovery
   - Show example documents
   - List available workflows

2. **Workflow Operation**
   - Add workflow recording
   - Create custom workflows
   - Share workflow patterns

3. **Archive Operation**
   - Add version comparison
   - Implement branching
   - Support merge operations

## Implementation Status

| Operation | Status | Notes |
|-----------|--------|-------|
| document | ✅ Implemented | Full functionality |
| output | ✅ Implemented | Full functionality |
| project | ✅ Implemented | Full functionality |
| printer | 🔄 Planned | Needs semantic wrapper |
| discover | 🔄 Planned | Needs semantic wrapper |
| archive | ✅ Implemented | Full functionality |
| workflow | 🔄 Planned | Needs semantic wrapper |

## Migration Path

1. **Phase 1**: Implement remaining semantic wrappers (printer, discover, workflow)
2. **Phase 2**: Add deprecation notices to direct tool usage
3. **Phase 3**: Update documentation to emphasize semantic operations
4. **Phase 4**: Consider removing direct tool access in major version

## Example Usage Comparison

### Archive Workflow

**Before (Direct Tools):**
```python
# Archive old drafts
archive_document("draft_v1.md", "outdated")
archive_document("draft_v2.md", "outdated")
list_archived_documents()

# Find versions
find_document_versions("report.tex")

# Restore a version
restore_archived_document(".texflow_archive/20250611_123456_draft_v1.md")
```

**After (Semantic Operations):**
```python
# Archive old drafts with context
archive(action="cleanup", pattern="draft_v*.md")

# Find and manage versions
versions = archive(action="versions", filename="report.tex")
# System shows all versions with metadata

# Restore with guidance
archive(action="restore", archive_path=versions["archived"][0]["path"])
# System suggests next steps like reading or editing
```

The semantic approach provides:
- Clearer intent expression
- Contextual workflow hints
- Reduced cognitive load
- Better error handling and guidance