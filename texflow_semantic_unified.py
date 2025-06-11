#!/usr/bin/env python3
"""TeXFlow Unified Semantic MCP Server

This server exposes only 7 semantic MCP tools that provide:
1. Inward hints - guidance on how to use each action effectively
2. Outward hints - suggestions for logical next steps

Each tool represents a semantic group with multiple actions.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP
import texflow
from src.texflow_semantic import TeXFlowSemantic

# Create MCP server instance
mcp = FastMCP("texflow")

# Create texflow instance (this has all the original tools)
texflow_instance = texflow.mcp

# Create semantic wrapper
semantic = TeXFlowSemantic(texflow_instance)


def format_response(result: Dict[str, Any]) -> str:
    """Format semantic operation response with helpful structure."""
    response_parts = []
    
    # Main result
    if "success" in result and result["success"]:
        if "message" in result:
            response_parts.append(f"✓ {result['message']}")
        if "path" in result:
            response_parts.append(f"📄 Path: {result['path']}")
        if "output_path" in result:
            response_parts.append(f"📄 Output: {result['output_path']}")
    elif "error" in result:
        response_parts.append(f"❌ Error: {result['error']}")
        if "help" in result:
            response_parts.append(f"💡 Help: {result['help']}")
    
    # Content preview if applicable
    if "content" in result and isinstance(result["content"], str):
        preview = result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"]
        response_parts.append(f"\n--- Content Preview ---\n{preview}")
    
    # Suggested next steps
    if "suggested_next" in result and result["suggested_next"]:
        response_parts.append("\n💡 Suggested next steps:")
        for suggestion in result["suggested_next"]:
            if suggestion:  # Check for None values
                hint = suggestion.get("hint", "")
                operation = suggestion.get("operation", "")
                action = suggestion.get("action", "")
                response_parts.append(f"   → {hint} (use: {operation} action='{action}')")
    
    return "\n".join(response_parts)


@mcp.tool()
def document(
    action: str,
    content: Optional[str] = None,
    path: Optional[str] = None,
    format: str = "auto",
    intent: Optional[str] = None,
    source: Optional[str] = None,
    target_format: Optional[str] = None,
    changes: Optional[List[Dict[str, str]]] = None,
    old_string: Optional[str] = None,
    new_string: Optional[str] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None
) -> str:
    """Manage document lifecycle - create, read, edit, convert, validate, and track changes.
    
    BEST PRACTICES:
    - Use 'convert' action to transform existing documents instead of recreating content
    - Use 'status' to check for external changes before editing
    - Use 'validate' before generating PDFs from LaTeX
    
    Actions:
    - create: Create new document (auto-detects format from content/intent)
    - read: Read document with line numbers
    - edit: Make targeted edits with conflict detection
    - convert: Transform between formats (e.g., markdown→latex)
    - validate: Check syntax and structure
    - status: Check for external modifications
    
    Examples:
    - Create: document(action="create", content="# Title", intent="blog post")
    - Convert: document(action="convert", source="notes.md", target_format="latex")
    - Edit: document(action="edit", path="doc.tex", old_string="foo", new_string="bar")
    
    Args:
        action: The action to perform
        content: Document content (for create/validate)
        path: Document path (for read/edit/status)
        source: Source file path (for convert)
        target_format: Target format for conversion
        format: Document format (auto/markdown/latex)
        intent: Purpose/type of document (helps format selection)
        changes: List of edits [{old: "text", new: "replacement"}]
        old_string/new_string: Single edit (alternative to changes)
        offset/limit: For reading portions of large files
    """
    params = {
        "content": content,
        "path": path,
        "format": format,
        "intent": intent,
        "source": source,
        "target_format": target_format,
        "changes": changes,
        "old_string": old_string,
        "new_string": new_string,
        "offset": offset,
        "limit": limit
    }
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}
    
    result = semantic.execute("document", action, params)
    return format_response(result)


@mcp.tool()
def output(
    action: str,
    source: Optional[str] = None,
    content: Optional[str] = None,
    document: Optional[str] = None,
    path: Optional[str] = None,
    format: str = "auto",
    printer: Optional[str] = None,
    output_path: Optional[str] = None,
    title: Optional[str] = None
) -> str:
    """Generate output from documents - print to paper or export to PDF.
    
    BEST PRACTICES:
    - Use 'source' parameter with existing files instead of 'content' to avoid regeneration
    - Export to PDF first if you need both digital and printed copies
    - Let the system auto-detect format when possible
    
    Actions:
    - print: Send to physical printer (auto-converts to PDF if needed)
    - export: Save as PDF without printing
    - preview: View rendered output (future feature)
    
    Smart Features:
    - Auto-detects format from file extension or content
    - Remembers printer choice for session
    - Converts Markdown/LaTeX to PDF automatically
    
    Examples:
    - Print existing: output(action="print", source="report.tex")
    - Export to PDF: output(action="export", source="notes.md", output_path="notes.pdf")
    - Quick print: output(action="print", content="Quick note", format="text")
    
    Args:
        action: The action to perform (print/export)
        source: Path to existing file (preferred over content)
        content: Direct content to output (avoid if file exists)
        document: Document name in current project
        path: Full path to file
        format: Output format (auto/text/markdown/latex/pdf)
        printer: Printer name (uses default if not specified)
        output_path: Where to save PDF (for export)
        title: Document title
    """
    params = {
        "source": source,
        "content": content,
        "document": document,
        "path": path,
        "format": format,
        "printer": printer,
        "output_path": output_path,
        "title": title
    }
    params = {k: v for k, v in params.items() if v is not None}
    
    result = semantic.execute("output", action, params)
    return format_response(result)


@mcp.tool()
def project(
    action: str,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> str:
    """Organize documents into projects with intelligent structure.
    
    Projects provide:
    - Organized directory structure (content/, output/, assets/)
    - Context-aware file operations
    - Automatic path resolution
    - Project-specific workflows
    
    Actions:
    - create: Create new project with AI-guided structure
    - switch: Change active project
    - list: Show all projects
    - info: Get current project details
    - close: Return to default Documents mode
    
    Examples:
    - Create: project(action="create", name="my-thesis", description="PhD thesis on quantum computing")
    - Switch: project(action="switch", name="my-thesis")
    - List: project(action="list")
    
    Args:
        action: The action to perform
        name: Project name
        description: Free-form description for AI structure generation
    """
    params = {"name": name, "description": description}
    params = {k: v for k, v in params.items() if v is not None}
    
    result = semantic.execute("project", action, params)
    return format_response(result)


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
    
    Examples:
    - List all: printer(action="list")
    - Set default: printer(action="set_default", name="Office_Laser")
    - Update info: printer(action="update", name="HP_Printer", location="Room 201")
    
    Args:
        action: The action to perform
        name: Printer name
        description: Printer description (for update)
        location: Printer location (for update)
    """
    # Map to existing printer tools
    if action == "list":
        return texflow_instance.list_printers()
    elif action == "info":
        if not name:
            return "❌ Error: Printer name required for info action"
        return texflow_instance.get_printer_info(name)
    elif action == "set_default":
        if not name:
            return "❌ Error: Printer name required for set_default action"
        return texflow_instance.set_default_printer(name)
    elif action == "enable":
        if not name:
            return "❌ Error: Printer name required for enable action"
        return texflow_instance.enable_printer(name)
    elif action == "disable":
        if not name:
            return "❌ Error: Printer name required for disable action"
        return texflow_instance.disable_printer(name)
    elif action == "update":
        if not name:
            return "❌ Error: Printer name required for update action"
        return texflow_instance.update_printer_info(name, description, location)
    else:
        return f"❌ Error: Unknown printer action '{action}'. Available: list, info, set_default, enable, disable, update"


