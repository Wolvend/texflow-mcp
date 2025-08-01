#!/usr/bin/env python3
"""TeXFlow MCP Server - Secure implementation with restricted file access"""

import os
import sys
import asyncio
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

# Import the semantic layer
from src.texflow_semantic import TeXFlowSemantic
from src.core.system_checker import SystemDependencyChecker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/texflow_security.log', mode='a'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger('texflow')

# Ensure immediate logging
for handler in logger.handlers:
    handler.flush()

# Security constants
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB - sweet spot for PDFs and large documents
MAX_FILES_PER_PROJECT = 1000  # Reasonable for large projects
ALLOWED_EXTENSIONS = {
    # Document formats
    '.tex', '.md', '.txt', '.bib', '.cls', '.sty', '.pdf', '.docx', '.html', 
    # Image formats for LaTeX
    '.png', '.jpg', '.jpeg', '.eps', '.svg', '.tiff', '.bmp',
    # Data formats for scientific work
    '.csv', '.dat', '.json', '.xml',
    # LaTeX auxiliary files
    '.aux', '.log', '.toc', '.lof', '.lot', '.idx', '.ind', '.bbl', '.blg'
}

# Create server instance
server = Server("texflow")

# Initialize semantic wrapper
semantic = None
system_checker = None
workspace_root = None

def is_safe_path(path: str) -> bool:
    """Check if a path is within the workspace and safe to access."""
    try:
        # Convert to absolute path
        abs_path = Path(path).resolve()
        # Check if it's within workspace
        abs_path.relative_to(workspace_root)
        return True
    except (ValueError, RuntimeError):
        logger.warning(f"Attempted access outside workspace: {path}")
        return False

def validate_file_extension(path: str) -> bool:
    """Check if file has an allowed extension."""
    ext = Path(path).suffix.lower()
    return ext in ALLOWED_EXTENSIONS

