#!/usr/bin/env python3
"""CUPS MCP Server - Print documents via CUPS on Linux."""

import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional

from mcp.server.fastmcp import FastMCP

import cups
import magic


# Initialize FastMCP server  
mcp = FastMCP("cups-mcp")


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


@mcp.tool()
def print_markdown(content: str, printer: Optional[str] = None, title: str = "Document") -> str:
    """Print markdown content (rendered to PDF via pandoc).
    
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
            "-V", "geometry:margin=1in"
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


@mcp.tool()
def print_file(path: str, printer: Optional[str] = None) -> str:
    """Print a file from the filesystem.
    
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