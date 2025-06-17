"""
Document Operation implementation for TeXFlow.

Bundles document-related tools into a unified semantic interface.
"""

from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
import re
import sys
import difflib
import base64
import io

# Import the resolve_path function and session context from the main texflow module
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
import texflow

# Import core services
from ...core.conversion_service import get_conversion_service
from ...core.validation_service import get_validation_service
from ...core.format_detector import get_format_detector


class DocumentOperation:
    """Handles all document-related operations with semantic understanding."""
    
    def __init__(self, texflow_instance):
        """
        Initialize with reference to TeXFlow instance for tool access.
        
        Args:
            texflow_instance: Instance of TeXFlow with all original tools
        """
        self.texflow = texflow_instance
        # Initialize core services
        self.conversion_service = get_conversion_service()
        self.validation_service = get_validation_service()
        self.format_detector = get_format_detector()
        # Simple fallback buffer - stores the last generated content
        self.last_generated_content = None
        
    def execute(self, action: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a document operation action.
        
        Actions:
            - create: Create a new document (auto-detects format)
            - read: Read document contents
            - edit: Edit existing document (with intelligent fallbacks and content buffering)
            - edit_from_buffer: Edit using previously buffered content with fuzzy matching
            - insert_at_line: Insert content at specific line number (uses buffer if no content provided)
            - convert: Convert between formats
            - validate: Validate document syntax
            - status: Check document modification status
            - inspect: Render PDF page to base64 PNG image for visual review
        """
        action_map = {
            "create": self._create_document,
            "read": self._read_document,
            "edit": self._edit_document,
            "edit_from_buffer": self._edit_from_buffer,
            "insert_at_line": self._insert_at_line,
            "convert": self._convert_document,
            "validate": self._validate_document,
            "status": self._check_status,
            "inspect": self._inspect_pdf_page
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
                    "description": "Edit existing document with intelligent fallbacks. Automatically buffers content when exact match fails and provides suggestions for recovery.",
                    "required_params": ["path", "old_string", "new_string"],
                    "optional_params": ["validate_after"],
                    "features": ["content_buffering", "fuzzy_matching", "intelligent_suggestions"]
                },
                "edit_from_buffer": {
                    "description": "Edit document using previously buffered content from failed edits. Uses fuzzy matching to find similar text when exact matches fail.",
                    "required_params": ["path"],
                    "optional_params": ["old_string", "new_string", "fuzzy_threshold"],
                    "notes": "Uses buffered content if new_string not provided. Ideal for recovering from failed edit attempts without regenerating content."
                },
                "insert_at_line": {
                    "description": "Insert content at a specific line number. Uses buffered content if no content provided.",
                    "required_params": ["path", "line_number"],
                    "optional_params": ["content", "mode"],
                    "modes": ["before", "after", "replace"],
                    "notes": "Fallback strategy when string-based edits fail. Uses buffered content to avoid regeneration."
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
            ],
            "workflow_guidance": {
                "edit_failure_recovery": {
                    "problem": "When edit action fails due to exact string match failure",
                    "solution": "Content is automatically buffered. Use edit_from_buffer or insert_at_line to recover without regenerating content.",
                    "workflow": [
                        "1. edit action fails → content automatically buffered",
                        "2. Use edit_from_buffer for fuzzy matching recovery",
                        "3. Use insert_at_line for precise line-based insertion",
                        "4. Both actions use buffered content to avoid regeneration waste"
                    ]
                },
                "content_buffering": {
                    "description": "System automatically stores last generated content when edits fail",
                    "benefits": ["Eliminates expensive content regeneration", "Enables recovery strategies", "Maintains context efficiency"],
                    "usage": "Buffer is automatically populated on edit failures. Access via edit_from_buffer or insert_at_line without content parameter."
                },
                "best_practices": {
                    "for_long_content": "Use edit action first. If it fails, use edit_from_buffer or insert_at_line with buffered content.",
                    "for_precise_placement": "Use insert_at_line when you know the exact location",
                    "for_similar_content": "Use edit_from_buffer with adjusted fuzzy_threshold for approximate matching"
                }
            }
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
        ext = ".tex" if format_type == "latex" else ".md"
        if not filename.endswith(ext):
            # Remove any existing extension and add the correct one
            base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
            filename = f"{base_name}{ext}"
        
        # Use resolve_path to determine the correct location
        try:
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
        """Edit existing document with intelligent fallback strategies."""
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
            
            # Read file content
            content = file_path.read_text()
            
            # Try exact match first
            if old_string in content:
                new_content = content.replace(old_string, new_string, 1)
                file_path.write_text(new_content)
                
                return {
                    "success": True,
                    "path": str(file_path),
                    "message": "Document edited successfully (exact match)",
                    "changes_applied": 1,
                    "strategy_used": "exact_match"
                }
            
            # Store the generated content for potential reuse
            self.last_generated_content = new_string
            
            # Try intelligent fallback strategies
            fallback_result = self._try_fallback_edit_strategies(
                content, old_string, new_string, file_path
            )
            
            if fallback_result["success"]:
                # Optionally validate after edit
                if validate_after:
                    format_type = self._detect_format_from_path(str(file_path))
                    if format_type == "latex":
                        validation_result = self.validation_service.validate(fallback_result["new_content"], "latex")
                        fallback_result["validation"] = validation_result
                
                return fallback_result
            
            # If all strategies fail, provide helpful suggestions
            suggestions = self._generate_edit_suggestions(content, old_string, new_string)
            
            return {
                "success": False,
                "error": f"String not found: '{old_string[:100]}{'...' if len(old_string) > 100 else ''}'",
                "path": str(file_path),
                "last_content_buffered": True,
                "suggestions": suggestions,
                "alternative_actions": [
                    f"document(action='edit_from_buffer', path='{path}') # Uses buffered content",
                    f"document(action='insert_at_line', path='{path}', line_number=<line>) # Uses buffered content", 
                    "Use document(action='read') to examine the file structure"
                ]
            }
            
        except Exception as e:
            return {"error": str(e), "path": path}
    
    def _convert_document(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Convert document between formats using core conversion service."""
        source = params.get("source")
        target_format = params.get("target_format", "latex")
        output_path = params.get("output_path")
        
        if not source:
            return {"error": "Source parameter is required"}
        
        try:
            # Resolve paths
            source_path = texflow.resolve_path(source)
            if output_path:
                output_path = texflow.resolve_path(output_path)
            
            # Use core conversion service
            result = self.conversion_service.convert(source_path, target_format, output_path)
            
            # Add semantic enhancements on success
            if result.get("success"):
                result["workflow"] = {
                    "message": f"Document converted to {target_format} successfully",
                    "next_steps": []
                }
                
                # Add format-specific suggestions
                if target_format == "latex":
                    result["workflow"]["next_steps"].extend([
                        {"action": "validate", "description": "Check LaTeX syntax before compiling"},
                        {"action": "export", "description": "Generate PDF from LaTeX"}
                    ])
                elif target_format == "pdf":
                    result["workflow"]["next_steps"].extend([
                        {"action": "inspect", "description": "Preview the generated PDF"},
                        {"action": "print", "description": "Send to printer"}
                    ])
                
            return result
                
        except Exception as e:
            return {"error": str(e)}
    
    def _validate_document(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate document syntax using core validation service."""
        content_or_path = params.get("content_or_path")
        format_type = params.get("format", "auto")
        
        if not content_or_path:
            return {"error": "content_or_path parameter is required"}
        
        try:
            # Use core validation service
            result = self.validation_service.validate(content_or_path, format_type)
            
            # Add semantic enhancements
            if result.get("success"):
                # Use the validation service's message which includes format info
                result["workflow"] = {
                    "message": result.get("message", "Validation completed"),
                    "next_steps": []
                }
                
                # Add appropriate next steps based on validation result
                if result.get("valid"):
                    result["workflow"]["next_steps"].append(
                        {"action": "export", "description": "Generate PDF from validated document"}
                    )
                else:
                    result["workflow"]["next_steps"].extend([
                        {"action": "edit", "description": "Fix the reported errors"},
                        {"action": "validate", "description": "Re-validate after fixing"}
                    ])
            else:
                result["workflow"] = {
                    "message": result.get("message", "Validation failed"),
                    "next_steps": [
                        {"action": "edit", "description": "Fix the reported errors"},
                        {"action": "read", "description": "Review the document content"}
                    ]
                }
            
            return result
                
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
        """Detect optimal format based on content and intent using core service."""
        result = self.format_detector.detect(content, intent)
        return result["format"]
    
    def _detect_format_from_path(self, path: str) -> str:
        """Detect format from file extension using core service."""
        return self.format_detector.detect_from_path(path)
    
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
    
    
    def _try_fallback_edit_strategies(self, content: str, old_string: str, new_string: str, file_path: Path) -> Dict[str, Any]:
        """Try intelligent fallback strategies when exact string match fails."""
        
        # Strategy 1: Fuzzy string matching
        lines = content.splitlines()
        best_match = None
        best_ratio = 0.6  # Minimum similarity threshold
        
        for i, line in enumerate(lines):
            ratio = difflib.SequenceMatcher(None, old_string.strip(), line.strip()).ratio()
            if ratio > best_ratio:
                best_match = (i, line, ratio)
                best_ratio = ratio
        
        if best_match:
            line_num, matched_line, ratio = best_match
            new_content = content.replace(matched_line, new_string, 1)
            file_path.write_text(new_content)
            
            return {
                "success": True,
                "path": str(file_path),
                "message": f"Document edited successfully using fuzzy match (similarity: {ratio:.2f})",
                "changes_applied": 1,
                "strategy_used": "fuzzy_match",
                "matched_line": matched_line,
                "line_number": line_num + 1,
                "new_content": new_content
            }
        
        # Strategy 2: Look for partial matches (key phrases)
        # Extract potential key phrases from the search string
        key_phrases = self._extract_key_phrases(old_string)
        
        for phrase in key_phrases:
            if phrase in content:
                # Found a key phrase - suggest line-based insertion instead
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    if phrase in line:
                        return {
                            "success": False,
                            "strategy_tried": "partial_match",
                            "found_phrase": phrase,
                            "suggestion": {
                                "line_number": i + 1,
                                "context": line.strip(),
                                "action": f"document(action='insert_at_line', path='{file_path.name}', line_number={i + 1})"
                            }
                        }
        
        return {"success": False}
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract meaningful phrases that might be found even if exact match fails."""
        # Remove LaTeX commands and extract meaningful content
        import re
        
        # Remove common LaTeX patterns
        cleaned = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', text)
        cleaned = re.sub(r'\\[a-zA-Z]+', '', cleaned)
        
        # Split into potential phrases
        phrases = []
        
        # Look for sentences or significant phrases
        sentences = re.split(r'[.!?]\s+', cleaned)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # Significant length
                phrases.append(sentence[:50])  # First 50 chars
        
        # Look for section headers or distinctive patterns
        header_match = re.search(r'(subsection|section|chapter)\{([^}]+)\}', text)
        if header_match:
            phrases.append(header_match.group(2))
        
        return [p for p in phrases if len(p) > 10]
    
    def _generate_edit_suggestions(self, content: str, old_string: str, new_string: str) -> Dict[str, Any]:
        """Generate helpful suggestions when edit fails."""
        lines = content.splitlines()
        suggestions = []
        
        # Look for similar content
        old_words = set(old_string.lower().split())
        
        for i, line in enumerate(lines):
            line_words = set(line.lower().split())
            common_words = old_words.intersection(line_words)
            
            if len(common_words) >= 2:  # At least 2 words in common
                suggestions.append({
                    "line_number": i + 1,
                    "content": line.strip(),
                    "common_words": len(common_words),
                    "similarity": len(common_words) / len(old_words) if old_words else 0
                })
        
        # Sort by similarity
        suggestions.sort(key=lambda x: x["similarity"], reverse=True)
        
        return {
            "total_lines": len(lines),
            "similar_lines": suggestions[:5],  # Top 5 matches
            "search_words": list(old_words),
            "recommendation": "Use document(action='read') to examine context, then try line-based insertion"
        }
    
    def _edit_from_buffer(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Edit using buffered content with fuzzy matching strategies."""
        path = params.get("path")
        old_string = params.get("old_string")
        new_string = params.get("new_string") or self.last_generated_content
        fuzzy_threshold = params.get("fuzzy_threshold", 0.7)
        
        if not path:
            return {"error": "Path parameter is required"}
        
        if not new_string:
            return {"error": "No new_string provided and no content in buffer"}
        
        try:
            file_path = texflow.resolve_path(path)
            if not file_path.exists():
                return {"error": f"File not found: {file_path}"}
            
            content = file_path.read_text()
            
            # If old_string provided, try exact match first
            if old_string and old_string in content:
                new_content = content.replace(old_string, new_string, 1)
                file_path.write_text(new_content)
                return {
                    "success": True,
                    "path": str(file_path),
                    "message": "Edit from buffer successful (exact match)",
                    "strategy_used": "exact_match"
                }
            
            # Try fuzzy matching with adjustable threshold
            lines = content.splitlines()
            best_match = None
            best_ratio = fuzzy_threshold
            
            search_text = old_string if old_string else new_string[:100]  # Use beginning of new content
            
            for i, line in enumerate(lines):
                ratio = difflib.SequenceMatcher(None, search_text.strip(), line.strip()).ratio()
                if ratio > best_ratio:
                    best_match = (i, line, ratio)
                    best_ratio = ratio
            
            if best_match:
                line_num, matched_line, ratio = best_match
                new_content = content.replace(matched_line, new_string, 1)
                file_path.write_text(new_content)
                
                return {
                    "success": True,
                    "path": str(file_path),
                    "message": f"Edit from buffer successful using fuzzy match (similarity: {ratio:.2f})",
                    "strategy_used": "fuzzy_match",
                    "matched_line": matched_line,
                    "line_number": line_num + 1
                }
            
            return {
                "success": False,
                "error": "No suitable match found for edit from buffer",
                "suggestion": "Try document(action='insert_at_line') instead"
            }
            
        except Exception as e:
            return {"error": str(e), "path": path}
    
    def _insert_at_line(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Insert content at a specific line number."""
        path = params.get("path")
        line_number = params.get("line_number")
        content_to_insert = params.get("content") or self.last_generated_content
        insert_mode = params.get("mode", "after")  # "before", "after", "replace"
        
        if not path:
            return {"error": "Path parameter is required"}
        
        if line_number is None:
            return {"error": "line_number parameter is required"}
        
        if not content_to_insert:
            return {"error": "No content provided and no content in buffer"}
        
        try:
            file_path = texflow.resolve_path(path)
            if not file_path.exists():
                return {"error": f"File not found: {file_path}"}
            
            content = file_path.read_text()
            lines = content.splitlines()
            
            # Convert to 0-based indexing
            line_index = int(line_number) - 1
            
            if line_index < 0 or line_index > len(lines):
                return {"error": f"Line number {line_number} is out of range (1-{len(lines)})"}
            
            # Perform insertion based on mode
            if insert_mode == "before":
                lines.insert(line_index, content_to_insert)
            elif insert_mode == "after":
                lines.insert(line_index + 1, content_to_insert)
            elif insert_mode == "replace":
                if line_index < len(lines):
                    lines[line_index] = content_to_insert
                else:
                    lines.append(content_to_insert)
            
            new_content = "\n".join(lines)
            file_path.write_text(new_content)
            
            return {
                "success": True,
                "path": str(file_path),
                "message": f"Content inserted at line {line_number} ({insert_mode} mode)",
                "line_number": line_number,
                "insert_mode": insert_mode,
                "content_length": len(content_to_insert)
            }
            
        except Exception as e:
            return {"error": str(e), "path": path}
    
    def _inspect_pdf_page(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inspect a PDF page by rendering to base64 PNG image for visual review.
        
        Args:
            path: Path to PDF file
            page: Page number to render (1-indexed)
            dpi: DPI for rendering (default: 120)
            
        Returns:
            Dict with base64 PNG image data or error
        """
        path = params.get("path", "")
        page = params.get("page", 1)
        dpi = params.get("dpi", 120)
        
        if not path:
            return {"error": "PDF path is required"}
        
        try:
            # Resolve path using texflow's project-aware resolution
            pdf_path = texflow.resolve_path(path)
            
            if not pdf_path.exists():
                return {"error": f"PDF file not found: {pdf_path}"}
            
            if not str(pdf_path).lower().endswith('.pdf'):
                return {"error": f"File is not a PDF: {pdf_path}"}
            
            # Check if pdf2image is available
            try:
                from pdf2image import convert_from_path
                from PIL import Image
            except ImportError:
                return {
                    "error": "PDF rendering requires pdf2image and Pillow libraries",
                    "system_check": "Install with: pip install pdf2image pillow",
                    "dependencies": ["pdf2image", "pillow", "poppler-utils"]
                }
            
            # Convert specified page to image
            try:
                images = convert_from_path(
                    str(pdf_path),
                    dpi=dpi,
                    first_page=page,
                    last_page=page
                )
                
                if not images:
                    return {"error": f"Could not render page {page} from PDF"}
                
                # Convert PIL Image to base64 PNG
                image = images[0]
                buffer = io.BytesIO()
                image.save(buffer, format='PNG')
                buffer.seek(0)
                
                base64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                return {
                    "success": True,
                    "action": "inspect",
                    "pdf_path": str(pdf_path),
                    "page": page,
                    "dpi": dpi,
                    "image": {
                        "mimeType": "image/png",
                        "base64": base64_data,
                        "width": image.width,
                        "height": image.height
                    },
                    "message": f"Rendered page {page} of {pdf_path.name} at {dpi} DPI"
                }
                
            except Exception as e:
                return {
                    "error": f"Failed to render PDF page: {str(e)}",
                    "hint": "Ensure PDF is valid and page number exists"
                }
                
        except Exception as e:
            return {"error": f"PDF rendering error: {str(e)}"}