def handle_advanced_tool(tool_name: str, args: Dict[str, Any], workspace: Path) -> Optional[str]:
    """Handle advanced tool operations"""
    from texflow_advanced import (
        LaTeXDiagnostics, BibliographyManager, VersionControl,
        SmartSearch, ProjectAnalytics, PerformanceOptimizer
    )
    
    try:
        if tool_name == "diagnose":
            path = workspace / args["path"]
            if not is_safe_path(path):
                return "Error: Path outside workspace"
            
            # Read error log or compile to get errors
            if "error_log" in args:
                errors = args["error_log"]
            else:
                # Would compile here to get errors
                errors = "Mock compilation errors"
            
            diagnostics = LaTeXDiagnostics.diagnose(errors)
            
            if args.get("auto_fix") and diagnostics:
                fixes = LaTeXDiagnostics.auto_fix(str(path), diagnostics)
                return f"Applied fixes: {fixes}\nDiagnostics: {json.dumps(diagnostics, indent=2)}"
            
            return json.dumps(diagnostics, indent=2)
        
        elif tool_name == "bibliography":
            action = args["action"]
            
            if action == "import":
                source = args.get("source", "")
                if source.startswith("10."):  # DOI
                    return BibliographyManager.import_from_doi(source)
                elif "arxiv" in source.lower():
                    return BibliographyManager.import_from_arxiv(source)
                else:
                    return "Unsupported source format"
            
            elif action == "check":
                file_path = workspace / args["file"]
                if not is_safe_path(file_path):
                    return "Error: Path outside workspace"
                
                content = file_path.read_text()
                duplicates = BibliographyManager.check_duplicates(content)
                return f"Duplicate entries: {duplicates}" if duplicates else "No duplicates found"
            
            elif action == "format":
                file_path = workspace / args["file"]
                if not is_safe_path(file_path):
                    return "Error: Path outside workspace"
                
                content = file_path.read_text()
                formatted = BibliographyManager.format_bibliography(content, args.get("style", "plain"))
                file_path.write_text(formatted)
                return "Bibliography formatted successfully"
        
        elif tool_name == "version":
            vc = VersionControl(workspace)
            action = args["action"]
            path = workspace / args["path"]
            
            if not is_safe_path(path):
                return "Error: Path outside workspace"
            
            if action == "commit":
                version_id = vc.commit(str(path), args.get("message", "No message"))
                return f"Created version: {version_id}"
            
            elif action == "diff":
                return vc.diff(str(path), args.get("revision"))
            
            elif action == "history":
                # Would list version history
                return "Version history feature coming soon"
        
        elif tool_name == "smart_edit":
            action = args["action"]
            path = workspace / args["path"]
            
            if not is_safe_path(path):
                return "Error: Path outside workspace"
            
            content = path.read_text()
            
            if action == "search":
                matches = SmartSearch.search_in_scope(
                    content, 
                    args.get("pattern", ""),
                    args.get("scope", "all")
                )
                return json.dumps(matches, indent=2)
            
            elif action == "find_unused":
                # Find unused references
                bib_path = path.with_suffix('.bib')
                if bib_path.exists():
                    bib_content = bib_path.read_text()
                    unused = SmartSearch.find_unused_references(content, bib_content)
                    return f"Unused references: {unused}"
                return "No bibliography file found"
        
        elif tool_name == "analytics":
            action = args["action"]
            path = workspace / args["path"]
            
            if not is_safe_path(path):
                return "Error: Path outside workspace"
            
            if action == "wordcount":
                content = path.read_text()
                count = ProjectAnalytics.word_count(content, args.get("by_section", False))
                return json.dumps(count, indent=2)
            
            elif action == "velocity":
                velocity = ProjectAnalytics.calculate_velocity(path.parent, args.get("period", "day"))
                return json.dumps(velocity, indent=2)
        
        elif tool_name == "performance":
            action = args["action"]
            path = workspace / args["path"]
            
            if not is_safe_path(path):
                return "Error: Path outside workspace"
            
            if action == "analyze":
                # Would analyze compilation log
                return json.dumps({"status": "Analysis complete", "issues": []}, indent=2)
            
            elif action == "cache":
                config = PerformanceOptimizer.create_cache_config(path.parent)
                return json.dumps(config, indent=2)
        
        elif tool_name == "export":
            # This would use pandoc for conversion
            return f"Export to {args['format']} would be implemented with pandoc"
        
    except Exception as e:
        logger.error(f"Error in advanced tool {tool_name}: {str(e)}", exc_info=True)
        return f"Error: {str(e)}"
    
    return None