@mcp.tool()
def discover(
    action: str,
    folder: Optional[str] = None,
    style: Optional[str] = None
) -> str:
    """Find documents, fonts, and system capabilities.
    
    Actions:
    - documents: List documents in project or folder
    - fonts: Browse available fonts for LaTeX
    - capabilities: Check system dependencies
    
    Examples:
    - Find docs: discover(action="documents", folder="reports")
    - Find fonts: discover(action="fonts", style="serif")
    - Check system: discover(action="capabilities")
    
    Args:
        action: The action to perform
        folder: Subfolder to search (for documents)
        style: Font style filter - serif/sans/mono (for fonts)
    """
    if action == "documents":
        return texflow_instance.list_documents(folder or "")
    elif action == "fonts":
        return texflow_instance.list_available_fonts(style)
    elif action == "capabilities":
        # Check system capabilities
        caps = []
        caps.append("✓ CUPS printing system")
        if texflow_instance.has_pandoc:
            caps.append("✓ Pandoc (Markdown conversion)")
        else:
            caps.append("✗ Pandoc not found - install for Markdown support")
        if texflow_instance.has_xelatex:
            caps.append("✓ XeLaTeX (LaTeX compilation)")
        else:
            caps.append("✗ XeLaTeX not found - install texlive-xetex")
        return "System Capabilities:\n" + "\n".join(caps)
    else:
        return f"❌ Error: Unknown discover action '{action}'. Available: documents, fonts, capabilities"


