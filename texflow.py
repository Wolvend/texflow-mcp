#!/usr/bin/env python3
"""TeXFlow Core Implementation - Base MCP Server

This is the CORE IMPLEMENTATION file that contains all the actual tool logic
for TeXFlow. It serves as the foundation that texflow_unified.py builds upon.

ARCHITECTURE:
- This file: Contains all the raw tool implementations (file operations, 
  project management, document conversion, etc.)
- texflow_unified.py: Imports this module and wraps it with a semantic layer
  for intelligent guidance and enhanced user experience

WHY THIS SEPARATION?
1. Modularity: Core logic is separate from semantic enhancements
2. Testability: Can test core functions without MCP/semantic overhead  
3. Reusability: Other systems could import and use these functions directly
4. Backwards compatibility: Original implementation remains intact

WORKFLOW PHILOSOPHY:
1. Projects First: Always work within a project context for organization
2. Edit Don't Recreate: Use edit operations on existing documents to save tokens
3. Convert Don't Rewrite: Transform between formats instead of regenerating
4. Validate Before Export: Check LaTeX syntax before generating PDFs

NOTE: Users typically interact with texflow_unified.py, not this file directly.
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from mcp.server.fastmcp import FastMCP
    # Create MCP server instance
    mcp = FastMCP("texflow")
except ImportError:
    # Running in test mode without MCP
    class MockMCP:
        def tool(self):
            def decorator(func):
                return func
            return decorator
    mcp = MockMCP()

# SHARED STATE: This SESSION_CONTEXT is imported and used by texflow_unified.py
# Both files need access to the same session state to maintain consistency
SESSION_CONTEXT = {
    "current_project": None,
    "default_printer": None,
    "last_used_format": None,
    "workspace_root": Path.cwd(),  # Store the initial working directory
    "workflow_warnings_shown": set()  # Track which warnings have been shown
}

# SHARED CONSTANTS: These paths are also used by texflow_unified.py
# The unified server updates TEXFLOW_ROOT based on command line args
TEXFLOW_ROOT = Path.home() / "Documents" / "TeXFlow"
TEMPLATES_DIR = TEXFLOW_ROOT / "templates"  # Lowercase for convention


def initialize_default_template():
    """Initialize the default template if it doesn't exist."""
    default_template_path = TEMPLATES_DIR / "default" / "minimal"
    
    # Only create if it doesn't exist
    if not default_template_path.exists():
        default_template_path.mkdir(parents=True, exist_ok=True)
        
        # Create main.tex
        main_tex = default_template_path / "main.tex"
        main_tex.write_text(r"""\documentclass[12pt,a4paper]{article}

% Packages
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{geometry}
\usepackage{hyperref}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{amssymb}

% Document settings
\geometry{margin=1in}
\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,      
    urlcolor=cyan,
}

% Document metadata
\title{Document Title}
\author{Your Name}
\date{\today}

\begin{document}

\maketitle

\begin{abstract}
This is the abstract of your document. Provide a brief summary of your work here.
\end{abstract}

\tableofcontents
\newpage

\section{Introduction}
Start writing your document here. This template includes commonly used packages and a standard structure.

\section{Main Content}
Your main content goes here.

\subsection{Subsection Example}
You can organize your content with subsections.

\section{Conclusion}
Summarize your work here.

% Bibliography example (uncomment to use)
% \bibliographystyle{plain}
% \bibliography{references}

\end{document}""")
        
        # Create a sample bibliography file
        references_bib = default_template_path / "references.bib"
        references_bib.write_text(r"""@article{example2024,
    author = {Author, First and Second, Author},
    title = {An Example Article},
    journal = {Journal Name},
    year = {2024},
    volume = {1},
    number = {1},
    pages = {1--10}
}

@book{examplebook2024,
    author = {Book Author},
    title = {An Example Book},
    publisher = {Publisher Name},
    year = {2024},
    edition = {1st}
}""")
        
        # Create a README for the template
        readme = default_template_path / "README.md"
        readme.write_text("""# Default Minimal Template

This is the default TeXFlow template that demonstrates the basic structure for LaTeX documents.

## Files Included

- `main.tex` - The main LaTeX document with common packages and structure
- `references.bib` - Sample bibliography file
- `README.md` - This file

## Usage

This template includes:
- Common LaTeX packages (geometry, hyperref, graphicx, amsmath)
- Standard document structure (title, abstract, table of contents, sections)
- Bibliography setup (commented out by default)
- Proper UTF-8 encoding and font setup

## Customization

Feel free to modify this template to suit your needs. It will not be overwritten by TeXFlow.
""")


# Initialize default template on import
initialize_default_template()


