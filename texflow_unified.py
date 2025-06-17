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
semantic = TeXFlowSemantic(texflow.mcp)

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
    result = semantic.execute("organizer", action, params)
    return format_semantic_result(result)


def main():
    """Run the unified semantic MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()