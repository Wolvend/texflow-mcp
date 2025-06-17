#!/usr/bin/env python3
"""TeXFlow Unified MCP Server - Semantic Document Authoring System

This is the SEMANTIC WRAPPER that users interact with. It provides an intelligent
layer on top of the core texflow.py implementation.

ARCHITECTURE:
- Imports texflow.py for all core tool implementations
- Wraps each tool with semantic routing for enhanced guidance
- Adds system dependency checking and MCP resources
- Provides workflow hints, format suggestions, and efficiency tips

HOW IT WORKS:
1. User calls a tool (e.g., document(action='create', ...))
2. This file routes through semantic layer: semantic.execute("document", "create", params)
3. Semantic layer eventually calls the original texflow.document()
4. Gets raw result back from core implementation
5. Enhances with workflow hints, format suggestions, etc.
6. Returns enriched result to user

RELATIONSHIP TO texflow.py:
- texflow.py = The engine (core logic)
- texflow_unified.py = The intelligent dashboard (enhanced UX)

Users get a much better experience through this unified interface while
all the heavy lifting is still done by the proven core implementation.

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
from src.core.system_checker import SystemDependencyChecker
import texflow  # CRITICAL: Import the core implementation module

# Create MCP server instance
mcp = FastMCP("texflow")

# Create semantic wrapper that enhances the core texflow functionality
# This wrapper intercepts all tool calls and adds intelligent guidance
semantic = TeXFlowSemantic(texflow)

# Create system dependency checker for monitoring external tools
# This runs independently and provides status via MCP resources
system_checker = SystemDependencyChecker()

# SHARED STATE: Import session context from texflow.py
# Both files share this state to maintain consistency
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
    
    # Handle image data for inspect operations
    if result.get("image"):
        image_data = result["image"]
        output += f"\n\n🔍 PDF Page Inspection:"
        output += f"\n   Type: {image_data.get('mimeType', 'image/png')}"
        output += f"\n   Dimensions: {image_data.get('width', 'unknown')}x{image_data.get('height', 'unknown')}"
        # Note: The base64 data is available in the result but not displayed in text output
        # The AI model will access it directly from the image field
    
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
    new_string: Optional[str] = None,
    page: Optional[int] = None,
    dpi: Optional[int] = None
) -> str:
    """SEMANTIC WRAPPER: Document tool with intelligent guidance.
    
    This wrapper:
    1. Receives the user's request
    2. Routes through semantic layer for enhancement
    3. Calls the core texflow.document() implementation
    4. Enhances the result with workflow hints and suggestions
    
    Manage document lifecycle - create, read, edit, convert, validate, and track changes.
    
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
    - inspect: Inspect PDF page by rendering to base64 PNG image
    """
    params = {k: v for k, v in locals().items() if v is not None and k != 'action'}
    
    # Document operation expects 'filename' for create action, not 'path'
    if action == "create" and path is not None:
        params["filename"] = params.pop("path", None)
    
    # Document operation expects 'content_or_path' for validate action
    if action == "validate" and path is not None:
        params["content_or_path"] = params.pop("path", None)
    
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
    # Route through semantic layer for enhanced discovery features
    params = {}
    if folder is not None:
        params["folder"] = folder
    if style is not None:
        params["style"] = style
    
    result = semantic.execute("discover", action, params)
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
    # Route through semantic layer for enhanced printer management
    params = {}
    if name is not None:
        params["name"] = name
    if description is not None:
        params["description"] = description
    if location is not None:
        params["location"] = location
    
    result = semantic.execute("printer", action, params)
    return format_semantic_result(result)


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
    # Route through semantic layer for enhanced guidance
    params = {}
    if task is not None:
        params["task"] = task
    
    result = semantic.execute("workflow", action, params)
    return format_semantic_result(result)


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
    # Route through semantic layer for enhanced template management
    params = {}
    if category is not None:
        params["category"] = category
    if name is not None:
        params["name"] = name
    if source is not None:
        params["source"] = source
    if target is not None:
        params["target"] = target
    if content is not None:
        params["content"] = content
    
    result = semantic.execute("templates", action, params)
    return format_semantic_result(result)


# Add MCP Resources for system dependency status
@mcp.resource("system-dependencies://status")
def get_system_dependencies_status() -> str:
    """Get current system dependencies status as JSON."""
    try:
        report = system_checker.check_all_dependencies()
        import json
        return json.dumps(report, indent=2)
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "message": "Failed to check system dependencies"
        }, indent=2)


@mcp.resource("system-dependencies://summary")  
def get_system_dependencies_summary() -> str:
    """Get summary of system dependencies status."""
    try:
        report = system_checker.check_all_dependencies()
        summary = report.get("summary", {})
        
        status_emoji = {
            "fully_operational": "✅",
            "operational": "⚡", 
            "degraded": "⚠️",
            "unknown": "❓"
        }
        
        emoji = status_emoji.get(summary.get("overall_status", "unknown"), "❓")
        
        lines = [
            f"{emoji} TeXFlow System Dependencies Status",
            f"Platform: {report['metadata']['platform']}",
            f"Overall Status: {summary.get('overall_status', 'unknown')}",
            "",
            f"Essential: {summary.get('essential_available', 0)}/{summary.get('essential_total', 0)} available",
            f"Optional: {summary.get('optional_available', 0)}/{summary.get('optional_total', 0)} available",
            "",
            "Categories:"
        ]
        
        for cat_name, cat_info in report.get("categories", {}).items():
            status_icon = "✅" if cat_info["status"] == "available" else "⚠️" if cat_info["status"] == "partial" else "❌"
            lines.append(f"  {status_icon} {cat_name}: {cat_info['available_count']}/{cat_info['dependencies_count']}")
        
        return "\n".join(lines)
        
    except Exception as e:
        return f"❌ Error checking dependencies: {str(e)}"


@mcp.resource("system-dependencies://missing")
def get_missing_dependencies() -> str:
    """Get information about missing dependencies with installation hints."""
    try:
        suggestions = system_checker.get_installation_suggestions()
        
        if not suggestions["missing_essential"] and not suggestions["missing_optional"]:
            return "✅ All dependencies are available!"
        
        lines = [f"Missing Dependencies ({suggestions['platform']}):", ""]
        
        if suggestions["missing_essential"]:
            lines.extend([
                "🚨 ESSENTIAL (required for core functionality):",
                ""
            ])
            
            for dep in suggestions["missing_essential"]:
                lines.append(f"• {dep['name']}: {dep['description']}")
                if dep.get("installation_options"):
                    for pkg_mgr, pkg_name in dep["installation_options"].items():
                        lines.append(f"  Install: {pkg_mgr} install {pkg_name}")
                if dep.get("platform_note"):
                    lines.append(f"  Note: {dep['platform_note']}")
                lines.append("")
        
        if suggestions["missing_optional"]:
            lines.extend([
                "💡 OPTIONAL (enhanced functionality):",
                ""
            ])
            
            for dep in suggestions["missing_optional"]:
                lines.append(f"• {dep['name']}: {dep['description']}")
                if dep.get("installation_options"):
                    for pkg_mgr, pkg_name in dep["installation_options"].items():
                        lines.append(f"  Install: {pkg_mgr} install {pkg_name}")
                if dep.get("platform_note"):
                    lines.append(f"  Note: {dep['platform_note']}")
                lines.append("")
        
        return "\n".join(lines)
        
    except Exception as e:
        return f"❌ Error getting missing dependencies: {str(e)}"


@mcp.resource("system-dependencies://packages")
def get_discovered_packages() -> str:
    """Get discovered LaTeX packages from system package manager."""
    try:
        packages_info = system_checker.get_discovered_packages()
        
        if not packages_info.get("available", False):
            return f"Package discovery not available: {packages_info.get('message', 'Unknown error')}"
        
        # Format as human-readable text
        lines = [
            f"📦 Discovered LaTeX Packages",
            f"Total: {packages_info['total_packages']} packages",
            f"Distribution: {packages_info['distribution']['name']} {packages_info['distribution']['version']}",
            f"Package Manager: {packages_info['package_manager']}",
            "",
            "Categories:"
        ]
        
        # Show category breakdown
        for cat_name, cat_info in sorted(packages_info['categories'].items()):
            lines.append(f"  • {cat_name}: {cat_info['count']} packages")
            # Show first 5 packages in each category
            sample_packages = cat_info['packages'][:5]
            if sample_packages:
                for pkg in sample_packages:
                    lines.append(f"    - {pkg}")
                if len(cat_info['packages']) > 5:
                    lines.append(f"    ... and {len(cat_info['packages']) - 5} more")
        
        lines.extend([
            "",
            "⚠️  Important Notes:"
        ])
        
        for warning in packages_info.get('warnings', []):
            lines.append(f"  - {warning}")
        
        return "\n".join(lines)
        
    except Exception as e:
        return f"❌ Error discovering packages: {str(e)}"


# Additional TeXFlow content resources
# These resources provide discoverable information about TeXFlow's state
# They complement the system dependency resources above
@mcp.resource("texflow://projects")
def get_projects_list() -> str:
    """List all TeXFlow projects with their status and information."""
    try:
        # Call the core implementation to get project list
        result = texflow.project(action="list")
        
        # Enhanced output with helpful hints
        lines = ["📁 TeXFlow Projects", "=" * 40]
        
        if "No projects" in result:
            lines.extend([
                "",
                "No projects found yet!",
                "",
                "💡 Get started:",
                "→ Create a new project: project(action='create', name='my-project')",
                "→ Import existing folder: project(action='import', name='existing-folder')"
            ])
        else:
            lines.append("")
            lines.append(result)
            
            # Add current project info if available
            if SESSION_CONTEXT.get("current_project"):
                lines.extend([
                    "",
                    f"📍 Current: {SESSION_CONTEXT['current_project']}",
                    "",
                    "💡 Project commands:",
                    "→ Switch: project(action='switch', name='project-name')",
                    "→ Info: project(action='info')",
                    "→ Create document: document(action='create', content='...')"
                ])
                
        return "\n".join(lines)
        
    except Exception as e:
        return f"❌ Error listing projects: {str(e)}"


@mcp.resource("texflow://templates") 
def get_templates_list() -> str:
    """List available document templates organized by category."""
    try:
        result = texflow.templates(action="list")
        
        lines = ["📄 Document Templates", "=" * 40, ""]
        
        if "No templates found" in result:
            lines.extend([
                "No templates found.",
                "",
                "💡 Get started with templates:",
                "→ Create from scratch: templates(action='create', category='research', name='paper')",
                "→ Activate current project as template: templates(action='activate', category='custom', name='my-template')",
                "→ Clone template repository: git clone https://github.com/[user]/texflow-templates ~/Documents/TeXFlow/templates"
            ])
        else:
            lines.append(result)
            lines.extend([
                "",
                "💡 Template commands:",
                "→ Use: templates(action='use', category='...', name='...')",
                "→ Info: templates(action='info', category='...', name='...')",
                "→ Create new: templates(action='create', category='...', name='...')"
            ])
            
        return "\n".join(lines)
        
    except Exception as e:
        return f"❌ Error listing templates: {str(e)}"


@mcp.resource("texflow://recent-documents")
def get_recent_documents() -> str:
    """List recently modified documents across all projects."""
    try:
        # Use the new "recent" action we added to texflow.py
        # This demonstrates how the unified server leverages core functionality
        result = texflow.discover(action="recent")
        
        lines = ["📝 Recent Documents", "=" * 40, ""]
        
        if "No recent documents" in result or "not yet implemented" in result.lower():
            # Fallback: list documents in current project
            if SESSION_CONTEXT.get("current_project"):
                docs_result = texflow.discover(action="documents")
                lines.extend([
                    f"Documents in current project ({SESSION_CONTEXT['current_project']}):",
                    "",
                    docs_result,
                    "",
                    "💡 Document commands:",
                    "→ Read: document(action='read', path='...')",
                    "→ Edit: document(action='edit', path='...')",
                    "→ Export PDF: output(action='export', source='...')"
                ])
            else:
                lines.extend([
                    "No current project active.",
                    "",
                    "💡 Get started:",
                    "→ List projects: project(action='list')",
                    "→ Create project: project(action='create', name='...')",
                    "→ Switch project: project(action='switch', name='...')"
                ])
        else:
            lines.append(result)
            
        return "\n".join(lines)
        
    except Exception as e:
        return f"❌ Error listing recent documents: {str(e)}"


@mcp.resource("texflow://workflow-guide")
def get_workflow_guide() -> str:
    """Get context-aware workflow guidance based on current state."""
    try:
        lines = ["🎯 TeXFlow Workflow Guide", "=" * 40, ""]
        
        # Check current context
        current_project = SESSION_CONTEXT.get("current_project")
        
        if not current_project:
            # No project context - suggest getting started
            lines.extend([
                "📍 Status: No active project",
                "",
                "🚀 Getting Started Workflow:",
                "",
                "1️⃣ Create or select a project:",
                "   project(action='create', name='my-paper', description='Research paper on...')",
                "   OR",
                "   project(action='list')  # See existing projects",
                "   project(action='switch', name='existing-project')",
                "",
                "2️⃣ Choose a template (optional):",
                "   templates(action='list')  # Browse available templates",
                "   templates(action='use', category='default', name='minimal')",
                "",
                "3️⃣ Create your document:",
                "   document(action='create', content='# Title', path='introduction.md')",
                "",
                "4️⃣ Edit and develop:",
                "   document(action='read', path='...')  # Review content",
                "   document(action='edit', path='...', old_string='...', new_string='...')",
                "",
                "5️⃣ Generate output:",
                "   output(action='export', source='...', output_path='output/paper.pdf')"
            ])
        else:
            # Project active - provide contextual guidance
            lines.extend([
                f"📍 Current Project: {current_project}",
                "",
                "📋 Available Workflows:",
                ""
            ])
            
            # Get workflow suggestions
            workflows = [
                ("📝 Write a Document", [
                    "document(action='create', content='# Title\\nContent...', path='document.md')",
                    "document(action='edit', path='document.md', old_string='...', new_string='...')",
                    "document(action='validate', path='document.md')"
                ]),
                ("📄 Convert Formats", [
                    "document(action='convert', source='document.md', target_format='latex')",
                    "document(action='validate', path='document.tex')",
                    "output(action='export', source='document.tex')"
                ]),
                ("🖨️ Generate Output", [
                    "output(action='export', source='document.md', output_path='output/document.pdf')",
                    "output(action='print', source='output/document.pdf')"
                ]),
                ("🗂️ Organize Documents", [
                    "organizer(action='list_archived')  # See archived docs",
                    "organizer(action='archive', path='old-draft.md', reason='Superseded')",
                    "organizer(action='clean_aux', path='document.tex')  # Clean LaTeX files"
                ])
            ]
            
            for title, commands in workflows:
                lines.append(f"{title}:")
                for cmd in commands:
                    lines.append(f"  → {cmd}")
                lines.append("")
            
            # Add tips based on system status
            missing_deps = system_checker.get_missing_essential_dependencies()
            if missing_deps:
                lines.extend([
                    "⚠️  Limited functionality - missing dependencies:",
                    f"   {', '.join(missing_deps)}",
                    "   View details: ReadMcpResourceTool(uri='system-dependencies://missing')",
                    ""
                ])
                
        lines.extend([
            "💡 Pro Tips:",
            "• Work in projects for better organization",
            "• Use templates to save time",  
            "• Edit existing files instead of recreating",
            "• Convert formats instead of rewriting",
            "• Validate LaTeX before generating PDFs"
        ])
        
        return "\n".join(lines)
        
    except Exception as e:
        return f"❌ Error generating workflow guide: {str(e)}"


def main():
    """Run the unified semantic MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()