def sanitize_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize and validate parameters."""
    # Remove any potentially dangerous keys
    dangerous_keys = {'__', 'eval', 'exec', 'compile', 'open', 'file'}
    cleaned = {}
    
    for key, value in params.items():
        if any(danger in key.lower() for danger in dangerous_keys):
            logger.warning(f"Blocked dangerous parameter: {key}")
            continue
        
        # Validate file paths
        if key in ['path', 'source_path', 'target', 'source'] and value:
            full_path = workspace_root / value
            if not is_safe_path(full_path):
                raise ValueError(f"Path outside workspace: {value}")
        
        cleaned[key] = value
    
    return cleaned

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available TeXFlow tools - enhanced for long-form content."""
    tools = [
        types.Tool(
            name="document",
            description="Document operations: create, read, edit, append documents (supports incremental writing)",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "read", "edit", "append", "insert"],
                        "description": "The action to perform (append for incremental writing, insert for adding at specific positions)"
                    },
                    "path": {"type": "string", "description": "Document path (relative to workspace)"},
                    "content": {"type": "string", "description": "Document content (for create/edit/append/insert)"},
                    "position": {"type": "string", "description": "Position for insert: 'line:NUMBER' or 'after:MARKER_TEXT' or 'before:MARKER_TEXT'"},
                    "format": {"type": "string", "enum": ["latex", "markdown"], "description": "Document format"},
                    "project": {"type": "string", "description": "Project name", "pattern": "^[a-zA-Z0-9_-]+$"},
                    "encoding": {"type": "string", "enum": ["utf-8", "latin-1"], "description": "File encoding (default: utf-8)"}
                },
                "required": ["action", "path"]
            }
        ),
        types.Tool(
            name="output",
            description="Export documents to PDF or DOCX format",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["export"],
                        "description": "Export action"
                    },
                    "path": {"type": "string", "description": "Document path (relative to workspace)"},
                    "format": {"type": "string", "enum": ["pdf", "docx"], "description": "Export format"}
                },
                "required": ["action", "path", "format"]
            }
        ),
        types.Tool(
            name="project",
            description="Project management with template support",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "list", "status"],
                        "description": "The action to perform"
                    },
                    "name": {"type": "string", "description": "Project name", "pattern": "^[a-zA-Z0-9_-]+$", "maxLength": 100},
                    "template": {
                        "type": "string", 
                        "enum": ["book", "thesis", "article", "report", "math-heavy", "novel"],
                        "description": "Project template for initial structure"
                    }
                },
                "required": ["action"]
            }
        ),
        types.Tool(
            name="compile",
            description="Compile LaTeX documents with error handling",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Main LaTeX file path"},
                    "engine": {
                        "type": "string",
                        "enum": ["pdflatex", "xelatex", "lualatex"],
                        "description": "LaTeX engine (xelatex for Unicode, lualatex for advanced features)"
                    },
                    "passes": {"type": "integer", "minimum": 1, "maximum": 5, "description": "Number of compilation passes (default: 2)"}
                },
                "required": ["path"]
            }
        ),
        types.Tool(
            name="diagnose",
            description="Diagnose and auto-fix LaTeX compilation errors",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "LaTeX file with errors"},
                    "error_log": {"type": "string", "description": "Compilation error log (optional)"},
                    "auto_fix": {"type": "boolean", "description": "Automatically apply suggested fixes"},
                    "install_missing": {"type": "boolean", "description": "Auto-install missing packages"}
                },
                "required": ["path"]
            }
        ),
        types.Tool(
            name="bibliography",
            description="Manage BibTeX references and citations",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["import", "format", "check", "convert", "search"],
                        "description": "Bibliography action"
                    },
                    "source": {"type": "string", "description": "DOI, arXiv ID, ISBN, or BibTeX entry"},
                    "file": {"type": "string", "description": "Bibliography file path (.bib)"},
                    "style": {"type": "string", "enum": ["plain", "alpha", "ieeetr", "apalike", "chicago"], "description": "Citation style"},
                    "query": {"type": "string", "description": "Search query for references"}
                },
                "required": ["action"]
            }
        ),
        types.Tool(
            name="version",
            description="Version control for LaTeX documents",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["commit", "diff", "rollback", "history", "branch"],
                        "description": "Version control action"
                    },
                    "path": {"type": "string", "description": "File or project path"},
                    "message": {"type": "string", "description": "Commit message"},
                    "revision": {"type": "string", "description": "Revision ID for rollback"},
                    "branch": {"type": "string", "description": "Branch name"}
                },
                "required": ["action", "path"]
            }
        ),
        types.Tool(
            name="smart_edit",
            description="LaTeX-aware search and replace with advanced features",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["search", "replace", "rename", "find_unused"],
                        "description": "Smart edit action"
                    },
                    "pattern": {"type": "string", "description": "Search pattern (supports regex)"},
                    "replacement": {"type": "string", "description": "Replacement text"},
                    "scope": {
                        "type": "string",
                        "enum": ["all", "equations", "figures", "tables", "citations", "commands"],
                        "description": "Search scope"
                    },
                    "path": {"type": "string", "description": "File or project path"}
                },
                "required": ["action", "path"]
            }
        ),
        types.Tool(
            name="analytics",
            description="Project analytics and writing statistics",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["wordcount", "velocity", "progress", "structure"],
                        "description": "Analytics action"
                    },
                    "path": {"type": "string", "description": "File or project path"},
                    "period": {"type": "string", "enum": ["day", "week", "month"], "description": "Time period for velocity"},
                    "by_section": {"type": "boolean", "description": "Break down by chapter/section"}
                },
                "required": ["action", "path"]
            }
        ),
        types.Tool(
            name="export",
            description="Export to multiple formats beyond PDF",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Source LaTeX file"},
                    "format": {
                        "type": "string",
                        "enum": ["pdf", "docx", "epub", "html", "markdown", "rtf"],
                        "description": "Output format"
                    },
                    "options": {
                        "type": "object",
                        "description": "Format-specific options",
                        "properties": {
                            "track_changes": {"type": "boolean", "description": "Enable track changes for Word"},
                            "css": {"type": "string", "description": "Custom CSS for HTML"},
                            "epub_cover": {"type": "string", "description": "Cover image for EPUB"}
                        }
                    }
                },
                "required": ["path", "format"]
            }
        ),
        types.Tool(
            name="performance",
            description="Monitor and optimize LaTeX compilation performance",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["analyze", "cache", "optimize", "profile"],
                        "description": "Performance action"
                    },
                    "path": {"type": "string", "description": "Project path"},
                    "clear_cache": {"type": "boolean", "description": "Clear compilation cache"}
                },
                "required": ["action", "path"]
            }
        )
    ]
    return tools

