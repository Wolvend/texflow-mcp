"""
Output Operation implementation for TeXFlow.

Bundles all output-related tools (printing, PDF export) into a unified interface.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import re


class OutputOperation:
    """Handles all output operations including print and export."""
    
    def __init__(self, texflow_instance):
        """
        Initialize with reference to TeXFlow instance for tool access.
        
        Args:
            texflow_instance: Instance of TeXFlow with all original tools
        """
        self.texflow = texflow_instance
        self._printer_memory = {}  # Remember printer choices per session
        
    def execute(self, action: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an output operation action.
        
        Actions:
            - print: Send document to printer
            - export: Generate PDF from document
            - preview: Generate preview (future)
        """
        action_map = {
            "print": self._print_document,
            "export": self._export_document,
            "preview": self._preview_document
        }
        
        if action not in action_map:
            return {
                "error": f"Unknown output action: {action}",
                "available_actions": list(action_map.keys())
            }
        
        return action_map[action](params, context)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get operation capabilities and requirements."""
        return {
            "actions": {
                "print": {
                    "description": "Send document to printer",
                    "required_params": [],  # Very flexible - can use content, source, path, etc.
                    "optional_params": ["content", "source", "path", "document", "printer", "format"],
                    "auto_detects": ["format", "printer"]
                },
                "export": {
                    "description": "Export document to PDF",
                    "required_params": [],  # Flexible input
                    "optional_params": ["source", "content", "output_path", "format", "title"],
                    "supported_exports": ["pdf"]
                },
                "preview": {
                    "description": "Generate document preview",
                    "required_params": ["source"],
                    "optional_params": ["format"],
                    "status": "planned"
                }
            },
            "system_requirements": {
                "command": [
                    {
                        "name": "lp",
                        "required_for": ["print"],
                        "install_hint": "CUPS printing system required"
                    },
                    {
                        "name": "pandoc",
                        "required_for": ["export", "print"],
                        "install_hint": "Install pandoc for document conversion"
                    },
                    {
                        "name": "xelatex",
                        "required_for": ["export", "print"],
                        "install_hint": "Install TeX Live for LaTeX support",
                        "user_install": True
                    }
                ]
            },
            "optional_features": [
                {
                    "name": "pdf_optimization",
                    "description": "Optimize PDF file size",
                    "requirements": [
                        {"type": "command", "name": "gs"}
                    ]
                }
            ]
        }
    
    def _print_document(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Print a document with intelligent format detection and printer selection.
        
        Accepts multiple input formats:
        - content: Raw content to print
        - source: Path to source file (auto-detects format)
        - path: Alias for source
        - document: Document name from project
        """
        # Determine input source
        content = params.get("content")
        source = params.get("source") or params.get("path") or params.get("document")
        printer = params.get("printer")
        format_hint = params.get("format")
        
        # Handle printer selection intelligently
        if not printer:
            printer = self._get_printer_preference(context)
        else:
            # Remember this printer choice
            self._printer_memory["selected"] = printer
        
        try:
            # Route to appropriate print function
            if content:
                # Direct content printing
                return self._print_content(content, printer, format_hint)
            elif source:
                # File-based printing
                return self._print_file(source, printer, format_hint)
            else:
                return {
                    "error": "No input provided",
                    "hint": "Provide either 'content' or 'source' parameter"
                }
                
        except Exception as e:
            return {
                "error": str(e),
                "printer_attempted": printer,
                "hint": "Check printer status with printer(action='list')"
            }
    
    def _print_content(self, content: str, printer: Optional[str], format_hint: Optional[str]) -> Dict[str, Any]:
        """Print raw content."""
        # Detect format if not provided
        if not format_hint:
            format_hint = self._detect_content_format(content)
        
        # Route based on format
        if format_hint == "text":
            result = self.texflow.print_text(content, printer)
        elif format_hint == "markdown":
            result = self.texflow.print_markdown(content, printer=printer)
        elif format_hint == "latex":
            result = self.texflow.print_latex(content, printer=printer)
        else:
            # Default to text
            result = self.texflow.print_text(content, printer)
        
        return {
            "success": True,
            "action": "print",
            "format": format_hint,
            "printer": printer or "default",
            "content_length": len(content),
            "message": "Document sent to printer"
        }
    
    def _print_file(self, source: str, printer: Optional[str], format_hint: Optional[str]) -> Dict[str, Any]:
        """Print a file."""
        # Use unified output function for printing
        result_str = self.texflow.output(
            action="print",
            source=source,
            printer=printer
        )
        
        # Return formatted result
        if result_str.startswith("❌"):
            return {"error": result_str}
        else:
            return {"message": result_str, "source": source, "printer": printer or "default"}
    
    def _export_document(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Export document to PDF.
        
        Accepts:
        - source: Path to source file
        - content: Raw content
        - output_path: Where to save PDF
        """
        source = params.get("source") or params.get("path")
        content = params.get("content")
        output_path = params.get("output_path")
        title = params.get("title", "Document")
        format_hint = params.get("format")
        
        try:
            # Determine format
            if source and (not format_hint or format_hint == "auto"):
                format_hint = self._detect_file_format(source)
            elif content and (not format_hint or format_hint == "auto"):
                format_hint = self._detect_content_format(content)
            
            # Route to unified output function
            if format_hint in ["markdown", "latex"]:
                result_str = self.texflow.output(
                    action="export",
                    source=source,
                    content=content,
                    format=format_hint,
                    output_path=output_path
                )
                
                # The unified output function returns a string result
                if result_str.startswith("❌"):
                    return {"error": result_str}
                else:
                    return {"message": result_str, "path": output_path}
            else:
                return {
                    "error": f"Cannot export from format '{format_hint}' to PDF. Auto-detected format may be unsupported.",
                    "supported_formats": ["markdown", "latex"],
                    "hint": "Try specifying format='markdown' or format='latex' explicitly"
                }
            
            return {
                "success": True,
                "action": "export",
                "format": "pdf",
                "source_format": format_hint,
                "output": pdf_path,
                "message": f"Exported to PDF: {pdf_path}"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "format_attempted": format_hint
            }
    
    def _preview_document(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate document preview (future feature)."""
        return {
            "error": "Preview feature not yet implemented",
            "hint": "Use export(action='export') to generate PDF instead"
        }
    
    def _get_printer_preference(self, context: Dict[str, Any]) -> Optional[str]:
        """Get printer preference from memory or context."""
        # Check session memory first
        if "selected" in self._printer_memory:
            return self._printer_memory["selected"]
        
        # Check context for default
        if "default_printer" in context:
            return context["default_printer"]
        
        # Return None to use system default
        return None
    
    def _detect_content_format(self, content: str) -> str:
        """Detect format from content."""
        # Check for LaTeX
        latex_patterns = [r'\\documentclass', r'\\begin{', r'\\usepackage', r'\\section{']
        if any(re.search(pattern, content) for pattern in latex_patterns):
            return "latex"
        
        # Check for Markdown
        markdown_patterns = [r'^#+\s', r'^\*\s', r'^\d+\.\s', r'\[.*\]\(.*\)', r'```']
        if any(re.search(pattern, content, re.MULTILINE) for pattern in markdown_patterns):
            return "markdown"
        
        # Default to text
        return "text"
    
    def _detect_file_format(self, path: str) -> str:
        """Detect format from file extension."""
        path_lower = str(path).lower()
        
        if path_lower.endswith('.md'):
            return "markdown"
        elif path_lower.endswith('.tex'):
            return "latex"
        elif path_lower.endswith('.txt'):
            return "text"
        elif path_lower.endswith('.pdf'):
            return "pdf"
        else:
            # Try to read first few lines
            try:
                with open(path, 'r') as f:
                    sample = f.read(500)
                return self._detect_content_format(sample)
            except:
                return "unknown"
    
    def _extract_path_from_result(self, result: str) -> str:
        """Extract file path from tool result string."""
        patterns = [
            r'saved to:\s*(.+?)(?:\n|$)',
            r'created:\s*(.+?)(?:\n|$)',
            r'PDF saved to:\s*(.+?)(?:\n|$)',
            r'at:\s*(.+?)(?:\n|$)',
            r'(/[\w/.-]+\.pdf)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, result, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "output.pdf"