#!/usr/bin/env python3
"""TeXFlow Semantic MCP Server

This is the new entry point that exposes semantic operations as MCP tools.
It wraps the existing texflow.py functionality with the semantic layer.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP
import texflow  # Import the existing texflow module
from src.texflow_semantic import TeXFlowSemantic

# Create MCP server instance
mcp = FastMCP("texflow-semantic")

# Create texflow instance (this has all the original tools)
texflow_instance = texflow.mcp

# Create semantic wrapper
semantic = TeXFlowSemantic(texflow_instance)

# Register semantic operations as MCP tools
@mcp.tool()
def document(action: str, content: str = None, path: str = None, format: str = "auto", 
            intent: str = None, old_string: str = None, new_string: str = None, 
            expected_replacements: int = 1) -> str:
    """Document operations - create, read, edit, validate, convert, status.
    
    Actions:
    - create: Create new document (auto-detects format)
    - read: Read document content
    - edit: Edit document content
    - validate: Check document syntax
    - convert: Convert between formats
    - status: Check modification status
    
    Args:
        action: The action to perform
        content: Document content (for create/validate)
        path: Document path (for read/edit/status/convert)
        format: Document format (auto/markdown/latex)
        intent: Document purpose (helps format selection)
        old_string: String to replace (for edit)
        new_string: Replacement string (for edit)
        expected_replacements: Expected number of replacements (for edit)
    """
    params = {k: v for k, v in locals().items() if v is not None and k != 'action'}
    result = semantic.execute("document", action, params)
    
    if result.get("success"):
        return result.get("message", "Operation completed successfully")
    else:
        return f"Error: {result.get('error', 'Unknown error')}"


@mcp.tool()
def output(action: str, source: str = None, content: str = None, format: str = None,
          printer: str = None, output_path: str = None) -> str:
    """Output operations - print documents or export to various formats.
    
    Actions:
    - print: Send to printer
    - export: Export to file (PDF, etc.)
    - preview: Preview without printing
    
    Args:
        action: The action to perform
        source: Source document path
        content: Direct content to output
        format: Target format for export
        printer: Printer name (for print)
        output_path: Output file path (for export)
    """
    params = {k: v for k, v in locals().items() if v is not None and k != 'action'}
    result = semantic.execute("output", action, params)
    
    if result.get("success"):
        return result.get("message", "Operation completed successfully")
    else:
        return f"Error: {result.get('error', 'Unknown error')}"


@mcp.tool()
def project(action: str, name: str = None, description: str = None) -> str:
    """Project operations - create and manage document projects.
    
    Actions:
    - create: Create new project with AI-guided structure
    - switch: Switch to different project
    - list: List all projects
    - info: Show current project info
    
    Args:
        action: The action to perform
        name: Project name
        description: Project description (AI uses this to create structure)
    """
    params = {k: v for k, v in locals().items() if v is not None and k != 'action'}
    result = semantic.execute("project", action, params)
    
    if result.get("success"):
        return result.get("message", "Operation completed successfully")
    else:
        return f"Error: {result.get('error', 'Unknown error')}"


@mcp.tool()
def organizer(action: str, source: str = None, destination: str = None, path: str = None,
             archive_path: str = None, restore_path: str = None, directory: str = None,
             filename: str = None, pattern: str = None, reason: str = None,
             keep_bib: bool = True, types: str = None, operations: list = None,
             stop_on_error: bool = False, dry_run: bool = False) -> str:
    """Organizer operations - manage document lifecycle and organization.
    
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
    
    Args:
        action: The action to perform
        source: Source path (for move)
        destination: Destination path (for move)
        path: File/directory path
        archive_path: Path to archived file (for restore)
        restore_path: Where to restore (for restore)
        directory: Directory to operate on
        filename: Filename to search for
        pattern: Glob pattern for matching files
        reason: Reason for archiving
        keep_bib: Keep bibliography files when cleaning aux
        types: Types of aux files to refresh (toc, bib, all)
        operations: List of operations for batch
        stop_on_error: Stop batch on first error
        dry_run: Validate batch without executing
    """
    params = {k: v for k, v in locals().items() if v is not None and k != 'action'}
    result = semantic.execute("organizer", action, params)
    
    if result.get("success"):
        # Format the response based on action
        if action == "list_archived" and "archives" in result:
            archives = result["archives"]
            if not archives:
                return "No archived documents found"
            
            output = f"Found {len(archives)} archived document(s):\n"
            for arch in archives:
                output += f"\n- {arch['name']}"
                output += f"\n  Archived: {arch['archived_at']}"
                output += f"\n  Reason: {arch['reason']}"
                output += f"\n  Size: {arch['size']}"
                output += f"\n  Path: {arch['path']}"
            return output
            
        elif action == "find_versions" and "versions" in result:
            versions = result["versions"]
            if not versions:
                return f"No versions found for '{filename}'"
                
            output = f"Found {len(versions)} version(s):\n"
            for ver in versions:
                output += f"\n- {ver['name']} ({ver['type']})"
                output += f"\n  Modified: {ver['modified']}"
                output += f"\n  Size: {ver['size']}"
                output += f"\n  Path: {ver['path']}"
            return output
            
        elif action == "list_aux" and "files" in result:
            aux_files = result["files"]
            total = sum(len(files) for files in aux_files.values())
            
            output = f"Found {total} auxiliary file(s) - Total size: {result['total_size']}\n"
            for category, files in aux_files.items():
                if files:
                    output += f"\n{category.title()}:"
                    for f in files:
                        output += f"\n  - {f['name']} ({f['size']})"
            return output
            
        elif action == "batch" and "results" in result:
            output = result["message"] + "\n"
            for r in result["results"]:
                status = "✓" if r.get("success") else "✗"
                output += f"\n{status} Operation {r['operation_index']}: {r['operation_action']}"
                if r.get("message"):
                    output += f" - {r['message']}"
            return output
            
        else:
            return result.get("message", "Operation completed successfully")
    else:
        return f"Error: {result.get('error', 'Unknown error')}"


# This is needed for FastMCP to find the server
server = mcp

def main():
    """Main entry point for the semantic MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()