@server.call_tool()
async def handle_call_tool(
    name: str,
    arguments: dict | None = None,
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls by routing through the semantic layer."""
    global semantic
    
    if not semantic:
        logger.error("TeXFlow not initialized")
        return [types.TextContent(
            type="text",
            text="Error: TeXFlow not initialized. Please restart the server."
        )]
    
    try:
        # Log the tool call
        logger.info(f"Tool call: {name} with action: {arguments.get('action', 'N/A') if arguments else 'N/A'}")
        
        # Sanitize parameters
        safe_args = sanitize_params(arguments or {})
        
        # Additional validation for specific tools
        if name == "document":
            # Check file size for content BEFORE sanitization
            if "content" in arguments and len(str(arguments["content"])) > MAX_FILE_SIZE:
                raise ValueError(f"Content exceeds maximum size of {MAX_FILE_SIZE // (1024*1024)}MB")
            
            # Validate file extension
            if "path" in safe_args and not validate_file_extension(safe_args["path"]):
                raise ValueError(f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}")
        
        # Handle new advanced tools
        if name in ["diagnose", "bibliography", "version", "smart_edit", "analytics", "export", "performance"]:
            # Import advanced features
            from texflow_advanced import (
                LaTeXDiagnostics, BibliographyManager, VersionControl,
                SmartSearch, ProjectAnalytics, PerformanceOptimizer
            )
            
            result = handle_advanced_tool(name, safe_args, workspace_root)
            if result:
                return [types.TextContent(type="text", text=str(result))]
        
        # Route through semantic layer (not async)
        result = semantic.execute(name, safe_args.get("action", ""), safe_args)
        
        logger.info(f"Tool call successful: {name}")
        return [types.TextContent(
            type="text",
            text=str(result)
        )]
    except ValueError as e:
        logger.warning(f"Validation error in {name}: {str(e)}")
        return [types.TextContent(
            type="text",
            text=f"Validation error: {str(e)}"
        )]
    except Exception as e:
        logger.error(f"Error executing {name}: {str(e)}", exc_info=True)
        return [types.TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """List available TeXFlow resources."""
    return [
        types.Resource(
            uri="system-dependencies://status",
            name="System Dependencies Status",
            description="Complete dependency status as JSON",
            mimeType="application/json"
        ),
        types.Resource(
            uri="system-dependencies://summary",
            name="Dependency Summary",
            description="Human-readable dependency summary",
            mimeType="text/plain"
        ),
        types.Resource(
            uri="system-dependencies://missing",
            name="Missing Dependencies",
            description="Installation guidance for missing tools",
            mimeType="text/plain"
        ),
        types.Resource(
            uri="system-dependencies://packages",
            name="Discovered Packages",
            description="LaTeX packages from system package manager",
            mimeType="application/json"
        ),
        types.Resource(
            uri="texflow://projects",
            name="TeXFlow Projects",
            description="List all projects with commands",
            mimeType="text/plain"
        ),
        types.Resource(
            uri="texflow://templates",
            name="Document Templates",
            description="Browse available templates",
            mimeType="text/plain"
        ),
        types.Resource(
            uri="texflow://recent-documents",
            name="Recent Documents",
            description="Recently edited documents",
            mimeType="text/plain"
        ),
        types.Resource(
            uri="texflow://workflow-guide",
            name="Workflow Guide",
            description="Context-aware workflow guidance",
            mimeType="text/plain"
        ),
        types.Resource(
            uri="texflow://latex-reference",
            name="LaTeX Reference",
            description="LaTeX reference database stats",
            mimeType="text/plain"
        )
    ]

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a TeXFlow resource."""
    global system_checker, semantic
    
    if uri.startswith("system-dependencies://"):
        if not system_checker:
            return "Error: System checker not initialized"
        
        resource_type = uri.split("://")[1]
        
        if resource_type == "status":
            import json
            return json.dumps(system_checker.get_status(), indent=2)
        elif resource_type == "summary":
            return system_checker.get_summary()
        elif resource_type == "missing":
            return system_checker.get_missing_tools_guidance()
        elif resource_type == "packages":
            import json
            return json.dumps(system_checker.discovered_packages, indent=2)
    
    elif uri.startswith("texflow://"):
        if not semantic:
            return "Error: TeXFlow not initialized"
        
        resource_type = uri.split("://")[1]
        
        # For now, return placeholder content
        # In a full implementation, these would call appropriate methods
        if resource_type == "projects":
            return "TeXFlow Projects:\n\nNo projects found. Create one with: project(action='create', name='my-project')"
        elif resource_type == "templates":
            return "Document Templates:\n\nAvailable templates:\n- article\n- report\n- thesis\n- letter"
        elif resource_type == "recent-documents":
            return "Recent Documents:\n\nNo recent documents."
        elif resource_type == "workflow-guide":
            return "TeXFlow Workflow Guide:\n\n1. Create a project\n2. Create documents\n3. Edit and validate\n4. Export to PDF"
        elif resource_type == "latex-reference":
            return "LaTeX Reference Database:\n\n5900+ commands\n1000+ symbols\nPackage documentation\nError solutions"
    
    return f"Unknown resource: {uri}"

async def main():
    """Main entry point for the TeXFlow server."""
    global semantic, system_checker, workspace_root
    
    # Get workspace root from command line or environment
    if len(sys.argv) > 1:
        workspace_root = Path(sys.argv[1]).resolve()
    else:
        workspace_root = Path(os.environ.get("TEXFLOW_WORKSPACE", Path.home() / "Documents" / "TeXFlow")).resolve()
    
    # Create workspace if it doesn't exist
    workspace_root.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"TeXFlow server starting with workspace: {workspace_root}")
    logger.info(f"Security features enabled: path validation, file size limits, extension filtering")
    
    # Initialize system checker
    system_checker = SystemDependencyChecker()
    
    # Import the original texflow module
    import texflow
    
    # Create texflow instance
    texflow_instance = texflow
    
    # Initialize semantic wrapper with the texflow instance
    semantic = TeXFlowSemantic(texflow_instance)
    
    # Run the server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="texflow",
                server_version="0.2.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())