def resolve_path(path_str: Optional[str] = None, default_name: str = "document", 
                 extension: str = ".txt", use_project: bool = True) -> Path:
    """
    CRITICAL SHARED FUNCTION: This is used throughout the codebase by both
    texflow.py and the semantic layer to resolve file paths intelligently.
    
    Resolve a path intelligently based on context.
    
    Priority order:
    1. If path is absolute, use it as-is
    2. If path is relative and we have a current project, use project directory
    3. If path is relative, use workspace root
    4. If no path given and we have a project, use project content directory
    5. If no path given, use workspace root
    
    This function ensures consistent path handling across all tools.
    """
    if path_str:
        path = Path(path_str)
        
        # Handle absolute paths
        if path.is_absolute():
            # When in a project, restrict absolute paths to workspace
            if use_project and SESSION_CONTEXT["current_project"]:
                # Extract just the filename from absolute path
                filename = path.name
                project_base = TEXFLOW_ROOT / SESSION_CONTEXT["current_project"]
                return project_base / "content" / filename
            else:
                # Outside project, allow absolute paths within workspace only
                abs_path = path.expanduser()
                if TEXFLOW_ROOT in abs_path.parents or abs_path == TEXFLOW_ROOT:
                    return abs_path
                else:
                    # Path outside workspace - use filename only in workspace root
                    return SESSION_CONTEXT["workspace_root"] / path.name
            
        # Relative path with project context
        if use_project and SESSION_CONTEXT["current_project"]:
            # current_project now contains the full relative path from TeXFlow root
            project_base = TEXFLOW_ROOT / SESSION_CONTEXT["current_project"]
            # If path starts with common project folders, use it directly
            if str(path).startswith(("content/", "output/", "assets/")):
                return project_base / path
            else:
                # Default to content directory for relative paths
                return project_base / "content" / path
        
        # Relative path without project - use workspace
        return SESSION_CONTEXT["workspace_root"] / path
    
    else:
        # No path given - generate default
        if use_project and SESSION_CONTEXT["current_project"]:
            # current_project now contains the full relative path from TeXFlow root
            project_base = TEXFLOW_ROOT / SESSION_CONTEXT["current_project"]
            return project_base / "content" / f"{default_name}{extension}"
        else:
            # Use workspace root
            return SESSION_CONTEXT["workspace_root"] / f"{default_name}{extension}"


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
    """CORE TOOL: Document management implementation.
    
    This is the actual implementation that handles all document operations.
    When called through texflow_unified.py, this function:
    1. Receives parameters from the semantic layer
    2. Performs the actual file operations
    3. Returns raw results that get enhanced by the semantic layer
    
    Manage document lifecycle - create, read, edit, convert, validate, and track changes.
    
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
    """
    if action == "create":
        if not content:
            return "❌ Error: Content required for create action"
            
        # Auto-detect format
        if format == "auto":
            if intent and ("paper" in intent.lower() or "academic" in intent.lower() or "research" in intent.lower()):
                format = "latex"
            elif "\\documentclass" in content or "\\begin{" in content:
                format = "latex"
            else:
                format = "markdown"
        
        # Determine file extension
        ext = ".tex" if format == "latex" else ".md"
        
        # Create file path using intelligent resolution
        file_path = resolve_path(path, "document", ext)
            
        # Write content
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            
            next_steps = ["💡 Next steps:"]
            next_steps.append(f"→ Read: document(action='read', path='{file_path}')")
            next_steps.append(f"→ Edit: document(action='edit', path='{file_path}')")
            if file_path.suffix == ".tex":
                next_steps.append(f"→ Validate: document(action='validate', path='{file_path}')")
            next_steps.append(f"→ Export: output(action='export', source='{file_path}')")
            
            project_info = f" (Project: {SESSION_CONTEXT['current_project']})" if SESSION_CONTEXT['current_project'] else ""
            return f"✓ Document created: {file_path}{project_info}\n" + "\n".join(next_steps)
        except Exception as e:
            return f"❌ Error creating document: {e}"
            
    elif action == "read":
        if not path:
            return "❌ Error: Path required for read action"
            
        file_path = resolve_path(path)
        if not file_path.exists():
            return f"❌ Error: File not found: {file_path}"
            
        try:
            lines = file_path.read_text().splitlines()
            # Format with line numbers
            result = []
            for i, line in enumerate(lines[:50], 1):  # Limit to 50 lines
                result.append(f"{i:4d}\t{line}")
            return "\n".join(result) + (f"\n... ({len(lines)} total lines)" if len(lines) > 50 else "")
        except Exception as e:
            return f"❌ Error reading document: {e}"
            
    elif action == "edit":
        if not path or not old_string or not new_string:
            return "❌ Error: Path, old_string, and new_string required for edit action"
            
        file_path = resolve_path(path)
        if not file_path.exists():
            return f"❌ Error: File not found: {file_path}"
            
        try:
            content = file_path.read_text()
            if old_string not in content:
                return f"❌ Error: String '{old_string}' not found in file"
                
            new_content = content.replace(old_string, new_string, 1)
            file_path.write_text(new_content)
            
            # Provide multiple next step options based on file type
            next_steps = ["💡 Next steps:"]
            next_steps.append(f"→ Edit more: document(action='edit', path='{file_path}')")
            next_steps.append(f"→ Review changes: document(action='read', path='{file_path}')")
            
            if file_path.suffix == ".tex":
                next_steps.append(f"→ Validate: document(action='validate', path='{file_path}')")
            
            next_steps.append(f"→ Export: output(action='export', source='{file_path}')")
            
            return f"✓ Document edited: {file_path}\n" + "\n".join(next_steps)
        except Exception as e:
            return f"❌ Error editing document: {e}"
            
    elif action == "convert":
        if not source or not target_format:
            return "❌ Error: Source and target_format required for convert action"
            
        source_path = resolve_path(source)
        if not source_path.exists():
            return f"❌ Error: Source file not found: {source_path}"
            
        if target_format == "latex" and source_path.suffix == ".md":
            # Convert Markdown to LaTeX using pandoc
            output_path = source_path.with_suffix(".tex")
            try:
                subprocess.run(["pandoc", "-f", "markdown", "-t", "latex", "-o", str(output_path), str(source_path)], check=True)
                return f"✓ Converted to LaTeX: {output_path}\n💡 Next: document(action='edit', path='{output_path}')"
            except subprocess.CalledProcessError as e:
                return f"❌ Error converting document: {e}"
        else:
            return f"❌ Error: Conversion from {source_path.suffix} to {target_format} not supported"
            
    elif action == "validate":
        if not path:
            return "❌ Error: Path required for validate action"
            
        file_path = resolve_path(path)
        if not file_path.exists():
            return f"❌ Error: File not found: {file_path}"
            
        if file_path.suffix == ".tex":
            # Validate LaTeX file
            errors = []
            warnings = []
            
            # Try chktex if available
            try:
                result = subprocess.run(["chktex", str(file_path)], capture_output=True, text=True)
                if "Error" in result.stderr:
                    errors.append(result.stderr)
                if "Warning" in result.stdout:
                    # Extract warning count
                    import re
                    match = re.search(r'(\d+) warnings? printed', result.stdout)
                    if match:
                        warnings.append(f"{match.group(1)} warnings found (run chktex for details)")
            except FileNotFoundError:
                pass  # chktex not available
                
            # Try test compilation
            try:
                result = subprocess.run(
                    ["xelatex", "-interaction=nonstopmode", "-halt-on-error", str(file_path)],
                    cwd=file_path.parent,
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    # Extract error from output
                    error_lines = []
                    for line in result.stdout.split('\n'):
                        if line.startswith('!'):
                            error_lines.append(line)
                    if error_lines:
                        errors.extend(error_lines[:3])  # First 3 errors
                    else:
                        errors.append("Compilation failed (check log file)")
            except FileNotFoundError:
                errors.append("XeLaTeX not found - cannot validate compilation")
                
            if errors:
                return f"❌ Validation failed:\n" + "\n".join(errors) + "\n💡 Next: document(action='edit', path='{file_path}') to fix errors"
            elif warnings:
                return f"✓ Validation passed with warnings:\n" + "\n".join(warnings) + "\n💡 Next steps:\n→ Edit: document(action='edit', path='{file_path}') to fix warnings\n→ Export: output(action='export', source='{file_path}') to generate PDF"
            else:
                return f"✓ Validation passed!\n💡 Next: output(action='export', source='{file_path}') to generate PDF"
        else:
            return f"✓ No validation available for {file_path.suffix} files\n💡 Next: output(action='export', source='{file_path}')"
            
    elif action == "status":
        if not path:
            return "❌ Error: Path required for status action"
            
        file_path = resolve_path(path)
        if not file_path.exists():
            return f"❌ Error: File not found: {file_path}"
            
        # Get file info
        stat = file_path.stat()
        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        size = stat.st_size
        
        return f"📄 File: {file_path}\n🕒 Modified: {modified}\n📏 Size: {size} bytes\n💡 Next steps:\n→ Read: document(action='read', path='{file_path}')\n→ Edit: document(action='edit', path='{file_path}')"
        
    else:
        return f"❌ Error: Unknown document action '{action}'. Available: create, read, edit, convert, validate, status"


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
    - Use 'source' parameter with existing files instead of 'content' to avoid regeneration
    - Default export format is PDF (most faithful to LaTeX)
    - Supported formats: PDF, DOCX, ODT, RTF, HTML, EPUB
    
    Actions:
    - print: Send to physical printer (auto-converts to PDF if needed)
    - export: Save to various formats (PDF, DOCX, ODT, RTF, HTML, EPUB)
    """
    if action == "print":
        if not source and not content:
            return "❌ Error: Either source or content required for print action"
            
        # Use default printer if not specified
        if not printer and SESSION_CONTEXT["default_printer"]:
            printer = SESSION_CONTEXT["default_printer"]
            
        if source:
            file_path = resolve_path(source)
            if not file_path.exists():
                return f"❌ Error: Source file not found: {file_path}"
                
            # Print the file
            try:
                cmd = ["lp", str(file_path)]
                if printer:
                    cmd.extend(["-d", printer])
                subprocess.run(cmd, check=True)
                return f"✓ Sent to printer: {file_path}"
            except subprocess.CalledProcessError as e:
                return f"❌ Error printing: {e}"
        else:
            # Print content directly
            try:
                process = subprocess.Popen(["lp"] + (["-d", printer] if printer else []), stdin=subprocess.PIPE)
                process.communicate(content.encode())
                return "✓ Content sent to printer"
            except Exception as e:
                return f"❌ Error printing: {e}"
                
    elif action == "export":
        if not source:
            return "❌ Error: Source required for export action"
            
        source_path = resolve_path(source)
        if not source_path.exists():
            return f"❌ Error: Source file not found: {source_path}"
            
        # Determine output path and format
        if output_path:
            out_path = resolve_path(output_path)
            output_format = out_path.suffix.lower()
        else:
            out_path = source_path.with_suffix(".pdf")
            output_format = ".pdf"
            
        # Supported output formats
        supported_formats = {
            ".pdf": "PDF document",
            ".docx": "Word document", 
            ".odt": "OpenDocument text",
            ".rtf": "Rich Text Format",
            ".html": "HTML webpage",
            ".epub": "EPUB ebook"
        }
        
        if output_format not in supported_formats:
            return f"❌ Error: Unsupported output format '{output_format}'. Supported: {', '.join(supported_formats.keys())}"
            
        # Convert based on source type and output format
        try:
            if output_format == ".pdf":
                # Special handling for PDF generation
                if source_path.suffix == ".md":
                    # Markdown to PDF via pandoc with XeLaTeX
                    subprocess.run(["pandoc", source_path, "-o", out_path, "--pdf-engine=xelatex"], check=True)
                elif source_path.suffix == ".tex":
                    # LaTeX to PDF via xelatex directly
                    result = subprocess.run(["xelatex", "-interaction=nonstopmode", source_path.name], 
                                          cwd=source_path.parent, check=True)
                    # The PDF is created in the same directory as the .tex file
                    actual_pdf_path = source_path.with_suffix(".pdf")
                    # Move to desired location if different
                    if output_path and out_path != actual_pdf_path:
                        out_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(actual_pdf_path), str(out_path))
                else:
                    # Other formats to PDF via pandoc
                    subprocess.run(["pandoc", source_path, "-o", out_path], check=True)
            else:
                # All other conversions via pandoc
                if source_path.suffix in [".md", ".tex", ".rst", ".org", ".txt"]:
                    subprocess.run(["pandoc", source_path, "-o", out_path], check=True)
                else:
                    return f"❌ Error: Cannot convert {source_path.suffix} to {output_format}"
                    
            # Success message with appropriate next action
            if output_format == ".pdf":
                return f"✓ {supported_formats[output_format]} created: {out_path}\n💡 Next: output(action='print', source='{out_path}')"
            else:
                # For non-PDF formats, suggest converting to PDF for printing
                return f"✓ {supported_formats[output_format]} created: {out_path}\n💡 Next steps:\n→ To print: output(action='export', source='{out_path}', output_path='{out_path.with_suffix('.pdf')}')\n→ To view/share: Open {out_path} in appropriate application"
                
        except subprocess.CalledProcessError as e:
            return f"❌ Error creating {supported_formats[output_format]}: {e}"
            
    else:
        return f"❌ Error: Unknown output action '{action}'. Available: print, export"


@mcp.tool()
def project(
    action: str,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> str:
    """Organize documents into projects with intelligent structure.
    
    Actions:
    - create: Create new project with AI-guided structure
    - switch: Change active project
    - list: Show all projects (including importable directories)
    - info: Get current project details
    - import: Import an existing directory as a TeXFlow project
    """
    base_dir = Path.home() / "Documents" / "TeXFlow"
    
    if action == "create":
        if not name:
            return "❌ Error: Name required for create action"
            
        project_dir = base_dir / name
        if project_dir.exists():
            return f"❌ Error: Project '{name}' already exists"
            
        try:
            # Create project structure
            (project_dir / "content").mkdir(parents=True)
            (project_dir / "output" / "pdf").mkdir(parents=True)
            (project_dir / "assets").mkdir(parents=True)
            
            # Create project info
            info = {
                "name": name,
                "description": description or "",
                "created": datetime.now().isoformat(),
                "structure": {
                    "content": "Source documents (Markdown, LaTeX)",
                    "output/pdf": "Generated PDFs",
                    "assets": "Images, data, references"
                }
            }
            
            (project_dir / ".texflow_project.json").write_text(json.dumps(info, indent=2))
            SESSION_CONTEXT["current_project"] = str(project_dir.relative_to(base_dir))
            
            return f"✓ Project created: {project_dir}\n💡 Structure:\n  - content/ (for source files)\n  - output/pdf/ (for PDFs)\n  - assets/ (for images/data)\n💡 Next: document(action='create', content='...', path='content/intro.md')"
        except Exception as e:
            return f"❌ Error creating project: {e}"
            
    elif action == "switch":
        if not name:
            return "❌ Error: Name required for switch action"
            
        # Handle both simple names and paths
        if '/' in name:
            # Full path provided
            project_dir = base_dir / name
        else:
            # Simple name - try to find it
            project_dir = base_dir / name
            
        # Check if it's a valid project (has .texflow_project.json)
        if not project_dir.exists() or not (project_dir / ".texflow_project.json").exists():
            # Try to find the project in nested directories
            found_projects = []
            for p in base_dir.rglob(".texflow_project.json"):
                project_path = p.parent
                project_rel_path = project_path.relative_to(base_dir)
                if project_path.name == name or str(project_rel_path) == name:
                    found_projects.append(str(project_rel_path))
            
            if len(found_projects) == 1:
                # Found exactly one match
                name = found_projects[0]
                project_dir = base_dir / name
            elif len(found_projects) > 1:
                return f"❌ Error: Multiple projects found with name '{name}':\n" + \
                       "\n".join(f"  - {p}" for p in found_projects) + \
                       "\n💡 Use the full path to specify which one"
            else:
                return f"❌ Error: Project '{name}' not found"
        
        # Store the full relative path from TeXFlow root
        SESSION_CONTEXT["current_project"] = str(project_dir.relative_to(base_dir))
        return f"✓ Switched to project: {SESSION_CONTEXT['current_project']}"
        
    elif action == "list":
        if not base_dir.exists():
            return "No projects or directories found"
            
        # Separate projects and importable directories
        projects = []
        importable_dirs = []
        
        # Check all subdirectories including nested ones
        for p in base_dir.rglob("*"):
            if p.is_dir():
                # Skip hidden directories and __pycache__
                if any(part.startswith('.') or part == '__pycache__' for part in p.relative_to(base_dir).parts):
                    continue
                    
                # Check if it's a proper project
                if (p / ".texflow_project.json").exists():
                    projects.append(p.relative_to(base_dir))
                else:
                    # Check if it has any content files that could be imported
                    has_content = any(p.glob("*.md")) or any(p.glob("*.tex")) or any(p.glob("*.txt"))
                    if has_content:
                        importable_dirs.append(p.relative_to(base_dir))
        
        if not projects and not importable_dirs:
            return "No projects or directories found"
            
        current = SESSION_CONTEXT.get("current_project")
        result = ""
        
        # List active projects
        if projects:
            result += "Projects:\n"
            for p in sorted(projects, key=str):
                marker = " (current)" if str(p) == current else ""
                result += f"  - {p}{marker}\n"
        
        # List importable directories
        if importable_dirs:
            if projects:
                result += "\nDirectories available for import:\n"
            else:
                result += "Directories available for import:\n"
            for d in sorted(importable_dirs, key=str):
                result += f"  - {d} (use: project(action='import', name='{d}'))\n"
                
        return result
    
    elif action == "info":
        current = SESSION_CONTEXT.get("current_project")
        if not current:
            return "No project currently active. Use project(action='switch') or project(action='import') to activate one."
            
        # Current is now a full path relative to base_dir
        project_dir = base_dir / current
        if not project_dir.exists():
            SESSION_CONTEXT["current_project"] = None
            return f"❌ Error: Current project '{current}' directory not found"
            
        try:
            info_file = project_dir / ".texflow_project.json"
            if info_file.exists():
                info = json.loads(info_file.read_text())
                result = f"Project: {info['name']}\n"
                if info.get('description'):
                    result += f"Description: {info['description']}\n"
                result += f"Created: {info.get('created', 'Unknown')}\n"
                result += f"Path: {project_dir}\n"
                result += "Structure:\n"
                for folder, desc in info.get('structure', {}).items():
                    result += f"  - {folder}: {desc}\n"
                return result
            else:
                return f"Project: {current}\nPath: {project_dir}\n⚠️  No project metadata found"
        except Exception as e:
            return f"❌ Error reading project info: {e}"
    
    elif action == "close":
        current = SESSION_CONTEXT.get("current_project")
        if not current:
            return "No project is currently active"
        
        # Extract just the project name for display
        project_name = Path(current).name
        SESSION_CONTEXT["current_project"] = None
        return f"✓ Closed project '{project_name}'. File operations will now use default paths."
        
    elif action == "import":
        if not name:
            return "❌ Error: Name required for import action"
        
        # Handle nested paths by converting to Path object
        import_path = Path(name)
        if import_path.is_absolute():
            project_dir = import_path
            name = project_dir.name
        else:
            project_dir = base_dir / name
            
        if not project_dir.exists():
            return f"❌ Error: Directory '{name}' not found"
            
        # Check if already a project
        if (project_dir / ".texflow_project.json").exists():
            return f"❌ Error: '{name}' is already a TeXFlow project. Use project(action='switch', name='{name}') instead."
            
        try:
            # Create standard project directories if they don't exist
            content_dir = project_dir / "content"
            output_dir = project_dir / "output" / "pdf"
            assets_dir = project_dir / "assets"
            
            # Create directories only if they don't exist
            content_dir.mkdir(exist_ok=True)
            output_dir.mkdir(parents=True, exist_ok=True)
            assets_dir.mkdir(exist_ok=True)
            
            # Move existing files to appropriate directories
            moved_files = []
            for file in project_dir.iterdir():
                if file.is_file() and file.suffix in ['.md', '.tex', '.txt']:
                    # Only move if not already in content directory
                    if file.parent == project_dir:
                        new_path = content_dir / file.name
                        if not new_path.exists():
                            file.rename(new_path)
                            moved_files.append(file.name)
            
            # Create project info
            info = {
                "name": project_dir.name,
                "description": description or f"Imported from existing directory",
                "created": datetime.now().isoformat(),
                "imported": True,
                "structure": {
                    "content": "Source documents (Markdown, LaTeX)",
                    "output/pdf": "Generated PDFs",
                    "assets": "Images, data, references"
                }
            }
            
            (project_dir / ".texflow_project.json").write_text(json.dumps(info, indent=2))
            SESSION_CONTEXT["current_project"] = str(project_dir.relative_to(base_dir))
            
            result = f"✓ Project imported: {project_dir.name}\n"
            if moved_files:
                result += f"📁 Moved {len(moved_files)} files to content/:\n"
                for f in moved_files[:5]:  # Show first 5 files
                    result += f"  - {f}\n"
                if len(moved_files) > 5:
                    result += f"  ... and {len(moved_files) - 5} more\n"
            result += "💡 Project structure organized and ready to use"
            return result
            
        except Exception as e:
            return f"❌ Error importing project: {e}"
        
    else:
        return f"❌ Error: Unknown project action '{action}'. Available: create, switch, list, info, close, import"


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
    if action == "list":
        try:
            result = subprocess.run(["lpstat", "-p", "-d"], capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"❌ Error listing printers: {e.stderr}"
            
    elif action == "set_default":
        if not name:
            return "❌ Error: Printer name required for set_default action"
        try:
            subprocess.run(["lpoptions", "-d", name], check=True)
            SESSION_CONTEXT["default_printer"] = name
            return f"✓ Default printer set to: {name}"
        except subprocess.CalledProcessError as e:
            return f"❌ Error setting default printer: {e}"
            
    else:
        return f"❌ Error: Unknown printer action '{action}'. Available: list, set_default"


@mcp.tool()
def discover(
    action: str,
    folder: Optional[str] = None,
    style: Optional[str] = None
) -> str:
    """Find documents, fonts, and system capabilities.
    
    Actions:
    - documents: List documents in project or folder
    - recent: Show recently modified documents across all projects
    - fonts: Browse available fonts for LaTeX
    - capabilities: Check system dependencies
    - packages: Discover installed LaTeX packages (Linux only)
    """
    if action == "documents":
        # List documents
        if SESSION_CONTEXT.get("current_project"):
            base_path = TEXFLOW_ROOT / SESSION_CONTEXT["current_project"] / "content"
        else:
            base_path = SESSION_CONTEXT["workspace_root"]
            
        if folder:
            base_path = base_path / folder
            
        if not base_path.exists():
            return f"❌ Error: Directory {base_path} does not exist"
            
        files = []
        for ext in ["*.pdf", "*.md", "*.tex"]:
            files.extend(base_path.glob(ext))
            
        if not files:
            return f"No documents found in {base_path}"
            
        result = f"Documents in {base_path}:\n"
        for f in sorted(files):
            result += f"  - {f.name}\n"
        return result
        
    elif action == "fonts":
        # List available system fonts using fc-list
        try:
            # Get all fonts with family names
            result = subprocess.run(["fc-list", ":", "family"], 
                                  capture_output=True, text=True, check=True)
            
            # Parse and deduplicate font families
            font_families = set()
            for line in result.stdout.strip().split('\n'):
                if line:
                    # fc-list returns fonts with variants, extract base family
                    family = line.split(',')[0].strip()
                    if family:
                        font_families.add(family)
            
            # Sort fonts alphabetically
            sorted_fonts = sorted(font_families)
            
            # Filter by style if requested
            if style:
                style_lower = style.lower()
                if style_lower == "serif":
                    sorted_fonts = [f for f in sorted_fonts if any(s in f.lower() for s in ["serif", "times", "georgia", "book"])]
                elif style_lower == "sans":
                    sorted_fonts = [f for f in sorted_fonts if any(s in f.lower() for s in ["sans", "arial", "helvetica", "calibri"])]
                elif style_lower == "mono":
                    sorted_fonts = [f for f in sorted_fonts if any(s in f.lower() for s in ["mono", "courier", "consolas", "code"])]
                elif style_lower == "display":
                    sorted_fonts = [f for f in sorted_fonts if any(s in f.lower() for s in ["display", "headline", "title"])]
            
            if not sorted_fonts:
                return f"No fonts found{f' matching style {style}' if style else ''}"
                
            result = f"📝 Available{f' {style}' if style else ''} fonts ({len(sorted_fonts)} found):\n"
            for font in sorted_fonts[:50]:  # Limit to first 50 to avoid overwhelming output
                result += f"  - {font}\n"
                
            if len(sorted_fonts) > 50:
                result += f"\n... and {len(sorted_fonts) - 50} more fonts"
                
            result += "\n💡 Use in LaTeX with: \\setmainfont{FontName}"
            result += "\n💡 Filter by style: discover(action='fonts', style='serif|sans|mono|display')"
            
            return result
            
        except subprocess.CalledProcessError:
            return "❌ Error: fc-list command not found. Install fontconfig package."
        except Exception as e:
            return f"❌ Error listing fonts: {e}"
            
    elif action == "recent":
        # List recently modified documents across all projects
        recent_files = []
        
        # Traverse all projects
        for project_dir in TEXFLOW_ROOT.iterdir():
            if project_dir.is_dir() and (project_dir / ".texflow_project.json").exists():
                # Look in content directory
                content_dir = project_dir / "content"
                if content_dir.exists():
                    for ext in ["*.md", "*.tex", "*.pdf"]:
                        for file in content_dir.glob(ext):
                            if file.is_file():
                                stat = file.stat()
                                recent_files.append({
                                    "path": file,
                                    "project": project_dir.name,
                                    "mtime": stat.st_mtime,
                                    "size": stat.st_size
                                })
                
                # Also check project root for documents
                for ext in ["*.md", "*.tex", "*.pdf"]:
                    for file in project_dir.glob(ext):
                        if file.is_file():
                            stat = file.stat()
                            recent_files.append({
                                "path": file,
                                "project": project_dir.name,
                                "mtime": stat.st_mtime,
                                "size": stat.st_size
                            })
        
        # Sort by modification time (most recent first)
        recent_files.sort(key=lambda x: x["mtime"], reverse=True)
        
        # Limit to top 20 most recent
        recent_files = recent_files[:20]
        
        if not recent_files:
            return "No recent documents found across projects"
        
        # Format output
        result = "📝 Recent Documents (across all projects):\n\n"
        current_date = datetime.now()
        
        for file_info in recent_files:
            # Calculate relative time
            mtime = datetime.fromtimestamp(file_info["mtime"])
            delta = current_date - mtime
            
            if delta.days == 0:
                if delta.seconds < 3600:
                    time_str = f"{delta.seconds // 60} minutes ago"
                else:
                    time_str = f"{delta.seconds // 3600} hours ago"
            elif delta.days == 1:
                time_str = "yesterday"
            elif delta.days < 7:
                time_str = f"{delta.days} days ago"
            else:
                time_str = mtime.strftime("%Y-%m-%d")
            
            # Format file size
            size = file_info["size"]
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            
            # Relative path from content directory
            rel_path = file_info["path"].relative_to(TEXFLOW_ROOT / file_info["project"])
            
            result += f"  📄 {file_info['path'].name}\n"
            result += f"     Project: {file_info['project']}\n"
            result += f"     Path: {rel_path}\n"
            result += f"     Modified: {time_str} ({size_str})\n\n"
        
        return result
        
    elif action == "packages":
        # Discover installed LaTeX packages
        try:
            from src.core.system_checker import SystemDependencyChecker
            checker = SystemDependencyChecker()
            packages_info = checker.get_discovered_packages()
            
            # Check if it's an error response
            if isinstance(packages_info, dict) and packages_info.get("available") is False:
                return f"❌ Package discovery not available: {packages_info.get('message', 'Unknown error')}"
            
            # Check if we have valid package data
            if not isinstance(packages_info, dict) or "total_packages" not in packages_info:
                return "❌ Unexpected package discovery format"
            
            # Format output
            result = f"📦 Discovered LaTeX Packages ({packages_info['total_packages']} total)\n"
            result += f"Distribution: {packages_info['distribution']['name']} {packages_info['distribution']['version']}\n"
            result += f"Package Manager: {packages_info['package_manager']}\n\n"
            
            # Show categories summary
            result += "Categories:\n"
            for cat_name, cat_info in sorted(packages_info['categories'].items()):
                result += f"  📁 {cat_name}: {cat_info['count']} packages\n"
            
            result += "\n⚠️  Caveats:\n"
            for warning in packages_info.get('warnings', []):
                result += f"  - {warning}\n"
            
            result += "\n💡 Use 'tlmgr list --only-installed' for additional TeX Live packages"
            result += "\n💡 Package availability depends on your TeX distribution installation"
            
            return result
            
        except Exception as e:
            return f"❌ Error discovering packages: {e}"
    
    elif action == "capabilities":
        caps = ["✓ CUPS printing system"]
        
        # Check for pandoc
        try:
            subprocess.run(["pandoc", "--version"], capture_output=True, check=True)
            caps.append("✓ Pandoc (Markdown conversion)")
        except:
            caps.append("✗ Pandoc not found")
            
        # Check for XeLaTeX
        try:
            subprocess.run(["xelatex", "--version"], capture_output=True, check=True)
            caps.append("✓ XeLaTeX (LaTeX compilation)")
        except:
            caps.append("✗ XeLaTeX not found")
            
        # Check for fontconfig (fc-list)
        try:
            subprocess.run(["fc-list", "--version"], capture_output=True, check=True)
            caps.append("✓ Fontconfig (Font discovery)")
        except:
            caps.append("✗ Fontconfig not found")
            
        # Check for PDF rendering dependencies
        try:
            import pdf2image
            from PIL import Image
            caps.append("✓ PDF rendering (pdf2image + Pillow)")
        except ImportError:
            caps.append("✗ PDF rendering not available (missing pdf2image or Pillow)")
            
        return "System Capabilities:\n" + "\n".join(caps)
        
    else:
        return f"❌ Error: Unknown discover action '{action}'. Available: documents, fonts, capabilities, recent"


@mcp.tool()
def archive(
    action: str,
    path: Optional[str] = None,
    pattern: Optional[str] = None
) -> str:
    """Manage document versions and history with soft delete functionality.
    
    Actions:
    - archive: Soft delete a document (preserves in hidden folder)
    - cleanup: Archive multiple files matching a pattern
    - versions: Find all versions of a document
    """
    if action == "archive":
        if not path:
            return "❌ Error: Path required for archive action"
            
        file_path = resolve_path(path)
        if not file_path.exists():
            return f"❌ Error: File not found: {file_path}"
            
        # Create archive directory
        archive_dir = file_path.parent / ".texflow_archive"
        archive_dir.mkdir(exist_ok=True)
        
        # Move to archive with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = archive_dir / f"{timestamp}_{file_path.name}"
        
        try:
            file_path.rename(archive_path)
            return f"✓ Archived: {file_path.name} → .texflow_archive/\n💡 Restore with: archive(action='restore', path='{archive_path}')"
        except Exception as e:
            return f"❌ Error archiving: {e}"
            
    elif action == "cleanup":
        if not pattern:
            pattern = "*_old*"
            
        # Find files matching pattern
        base_path = Path.cwd()
        if SESSION_CONTEXT.get("current_project"):
            # current_project now contains the full relative path from TeXFlow root
            base_path = Path.home() / "Documents" / "TeXFlow" / SESSION_CONTEXT["current_project"] / "content"
            
        files = list(base_path.glob(pattern))
        if not files:
            return f"No files found matching pattern: {pattern}"
            
        archived = []
        for f in files:
            if f.is_file():
                archive_dir = f.parent / ".texflow_archive"
                archive_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_path = archive_dir / f"{timestamp}_{f.name}"
                f.rename(archive_path)
                archived.append(f.name)
                
        return f"✓ Archived {len(archived)} files: {', '.join(archived)}"
        
    else:
        return f"❌ Error: Unknown archive action '{action}'. Available: archive, cleanup, versions"


@mcp.tool()
def workflow(
    action: str,
    task: Optional[str] = None
) -> str:
    """Get intelligent guidance and workflow automation.
    
    Actions:
    - suggest: Get workflow recommendations for a task
    - next_steps: See contextual next actions
    """
    if action == "suggest":
        if not task:
            return "❌ Error: Task description required"
            
        # Get available templates
        available_templates = []
        if TEMPLATES_DIR.exists():
            for cat_dir in TEMPLATES_DIR.iterdir():
                if cat_dir.is_dir() and not cat_dir.name.startswith('.'):
                    for template in cat_dir.iterdir():
                        if template.is_dir():
                            available_templates.append(f"{cat_dir.name}/{template.name}")
        
        # Build workflow suggestion
        workflow = f"💡 Workflow for '{task}':\n\n"
        
        # Step 1: Create project
        workflow += f"1. Create project:\n   project(action='create', name='my-{task.lower().replace(' ', '-')}', description='{task}')\n\n"
        
        # Step 2: Suggest template if available
        if available_templates:
            workflow += "2. Start from template:\n"
            workflow += "   templates(action='list')  # See available templates\n"
            if "default/minimal" in available_templates:
                workflow += "   templates(action='use', category='default', name='minimal')  # Use default template\n"
            workflow += "\n"
            next_step = 3
        else:
            workflow += "2. Create your first document:\n"
            workflow += "   document(action='create', content='# Title', path='content/document.md')\n\n"
            next_step = 3
            
        # Remaining steps
        workflow += f"{next_step}. Edit and develop:\n"
        workflow += "   document(action='edit', path='...')  # Make changes\n"
        workflow += "   document(action='validate', path='...')  # Check LaTeX syntax\n\n"
        
        workflow += f"{next_step + 1}. Generate output:\n"
        workflow += "   output(action='export', source='...', output_path='output/document.pdf')\n"
        workflow += "   output(action='export', source='...', output_path='output/document.docx')  # For collaboration\n\n"
        
        workflow += f"{next_step + 2}. Print if needed:\n"
        workflow += "   output(action='print', source='output/document.pdf')"
        
        return workflow
            
    elif action == "next_steps":
        current_project = SESSION_CONTEXT.get("current_project")
        if current_project:
            return f"""💡 Next steps in project '{current_project}':
→ Use template: templates(action='use', category='default', name='minimal')
→ Create document: document(action='create', content='...', path='content/...')
→ List documents: discover(action='documents')
→ Export to PDF: output(action='export', source='...')"""
        else:
            return """💡 Getting started:
→ Create project: project(action='create', name='...', description='...')
→ Browse templates: templates(action='list')
→ Check system: discover(action='capabilities')
→ List printers: printer(action='list')"""
            
    else:
        return f"❌ Error: Unknown workflow action '{action}'. Available: suggest, next_steps"


@mcp.tool()
def templates(
    action: str,
    category: Optional[str] = None,
    name: Optional[str] = None,
    source: Optional[str] = None,
    target: Optional[str] = None,
    content: Optional[str] = None
) -> str:
    """Manage LaTeX document templates for quick project starts.
    
    Templates are pure content collections (no project metadata) organized by 
    category in ~/Documents/TeXFlow/templates/. To create or edit templates, 
    work on them as regular projects first, then activate them as templates.
    
    Actions:
    - list: Show available templates (optionally filtered by category)
    - use: Copy a template to current project or specified location
    - activate: Convert current project into a template (moves to templates dir)
    - create: Create a new template from content or existing document
    - rename: Rename a template
    - delete: Remove a template
    - info: Get details about a specific template
    """
    # Ensure templates directory exists
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    
    if action == "list":
        templates_found = []
        
        if category:
            # List templates in specific category
            cat_path = TEMPLATES_DIR / category
            if cat_path.exists():
                for template in cat_path.iterdir():
                    if template.is_dir():
                        templates_found.append(f"{category}/{template.name}")
            else:
                return f"❌ Error: Category '{category}' not found"
        else:
            # List all templates by category
            for cat_dir in TEMPLATES_DIR.iterdir():
                if cat_dir.is_dir() and not cat_dir.name.startswith('.'):
                    for template in cat_dir.iterdir():
                        if template.is_dir():
                            templates_found.append(f"{cat_dir.name}/{template.name}")
        
        if not templates_found:
            return """📄 No templates found.
💡 Get started:
→ Clone template repository: git clone https://github.com/[user]/texflow-templates ~/Documents/TeXFlow/templates
→ Create your own: templates(action='create', category='research', name='my-style', source='path/to/document.tex')"""
        
        result = "📄 Available templates:\n"
        for template in sorted(templates_found):
            result += f"  - {template}\n"
        result += "\n💡 Next: templates(action='use', category='...', name='...')"
        return result
        
    elif action == "use":
        if not category or not name:
            return "❌ Error: Both category and name required for use action"
            
        template_path = TEMPLATES_DIR / category / name
        if not template_path.exists():
            return f"❌ Error: Template '{category}/{name}' not found"
            
        # Determine target location
        if target:
            dest_path = resolve_path(target, use_project=False)
        elif SESSION_CONTEXT["current_project"]:
            # Copy to current project's content directory
            # current_project now contains the full relative path from TeXFlow root
            project_root = TEXFLOW_ROOT / SESSION_CONTEXT["current_project"]
            dest_path = project_root / "content" / f"{name}-from-template"
        else:
            # Copy to current directory
            dest_path = Path.cwd() / f"{name}-from-template"
            
        # Copy template
        try:
            if dest_path.exists():
                return f"❌ Error: Destination already exists: {dest_path}"
            shutil.copytree(template_path, dest_path)
            
            # Find main .tex file in copied template
            tex_files = list(dest_path.glob("*.tex"))
            main_tex = tex_files[0] if tex_files else None
            
            return f"""✓ Template copied to: {dest_path}
💡 Next steps:
→ Edit: document(action='edit', path='{main_tex if main_tex else dest_path}')
→ Customize and start working on your document"""
        except Exception as e:
            return f"❌ Error copying template: {e}"
    
    elif action == "activate":
        if not category or not name:
            return "❌ Error: Both category and name required for activate action"
        
        # Get current project or use source parameter
        if source:
            project_name = source
        elif SESSION_CONTEXT.get("current_project"):
            project_name = SESSION_CONTEXT["current_project"]
        else:
            return "❌ Error: No current project. Use source parameter or switch to a project first"
        
        # Handle both simple names and full paths
        if '/' in project_name:
            # Assume it's a full path relative to TeXFlow root
            project_dir = Path.home() / "Documents" / "TeXFlow" / project_name
        else:
            # Try to find project by name
            base_dir = Path.home() / "Documents" / "TeXFlow"
            found_projects = []
            for p in base_dir.rglob(".texflow_project.json"):
                if p.parent.name == project_name:
                    found_projects.append(p.parent)
            
            if len(found_projects) == 1:
                project_dir = found_projects[0]
                project_name = str(project_dir.relative_to(base_dir))
            elif len(found_projects) > 1:
                return f"❌ Error: Multiple projects found with name '{project_name}'. Use source parameter with full path."
            else:
                # Try direct path
                project_dir = base_dir / project_name
        
        if not project_dir.exists() or not (project_dir / ".texflow_project.json").exists():
            return f"❌ Error: Project '{project_name}' not found"
        
        template_path = TEMPLATES_DIR / category / name
        if template_path.exists():
            return f"❌ Error: Template '{category}/{name}' already exists"
        
        try:
            # Create category directory if needed
            template_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy content files only (not project metadata)
            for item in project_dir.iterdir():
                if item.name == ".texflow_project.json":
                    continue  # Skip project metadata
                elif item.name in ['.git', '__pycache__', '.DS_Store', '.texflow_archive']:
                    continue  # Skip system/hidden directories
                elif item.is_dir() and item.name == "output":
                    continue  # Skip output directory
                elif item.is_dir() and item.name == "content":
                    # Copy contents of content directory directly
                    for content_item in item.iterdir():
                        if content_item.is_file():
                            shutil.copy2(content_item, template_path / content_item.name)
                        else:
                            shutil.copytree(content_item, template_path / content_item.name)
                elif item.is_file():
                    shutil.copy2(item, template_path / item.name)
                elif item.is_dir() and item.name == "assets":
                    # Include assets directory
                    shutil.copytree(item, template_path / item.name)
            
            # Remove the original project
            shutil.rmtree(project_dir)
            
            # Clear from session if it was the current project
            if SESSION_CONTEXT.get("current_project") == project_name:
                SESSION_CONTEXT["current_project"] = None
            
            return f"""✓ Project '{project_name}' activated as template: {category}/{name}
📁 Template created with content from project
🗑️  Original project removed
💡 Next: templates(action='use', category='{category}', name='{name}') to use this template"""
            
        except Exception as e:
            return f"❌ Error activating template: {e}"
            
    elif action == "create":
        if not category or not name:
            return "❌ Error: Both category and name required for create action"
            
        template_path = TEMPLATES_DIR / category / name
        if template_path.exists():
            return f"❌ Error: Template '{category}/{name}' already exists"
            
        try:
            # Create template directory
            template_path.mkdir(parents=True, exist_ok=True)
            
            if source:
                # Copy from existing document/project
                source_path = resolve_path(source)
                if source_path.is_file():
                    # Single file - copy it
                    shutil.copy2(source_path, template_path / source_path.name)
                elif source_path.is_dir():
                    # Directory - copy contents
                    for item in source_path.iterdir():
                        if item.name not in ['.git', '__pycache__', '.DS_Store']:
                            if item.is_file():
                                shutil.copy2(item, template_path / item.name)
                            else:
                                shutil.copytree(item, template_path / item.name)
                else:
                    return f"❌ Error: Source not found: {source_path}"
            elif content:
                # Create from provided content
                main_tex = template_path / "main.tex"
                main_tex.write_text(content)
            else:
                # Create minimal template
                main_tex = template_path / "main.tex"
                main_tex.write_text(r"""\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage{geometry}
\geometry{margin=1in}

\title{Title}
\author{Author}
\date{\today}

\begin{document}
\maketitle

\section{Introduction}
Start your document here.

\end{document}""")
            
            return f"""✓ Template created: {category}/{name}
💡 Next steps:
→ Use template: templates(action='use', category='{category}', name='{name}')
→ To edit: Create a project from it, modify, then activate again"""
        except Exception as e:
            return f"❌ Error creating template: {e}"
            
    elif action == "rename":
        if not category or not name or not target:
            return "❌ Error: Category, name, and target required for rename action"
            
        source_path = TEMPLATES_DIR / category / name
        if not source_path.exists():
            return f"❌ Error: Template '{category}/{name}' not found"
            
        # Parse target
        if '/' in target:
            target_cat, target_name = target.split('/', 1)
        else:
            target_cat, target_name = category, target
            
        target_path = TEMPLATES_DIR / target_cat / target_name
        
        try:
            if target_path.exists():
                return f"❌ Error: Target already exists: {target_cat}/{target_name}"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            source_path.rename(target_path)
            return f"✓ Template renamed: {category}/{name} → {target_cat}/{target_name}"
        except Exception as e:
            return f"❌ Error renaming template: {e}"
            
    elif action == "delete":
        if not category or not name:
            return "❌ Error: Both category and name required for delete action"
            
        template_path = TEMPLATES_DIR / category / name
        if not template_path.exists():
            return f"❌ Error: Template '{category}/{name}' not found"
            
        try:
            shutil.rmtree(template_path)
            # Clean up empty category directory
            if not list((TEMPLATES_DIR / category).iterdir()):
                (TEMPLATES_DIR / category).rmdir()
            return f"✓ Template deleted: {category}/{name}"
        except Exception as e:
            return f"❌ Error deleting template: {e}"
            
    elif action == "info":
        if not category or not name:
            return "❌ Error: Both category and name required for info action"
            
        template_path = TEMPLATES_DIR / category / name
        if not template_path.exists():
            return f"❌ Error: Template '{category}/{name}' not found"
            
        # Gather template information
        files = list(template_path.rglob("*"))
        tex_files = [f for f in files if f.suffix == ".tex" and f.is_file()]
        style_files = [f for f in files if f.suffix in [".sty", ".cls"] and f.is_file()]
        bib_files = [f for f in files if f.suffix in [".bib", ".bst"] and f.is_file()]
        
        info = f"""📄 Template: {category}/{name}
📂 Location: {template_path}

Files:
  - TeX files: {len(tex_files)}
  - Style files: {len(style_files)}
  - Bibliography: {len(bib_files)}
  - Total files: {len([f for f in files if f.is_file()])}
  
💡 Next steps:
→ Use: templates(action='use', category='{category}', name='{name}')
→ To modify: Use it in a project, edit, then activate as a new template"""
        
        return info
        
    else:
        return f"❌ Error: Unknown templates action '{action}'. Available: list, use, activate, create, rename, delete, info"


def main():
    """Run the unified MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()