@mcp.tool()
def archive(
    action: str,
    path: Optional[str] = None,
    archive_path: Optional[str] = None,
    restore_path: Optional[str] = None,
    filename: Optional[str] = None,
    directory: Optional[str] = None,
    pattern: Optional[str] = None,
    reason: Optional[str] = None
) -> str:
    """Manage document versions and history with soft delete functionality.
    
    Documents are moved to .texflow_archive folder, preserving them for recovery.
    
    Actions:
    - archive: Soft delete a document (preserves in hidden folder)
    - restore: Recover an archived document
    - list: Show archived documents in a directory
    - versions: Find all versions of a document (current + archived)
    - cleanup: Archive multiple files matching a pattern
    
    Examples:
    - Archive: archive(action="archive", path="old_draft.md", reason="outdated")
    - Find versions: archive(action="versions", filename="report.tex")
    - Cleanup: archive(action="cleanup", pattern="*_backup*")
    - Restore: archive(action="restore", archive_path=".texflow_archive/...")
    
    Args:
        action: The action to perform
        path: Document path to archive
        archive_path: Path to archived document (for restore)
        restore_path: Where to restore document (optional)
        filename: Base filename for version search
        directory: Directory to search/clean
        pattern: File pattern for cleanup (e.g., "*_old*")
        reason: Reason for archiving
    """
    params = {
        "path": path,
        "archive_path": archive_path,
        "restore_path": restore_path,
        "filename": filename,
        "directory": directory,
        "pattern": pattern,
        "reason": reason
    }
    params = {k: v for k, v in params.items() if v is not None}
    
    result = semantic.execute("archive", action, params)
    return format_response(result)


@mcp.tool()
def workflow(
    action: str,
    task: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """Get intelligent guidance and workflow automation.
    
    This tool provides context-aware suggestions based on:
    - Current task requirements
    - Document types and content
    - Previous actions in session
    - Best practices for document workflows
    
    Actions:
    - suggest: Get workflow recommendations for a task
    - guide: Get help with specific topics
    - next_steps: See contextual next actions
    
    Examples:
    - Get help: workflow(action="suggest", task="write academic paper with citations")
    - Next steps: workflow(action="next_steps")
    
    Args:
        action: The action to perform
        task: Description of what you want to accomplish
        context: Additional context for suggestions
    """
    if action == "suggest":
        if not task:
            return "❌ Error: Please provide a task description"
        return texflow_instance.suggest_document_workflow(task)
    
    elif action == "guide":
        guides = {
            "citations": """📚 Citation Guide:
1. Use LaTeX for documents with citations
2. Create .bib file: document(action="create", content="@article{...}", path="refs.bib")
3. Add \\bibliography{refs} to your LaTeX document
4. Use \\cite{key} for citations""",
            
            "math": """🔢 Math Expression Guide:
1. Markdown: Use $ for inline math, $$ for display math
2. LaTeX: Full math support with amsmath package
3. Convert existing: document(action="convert", source="notes.md", target_format="latex")""",
            
            "collaboration": """🤝 Collaboration Guide:
1. Check status before editing: document(action="status", path="shared.tex")
2. Review changes if modified externally
3. Use version history: archive(action="versions", filename="shared.tex")"""
        }
        
        if task and task.lower() in guides:
            return guides[task.lower()]
        else:
            return "Available guides: citations, math, collaboration"
    
    elif action == "next_steps":
        # This would ideally check session context
        return """💡 Common next steps:
→ Create document: document(action="create", content="...", intent="your purpose")
→ List projects: project(action="list")
→ Check printers: printer(action="list")
→ Find documents: discover(action="documents")"""
    
    else:
        return f"❌ Error: Unknown workflow action '{action}'. Available: suggest, guide, next_steps"


def main():
    """Run the semantic MCP server."""
    # Initialize the original texflow instance
    texflow.initialize()
    
    # Run the MCP server
    mcp.run()


if __name__ == "__main__":
    main()