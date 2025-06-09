"""
Document Operation implementation for TeXFlow.

Bundles document-related tools into a unified semantic interface.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import re


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
        
        # Use original tools based on format
        try:
            if format_type == "markdown":
                result = self.texflow.save_markdown(content, filename)
            elif format_type == "latex":
                result = self.texflow.save_latex(content, filename)
            else:
                return {"error": f"Unsupported format: {format_type}"}
            
            # Parse result and add metadata
            path = self._extract_path_from_result(result)
            return {
                "success": True,
                "path": path,
                "format": format_type,
                "message": f"Document created: {path}",
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
            result = self.texflow.read_document(path, offset, limit)
            
            # Detect format from extension
            format_type = self._detect_format_from_path(path)
            
            return {
                "success": True,
                "content": result,
                "path": path,
                "format": format_type,
                "lines_read": result.count('\n'),
                "offset": offset,
                "limit": limit
            }
            
        except Exception as e:
            return {"error": str(e), "path": path}
    
    def _edit_document(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Edit existing document."""
        path = params.get("path")
        changes = params.get("changes", [])
        validate_after = params.get("validate_after", False)
        
        if not path:
            return {"error": "Path parameter is required"}
        
        if not changes:
            return {"error": "Changes parameter is required"}
        
        try:
            # Handle different change formats
            if isinstance(changes, list):
                # Multiple changes
                for change in changes:
                    old_string = change.get("old")
                    new_string = change.get("new")
                    expected = change.get("expected_replacements", 1)
                    
                    result = self.texflow.edit_document(
                        path, old_string, new_string, expected
                    )
            else:
                # Single change
                result = self.texflow.edit_document(
                    path, 
                    changes.get("old"), 
                    changes.get("new"),
                    changes.get("expected_replacements", 1)
                )
            
            response = {
                "success": True,
                "path": path,
                "message": "Document edited successfully",
                "changes_applied": len(changes) if isinstance(changes, list) else 1
            }
            
            # Optionally validate after edit
            if validate_after:
                format_type = self._detect_format_from_path(path)
                if format_type == "latex":
                    # Read content for validation
                    content = self.texflow.read_document(path)
                    validation = self.texflow.validate_latex(content)
                    response["validation"] = validation
            
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
                result = self.texflow.markdown_to_latex(
                    source,
                    output_path,
                    title=params.get("title", "Document"),
                    standalone=params.get("standalone", True)
                )
                
                # Extract output path from result
                output_file = self._extract_path_from_result(result)
                
                return {
                    "success": True,
                    "source": source,
                    "source_format": source_format,
                    "target_format": target_format,
                    "output": output_file,
                    "message": f"Converted to {target_format}: {output_file}"
                }
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
            if Path(content_or_path).exists():
                # It's a path - read the content
                content = self.texflow.read_document(content_or_path)
                if not format_type:
                    format_type = self._detect_format_from_path(content_or_path)
                source = content_or_path
            else:
                # It's content
                content = content_or_path
                if not format_type:
                    format_type = self._detect_format(content, "")
                source = "inline content"
            
            # Currently only LaTeX validation is supported
            if format_type == "latex":
                result = self.texflow.validate_latex(content)
                
                # Parse validation result
                is_valid = "valid" in result.lower() or "success" in result.lower()
                
                return {
                    "success": True,
                    "valid": is_valid,
                    "format": format_type,
                    "source": source,
                    "validation_report": result
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
            result = self.texflow.check_document_status(path)
            
            # Parse result to extract status info
            has_changes = "modified" in result.lower() or "changed" in result.lower()
            
            return {
                "success": True,
                "path": path,
                "has_external_changes": has_changes,
                "status_report": result,
                "format": self._detect_format_from_path(path)
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