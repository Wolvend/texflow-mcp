#!/usr/bin/env python3
"""TeXFlow Unified MCP Server - Semantic Document Authoring System

This server provides semantic MCP tools that guide document authoring workflows.
All operations are routed through the semantic layer for consistent guidance.

Usage:
    texflow [workspace_root]
    
    workspace_root: Base directory for TeXFlow projects (default: ~/Documents/TeXFlow)
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP
from src.texflow_semantic import TeXFlowSemantic
import texflow  # For base functionality and session context

# Create MCP server instance
mcp = FastMCP("texflow")

# Create semantic wrapper
semantic = TeXFlowSemantic(texflow)

# Import session context
SESSION_CONTEXT = texflow.SESSION_CONTEXT

# Set workspace root from command line argument or environment variable
if len(sys.argv) > 1:
    workspace_root = Path(sys.argv[1]).expanduser().resolve()
elif os.environ.get("TEXFLOW_WORKSPACE"):
    workspace_root = Path(os.environ["TEXFLOW_WORKSPACE"]).expanduser().resolve()
else:
    workspace_root = Path.home() / "Documents" / "TeXFlow"

# Update session context with proper workspace root
SESSION_CONTEXT["workspace_root"] = workspace_root
texflow.TEXFLOW_ROOT = workspace_root


def format_semantic_result(result: Dict[str, Any]) -> str:
    """Format semantic layer result for clean MCP tool output."""
    if result.get("error"):
        # Format error with helpful hints
        error_msg = f"❌ Error: {result['error']}"
        if result.get("hint"):
            error_msg += f"\n💡 Hint: {result['hint']}"
        if result.get("system_check"):
            error_msg += f"\n⚙️  System: {result['system_check']}"
        return error_msg
    
    # Format success message
    output = result.get("message", "✓ Operation completed")
    
    # Add workflow hints if present
    if result.get("workflow"):
        workflow = result["workflow"]
        if workflow.get("message"):
            output += f"\n\n{workflow['message']}"
        if workflow.get("suggested_next"):
            output += "\n💡 Next steps:"
            for suggestion in workflow["suggested_next"]:
                output += f"\n→ {suggestion['description']}: {suggestion['command']}"
    
    # Add efficiency hints
    if result.get("efficiency_hint"):
        hint = result["efficiency_hint"]
        output += f"\n\n⚡ {hint['message']}"
        if hint.get("important"):
            output += f"\n⚠️  {hint['important']}"
    
    # Add format suggestions
    if result.get("format_suggestion"):
        fmt = result["format_suggestion"]
        output += f"\n\n📝 Format suggestion: {fmt['message']}"
        for trigger in fmt.get("triggers", []):
            output += f"\n   - Detected: {trigger}"
    
    # Add conversion hints
    if result.get("conversion_hint"):
        conv = result["conversion_hint"]
        output += f"\n\n🔄 {conv['message']}"
        output += f"\n   Example: {conv['command']}"
    
    # Add project hints
    if result.get("project_hint"):
        hint = result["project_hint"]
        output += f"\n\n{hint['message']}"
        if hint.get("important"):
            output += f"\n{hint['important']}"
        if hint.get("next_steps"):
            for step in hint["next_steps"]:
                output += f"\n→ {step['description']}: {step['command']}"
    
    # Add archive list for organizer operations
    if result.get("archives"):
        archives = result["archives"]
        if archives:
            output += "\n\nArchived documents:"
            for arch in archives:
                output += f"\n  📄 {arch['name']} ({arch['size']})"
                output += f"\n     Path: {arch['path']}"
                output += f"\n     Archived: {arch['archived_at']}"
                if arch.get('reason'):
                    output += f"\n     Reason: {arch['reason']}"
                output += "\n"
    
    # Add general hints
    if result.get("hint"):
        output += f"\n💡 {result['hint']}"
    
    return output


@mcp.tool()
def document(
    action: str,
    content: Optional[str] = None,
    path: Optional[str] = None,
    format: str = "auto",
    intent: Optional[str] = None,
    source: Optional[str] = None,
    target_format: Optional[str] = None,
    old_string: Optional[str] = None,
    new_string: Optional[str] = None
) -> str:
    """Manage document lifecycle - create, read, edit, convert, validate, and track changes.
    
    BEST PRACTICES:
    - Work within projects for organization (use project tool first)
    - Use 'edit' on existing documents instead of recreating (saves tokens)
    - Use 'convert' to transform formats instead of rewriting
    - Use 'validate' before generating PDFs from LaTeX
    
    Actions:
    - create: Create new document (auto-detects format from content/intent)
    - read: Read document with line numbers
    - edit: Make targeted edits with conflict detection
    - convert: Transform between formats (e.g., markdown→latex)
    - validate: Check syntax and structure
    - status: Check for external modifications
    """
    params = {k: v for k, v in locals().items() if v is not None and k != 'action'}
    
    # Document operation expects 'filename' for create action, not 'path'
    if action == "create" and path is not None:
        params["filename"] = params.pop("path", None)
    
    result = semantic.execute("document", action, params)
    return format_semantic_result(result)


@mcp.tool()
def output(
    action: str,
    source: Optional[str] = None,
    content: Optional[str] = None,
    format: str = "auto",
    printer: Optional[str] = None,
    output_path: Optional[str] = None
) -> str:
    """Generate output from documents - print to paper or export to various formats.
    
    BEST PRACTICES:
    - Use 'source' parameter with existing files (avoids regeneration)
    - Default export format is PDF (most faithful to LaTeX)
    - Export to DOCX for collaboration with non-LaTeX users
    
    Actions:
    - print: Send to physical printer (auto-converts to PDF if needed)
    - export: Save to various formats (PDF, DOCX, ODT, RTF, HTML, EPUB)
    """
    params = {k: v for k, v in locals().items() if v is not None and k != 'action'}
    result = semantic.execute("output", action, params)
    return format_semantic_result(result)


@mcp.tool()
def project(
    action: str,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> str:
    """Organize documents into projects with intelligent structure.
    
    WORKFLOW TIP: Always start by creating or switching to a project!
    Projects provide:
    - Organized file structure (content/, output/, assets/)
    - Consistent paths for documents
    - Better collaboration and version control
    
    Actions:
    - create: Create new project with organized structure
    - switch: Change active project
    - list: Show all projects (including importable directories)
    - info: Get current project details
    - import: Import an existing directory as a TeXFlow project
    - close: Close current project (work with loose files)
    """
    params = {k: v for k, v in locals().items() if v is not None and k != 'action'}
    result = semantic.execute("project", action, params)
    return format_semantic_result(result)


@mcp.tool()
def discover(
    action: str,
    folder: Optional[str] = None,
    style: Optional[str] = None
) -> str:
    """Find documents, fonts, and system capabilities.
    
    WORKFLOW TIP: Use discover to find documents before editing or exporting.
    Shows relative paths from project root for easy reference.
    
    Actions:
    - documents: List documents in project or folder (shows relative paths)
    - recent: Show recently modified documents across all projects
    - fonts: Browse available fonts for LaTeX
    - capabilities: Check system dependencies
    """
    # For now, use the original implementation
    # TODO: Enhance with semantic layer for better discovery
    result = texflow.discover(action, folder, style)
    
    # Add guidance for documents outside projects
    if action == "documents" and not SESSION_CONTEXT.get("current_project"):
        if "Documents in" in result and "No documents found" not in result:
            result += "\n\n💡 TIP: These documents are outside a project."
            result += "\n→ To organize them: project(action='import', name='folder-name')"
            result += "\n→ Or create a project: project(action='create', name='my-project')"
    
    return result


@mcp.tool()
def organizer(
    action: str,
    source: Optional[str] = None,
    destination: Optional[str] = None,
    path: Optional[str] = None,
    archive_path: Optional[str] = None,
    restore_path: Optional[str] = None,
    directory: Optional[str] = None,
    filename: Optional[str] = None,
    pattern: Optional[str] = None,
    reason: Optional[str] = None,
    keep_bib: bool = True,
    types: Optional[str] = None,
    operations: Optional[List] = None,
    stop_on_error: bool = False,
    dry_run: bool = False
) -> str:
    """Organize and manage document lifecycle - archive, move, clean, and batch operations.
    
    WORKFLOW TIP: Use organizer to keep your workspace clean and documents organized.
    Archive old versions before major rewrites, clean auxiliary files when needed.
    
    Actions:
    - move: Move or rename documents (like Unix mv)
    - archive: Soft delete to hidden archive folder  
    - restore: Restore archived documents
    - list_archived: List all archived documents
    - find_versions: Find all versions of a document
    - clean: Archive multiple files by pattern
    - clean_aux: Clean LaTeX auxiliary files
    - refresh_aux: Remove aux files to force regeneration
    - list_aux: List auxiliary files for a document
    - batch: Execute multiple operations
    """
    params = {k: v for k, v in locals().items() if v is not None and k != 'action'}
    
    # Normalize parameter names for consistency
    # If both source and path are provided, source takes precedence
    if params.get("source") and params.get("path"):
        params.pop("path")
    elif params.get("path") and not params.get("source"):
        # For actions that expect 'source', map 'path' to 'source'
        if action in ["move"]:
            params["source"] = params.pop("path")
    
    result = semantic.execute("organizer", action, params)
    return format_semantic_result(result)


@mcp.tool()
def printer(
    action: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None
) -> str:
    """Manage printing hardware and configuration.
    
    Actions:
    - list: Show all available printers with status
    - info: Get detailed printer information
    - set_default: Change the default printer
    - enable: Allow printer to accept jobs
    - disable: Stop printer from accepting jobs
    - update: Update printer description/location
    """
    # Use original texflow implementation
    return texflow.printer(action, name, description, location)


@mcp.tool()
def workflow(
    action: str,
    task: Optional[str] = None
) -> str:
    """Get intelligent guidance and workflow automation.
    
    Actions:
    - suggest: Get workflow recommendations for a task
    - guide: Get comprehensive guidance for a workflow
    - next_steps: See contextual next actions based on current state
    """
    # Use original texflow implementation
    return texflow.workflow(action, task)


@mcp.tool()
def templates(
    action: str,
    category: Optional[str] = None,
    name: Optional[str] = None,
    source: Optional[str] = None,
    target: Optional[str] = None,
    content: Optional[str] = None
) -> str:
    """Manage document templates for quick project starts.
    
    Templates are organized by category in ~/Documents/TeXFlow/templates/.
    Start from templates to save time and ensure consistent formatting.
    
    Actions:
    - list: Show available templates (optionally filtered by category)
    - use: Copy a template to current project or specified location
    - activate: Convert current project into a template
    - create: Create a new template from content or existing document
    - rename: Rename a template
    - delete: Remove a template
    - info: Get details about a specific template
    """
    # Use original texflow implementation
    return texflow.templates(action, category, name, source, target, content)


def main():
    """Run the unified semantic MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()