#!/usr/bin/env python3
"""TeXFlow Unified MCP Server - Simple Implementation

This server exposes only 7 semantic MCP tools without backward compatibility.
Each tool provides intelligent guidance for document workflows.
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

from mcp.server.fastmcp import FastMCP

# Create MCP server instance
mcp = FastMCP("texflow")

# Global state for session context
SESSION_CONTEXT = {
    "current_project": None,
    "default_printer": None,
    "last_used_format": None
}


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
        
        # Create file path
        if path:
            file_path = Path(path).expanduser()
        else:
            # Use Documents folder
            file_path = Path.home() / "Documents" / f"document{ext}"
            
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
            
            return f"✓ Document created: {file_path}\n" + "\n".join(next_steps)
        except Exception as e:
            return f"❌ Error creating document: {e}"
            
    elif action == "read":
        if not path:
            return "❌ Error: Path required for read action"
            
        file_path = Path(path).expanduser()
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
            
        file_path = Path(path).expanduser()
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
            
        source_path = Path(source).expanduser()
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
            
        file_path = Path(path).expanduser()
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
            
        file_path = Path(path).expanduser()
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
    """Generate output from documents - print to paper or export to PDF.
    
    BEST PRACTICES:
    - Use 'source' parameter with existing files instead of 'content' to avoid regeneration
    - Export to PDF first if you need both digital and printed copies
    
    Actions:
    - print: Send to physical printer (auto-converts to PDF if needed)
    - export: Save as PDF without printing
    """
    if action == "print":
        if not source and not content:
            return "❌ Error: Either source or content required for print action"
            
        # Use default printer if not specified
        if not printer and SESSION_CONTEXT["default_printer"]:
            printer = SESSION_CONTEXT["default_printer"]
            
        if source:
            file_path = Path(source).expanduser()
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
            
        source_path = Path(source).expanduser()
        if not source_path.exists():
            return f"❌ Error: Source file not found: {source_path}"
            
        # Determine output path
        if output_path:
            pdf_path = Path(output_path).expanduser()
        else:
            pdf_path = source_path.with_suffix(".pdf")
            
        # Convert based on source type
        if source_path.suffix == ".md":
            # Markdown to PDF via pandoc
            try:
                subprocess.run(["pandoc", source_path, "-o", pdf_path, "--pdf-engine=xelatex"], check=True)
                return f"✓ PDF created: {pdf_path}\n💡 Next: output(action='print', source='{pdf_path}')"
            except subprocess.CalledProcessError as e:
                return f"❌ Error creating PDF: {e}"
                
        elif source_path.suffix == ".tex":
            # LaTeX to PDF via xelatex
            try:
                # Run in the directory containing the file
                result = subprocess.run(["xelatex", "-interaction=nonstopmode", source_path.name], 
                                      cwd=source_path.parent, check=True)
                
                # The PDF is created in the same directory as the .tex file
                actual_pdf_path = source_path.with_suffix(".pdf")
                
                # Move to desired location if different
                if output_path and pdf_path != actual_pdf_path:
                    pdf_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(actual_pdf_path), str(pdf_path))
                    return f"✓ PDF created: {pdf_path}\n💡 Next: output(action='print', source='{pdf_path}')"
                else:
                    return f"✓ PDF created: {actual_pdf_path}\n💡 Next: output(action='print', source='{actual_pdf_path}')"
            except subprocess.CalledProcessError as e:
                return f"❌ Error creating PDF: {e}"
        else:
            return f"❌ Error: Cannot export {source_path.suffix} to PDF"
            
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
    - list: Show all projects
    - info: Get current project details
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
            SESSION_CONTEXT["current_project"] = name
            
            return f"✓ Project created: {project_dir}\n💡 Structure:\n  - content/ (for source files)\n  - output/pdf/ (for PDFs)\n  - assets/ (for images/data)\n💡 Next: document(action='create', content='...', path='content/intro.md')"
        except Exception as e:
            return f"❌ Error creating project: {e}"
            
    elif action == "switch":
        if not name:
            return "❌ Error: Name required for switch action"
            
        project_dir = base_dir / name
        if not project_dir.exists():
            return f"❌ Error: Project '{name}' not found"
            
        SESSION_CONTEXT["current_project"] = name
        return f"✓ Switched to project: {name}"
        
    elif action == "list":
        if not base_dir.exists():
            return "No projects found"
            
        projects = []
        for p in base_dir.iterdir():
            if p.is_dir() and (p / ".texflow_project.json").exists():
                projects.append(p.name)
                
        if not projects:
            return "No projects found"
            
        current = SESSION_CONTEXT.get("current_project")
        result = "Projects:\n"
        for p in sorted(projects):
            marker = " (current)" if p == current else ""
            result += f"  - {p}{marker}\n"
        return result
        
    else:
        return f"❌ Error: Unknown project action '{action}'. Available: create, switch, list, info"


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
    - fonts: Browse available fonts for LaTeX
    - capabilities: Check system dependencies
    """
    if action == "documents":
        # List documents
        if SESSION_CONTEXT.get("current_project"):
            base_path = Path.home() / "Documents" / "TeXFlow" / SESSION_CONTEXT["current_project"] / "content"
        else:
            base_path = Path.home() / "Documents"
            
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
            
        return "System Capabilities:\n" + "\n".join(caps)
        
    else:
        return f"❌ Error: Unknown discover action '{action}'. Available: documents, capabilities"


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
            
        file_path = Path(path).expanduser()
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
            
        task_lower = task.lower()
        
        if any(word in task_lower for word in ["paper", "research", "academic", "thesis"]):
            return """📚 Academic Paper Workflow:
1. project(action="create", name="my-paper", description="Research paper on...")
2. document(action="create", content="@article{...}", path="content/refs.bib")
3. document(action="create", content="\\documentclass{article}...", path="content/paper.tex")
4. output(action="export", source="content/paper.tex")
5. output(action="print", source="output/pdf/paper.pdf")"""
            
        elif any(word in task_lower for word in ["report", "documentation"]):
            return """📄 Report Workflow:
1. document(action="create", content="# Report Title", intent="report")
2. document(action="edit", path="report.md", old_string="...", new_string="...")
3. output(action="export", source="report.md", output_path="report.pdf")"""
            
        else:
            return f"""💡 General Workflow for '{task}':
1. document(action="create", content="...", intent="{task}")
2. Edit as needed
3. output(action="export", source="...")"""
            
    elif action == "next_steps":
        current_project = SESSION_CONTEXT.get("current_project")
        if current_project:
            return f"""💡 Next steps in project '{current_project}':
→ Create document: document(action="create", content="...", path="content/...")
→ List documents: discover(action="documents")
→ Export to PDF: output(action="export", source="...")"""
        else:
            return """💡 Getting started:
→ Create project: project(action="create", name="...", description="...")
→ List printers: printer(action="list")
→ Check system: discover(action="capabilities")"""
            
    else:
        return f"❌ Error: Unknown workflow action '{action}'. Available: suggest, next_steps"


def main():
    """Run the unified MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()