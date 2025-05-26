#!/usr/bin/env python3
"""CUPS MCP Server - Print documents via CUPS on Linux."""

import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional

from mcp.server.fastmcp import FastMCP

import cups
import magic


# Check for system dependencies
def check_command(cmd: str) -> bool:
    """Check if a command is available in PATH."""
    return shutil.which(cmd) is not None


# Check for LaTeX fonts
def check_latex_fonts() -> bool:
    """Check if essential LaTeX fonts are available."""
    try:
        # Try to find Latin Modern Roman font (essential for XeLaTeX)
        result = subprocess.run(
            ["kpsewhich", "lmroman10-regular.otf"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except:
        return False


# Dependency checks
DEPENDENCIES = {
    "pandoc": {
        "available": check_command("pandoc"),
        "description": "pandoc (for markdown to PDF conversion)",
        "install_hint": "Install with: apt install pandoc, dnf install pandoc, or pacman -S pandoc"
    },
    "xelatex": {
        "available": check_command("xelatex"),
        "description": "XeLaTeX (for PDF generation from pandoc)",
        "install_hint": "Install with: apt install texlive-xetex, dnf install texlive-xetex, or pacman -S texlive-xetex"
    },
    "latex_fonts": {
        "available": check_latex_fonts(),
        "description": "LaTeX fonts (Latin Modern, etc.)",
        "install_hint": "Install with: apt install texlive-fonts-recommended, dnf install texlive-collection-fontsrecommended, or pacman -S texlive-fontsrecommended"
    }
}

# Initialize FastMCP server  
mcp = FastMCP("cups-mcp")

# Log dependency status at startup
missing_deps = []
for dep, info in DEPENDENCIES.items():
    if not info["available"]:
        missing_deps.append(f"- {info['description']}: {info['install_hint']}")

if missing_deps:
    print(f"Warning: Some optional dependencies are missing:")
    for dep in missing_deps:
        print(dep)
    print("Some features may be unavailable.")


def get_available_printers() -> List[Dict[str, Any]]:
    """Get list of available CUPS printers."""
    conn = cups.Connection()
    printers = conn.getPrinters()
    return [
        {
            "name": name,
            "info": attrs.get("printer-info", ""),
            "location": attrs.get("printer-location", ""),
            "state": attrs.get("printer-state", 0),
            "is_default": conn.getDefault() == name,
        }
        for name, attrs in printers.items()
    ]


@mcp.tool()
def list_printers() -> str:
    """List all available CUPS printers."""
    printers = get_available_printers()
    if not printers:
        return "No printers found."
    
    result = "Available printers:\n"
    for p in printers:
        default = " (default)" if p["is_default"] else ""
        state = "ready" if p["state"] == 3 else "not ready"
        result += f"- {p['name']}{default} - {p['info']} [{state}]\n"
    
    return result


@mcp.tool()
def get_printer_info(printer_name: str) -> str:
    """Get detailed information about a specific printer.
    
    Args:
        printer_name: Name of the printer to get info for
    """
    conn = cups.Connection()
    printers = conn.getPrinters()
    
    if printer_name not in printers:
        return f"Printer '{printer_name}' not found."
    
    attrs = printers[printer_name]
    is_default = conn.getDefault() == printer_name
    
    # Format state information
    state_map = {
        3: "idle/ready",
        4: "printing", 
        5: "stopped"
    }
    state = state_map.get(attrs.get("printer-state", 0), "unknown")
    
    result = f"Printer: {printer_name}\n"
    result += f"{'=' * (len(printer_name) + 9)}\n\n"
    
    result += f"Status: {state}\n"
    result += f"Default printer: {'Yes' if is_default else 'No'}\n"
    result += f"Info: {attrs.get('printer-info', 'N/A')}\n"
    result += f"Location: {attrs.get('printer-location', 'N/A')}\n"
    result += f"Make and Model: {attrs.get('printer-make-and-model', 'N/A')}\n"
    result += f"State Message: {attrs.get('printer-state-message', 'N/A')}\n"
    result += f"State Reasons: {attrs.get('printer-state-reasons', 'N/A')}\n"
    result += f"Shared: {'Yes' if attrs.get('printer-is-shared') else 'No'}\n"
    result += f"Device URI: {attrs.get('device-uri', 'N/A')}\n"
    result += f"Printer URI: {attrs.get('printer-uri-supported', 'N/A')}\n"
    result += f"Type: {attrs.get('printer-type', 'N/A')}\n"
    
    return result


@mcp.tool()
def set_default_printer(printer_name: str) -> str:
    """Set a printer as the default printer.
    
    Args:
        printer_name: Name of the printer to set as default
    """
    try:
        conn = cups.Connection()
        printers = conn.getPrinters()
        
        if printer_name not in printers:
            return f"Printer '{printer_name}' not found."
        
        conn.setDefault(printer_name)
        return f"Successfully set '{printer_name}' as the default printer."
    except Exception as e:
        return f"Failed to set default printer: {str(e)}"


@mcp.tool()
def enable_printer(printer_name: str) -> str:
    """Enable a printer (allow it to accept jobs).
    
    Args:
        printer_name: Name of the printer to enable
    """
    try:
        conn = cups.Connection()
        printers = conn.getPrinters()
        
        if printer_name not in printers:
            return f"Printer '{printer_name}' not found."
        
        conn.enablePrinter(printer_name)
        return f"Successfully enabled printer '{printer_name}'."
    except Exception as e:
        return f"Failed to enable printer: {str(e)}"


@mcp.tool()
def disable_printer(printer_name: str) -> str:
    """Disable a printer (stop accepting new jobs).
    
    Args:
        printer_name: Name of the printer to disable
    """
    try:
        conn = cups.Connection()
        printers = conn.getPrinters()
        
        if printer_name not in printers:
            return f"Printer '{printer_name}' not found."
        
        conn.disablePrinter(printer_name)
        return f"Successfully disabled printer '{printer_name}'."
    except Exception as e:
        return f"Failed to disable printer: {str(e)}"


@mcp.tool()
def update_printer_info(printer_name: str, description: Optional[str] = None, location: Optional[str] = None) -> str:
    """Update printer description and/or location.
    
    Args:
        printer_name: Name of the printer to update
        description: New printer description/info (optional)
        location: New printer location (optional)
    """
    try:
        conn = cups.Connection()
        printers = conn.getPrinters()
        
        if printer_name not in printers:
            return f"Printer '{printer_name}' not found."
        
        result = f"Updated printer '{printer_name}':\n"
        
        if description is not None:
            conn.setPrinterInfo(printer_name, description)
            result += f"  Description: {description}\n"
        
        if location is not None:
            conn.setPrinterLocation(printer_name, location)
            result += f"  Location: {location}\n"
        
        if description is None and location is None:
            return "No updates specified. Provide description and/or location."
        
        return result
    except Exception as e:
        return f"Failed to update printer: {str(e)}"


@mcp.tool()
def print_text(content: str, printer: Optional[str] = None) -> str:
    """Print plain text content.
    
    IMPORTANT printer selection logic for AI agents:
    1. First print: If user doesn't specify, ask "Would you like to print or save as PDF?"
    2. If printing: Check if default printer exists. If not, ask which printer to use.
    3. Remember the chosen printer for the rest of the session.
    4. Only change printer if user explicitly requests a different one.
    
    Args:
        content: Text content to print
        printer: Printer name (optional, uses default if not specified)
    """
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    try:
        # Print using lp command
        cmd = ["lp", "-d", printer, temp_path] if printer else ["lp", temp_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            job_id = result.stdout.strip().split()[-1]
            return f"Print job submitted: {job_id}"
        else:
            return f"Print failed: {result.stderr}"
    finally:
        Path(temp_path).unlink()


# Only register print_markdown if all dependencies are available
if DEPENDENCIES["pandoc"]["available"] and DEPENDENCIES["xelatex"]["available"] and DEPENDENCIES["latex_fonts"]["available"]:
    @mcp.tool()
    def print_markdown(content: str, printer: Optional[str] = None, title: str = "Document") -> str:
        """Print markdown content (rendered to PDF via pandoc and XeLaTeX).
        
        IMPORTANT printer selection logic for AI agents:
        1. First print: If user doesn't specify, ask "Would you like to print or save as PDF?"
        2. If printing: Check if default printer exists. If not, ask which printer to use.
        3. Remember the chosen printer for the rest of the session.
        4. Only change printer if user explicitly requests a different one.
        
        Supports:
        - Standard markdown formatting (headers, bold, italic, lists, tables)
        - Code blocks with syntax highlighting
        - LaTeX math expressions (use $ for inline, $$ for display math)
        - Latin scripts (including extended European characters)
        - Greek and Cyrillic alphabets
        - Basic symbols and punctuation
        
        Limited/No support for:
        - Complex Unicode (emoji, box drawing, etc.)
        - Right-to-left scripts (Arabic, Hebrew)
        - CJK characters (Chinese, Japanese, Korean)
        
        Args:
            content: Markdown content to print
            printer: Printer name (optional, uses default if not specified)
            title: Document title (optional)
        """
        # Create temporary markdown file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            md_path = f.name
        
        # Convert to PDF using pandoc
        pdf_path = md_path.replace('.md', '.pdf')
        
        try:
            # Run pandoc
            pandoc_cmd = [
                "pandoc", md_path,
                "-o", pdf_path,
                "--metadata", f"title={title}",
                "--pdf-engine=xelatex",
                "-V", "geometry:margin=1in",
                "-V", "mainfont=Noto Serif",
                "-V", "sansfont=Noto Sans",
                "-V", "monofont=Noto Sans Mono"
            ]
            result = subprocess.run(pandoc_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return f"Pandoc conversion failed: {result.stderr}"
            
            # Print the PDF
            cmd = ["lp", "-d", printer, pdf_path] if printer else ["lp", pdf_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                job_id = result.stdout.strip().split()[-1]
                return f"Print job submitted: {job_id}"
            else:
                return f"Print failed: {result.stderr}"
        finally:
            Path(md_path).unlink(missing_ok=True)
            Path(pdf_path).unlink(missing_ok=True)
else:
    # Create a placeholder function that explains what's missing
    @mcp.tool()
    def print_markdown(content: str, printer: Optional[str] = None, title: str = "Document") -> str:
        """Print markdown content (UNAVAILABLE - missing dependencies).
        
        This tool requires pandoc, XeLaTeX, and LaTeX fonts to be installed.
        Once installed, it will support standard markdown with good Latin/Greek/Cyrillic
        text rendering, but limited support for complex Unicode, RTL scripts, and CJK.
        
        Args:
            content: Markdown content to print
            printer: Printer name (optional, uses default if not specified)
            title: Document title (optional)
        """
        missing = []
        if not DEPENDENCIES["pandoc"]["available"]:
            missing.append(DEPENDENCIES["pandoc"]["install_hint"])
        if not DEPENDENCIES["xelatex"]["available"]:
            missing.append(DEPENDENCIES["xelatex"]["install_hint"])
        if not DEPENDENCIES["latex_fonts"]["available"]:
            missing.append(DEPENDENCIES["latex_fonts"]["install_hint"])
        
        return f"Markdown printing is not available. Missing dependencies:\n" + "\n".join(missing)


# Register markdown_to_pdf if dependencies are available
if DEPENDENCIES["pandoc"]["available"] and DEPENDENCIES["xelatex"]["available"] and DEPENDENCIES["latex_fonts"]["available"]:
    @mcp.tool()
    def markdown_to_pdf(content: str, output_path: str, title: str = "Document") -> str:
        """Convert markdown content to PDF and save to specified path.
        
        This is useful for generating PDFs without printing them, or for systems
        without a PDF printer configured.
        
        Supports:
        - Standard markdown formatting (headers, lists, tables, code blocks)
        - LaTeX math expressions (use $ for inline, $$ for display math)
        - Latin scripts including European languages
        - Greek and Cyrillic alphabets
        
        Args:
            content: Markdown content to convert
            output_path: Path where PDF should be saved (e.g., /home/user/document.pdf)
            title: Document title (optional)
        """
        # Ensure output path ends with .pdf
        if not output_path.endswith('.pdf'):
            output_path += '.pdf'
        
        # Create temporary markdown file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            md_path = f.name
        
        try:
            # Run pandoc
            pandoc_cmd = [
                "pandoc", md_path,
                "-o", output_path,
                "--metadata", f"title={title}",
                "--pdf-engine=xelatex",
                "-V", "geometry:margin=1in",
                "-V", "mainfont=Noto Serif",
                "-V", "sansfont=Noto Sans",
                "-V", "monofont=Noto Sans Mono"
            ]
            result = subprocess.run(pandoc_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return f"PDF conversion failed: {result.stderr}"
            
            return f"PDF saved successfully to: {output_path}"
        finally:
            Path(md_path).unlink(missing_ok=True)
else:
    @mcp.tool()
    def markdown_to_pdf(content: str, output_path: str, title: str = "Document") -> str:
        """Convert markdown to PDF (UNAVAILABLE - missing dependencies).
        
        This tool requires pandoc, XeLaTeX, and LaTeX fonts to be installed.
        
        Args:
            content: Markdown content to convert
            output_path: Path where PDF should be saved
            title: Document title (optional)
        """
        missing = []
        if not DEPENDENCIES["pandoc"]["available"]:
            missing.append(DEPENDENCIES["pandoc"]["install_hint"])
        if not DEPENDENCIES["xelatex"]["available"]:
            missing.append(DEPENDENCIES["xelatex"]["install_hint"])
        if not DEPENDENCIES["latex_fonts"]["available"]:
            missing.append(DEPENDENCIES["latex_fonts"]["install_hint"])
        
        return f"Markdown to PDF conversion is not available. Missing dependencies:\n" + "\n".join(missing)


@mcp.tool()
def print_file(path: str, printer: Optional[str] = None) -> str:
    """Print a file from the filesystem.
    
    IMPORTANT printer selection logic for AI agents:
    1. First print: If user doesn't specify, ask "Would you like to print or save as PDF?"
    2. If printing: Check if default printer exists. If not, ask which printer to use.
    3. Remember the chosen printer for the rest of the session.
    4. Only change printer if user explicitly requests a different one.
    
    Args:
        path: Path to the file to print
        printer: Printer name (optional, uses default if not specified)
    """
    if not Path(path).exists():
        return f"File not found: {path}"
    
    # Detect file type
    mime = magic.from_file(path, mime=True)
    
    # For now, let CUPS handle it directly
    cmd = ["lp", "-d", printer, path] if printer else ["lp", path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        job_id = result.stdout.strip().split()[-1]
        return f"Print job submitted: {job_id} (type: {mime})"
    else:
        return f"Print failed: {result.stderr}"


# This is needed for FastMCP to find the server
server = mcp