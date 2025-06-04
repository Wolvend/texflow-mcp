#!/usr/bin/env python3
"""CUPS MCP Server - Print documents via CUPS on Linux."""

import os
import subprocess
import tempfile
import shutil
import hashlib
import difflib
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

from mcp.server.fastmcp import FastMCP

import cups
import magic


def detect_distro() -> str:
    """Detect the Linux distribution."""
    # Try to read /etc/os-release first (standard for most modern distros)
    if os.path.exists('/etc/os-release'):
        with open('/etc/os-release', 'r') as f:
            content = f.read().lower()
            if 'arch' in content:
                return 'arch'
            elif 'debian' in content or 'ubuntu' in content:
                return 'debian'
            elif 'fedora' in content or 'rhel' in content or 'centos' in content:
                return 'redhat'
    
    # Fallback checks
    if os.path.exists('/etc/arch-release'):
        return 'arch'
    elif os.path.exists('/etc/debian_version'):
        return 'debian'
    elif os.path.exists('/etc/redhat-release'):
        return 'redhat'
    
    return 'unknown'


def check_arch_package(package: str) -> bool:
    """Check if a package is installed on Arch Linux using pacman."""
    try:
        result = subprocess.run(
            ["pacman", "-Qi", package],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        return result.returncode == 0
    except:
        return False


def check_debian_package(package: str) -> bool:
    """Check if a package is installed on Debian/Ubuntu using dpkg."""
    try:
        result = subprocess.run(
            ["dpkg", "-l", package],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        if result.returncode == 0:
            # Check if package is actually installed (ii status)
            for line in result.stdout.split('\n'):
                if line.startswith('ii') and package in line:
                    return True
        return False
    except:
        return False


def check_redhat_package(package: str) -> bool:
    """Check if a package is installed on Fedora/RHEL using rpm."""
    try:
        result = subprocess.run(
            ["rpm", "-q", package],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        return result.returncode == 0
    except:
        return False


def check_package_installed(packages: dict) -> bool:
    """Check if a package is installed based on the distribution.
    
    Args:
        packages: Dict mapping distro names to package names
    Returns:
        True if package is installed, False otherwise
    """
    distro = detect_distro()
    
    if distro == 'arch' and 'arch' in packages:
        return check_arch_package(packages['arch'])
    elif distro == 'debian' and 'debian' in packages:
        return check_debian_package(packages['debian'])
    elif distro == 'redhat' and 'redhat' in packages:
        return check_redhat_package(packages['redhat'])
    
    # Fallback to command check if distro detection fails
    return False


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


# Detect distribution for better dependency checking
DISTRO = detect_distro()

# Package mappings for different distributions
PACKAGE_MAPPINGS = {
    "pandoc": {
        "arch": "pandoc-cli",  # On Arch, pandoc-cli provides pandoc
        "debian": "pandoc",
        "redhat": "pandoc"
    },
    "xelatex": {
        "arch": "texlive-bin",  # XeLaTeX is in texlive-bin on Arch
        "debian": "texlive-xetex",
        "redhat": "texlive-xetex"
    },
    "latex_fonts": {
        "arch": "texlive-fontsrecommended",
        "debian": "texlive-fonts-recommended",
        "redhat": "texlive-collection-fontsrecommended"
    },
    "weasyprint": {
        "arch": "python-weasyprint",
        "debian": "weasyprint",
        "redhat": "weasyprint"
    },
    "rsvg": {
        "arch": "librsvg",
        "debian": "librsvg2-bin",
        "redhat": "librsvg2-tools"
    },
    "tikz": {
        "arch": "texlive-pictures",
        "debian": "texlive-pictures",
        "redhat": "texlive-collection-pictures"
    }
}

def get_install_command(packages: dict) -> str:
    """Get the install command for the current distribution."""
    if DISTRO == 'arch':
        return f"sudo pacman -S {packages.get('arch', 'PACKAGE_NAME')}"
    elif DISTRO == 'debian':
        return f"sudo apt install {packages.get('debian', 'PACKAGE_NAME')}"
    elif DISTRO == 'redhat':
        return f"sudo dnf install {packages.get('redhat', 'PACKAGE_NAME')}"
    else:
        # Fallback to showing all options
        return f"Install with: apt install {packages.get('debian', 'PACKAGE')}, dnf install {packages.get('redhat', 'PACKAGE')}, or pacman -S {packages.get('arch', 'PACKAGE')}"

# Dependency checks
DEPENDENCIES = {
    "pandoc": {
        "available": check_package_installed(PACKAGE_MAPPINGS["pandoc"]) or check_command("pandoc"),
        "description": "pandoc (for markdown to PDF conversion)",
        "install_hint": get_install_command(PACKAGE_MAPPINGS["pandoc"])
    },
    "xelatex": {
        "available": check_package_installed(PACKAGE_MAPPINGS["xelatex"]) or check_command("xelatex"),
        "description": "XeLaTeX (for PDF generation from pandoc)",
        "install_hint": get_install_command(PACKAGE_MAPPINGS["xelatex"])
    },
    "latex_fonts": {
        "available": check_package_installed(PACKAGE_MAPPINGS["latex_fonts"]) or check_latex_fonts(),
        "description": "LaTeX fonts (Latin Modern, etc.)",
        "install_hint": get_install_command(PACKAGE_MAPPINGS["latex_fonts"])
    },
    "weasyprint": {
        "available": check_package_installed(PACKAGE_MAPPINGS["weasyprint"]) or check_command("weasyprint"),
        "description": "WeasyPrint (for HTML to PDF conversion)",
        "install_hint": get_install_command(PACKAGE_MAPPINGS["weasyprint"])
    },
    "rsvg-convert": {
        "available": check_package_installed(PACKAGE_MAPPINGS["rsvg"]) or check_command("rsvg-convert"),
        "description": "rsvg-convert (for SVG to PDF conversion)",
        "install_hint": get_install_command(PACKAGE_MAPPINGS["rsvg"])
    },
    "tikz": {
        "available": check_package_installed(PACKAGE_MAPPINGS["tikz"]),
        "description": "TikZ package (for LaTeX diagrams and graphics)",
        "install_hint": get_install_command(PACKAGE_MAPPINGS["tikz"])
    }
}

# Initialize FastMCP server  
mcp = FastMCP("cups-mcp")

# Log distribution detection and dependency status at startup
print(f"Detected Linux distribution: {DISTRO}")

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
    def print_markdown(content: Optional[str] = None, file_path: Optional[str] = None, printer: Optional[str] = None, title: str = "Document") -> str:
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
            content: Markdown content to print (optional if file_path is provided)
            file_path: Path to Markdown file to print (optional if content is provided)
            printer: Printer name (optional, uses default if not specified)
            title: Document title (optional)
        """
        # Validate input
        if not content and not file_path:
            return "Error: Either content or file_path must be provided"
        
        if content and file_path:
            return "Error: Provide either content or file_path, not both"
        
        # Handle file_path input
        if file_path:
            # Expand path
            path = Path(file_path).expanduser()
            
            # If no directory specified, check Documents folder
            if not path.is_absolute() and "/" not in str(file_path):
                path = Path.home() / "Documents" / file_path
            elif not path.is_absolute():
                # Relative path within Documents
                path = Path.home() / "Documents" / file_path
            
            if not path.exists():
                return f"File not found: {path}"
            
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                md_path = str(path)
                temp_file = False
            except Exception as e:
                return f"Failed to read file: {str(e)}"
        else:
            # Create temporary markdown file from content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(content)
                md_path = f.name
            temp_file = True
        
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
            # Clean up temporary files only if we created them
            if temp_file:
                Path(md_path).unlink(missing_ok=True)
                Path(pdf_path).unlink(missing_ok=True)
            else:
                # For user files, don't delete the source, only the generated PDF
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


# Register LaTeX printing if XeLaTeX is available
if DEPENDENCIES["xelatex"]["available"] and DEPENDENCIES["latex_fonts"]["available"]:
    @mcp.tool()
    def print_latex(content: Optional[str] = None, file_path: Optional[str] = None, printer: Optional[str] = None, title: str = "Document") -> str:
        """Print LaTeX content (compiled to PDF via XeLaTeX).
        
        IMPORTANT: If you already saved LaTeX content using save_latex, use the file_path 
        parameter instead of content to avoid regenerating the same content.
        
        IMPORTANT printer selection logic for AI agents:
        1. First print: If user doesn't specify, ask "Would you like to print or save as PDF?"
        2. If printing: Check if default printer exists. If not, ask which printer to use.
        3. Remember the chosen printer for the rest of the session.
        4. Only change printer if user explicitly requests a different one.
        
        Workflow options:
        1. Direct printing: Provide content + printer
        2. File printing: Provide file_path + printer (PREFERRED if file exists)
        
        Supports:
        - Full LaTeX syntax and packages
        - Mathematical formulas and equations
        - TikZ diagrams and graphics
        - Bibliography and citations
        - Custom document classes
        
        Args:
            content: LaTeX content to print (DO NOT use if you already saved the file)
            file_path: Path to existing LaTeX file (USE THIS if you saved with save_latex)
            printer: Printer name (optional, uses default if not specified)
            title: Document title (optional, used in jobname)
        """
        # Validate input
        if not content and not file_path:
            return "Error: Either content or file_path must be provided"
        
        if content and file_path:
            return "Error: Provide either content or file_path, not both"
        
        # Handle file_path input
        if file_path:
            # Expand path
            path = Path(file_path).expanduser()
            
            # If no directory specified, check Documents folder
            if not path.is_absolute() and "/" not in str(file_path):
                path = Path.home() / "Documents" / file_path
            elif not path.is_absolute():
                # Relative path within Documents
                path = Path.home() / "Documents" / file_path
            
            if not path.exists():
                return f"File not found: {path}"
            
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                tex_path = str(path)
                temp_file = False
            except Exception as e:
                return f"Failed to read file: {str(e)}"
        else:
            # Create temporary LaTeX file from content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
                f.write(content)
                tex_path = f.name
            temp_file = True
        
        # Output PDF path
        pdf_path = tex_path.replace('.tex', '.pdf')
        
        try:
            # Compile with bibliography support
            success, error_msg = compile_latex_with_bibliography(tex_path)
            if not success:
                return error_msg
            
            # Print the PDF
            cmd = ["lp", "-d", printer, pdf_path] if printer else ["lp", pdf_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                job_id = result.stdout.strip().split()[-1]
                return f"Print job submitted: {job_id}"
            else:
                return f"Print failed: {result.stderr}"
        finally:
            # Clean up temporary files only if we created them
            if temp_file:
                for ext in ['.tex', '.pdf', '.aux', '.log', '.bbl', '.blg']:
                    Path(tex_path.replace('.tex', ext)).unlink(missing_ok=True)
            else:
                # For user files, only clean up auxiliary files
                for ext in ['.aux', '.log', '.bbl', '.blg']:
                    Path(tex_path.replace('.tex', ext)).unlink(missing_ok=True)
else:
    @mcp.tool()
    def print_latex(content: str, printer: Optional[str] = None, title: str = "Document") -> str:
        """Print LaTeX content (UNAVAILABLE - missing dependencies).
        
        This tool requires XeLaTeX and LaTeX fonts to be installed.
        
        Args:
            content: LaTeX content to print
            printer: Printer name (optional, uses default if not specified)
            title: Document title (optional)
        """
        missing = []
        if not DEPENDENCIES["xelatex"]["available"]:
            missing.append(DEPENDENCIES["xelatex"]["install_hint"])
        if not DEPENDENCIES["latex_fonts"]["available"]:
            missing.append(DEPENDENCIES["latex_fonts"]["install_hint"])
        
        return f"LaTeX printing is not available. Missing dependencies:\n" + "\n".join(missing)


# Register markdown_to_pdf if dependencies are available
if DEPENDENCIES["pandoc"]["available"] and DEPENDENCIES["xelatex"]["available"] and DEPENDENCIES["latex_fonts"]["available"]:
    @mcp.tool()
    def markdown_to_pdf(content: Optional[str] = None, file_path: Optional[str] = None, output_path: str = None, title: str = "Document") -> str:
        """Convert markdown content to PDF and save to specified path.
        
        This is useful for generating PDFs without printing them, or for systems
        without a PDF printer configured.
        
        Supports:
        - Standard markdown formatting (headers, lists, tables, code blocks)
        - LaTeX math expressions (use $ for inline, $$ for display math)
        - Latin scripts including European languages
        - Greek and Cyrillic alphabets
        
        Args:
            content: Markdown content to convert (optional if file_path is provided)
            file_path: Path to Markdown file to convert (optional if content is provided)
            output_path: Path where PDF should be saved. Can be:
                - Full path: /home/user/Documents/file.pdf
                - Relative to Documents: report.pdf (saves to ~/Documents/report.pdf)
                - With ~: ~/Downloads/file.pdf
            title: Document title (optional)
        """
        # Validate input
        if not content and not file_path:
            return "Error: Either content or file_path must be provided"
        
        if content and file_path:
            return "Error: Provide either content or file_path, not both"
        
        if not output_path:
            return "Error: output_path is required"
        
        # Check if content was recently saved
        if content:
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            if content_hash in saved_file_hashes:
                saved_path = saved_file_hashes[content_hash]
                return (f"WARNING: This content was already saved to {saved_path}\n"
                       f"Please use: latex_to_pdf(file_path='{saved_path}', output_path='{output_path}')\n"
                       f"This avoids regenerating the same content and is more efficient.")
        
        # Handle file_path input
        if file_path:
            # Expand path
            path = Path(file_path).expanduser()
            
            # If no directory specified, check Documents folder
            if not path.is_absolute() and "/" not in str(file_path):
                path = Path.home() / "Documents" / file_path
            elif not path.is_absolute():
                # Relative path within Documents
                path = Path.home() / "Documents" / file_path
            
            if not path.exists():
                return f"File not found: {path}"
            
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                return f"Failed to read file: {str(e)}"
        
        # Handle output path expansion
        output_path = str(Path(output_path).expanduser())
        
        # If no directory specified, default to Documents folder
        if "/" not in output_path:
            documents_dir = Path.home() / "Documents"
            try:
                documents_dir.mkdir(exist_ok=True)  # Create if doesn't exist
            except Exception as e:
                return f"Failed to create Documents directory: {str(e)}"
            output_path = str(documents_dir / output_path)
        
        # Ensure output path ends with .pdf
        if not output_path.endswith('.pdf'):
            output_path += '.pdf'
        
        # Check if file already exists
        if Path(output_path).exists():
            # Generate unique filename
            base = Path(output_path).stem
            dir_path = Path(output_path).parent
            counter = 1
            while Path(output_path).exists():
                output_path = str(dir_path / f"{base}_{counter}.pdf")
                counter += 1
        
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
            
            # Verify file was created
            if not Path(output_path).exists():
                return f"PDF generation failed - file was not created at {output_path}"
            
            return f"PDF saved successfully to: {output_path}"
        except PermissionError:
            return f"Permission denied: Cannot write to {output_path}"
        except Exception as e:
            return f"Failed to save PDF: {str(e)}"
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


# Register markdown_to_latex if dependencies are available
if DEPENDENCIES["pandoc"]["available"]:
    @mcp.tool()
    def markdown_to_latex(file_path: str, output_path: Optional[str] = None, title: str = "Document", standalone: bool = True) -> str:
        """Convert a Markdown file to LaTeX format.
        
        This tool provides access to the intermediate LaTeX file that pandoc generates,
        allowing for manual customization before final PDF compilation.
        
        Workflow:
        1. Write content in Markdown (easier to write)
        2. Convert to LaTeX using this tool
        3. Fine-tune the LaTeX if needed
        4. Compile to PDF using latex_to_pdf
        
        Args:
            file_path: Path to Markdown file. Can be:
                - Simple name: document.md (reads from ~/Documents/)
                - Full path: /home/user/Documents/document.md
                - Relative to Documents: notes/document.md
            output_path: Path where LaTeX file should be saved (optional).
                If not specified, uses same name with .tex extension
            title: Document title (optional)
            standalone: Create complete LaTeX document (True) or just fragment (False)
        
        Returns:
            Success message with output file path, or error description
        """
        # Handle input file path
        input_path = Path(file_path).expanduser()
        
        # If no directory specified, check Documents folder
        if not input_path.is_absolute() and "/" not in str(file_path):
            input_path = Path.home() / "Documents" / file_path
        elif not input_path.is_absolute():
            # Relative path within Documents
            input_path = Path.home() / "Documents" / file_path
        
        if not input_path.exists():
            return f"File not found: {input_path}"
        
        # Handle output path
        if output_path:
            output_path = str(Path(output_path).expanduser())
            # If no directory specified, default to Documents folder
            if "/" not in output_path:
                documents_dir = Path.home() / "Documents"
                documents_dir.mkdir(exist_ok=True)
                output_path = str(documents_dir / output_path)
        else:
            # Use same location as input file, just change extension
            output_path = str(input_path.with_suffix('.tex'))
        
        # Ensure output path ends with .tex
        if not output_path.endswith('.tex'):
            output_path += '.tex'
        
        # Check if output file already exists
        if Path(output_path).exists():
            # Generate unique filename
            base = Path(output_path).stem
            dir_path = Path(output_path).parent
            counter = 1
            while Path(output_path).exists():
                output_path = str(dir_path / f"{base}_{counter}.tex")
                counter += 1
        
        try:
            # Prepare pandoc command
            pandoc_cmd = [
                "pandoc",
                str(input_path),
                "-o", output_path,
                "--metadata", f"title={title}",
                "-t", "latex"
            ]
            
            if standalone:
                pandoc_cmd.extend([
                    "-s",  # standalone document
                    "--pdf-engine=xelatex",
                    "-V", "geometry:margin=1in",
                    "-V", "mainfont=Noto Serif",
                    "-V", "sansfont=Noto Sans",
                    "-V", "monofont=Noto Sans Mono"
                ])
            
            # Run pandoc
            result = subprocess.run(pandoc_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return f"Markdown to LaTeX conversion failed: {result.stderr}"
            
            # Verify file was created
            if not Path(output_path).exists():
                return f"Conversion failed - LaTeX file was not created at {output_path}"
            
            # Add a comment at the top of the LaTeX file about its origin
            with open(output_path, 'r', encoding='utf-8') as f:
                latex_content = f.read()
            
            # Add conversion info comment
            comment = f"% Converted from Markdown: {input_path.name}\n% Conversion date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n% Use latex_to_pdf to compile this file to PDF\n\n"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(comment + latex_content)
            
            return f"Markdown successfully converted to LaTeX: {output_path}\n\nNext steps:\n1. Review/edit the LaTeX file if needed\n2. Use latex_to_pdf(file_path='{output_path}', output_path='document.pdf') to create PDF"
            
        except PermissionError:
            return f"Permission denied: Cannot write to {output_path}"
        except Exception as e:
            return f"Failed to convert Markdown to LaTeX: {str(e)}"
else:
    @mcp.tool()
    def markdown_to_latex(file_path: str, output_path: Optional[str] = None, title: str = "Document", standalone: bool = True) -> str:
        """Convert Markdown to LaTeX (UNAVAILABLE - missing dependencies).
        
        This tool requires pandoc to be installed.
        """
        return f"Markdown to LaTeX conversion is not available. Missing dependency:\n{DEPENDENCIES['pandoc']['install_hint']}"


@mcp.tool()
def save_markdown(content: str, filename: str) -> str:
    """Save markdown content to a file.
    
    Args:
        content: Markdown content to save
        filename: Filename to save. Can be:
            - Simple name: document.md (saves to ~/Documents/document.md)
            - Full path: /home/user/Documents/document.md
            - With ~: ~/Downloads/document.md
    """
    # Handle path expansion
    output_path = str(Path(filename).expanduser())
    
    # If no directory specified, default to Documents folder
    if "/" not in output_path:
        documents_dir = Path.home() / "Documents"
        try:
            documents_dir.mkdir(exist_ok=True)  # Create if doesn't exist
        except Exception as e:
            return f"Failed to create Documents directory: {str(e)}"
        output_path = str(documents_dir / output_path)
    
    # Ensure output path ends with .md
    if not output_path.endswith('.md'):
        output_path += '.md'
    
    # Check if file already exists
    if Path(output_path).exists():
        # Generate unique filename
        base = Path(output_path).stem
        dir_path = Path(output_path).parent
        counter = 1
        while Path(output_path).exists():
            output_path = str(dir_path / f"{base}_{counter}.md")
            counter += 1
    
    try:
        # Write the markdown file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"Markdown saved successfully to: {output_path}"
    except PermissionError:
        return f"Permission denied: Cannot write to {output_path}"
    except Exception as e:
        return f"Failed to save markdown: {str(e)}"


@mcp.tool()
def list_available_fonts(style: Optional[str] = None) -> str:
    """List fonts available for use with XeLaTeX.
    
    Args:
        style: Filter by style - 'serif', 'sans', 'mono', or None for all
    
    Returns:
        List of available fonts with their properties
    """
    try:
        # Use fc-list to get font information
        cmd = ["fc-list", "--format=%{family}\\n", ":outline=True:scalable=True"]
        
        # Add style filter if specified
        if style:
            if style.lower() == "serif":
                cmd[1] = "--format=%{family}\\n"
                cmd.append(":serif")
            elif style.lower() == "sans":
                cmd[1] = "--format=%{family}\\n"
                cmd.append(":sans")
            elif style.lower() == "mono":
                cmd[1] = "--format=%{family}\\n"
                cmd.append(":mono:spacing=mono")
                
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return "Error: fontconfig tools not available. Install fontconfig package."
        
        # Parse and deduplicate font families
        fonts = set()
        for line in result.stdout.strip().split('\n'):
            if line:
                # Handle font families with language variants
                font_name = line.split(',')[0].strip()
                if font_name:
                    fonts.add(font_name)
        
        # Sort fonts alphabetically
        sorted_fonts = sorted(fonts)
        
        # Build response
        response = f"Available {style or 'system'} fonts for XeLaTeX ({len(sorted_fonts)} found):\n\n"
        
        # Group by first letter for easier browsing
        current_letter = ""
        for font in sorted_fonts:
            first_letter = font[0].upper()
            if first_letter != current_letter:
                current_letter = first_letter
                response += f"\n{current_letter}:\n"
            response += f"  {font}\n"
        
        # Add usage example
        response += "\n\nTo use a font in LaTeX:\n"
        response += "\\usepackage{fontspec}\n"
        response += "\\setmainfont{Font Name}     % for main text\n"
        response += "\\setsansfont{Font Name}     % for sans-serif\n"
        response += "\\setmonofont{Font Name}     % for monospace\n"
        
        # Add common recommendations
        response += "\n\nPopular choices:\n"
        
        common_fonts = {
            "serif": ["Liberation Serif", "DejaVu Serif", "Noto Serif", "Linux Libertine", "TeX Gyre Termes"],
            "sans": ["Liberation Sans", "DejaVu Sans", "Noto Sans", "Open Sans", "Roboto"],
            "mono": ["Liberation Mono", "DejaVu Sans Mono", "Noto Sans Mono", "Fira Code", "JetBrains Mono"]
        }
        
        for category, font_list in common_fonts.items():
            available = [f for f in font_list if f in sorted_fonts]
            if available:
                response += f"\n{category.title()}:"
                for font in available[:3]:  # Show up to 3
                    response += f"\n  - {font}"
        
        return response
        
    except FileNotFoundError:
        return "Error: fontconfig not installed. Install with:\n" + \
               "  Debian/Ubuntu: apt install fontconfig\n" + \
               "  Fedora: dnf install fontconfig\n" + \
               "  Arch: pacman -S fontconfig"
    except Exception as e:
        return f"Error listing fonts: {str(e)}"


@mcp.tool()
def validate_latex(content: str) -> str:
    """Validate LaTeX content for syntax errors before compilation.
    
    Uses lacheck and chktex (if available) and attempts a test compilation
    to identify issues before actually printing or saving.
    
    Args:
        content: LaTeX content to validate
    
    Returns:
        Validation report with any errors or warnings found
    """
    # Create temporary LaTeX file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
        f.write(content)
        tex_path = f.name
    
    try:
        report = []
        
        # Run lacheck if available
        if check_command("lacheck"):
            result = subprocess.run(
                ["lacheck", tex_path],
                capture_output=True,
                text=True
            )
            if result.stdout:
                report.append("=== LaCheck Warnings ===")
                report.append(result.stdout.strip())
        
        # Run chktex if available (more comprehensive)
        if check_command("chktex"):
            result = subprocess.run(
                ["chktex", "-q", "-n", "all", tex_path],
                capture_output=True,
                text=True
            )
            if result.stdout:
                report.append("\n=== ChkTeX Analysis ===")
                report.append(result.stdout.strip())
        
        # Try a quick compilation to catch more errors
        if DEPENDENCIES["xelatex"]["available"]:
            report.append("\n=== Compilation Test ===")
            # Run with batchmode to suppress output but catch errors
            result = subprocess.run(
                ["xelatex", "-interaction=batchmode", "-halt-on-error", tex_path],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(tex_path)
            )
            
            if result.returncode != 0:
                # Read the log file for errors
                log_path = tex_path.replace('.tex', '.log')
                if os.path.exists(log_path):
                    with open(log_path, 'r') as log:
                        log_content = log.read()
                        # Extract error messages
                        errors = []
                        in_error = False
                        for line in log_content.split('\n'):
                            if line.startswith('!'):
                                in_error = True
                                errors.append(line)
                            elif in_error and (line.startswith('l.') or line.strip() == ''):
                                errors.append(line)
                                if line.strip() == '':
                                    in_error = False
                            elif 'Error:' in line or 'error:' in line:
                                errors.append(line)
                        
                        if errors:
                            report.append("Compilation FAILED with errors:")
                            report.extend(errors[:20])  # First 20 error lines
                            if len(errors) > 20:
                                report.append(f"... and {len(errors)-20} more error lines")
                
                # Clean up auxiliary files
                for ext in ['.aux', '.log', '.out']:
                    aux_file = tex_path.replace('.tex', ext)
                    if os.path.exists(aux_file):
                        os.unlink(aux_file)
            else:
                report.append("✓ Compilation successful! Document is valid.")
                # Clean up PDF and auxiliary files
                for ext in ['.pdf', '.aux', '.log', '.out']:
                    aux_file = tex_path.replace('.tex', ext)
                    if os.path.exists(aux_file):
                        os.unlink(aux_file)
        else:
            report.append("\n⚠ XeLaTeX not available for compilation test.")
        
        # Clean up temp file
        os.unlink(tex_path)
        
        if not report:
            return "✓ LaTeX validation passed - no issues found!"
        
        return "\n".join(report)
        
    except Exception as e:
        if os.path.exists(tex_path):
            os.unlink(tex_path)
        return f"Validation error: {str(e)}"


@mcp.tool()
def save_latex(content: str, filename: str) -> str:
    """Save LaTeX content to a .tex file.
    
    After saving, you can:
    - Convert to PDF: Use latex_to_pdf with file_path=<saved_file>
    - Print: Use print_latex with file_path=<saved_file>
    
    IMPORTANT: Do NOT regenerate the content when using latex_to_pdf or print_latex.
    Instead, use the file_path parameter with the path returned by this function.
    
    Args:
        content: LaTeX content to save
        filename: Filename to save. Can be:
            - Simple name: document.tex (saves to ~/Documents/document.tex)
            - Full path: /home/user/Documents/document.tex
            - With ~: ~/Downloads/document.tex
    """
    # Handle path expansion
    output_path = str(Path(filename).expanduser())
    
    # If no directory specified, default to Documents folder
    if "/" not in output_path:
        documents_dir = Path.home() / "Documents"
        try:
            documents_dir.mkdir(exist_ok=True)  # Create if doesn't exist
        except Exception as e:
            return f"Failed to create Documents directory: {str(e)}"
        output_path = str(documents_dir / output_path)
    
    # Ensure output path ends with .tex
    if not output_path.endswith('.tex'):
        output_path += '.tex'
    
    # Check if file already exists
    if Path(output_path).exists():
        # Generate unique filename
        base = Path(output_path).stem
        dir_path = Path(output_path).parent
        counter = 1
        while Path(output_path).exists():
            output_path = str(dir_path / f"{base}_{counter}.tex")
            counter += 1
    
    try:
        # Write the LaTeX file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Track content hash to detect redundant regeneration
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        saved_file_hashes[content_hash] = output_path
        recent_content_hashes.append(content_hash)
        
        return f"LaTeX saved successfully to: {output_path}"
    except PermissionError:
        return f"Permission denied: Cannot write to {output_path}"
    except Exception as e:
        return f"Failed to save LaTeX: {str(e)}"


# Register latex_to_pdf if XeLaTeX is available
if DEPENDENCIES["xelatex"]["available"] and DEPENDENCIES["latex_fonts"]["available"]:
    @mcp.tool()
    def latex_to_pdf(content: Optional[str] = None, file_path: Optional[str] = None, output_path: str = None, title: str = "Document") -> str:
        """Convert LaTeX content to PDF and save to specified path.
        
        IMPORTANT: If you already saved LaTeX content using save_latex, use the file_path 
        parameter instead of content to avoid regenerating the same content.
        
        Workflow options:
        1. Direct conversion: Provide content + output_path
        2. File conversion: Provide file_path + output_path (PREFERRED if file exists)
        
        Args:
            content: LaTeX content to convert (DO NOT use if you already saved the file)
            file_path: Path to existing LaTeX file (USE THIS if you saved with save_latex)
            output_path: Path where PDF should be saved. Can be:
                - Full path: /home/user/Documents/file.pdf
                - Relative to Documents: report.pdf (saves to ~/Documents/report.pdf)
                - With ~: ~/Downloads/file.pdf
            title: Document title (optional, used in jobname)
        """
        # Validate input
        if not content and not file_path:
            return "Error: Either content or file_path must be provided"
        
        if content and file_path:
            return "Error: Provide either content or file_path, not both"
        
        if not output_path:
            return "Error: output_path is required"
        
        # Check if content was recently saved
        if content:
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            if content_hash in saved_file_hashes:
                saved_path = saved_file_hashes[content_hash]
                return (f"WARNING: This content was already saved to {saved_path}\n"
                       f"Please use: latex_to_pdf(file_path='{saved_path}', output_path='{output_path}')\n"
                       f"This avoids regenerating the same content and is more efficient.")
        
        # Handle file_path input
        if file_path:
            # Expand path
            path = Path(file_path).expanduser()
            
            # If no directory specified, check Documents folder
            if not path.is_absolute() and "/" not in str(file_path):
                path = Path.home() / "Documents" / file_path
            elif not path.is_absolute():
                # Relative path within Documents
                path = Path.home() / "Documents" / file_path
            
            if not path.exists():
                return f"File not found: {path}"
            
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                tex_path = str(path)
                temp_file = False
            except Exception as e:
                return f"Failed to read file: {str(e)}"
        else:
            # Create temporary LaTeX file from content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
                f.write(content)
                tex_path = f.name
            temp_file = True
        
        # Handle output path expansion
        output_path = str(Path(output_path).expanduser())
        
        # If no directory specified, default to Documents folder
        if "/" not in output_path:
            documents_dir = Path.home() / "Documents"
            try:
                documents_dir.mkdir(exist_ok=True)
            except Exception as e:
                return f"Failed to create Documents directory: {str(e)}"
            output_path = str(documents_dir / output_path)
        
        # Ensure output path ends with .pdf
        if not output_path.endswith('.pdf'):
            output_path += '.pdf'
        
        # Check if file already exists
        if Path(output_path).exists():
            # Generate unique filename
            base = Path(output_path).stem
            dir_path = Path(output_path).parent
            counter = 1
            while Path(output_path).exists():
                output_path = str(dir_path / f"{base}_{counter}.pdf")
                counter += 1
        
        try:
            # Compile with bibliography support
            success, error_msg = compile_latex_with_bibliography(tex_path)
            if not success:
                return error_msg
            
            # Move the generated PDF to the desired location
            generated_pdf = tex_path.replace('.tex', '.pdf')
            shutil.move(generated_pdf, output_path)
            
            return f"PDF saved successfully to: {output_path}"
            
        except PermissionError:
            return f"Permission denied: Cannot write to {output_path}"
        except Exception as e:
            return f"Failed to save PDF: {str(e)}"
        finally:
            # Clean up temporary files only if we created them
            if temp_file:
                for ext in ['.tex', '.aux', '.log', '.bbl', '.blg']:
                    Path(tex_path.replace('.tex', ext)).unlink(missing_ok=True)
            else:
                # For user files, only clean up auxiliary files
                for ext in ['.aux', '.log', '.bbl', '.blg']:
                    Path(tex_path.replace('.tex', ext)).unlink(missing_ok=True)
else:
    @mcp.tool()
    def latex_to_pdf(content: Optional[str] = None, file_path: Optional[str] = None, output_path: str = None, title: str = "Document") -> str:
        """Convert LaTeX to PDF (UNAVAILABLE - missing dependencies).
        
        This tool requires XeLaTeX and LaTeX fonts to be installed.
        """
        missing = []
        if not DEPENDENCIES["xelatex"]["available"]:
            missing.append(DEPENDENCIES["xelatex"]["install_hint"])
        if not DEPENDENCIES["latex_fonts"]["available"]:
            missing.append(DEPENDENCIES["latex_fonts"]["install_hint"])
        
        return f"LaTeX to PDF conversion is not available. Missing dependencies:\n" + "\n".join(missing)


@mcp.tool()
def list_documents(folder: str = "") -> str:
    """List all printable files in Documents folder or subfolder.
    
    IMPORTANT for AI agents: Use this tool to find files when the user provides
    partial or approximate filenames. This tool shows ALL file types including
    PDF, Markdown, LaTeX, HTML, SVG, images, and other documents.
    
    Args:
        folder: Subfolder within Documents (optional, e.g., "reports" for ~/Documents/reports)
    """
    documents_dir = Path.home() / "Documents"
    if folder:
        documents_dir = documents_dir / folder
    
    if not documents_dir.exists():
        return f"Directory not found: {documents_dir}"
    
    try:
        # Define file types to list
        file_patterns = {
            "PDF files": "*.pdf",
            "Markdown files": "*.md", 
            "LaTeX files": "*.tex",
            "HTML files": "*.html",
            "SVG files": "*.svg",
            "Image files": ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp", "*.webp"],
            "Text files": "*.txt",
            "Other documents": ["*.doc", "*.docx", "*.odt", "*.rtf"]
        }
        
        all_files = {}
        
        # Collect files by type
        for file_type, patterns in file_patterns.items():
            if isinstance(patterns, str):
                patterns = [patterns]
            
            files = []
            for pattern in patterns:
                files.extend(documents_dir.glob(pattern))
            
            if files:
                all_files[file_type] = sorted(files)
        
        if not all_files:
            return f"No document files found in {documents_dir}"
        
        result = f"Files in {documents_dir}:\n\n"
        
        # Display files by type
        for file_type, files in all_files.items():
            result += f"{file_type}:\n"
            for f in files:
                size = f.stat().st_size / 1024  # KB
                result += f"  - {f.name} ({size:.1f} KB)\n"
            result += "\n"
        
        return result.rstrip()
    except PermissionError:
        return f"Permission denied accessing {documents_dir}"
    except Exception as e:
        return f"Error listing documents: {str(e)}"


@mcp.tool()
def print_from_documents(filename: str, printer: Optional[str] = None, folder: str = "") -> str:
    """Print a PDF or Markdown file from Documents folder.
    
    IMPORTANT printer selection logic for AI agents:
    1. First print: Check if default printer exists. If not, ask which printer to use.
    2. Remember the chosen printer for the rest of the session.
    3. Only change printer if user explicitly requests a different one.
    
    Args:
        filename: Name of file to print (e.g., "report.pdf" or "notes.md")
        printer: Printer name (optional, uses default if not specified)
        folder: Subfolder within Documents (optional, e.g., "reports")
    """
    documents_dir = Path.home() / "Documents"
    if folder:
        documents_dir = documents_dir / folder
    
    file_path = documents_dir / filename
    
    if not file_path.exists():
        # Try with common extensions if not provided
        if not file_path.suffix:
            for ext in ['.pdf', '.md', '.tex']:
                test_path = documents_dir / f"{filename}{ext}"
                if test_path.exists():
                    file_path = test_path
                    break
    
    if not file_path.exists():
        return f"File not found: {file_path}"
    
    # If it's a markdown file, convert to PDF first
    if file_path.suffix.lower() == '.md':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Use our existing markdown printing logic
            return print_markdown(content, printer, title=file_path.stem)
        except Exception as e:
            return f"Failed to read markdown file: {str(e)}"
    
    # If it's a LaTeX file, compile and print
    if file_path.suffix.lower() == '.tex':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Use our existing LaTeX printing logic
            return print_latex(content, printer, title=file_path.stem)
        except Exception as e:
            return f"Failed to read LaTeX file: {str(e)}"
    
    # For PDFs and other files, use regular print_file
    return print_file(str(file_path), printer)


@mcp.tool()
def print_file(path: str, printer: Optional[str] = None) -> str:
    """Print a file from the filesystem.
    
    IMPORTANT printer selection logic for AI agents:
    1. First print: If user doesn't specify, ask "Would you like to print or save as PDF?"
    2. If printing: Check if default printer exists. If not, ask which printer to use.
    3. Remember the chosen printer for the rest of the session.
    4. Only change printer if user explicitly requests a different one.
    
    Args:
        path: Path to the file to print (use ~ for home directory)
        printer: Printer name (optional, uses default if not specified)
    """
    # Expand user home directory
    path = str(Path(path).expanduser())
    
    if not Path(path).exists():
        return f"File not found: {path}"
    
    # Detect file type
    mime = magic.from_file(path, mime=True)
    file_ext = Path(path).suffix.lower()
    
    # Handle HTML files
    if mime == "text/html" or file_ext == ".html":
        if DEPENDENCIES["weasyprint"]["available"]:
            # Convert HTML to PDF first
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
                pdf_path = tmp_pdf.name
            
            try:
                # Use weasyprint to convert HTML to PDF
                result = subprocess.run(
                    ["weasyprint", path, pdf_path],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    return f"HTML to PDF conversion failed: {result.stderr}"
                
                # Print the PDF
                cmd = ["lp", "-d", printer, pdf_path] if printer else ["lp", pdf_path]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                # Clean up
                os.unlink(pdf_path)
                
                if result.returncode == 0:
                    job_id = result.stdout.strip().split()[-1]
                    return f"Print job submitted: {job_id} (HTML rendered to PDF)"
                else:
                    return f"Print failed: {result.stderr}"
                    
            except Exception as e:
                if os.path.exists(pdf_path):
                    os.unlink(pdf_path)
                return f"Failed to convert HTML: {str(e)}"
        else:
            return f"HTML printing requires WeasyPrint. {DEPENDENCIES['weasyprint']['install_hint']}"
    
    # Handle SVG files
    elif mime == "image/svg+xml" or file_ext == ".svg":
        if DEPENDENCIES["rsvg-convert"]["available"]:
            # Convert SVG to PDF first
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
                pdf_path = tmp_pdf.name
            
            try:
                # Use rsvg-convert to convert SVG to PDF
                result = subprocess.run(
                    ["rsvg-convert", "-f", "pdf", "-o", pdf_path, path],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    return f"SVG to PDF conversion failed: {result.stderr}"
                
                # Print the PDF
                cmd = ["lp", "-d", printer, pdf_path] if printer else ["lp", pdf_path]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                # Clean up
                os.unlink(pdf_path)
                
                if result.returncode == 0:
                    job_id = result.stdout.strip().split()[-1]
                    return f"Print job submitted: {job_id} (SVG rendered to PDF)"
                else:
                    return f"Print failed: {result.stderr}"
                    
            except Exception as e:
                if os.path.exists(pdf_path):
                    os.unlink(pdf_path)
                return f"Failed to convert SVG: {str(e)}"
        else:
            return f"SVG printing requires rsvg-convert. {DEPENDENCIES['rsvg-convert']['install_hint']}"
    
    # For other files, let CUPS handle it directly
    else:
        cmd = ["lp", "-d", printer, path] if printer else ["lp", path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            job_id = result.stdout.strip().split()[-1]
            return f"Print job submitted: {job_id} (type: {mime})"
        else:
            return f"Print failed: {result.stderr}"


import time
import hashlib
from datetime import datetime
from collections import deque

# Store file metadata for change detection
file_metadata = {}

# Track recent content hashes to detect redundant regeneration
recent_content_hashes = deque(maxlen=10)  # Keep last 10 hashes
saved_file_hashes = {}  # Map content hash to saved file path


def detect_bibliography(content: str) -> bool:
    """Detect if LaTeX content uses bibliography features.
    
    Returns True if the document contains:
    - \bibliography{...}
    - \addbibresource{...}
    - \cite{...}
    - bibtex/biblatex package inclusion
    """
    bibliography_patterns = [
        r'\\bibliography\{',
        r'\\addbibresource\{',
        r'\\cite\{',
        r'\\citep\{',
        r'\\citet\{',
        r'\\usepackage.*\{.*bib(tex|latex)',
        r'\\bibliographystyle\{',
    ]
    
    for pattern in bibliography_patterns:
        if re.search(pattern, content):
            return True
    return False


def compile_latex_with_bibliography(tex_path: str, working_dir: str = None) -> tuple[bool, str]:
    """Compile LaTeX document with proper bibliography handling.
    
    Args:
        tex_path: Path to the .tex file
        working_dir: Working directory for compilation (defaults to tex file directory)
    
    Returns:
        Tuple of (success: bool, error_message: str)
    """
    if working_dir is None:
        working_dir = str(Path(tex_path).parent)
    
    base_name = Path(tex_path).stem
    
    # First pass - generate .aux file
    xelatex_cmd = [
        "xelatex",
        "-interaction=nonstopmode",
        f"-jobname={base_name}",
        "-output-directory", working_dir,
        tex_path
    ]
    
    # First XeLaTeX pass
    result = subprocess.run(xelatex_cmd, capture_output=True, text=True, cwd=working_dir)
    if result.returncode != 0:
        log_path = os.path.join(working_dir, f"{base_name}.log")
        return False, parse_latex_errors(result.stdout, result.stderr, log_path)
    
    # Check if .aux file exists and has citations
    aux_path = os.path.join(working_dir, f"{base_name}.aux")
    if os.path.exists(aux_path):
        with open(aux_path, 'r', encoding='utf-8', errors='ignore') as f:
            aux_content = f.read()
        
        # If citations exist, run bibtex
        if '\\citation{' in aux_content or '\\bibdata{' in aux_content:
            # Run BibTeX
            bibtex_cmd = ["bibtex", base_name]
            result = subprocess.run(bibtex_cmd, capture_output=True, text=True, cwd=working_dir)
            
            # BibTeX may have warnings but still succeed
            if result.returncode > 1:  # 0 = success, 1 = warnings, >1 = errors
                return False, f"BibTeX failed: {result.stderr}"
            
            # Second XeLaTeX pass - incorporate bibliography
            result = subprocess.run(xelatex_cmd, capture_output=True, text=True, cwd=working_dir)
            if result.returncode != 0:
                log_path = os.path.join(working_dir, f"{base_name}.log")
                return False, parse_latex_errors(result.stdout, result.stderr, log_path)
            
            # Third XeLaTeX pass - resolve all references
            result = subprocess.run(xelatex_cmd, capture_output=True, text=True, cwd=working_dir)
            if result.returncode != 0:
                log_path = os.path.join(working_dir, f"{base_name}.log")
                return False, parse_latex_errors(result.stdout, result.stderr, log_path)
        else:
            # No bibliography, just run second pass for TOC/references
            result = subprocess.run(xelatex_cmd, capture_output=True, text=True, cwd=working_dir)
            if result.returncode != 0:
                log_path = os.path.join(working_dir, f"{base_name}.log")
                return False, parse_latex_errors(result.stdout, result.stderr, log_path)
    
    return True, ""


def parse_latex_errors(stdout: str, stderr: str, log_path: str = None) -> str:
    """Parse LaTeX compilation errors and provide helpful installation instructions."""
    error_msg = []
    missing_packages = set()
    
    # Check for missing package errors
    for line in stdout.split('\n'):
        if '! LaTeX Error: File' in line and 'not found' in line:
            # Extract package name from error like "File `tikz.sty' not found"
            import re
            match = re.search(r"File `([^']+)' not found", line)
            if match:
                package = match.group(1).replace('.sty', '')
                missing_packages.add(package)
        elif 'Package' in line and 'was not found' in line:
            # Handle other package not found formats
            match = re.search(r"Package (\S+) was not found", line)
            if match:
                missing_packages.add(match.group(1))
        elif line.startswith('!'):
            error_msg.append(line)
    
    # Read log file for more details if available
    if log_path and os.path.exists(log_path):
        try:
            with open(log_path, 'r') as log:
                log_content = log.read()
                # Look for missing package patterns in log
                for match in re.finditer(r"! LaTeX Error: File `([^']+)' not found", log_content):
                    package = match.group(1).replace('.sty', '')
                    missing_packages.add(package)
                
                # Extract context around errors
                if not error_msg:
                    lines = log_content.split('\n')
                    for i, line in enumerate(lines):
                        if line.startswith('!'):
                            # Get error and context
                            error_context = lines[i:min(i+5, len(lines))]
                            error_msg.extend(error_context)
                            break
        except:
            pass
    
    # Build helpful error message
    if missing_packages:
        result = "LaTeX compilation failed due to missing packages:\n\n"
        result += "Missing packages:\n"
        for pkg in sorted(missing_packages):
            result += f"  - {pkg}\n"
        
        result += f"\nTo install these packages on {DISTRO}:\n"
        
        # Package suggestions based on common mappings
        package_suggestions = {
            'tikz': PACKAGE_MAPPINGS.get('tikz', {}),
            'graphicx': {'arch': 'texlive-pictures', 'debian': 'texlive-pictures', 'redhat': 'texlive-collection-pictures'},
            'amsmath': {'arch': 'texlive-science', 'debian': 'texlive-science', 'redhat': 'texlive-collection-mathscience'},
            'hyperref': {'arch': 'texlive-latexextra', 'debian': 'texlive-latex-extra', 'redhat': 'texlive-collection-latexextra'},
            'babel': {'arch': 'texlive-langeuropean', 'debian': 'texlive-lang-european', 'redhat': 'texlive-collection-langeuropean'},
        }
        
        # Provide installation commands
        install_commands = set()
        for pkg in missing_packages:
            if pkg in package_suggestions:
                cmd = get_install_command(package_suggestions[pkg])
                install_commands.add(cmd)
            else:
                # Generic suggestion for unknown packages
                if DISTRO == 'arch':
                    install_commands.add(f"sudo pacman -S texlive-latexextra  # (may contain {pkg})")
                elif DISTRO == 'debian':
                    install_commands.add(f"sudo apt install texlive-latex-extra  # (may contain {pkg})")
                elif DISTRO == 'redhat':
                    install_commands.add(f"sudo dnf install texlive-collection-latexextra  # (may contain {pkg})")
        
        for cmd in sorted(install_commands):
            result += f"  {cmd}\n"
        
        result += "\nAlternatively, install texlive-full for all packages (large download)."
        
        if error_msg:
            result += f"\n\nOriginal error:\n" + '\n'.join(error_msg[:5])
    elif error_msg:
        result = "LaTeX compilation failed:\n" + '\n'.join(error_msg[:10])
        if len(error_msg) > 10:
            result += f"\n... and {len(error_msg)-10} more error lines"
    else:
        result = f"LaTeX compilation failed: {stderr if stderr else 'Unknown error'}"
    
    return result

@mcp.tool()
def check_document_status(file_path: str) -> str:
    """Check if a document has been modified externally and show changes.
    
    Tracks document modification times and content hashes to detect external changes.
    If changes are detected, shows a diff of what changed.
    
    Args:
        file_path: Path to document to check
    
    Returns:
        Status report including modification info and diff if changed
    """
    # Handle path expansion
    path = Path(file_path).expanduser()
    
    # If no directory specified, default to Documents folder
    if not path.is_absolute() and "/" not in str(file_path):
        path = Path.home() / "Documents" / file_path
    elif not path.is_absolute():
        # Relative path within Documents
        path = Path.home() / "Documents" / file_path
    
    if not path.exists():
        return f"File not found: {path}"
    
    try:
        # Get current file stats
        stat = os.stat(path)
        current_mtime = stat.st_mtime
        current_size = stat.st_size
        
        # Read current content for hash
        with open(path, 'r', encoding='utf-8') as f:
            current_content = f.read()
        current_hash = hashlib.sha256(current_content.encode()).hexdigest()
        
        # Check if we have previous metadata
        path_str = str(path)
        if path_str in file_metadata:
            prev_meta = file_metadata[path_str]
            prev_mtime = prev_meta['mtime']
            prev_hash = prev_meta['hash']
            prev_content = prev_meta.get('content', '')
            
            if current_hash != prev_hash:
                # File has changed - generate diff
                import difflib
                
                prev_lines = prev_content.splitlines(keepends=True)
                curr_lines = current_content.splitlines(keepends=True)
                
                diff = difflib.unified_diff(
                    prev_lines,
                    curr_lines,
                    fromfile=f"{path.name} (previous)",
                    tofile=f"{path.name} (current)",
                    fromfiledate=datetime.fromtimestamp(prev_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    tofiledate=datetime.fromtimestamp(current_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    n=3
                )
                
                diff_text = ''.join(diff)
                
                # Update metadata
                file_metadata[path_str] = {
                    'mtime': current_mtime,
                    'size': current_size,
                    'hash': current_hash,
                    'content': current_content
                }
                
                return f"""File has been modified externally!

Last checked: {datetime.fromtimestamp(prev_mtime).strftime('%Y-%m-%d %H:%M:%S')}
Current time: {datetime.fromtimestamp(current_mtime).strftime('%Y-%m-%d %H:%M:%S')}
Size change: {prev_meta['size']} → {current_size} bytes

Changes detected:
{diff_text}"""
            else:
                return f"""No changes detected.
                
File: {path}
Last modified: {datetime.fromtimestamp(current_mtime).strftime('%Y-%m-%d %H:%M:%S')}
Size: {current_size} bytes
Status: Unchanged since last check"""
        else:
            # First time checking this file
            file_metadata[path_str] = {
                'mtime': current_mtime,
                'size': current_size,
                'hash': current_hash,
                'content': current_content
            }
            
            return f"""Now tracking document for changes.
            
File: {path}
Modified: {datetime.fromtimestamp(current_mtime).strftime('%Y-%m-%d %H:%M:%S')}
Size: {current_size} bytes
Hash: {current_hash[:16]}...
Status: Initial tracking started"""
            
    except Exception as e:
        return f"Error checking document status: {str(e)}"


@mcp.tool()
def read_document(file_path: str, offset: int = 1, limit: int = 50) -> str:
    """Read a document file with line numbers for editing.
    
    Similar to the system Read tool but specifically for documents.
    Returns content in 'cat -n' format with line numbers.
    
    Args:
        file_path: Path to document. Can be:
            - Simple name: document.tex (reads from ~/Documents/)
            - Full path: /home/user/Documents/file.tex
            - Relative to Documents: subfolder/file.tex
        offset: Starting line number (default: 1)
        limit: Number of lines to read (default: 50)
    
    Returns:
        File content with line numbers in format: "   123[TAB]content"
    """
    # Handle path expansion
    path = Path(file_path).expanduser()
    
    # If no directory specified, default to Documents folder
    if not path.is_absolute() and "/" not in str(file_path):
        path = Path.home() / "Documents" / file_path
    elif not path.is_absolute():
        # Relative path within Documents
        path = Path.home() / "Documents" / file_path
    
    if not path.exists():
        return f"File not found: {path}"
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Apply offset and limit
        start = max(0, offset - 1)  # Convert to 0-based index
        end = min(len(lines), start + limit)
        
        # Format with line numbers
        result = []
        for i in range(start, end):
            # Format: right-aligned line number + tab + content
            line_num = i + 1
            # Remove newline for display, it will be in the content already
            content = lines[i].rstrip('\n')
            result.append(f"{line_num:6d}\t{content}")
        
        if not result:
            return f"No content in range (lines {offset}-{offset+limit-1})"
        
        # Update tracking metadata when reading
        stat = os.stat(path)
        path_str = str(path)
        file_metadata[path_str] = {
            'mtime': stat.st_mtime,
            'size': stat.st_size,
            'hash': hashlib.sha256(''.join(lines).encode()).hexdigest(),
            'content': ''.join(lines)
        }
        
        return '\n'.join(result)
        
    except PermissionError:
        return f"Permission denied: Cannot read {path}"
    except Exception as e:
        return f"Failed to read document: {str(e)}"


@mcp.tool()
def edit_document(file_path: str, old_string: str, new_string: str, expected_replacements: int = 1) -> str:
    """Edit a document file by replacing exact string matches.
    
    Similar to the system Edit tool but specifically for documents.
    Performs exact string replacement with occurrence validation.
    
    This tool supports collaborative editing by detecting external changes:
    - Checks if the file has been modified since last read
    - Shows a diff of external changes if detected
    - Prevents accidental overwrites of user edits
    - Updates tracking metadata after successful edits
    
    Args:
        file_path: Path to document. Can be:
            - Simple name: document.tex (edits in ~/Documents/)
            - Full path: /home/user/Documents/file.tex
            - Relative to Documents: subfolder/file.tex
        old_string: Exact string to find and replace
        new_string: String to replace with
        expected_replacements: Expected number of replacements (default: 1)
    
    Returns:
        Success message with snippet of changes, or error description
    """
    # Validate inputs
    if old_string == new_string:
        return "Error: old_string and new_string are the same"
    
    # Handle path expansion
    path = Path(file_path).expanduser()
    
    # If no directory specified, default to Documents folder
    if not path.is_absolute() and "/" not in str(file_path):
        path = Path.home() / "Documents" / file_path
    elif not path.is_absolute():
        # Relative path within Documents
        path = Path.home() / "Documents" / file_path
    
    if not path.exists():
        return f"File not found: {path}"
    
    try:
        # Check for external changes first
        path_str = str(path)
        if path_str in file_metadata:
            stat = os.stat(path)
            stored_meta = file_metadata[path_str]
            
            # Check if file was modified externally
            if stat.st_mtime > stored_meta['mtime'] or stat.st_size != stored_meta['size']:
                # Read current content
                with open(path, 'r', encoding='utf-8') as f:
                    current_content = f.read()
                
                # Check if content actually changed
                current_hash = hashlib.sha256(current_content.encode()).hexdigest()
                if current_hash != stored_meta['hash']:
                    # Generate diff
                    stored_lines = stored_meta['content'].splitlines(keepends=True)
                    current_lines = current_content.splitlines(keepends=True)
                    
                    diff = list(difflib.unified_diff(
                        stored_lines,
                        current_lines,
                        fromfile=f"{path} (last read)",
                        tofile=f"{path} (current)",
                        n=3
                    ))
                    
                    diff_text = ''.join(diff) if diff else "No line-by-line differences found"
                    
                    return (f"Error: File has been modified externally since last read!\n\n"
                           f"External changes detected:\n{diff_text}\n\n"
                           f"Please use read_document to get the latest version before editing.")
        
        # Read the file
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count occurrences
        count = content.count(old_string)
        
        if count == 0:
            return f"String not found in file: {repr(old_string)}"
        
        if count != expected_replacements:
            return f"Expected {expected_replacements} replacement(s), but found {count} occurrence(s)"
        
        # Perform replacement
        new_content = content.replace(old_string, new_string)
        
        # Write back
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # Update tracking metadata after successful edit
        stat = os.stat(path)
        file_metadata[path_str] = {
            'mtime': stat.st_mtime,
            'size': stat.st_size,
            'hash': hashlib.sha256(new_content.encode()).hexdigest(),
            'content': new_content
        }
        
        # Return success with context
        # Find first replacement location for context
        pos = content.find(old_string)
        start = max(0, pos - 50)
        end = min(len(new_content), pos + len(new_string) + 50)
        snippet = new_content[start:end]
        
        return f"Successfully replaced {count} occurrence(s) in {path}\nContext: ...{snippet}..."
        
    except PermissionError:
        return f"Permission denied: Cannot write to {path}"
    except Exception as e:
        return f"Failed to edit document: {str(e)}"


# This is needed for FastMCP to find the server
server = mcp

def main():
    """Main entry point for the cups-mcp server."""
    mcp.run()

if __name__ == "__main__":
    main()