"""
Document Operation implementation for TeXFlow.

Bundles document-related tools into a unified semantic interface.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import re
import sys

# Import the resolve_path function and session context from the main texflow module
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
import texflow


class DocumentOperation:
    """Handles all document-related operations with semantic understanding."""
    
    def __init__(self, texflow_instance):
        """
        Initialize with reference to TeXFlow instance for tool access.
        
        Args:
            texflow_instance: Instance of TeXFlow with all original tools
        """
        self.texflow = texflow_instance
        
    def execute(self, action: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a document operation action.
        
        Actions:
            - create: Create a new document (auto-detects format)
            - read: Read document contents
            - edit: Edit existing document
            - convert: Convert between formats
            - validate: Validate document syntax
            - status: Check document modification status
        """
        action_map = {
            "create": self._create_document,
            "read": self._read_document,
            "edit": self._edit_document,
            "convert": self._convert_document,
            "validate": self._validate_document,
            "status": self._check_status
        }
        
        if action not in action_map:
            return {
                "error": f"Unknown document action: {action}",
                "available_actions": list(action_map.keys())
            }
        
        return action_map[action](params, context)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get operation capabilities and requirements."""
        return {
            "actions": {
                "create": {
                    "description": "Create a new document",
                    "required_params": ["content"],
                    "optional_params": ["format", "filename", "intent"],
                    "formats": ["markdown", "latex", "auto"]
                },
                "read": {
                    "description": "Read document contents",
                    "required_params": ["path"],
                    "optional_params": ["offset", "limit"]
                },
                "edit": {
                    "description": "Edit existing document",
                    "required_params": ["path", "changes"],
                    "optional_params": ["validate_after"]
                },
                "convert": {
                    "description": "Convert between formats",
                    "required_params": ["source"],
                    "optional_params": ["target_format", "output_path"]
                },
                "validate": {
                    "description": "Validate document syntax",
                    "required_params": ["content_or_path"],
                    "optional_params": ["format"]
                },
                "status": {
                    "description": "Check document modification status",
                    "required_params": ["path"]
                }
            },
            "system_requirements": {
                "command": [
                    {
                        "name": "pandoc",
                        "required_for": ["convert"],
                        "install_hint": "Install pandoc for format conversion"
                    },
                    {
                        "name": "xelatex",
                        "required_for": ["validate"],
                        "install_hint": "Install TeX Live for LaTeX support",
                        "user_install": True
                    }
                ],
                "tex_package": [
                    {
                        "name": "fontspec",
                        "required_for": ["validate", "convert"],
                        "install_hint": "Install fontspec package for XeLaTeX"
                    }
                ]
            },
            "optional_features": [
                {
                    "name": "syntax_highlighting",
                    "description": "Code syntax highlighting in documents",
                    "requirements": [
                        {"type": "command", "name": "pygmentize"}
                    ]
                }
            ]
        }
    
    def _create_document(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new document with format auto-detection."""
        content = params.get("content", "")
        format_type = params.get("format", "auto")
        filename = params.get("filename")
        intent = params.get("intent", "")
        
        # Auto-detect format if needed
        if format_type == "auto":
            format_type = self._detect_format(content, intent)
        
        # Generate filename if not provided
        if not filename:
            filename = self._generate_filename(content, format_type)
        
        # Ensure correct extension
        if not filename.endswith(f".{format_type[:3]}"):
            filename = f"{filename}.{format_type[:3]}"
        
        # Use resolve_path to determine the correct location
        try:
            # Determine file extension
            ext = ".tex" if format_type == "latex" else ".md"
            
            # Create file path using intelligent resolution
            file_path = texflow.resolve_path(filename, "document", ext)
            
            # Write content
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            
            return {
                "success": True,
                "path": str(file_path),
                "format": format_type,
                "message": f"Document created: {file_path}",
                "size": len(content),
                "intent_detected": intent or "general document"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "format_attempted": format_type,
                "filename_attempted": filename
            }
    
    def _read_document(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Read document contents."""
        path = params.get("path")
        offset = params.get("offset", 1)
        limit = params.get("limit", 50)
        
        if not path:
            return {"error": "Path parameter is required"}
        
        try:
            # Use resolve_path to get the correct path considering project context
            file_path = texflow.resolve_path(path)
            
            if not file_path.exists():
                return {"error": f"File not found: {file_path}"}
            
            # Read file contents
            content = file_path.read_text()
            lines = content.splitlines()
            
            # Apply offset and limit
            start_line = max(0, offset - 1)  # Convert to 0-based indexing
            end_line = start_line + limit if limit else len(lines)
            selected_lines = lines[start_line:end_line]
            
            # Format with line numbers like the original
            formatted_lines = []
            for i, line in enumerate(selected_lines, start=offset):
                formatted_lines.append(f"{i:4d}\t{line}")
            
            result_content = "\n".join(formatted_lines)
            if len(lines) > end_line:
                result_content += f"\n... ({len(lines)} total lines)"
            
            # Detect format from extension
            format_type = self._detect_format_from_path(str(file_path))
            
            return {
                "success": True,
                "content": result_content,
                "path": str(file_path),
                "format": format_type,
                "lines_read": len(selected_lines),
                "offset": offset,
                "limit": limit,
                "total_lines": len(lines)
            }
            
        except Exception as e:
            return {"error": str(e), "path": path}
    
    def _edit_document(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Edit existing document."""
        path = params.get("path")
        old_string = params.get("old_string")
        new_string = params.get("new_string")
        validate_after = params.get("validate_after", False)
        
        if not path:
            return {"error": "Path parameter is required"}
        
        if not old_string or not new_string:
            return {"error": "old_string and new_string parameters are required"}
        
        try:
            # Use resolve_path to get the correct path considering project context
            file_path = texflow.resolve_path(path)
            
            if not file_path.exists():
                return {"error": f"File not found: {file_path}"}
            
            # Read and edit file
            content = file_path.read_text()
            if old_string not in content:
                return {"error": f"String '{old_string}' not found in file"}
            
            new_content = content.replace(old_string, new_string, 1)
            file_path.write_text(new_content)
            
            response = {
                "success": True,
                "path": str(file_path),
                "message": "Document edited successfully",
                "changes_applied": 1
            }
            
            # Optionally validate after edit
            if validate_after:
                format_type = self._detect_format_from_path(str(file_path))
                if format_type == "latex":
                    # Read content for validation
                    validation_result = self._validate_latex_content(new_content)
                    response["validation"] = validation_result
            
            return response
            
        except Exception as e:
            return {"error": str(e), "path": path}
    
    def _convert_document(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Convert document between formats."""
        source = params.get("source")
        target_format = params.get("target_format", "latex")
        output_path = params.get("output_path")
        
        if not source:
            return {"error": "Source parameter is required"}
        
        # Detect source format
        source_format = self._detect_format_from_path(source)
        
        if source_format == target_format:
            return {"error": f"Source and target formats are the same: {source_format}"}
        
        try:
            # Currently only markdown to latex is supported
            if source_format == "markdown" and target_format == "latex":
                import subprocess
                
                source_path = texflow.resolve_path(source)
                if not source_path.exists():
                    return {"error": f"Source file not found: {source_path}"}
                
                # Generate output path if not provided
                if not output_path:
                    output_file = source_path.with_suffix(".tex")
                else:
                    output_file = texflow.resolve_path(output_path)
                
                # Convert using pandoc
                try:
                    subprocess.run(
                        ["pandoc", "-f", "markdown", "-t", "latex", "-o", str(output_file), str(source_path)], 
                        check=True
                    )
                    
                    return {
                        "success": True,
                        "source": str(source_path),
                        "source_format": source_format,
                        "target_format": target_format,
                        "output": str(output_file),
                        "message": f"Converted to {target_format}: {output_file}"
                    }
                except subprocess.CalledProcessError as e:
                    return {"error": f"Conversion failed: {e}"}
                except FileNotFoundError:
                    return {"error": "pandoc not found - install pandoc for format conversion"}
            else:
                return {
                    "error": f"Conversion from {source_format} to {target_format} not supported",
                    "supported_conversions": ["markdown -> latex"]
                }
                
        except Exception as e:
            return {"error": str(e), "source": source}
    
    def _validate_document(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate document syntax."""
        content_or_path = params.get("content_or_path")
        format_type = params.get("format")
        
        if not content_or_path:
            return {"error": "content_or_path parameter is required"}
        
        try:
            # Determine if it's a path or content
            potential_path = texflow.resolve_path(content_or_path) if content_or_path else None
            
            if potential_path and potential_path.exists():
                # It's a path - read the content
                content = potential_path.read_text()
                if not format_type:
                    format_type = self._detect_format_from_path(str(potential_path))
                source = str(potential_path)
            else:
                # It's content
                content = content_or_path
                if not format_type:
                    format_type = self._detect_format(content, "")
                source = "inline content"
            
            # Currently only LaTeX validation is supported
            if format_type == "latex":
                validation_result = self._validate_latex_content(content)
                
                return {
                    "success": True,
                    "valid": validation_result.get("valid", False),
                    "format": format_type,
                    "source": source,
                    "validation_report": validation_result.get("message", "Unknown validation result")
                }
            else:
                return {
                    "success": True,
                    "valid": True,
                    "format": format_type,
                    "message": f"No validation available for {format_type} format"
                }
                
        except Exception as e:
            return {"error": str(e)}
    
    def _check_status(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Check document modification status."""
        path = params.get("path")
        
        if not path:
            return {"error": "Path parameter is required"}
        
        try:
            # Use resolve_path to get the correct path considering project context
            file_path = texflow.resolve_path(path)
            
            if not file_path.exists():
                return {"error": f"File not found: {file_path}"}
            
            # Get file status information
            from datetime import datetime
            stat = file_path.stat()
            modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            size = stat.st_size
            
            status_report = f"File: {file_path}\nModified: {modified}\nSize: {size} bytes"
            
            return {
                "success": True,
                "path": str(file_path),
                "has_external_changes": False,  # We can't easily detect this without more complex tracking
                "status_report": status_report,
                "format": self._detect_format_from_path(str(file_path)),
                "modified": modified,
                "size": size
            }
            
        except Exception as e:
            return {"error": str(e), "path": path}
    
    def _detect_format(self, content: str, intent: str) -> str:
        """Detect optimal format based on content and intent."""
        # Check intent first
        intent_lower = intent.lower()
        if any(word in intent_lower for word in ['paper', 'thesis', 'article', 'academic', 'scientific']):
            return "latex"
        
        # Check for LaTeX indicators
        latex_indicators = [
            r'\\begin{', r'\\end{', r'\\documentclass', 
            r'\\usepackage', '\\\\', r'\\cite{', r'\\ref{',
            r'\\section{', r'\\chapter{', r'\\subsection{'
        ]
        
        if any(indicator in content for indicator in latex_indicators):
            return "latex"
        
        # Check for math content
        math_indicators = [
            r'\\int', r'\\sum', r'\\frac{', r'\\sqrt{',
            '$$', r'\\[', r'\\]', r'\\(', r'\\)'
        ]
        
        if any(indicator in content for indicator in math_indicators):
            return "latex"
        
        # Check for complex needs in content
        if any(word in content.lower() for word in ['equation', 'theorem', 'proof', 'citation', 'bibliography']):
            return "latex"
        
        # Default to markdown for simplicity
        return "markdown"
    
    def _detect_format_from_path(self, path: str) -> str:
        """Detect format from file extension."""
        path_str = str(path).lower()
        if path_str.endswith('.tex'):
            return "latex"
        elif path_str.endswith('.md'):
            return "markdown"
        elif path_str.endswith('.txt'):
            return "text"
        else:
            # Try to read and detect
            return "unknown"
    
    def _generate_filename(self, content: str, format_type: str) -> str:
        """Generate a filename based on content."""
        # Extract first meaningful line
        lines = content.strip().split('\n')
        first_line = ""
        
        for line in lines:
            # Skip LaTeX commands
            if line.strip() and not line.strip().startswith('\\'):
                first_line = line.strip()
                break
        
        if not first_line:
            first_line = "untitled"
        
        # Clean up for filename
        # Remove markdown headers
        first_line = re.sub(r'^#+\s*', '', first_line)
        # Remove special characters
        first_line = re.sub(r'[^\w\s-]', '', first_line)
        # Convert to snake_case
        filename = '_'.join(first_line.lower().split())[:50]
        
        if not filename:
            filename = "document"
        
        return filename
    
    def _extract_path_from_result(self, result: str) -> str:
        """Extract file path from tool result string."""
        # Look for patterns like "saved to: /path/to/file"
        import re
        patterns = [
            r'saved to:\s*(.+?)(?:\n|$)',
            r'created:\s*(.+?)(?:\n|$)',
            r'at:\s*(.+?)(?:\n|$)',
            r'(/[\w/.-]+\.(?:md|tex|pdf))'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, result, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Fallback - return the result itself if it looks like a path
        if '/' in result and len(result) < 200:
            return result.strip()
        
        return "unknown"
    
    def _validate_latex_content(self, content: str) -> Dict[str, Any]:
        """Validate LaTeX content and return structured result."""
        import subprocess
        import tempfile
        
        try:
            # Create a temporary file for validation
            with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as temp_file:
                temp_file.write(content)
                temp_path = Path(temp_file.name)
            
            try:
                # Try test compilation
                result = subprocess.run(
                    ["xelatex", "-interaction=nonstopmode", "-halt-on-error", str(temp_path)],
                    cwd=temp_path.parent,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    return {
                        "valid": True,
                        "message": "LaTeX validation passed"
                    }
                else:
                    # Extract error from output
                    error_lines = []
                    for line in result.stdout.split('\n'):
                        if line.startswith('!'):
                            error_lines.append(line)
                    
                    error_msg = "\n".join(error_lines[:3]) if error_lines else "Compilation failed"
                    return {
                        "valid": False,
                        "message": f"LaTeX validation failed: {error_msg}"
                    }
            finally:
                # Clean up temporary files
                temp_path.unlink(missing_ok=True)
                # Also try to clean up generated files
                for ext in ['.aux', '.log', '.pdf']:
                    temp_path.with_suffix(ext).unlink(missing_ok=True)
                    
        except FileNotFoundError:
            return {
                "valid": False,
                "message": "XeLaTeX not found - cannot validate compilation"
            }
        except Exception as e:
            return {
                "valid": False,
                "message": f"Validation error: {str(e)}"
            }