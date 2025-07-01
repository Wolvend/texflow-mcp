"""
Semantic Router for TeXFlow

Routes high-level semantic operations to appropriate handlers
and manages workflow suggestions.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from importlib import resources
except ImportError:
    # Fallback for Python < 3.9
    import importlib_resources as resources


class SemanticRouter:
    """Routes semantic operations to appropriate handlers with workflow awareness."""
    
    def __init__(self, config_dir: Path = None):
        self.config_dir = config_dir
        self.workflows = self._load_workflows()
        self.personalities = self._load_personalities()
        self.operation_handlers = {}
        self.current_context = {}
        
    def _load_config_file(self, filename: str, default: Dict[str, Any]) -> Dict[str, Any]:
        """Load a configuration file from various possible locations."""
        if self.config_dir:
            # Use provided directory
            config_path = self.config_dir / filename
            if config_path.exists():
                with open(config_path, 'r') as f:
                    return json.load(f)
            return default
        
        # Try multiple approaches to find the config file
        content = None
        
        # 1. Try relative to current file (development mode)
        dev_path = Path(__file__).parent.parent.parent / "config" / filename
        if dev_path.exists():
            with open(dev_path, 'r') as f:
                content = f.read()
        
        # 2. Try using importlib.resources (installed package)
        if not content:
            try:
                if hasattr(resources, 'files'):
                    # Python 3.9+
                    files = resources.files('config')
                    content = files.joinpath(filename).read_text()
                else:
                    # Older Python
                    content = resources.read_text('config', filename)
            except Exception:
                pass
        
        # 3. Try relative to package installation
        if not content:
            pkg_path = Path(__file__).parent.parent / "config" / filename
            if pkg_path.exists():
                with open(pkg_path, 'r') as f:
                    content = f.read()
        
        # 4. Try environment variable override
        if not content and os.getenv('TEXFLOW_CONFIG_DIR'):
            env_path = Path(os.getenv('TEXFLOW_CONFIG_DIR')) / filename
            if env_path.exists():
                with open(env_path, 'r') as f:
                    content = f.read()
        
        if content:
            return json.loads(content)
        else:
            return default
    
    def _load_workflows(self) -> Dict[str, Any]:
        """Load workflow hints from configuration."""
        return self._load_config_file("workflows.json", {"workflow_hints": {}, "format_escalation": {}})
    
    def _load_personalities(self) -> Dict[str, Any]:
        """Load personality definitions."""
        return self._load_config_file("personalities.json", {})
    
    def register_operation(self, name: str, handler: Any) -> None:
        """Register an operation handler."""
        self.operation_handlers[name] = handler
    
    def route(self, operation: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route a semantic operation to its handler.
        
        Args:
            operation: The semantic operation (document, output, project, etc.)
            action: The action within the operation (create, edit, print, etc.)
            params: Parameters for the operation
            
        Returns:
            Result dictionary with operation result and workflow hints
        """
        # Check if operation is registered
        if operation not in self.operation_handlers:
            return {
                "error": f"Unknown operation: {operation}",
                "available_operations": list(self.operation_handlers.keys())
            }
        
        # Get handler
        handler = self.operation_handlers[operation]
        
        # Pre-process based on operation type
        params = self._preprocess_params(operation, action, params)
        
        try:
            # Add project context from texflow SESSION_CONTEXT
            import texflow
            context = self.current_context.copy()
            context["project"] = texflow.SESSION_CONTEXT.get("current_project")
            context["workspace_root"] = texflow.SESSION_CONTEXT.get("workspace_root")
            
            # Execute operation
            result = handler.execute(action, params, context)
            
            # Post-process result
            result = self._postprocess_result(operation, action, result)
            
            # Add workflow hints
            result = self._add_workflow_hints(operation, action, result, params)
            
            # Update context for future operations
            self._update_context(operation, action, result)
            
            return result
            
        except Exception as e:
            return {
                "error": str(e),
                "operation": operation,
                "action": action,
                "hint": self._get_error_hint(operation, action, str(e))
            }
    
    def _preprocess_params(self, operation: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Pre-process parameters based on operation type."""
        # Auto-detect format for document operations
        if operation == "document" and action == "create":
            if "format" not in params or params["format"] == "auto":
                params["format"] = self._detect_format(params.get("content", ""))
            
            # Mark if creating outside a project for warning later
            if not self.current_context.get("project"):
                params["_outside_project"] = True
        
        # Add current project context if available
        if "project" in self.current_context and "path" not in params:
            params["_project_context"] = self.current_context["project"]
        
        return params
    
    def _detect_format(self, content: str) -> str:
        """Detect optimal format based on content analysis."""
        # Check for LaTeX indicators
        latex_indicators = [
            r'\begin{', r'\end{', r'\documentclass', 
            r'\usepackage', '\\\\', r'\cite{', r'\ref{'
        ]
        
        # Check for math indicators
        math_indicators = [
            r'\int', r'\sum', r'\frac{', r'\sqrt{',
            '$$', r'\[', r'\]'
        ]
        
        content_lower = content.lower()
        
        # Strong LaTeX indicators
        if any(indicator in content for indicator in latex_indicators):
            return "latex"
        
        # Math content suggests LaTeX
        if any(indicator in content for indicator in math_indicators):
            return "latex"
        
        # Complex formatting needs
        if any(word in content_lower for word in ['equation', 'theorem', 'proof', 'citation']):
            return "latex"
        
        # Default to markdown for simplicity
        return "markdown"
    
    def _postprocess_result(self, operation: str, action: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process operation results."""
        # Ensure consistent result structure
        if "success" not in result:
            result["success"] = "error" not in result
        
        # Add operation metadata
        result["_metadata"] = {
            "operation": operation,
            "action": action,
            "timestamp": self._get_timestamp()
        }
        
        return result
    
    def _add_workflow_hints(self, operation: str, action: str, result: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Add contextual workflow hints based on operation completion."""
        # Only add hints on success
        if not result.get("success", False):
            return result
        
        # Build workflow key
        workflow_key = f"{operation}_{action}_completed"
        
        # Check for specific workflow hints
        if workflow_key in self.workflows.get("workflow_hints", {}):
            hints = self.workflows["workflow_hints"][workflow_key]
            result["workflow"] = {
                "message": hints.get("message", ""),
                "suggested_next": self._format_suggestions(hints.get("next_steps", []))
            }
        
        # Check for format escalation hints
        if operation == "document" and "format" in result:
            # Add LaTeX-specific workflow hints
            if result["format"] == "latex" and action in ["create", "edit"]:
                result["workflow"] = {
                    "message": "LaTeX document saved successfully",
                    "suggested_next": [
                        {
                            "description": "Validate LaTeX syntax before compiling",
                            "command": f"document(action='validate', path='{result.get('path', 'document.tex')}')"
                        },
                        {
                            "description": "Export to PDF (don't use format='pdf')",
                            "command": f"output(action='export', source='{result.get('path', 'document.tex')}', output_path='output/document.pdf')",
                            "note": "The 'format' parameter is for source format only. Output format is determined by file extension."
                        }
                    ]
                }
            if result["format"] == "markdown":
                # Check if content might benefit from LaTeX
                triggers = self._check_format_triggers(result.get("content", ""))
                if triggers:
                    result["format_suggestion"] = self._get_format_escalation(triggers)
        
        # Add token efficiency hints for existing documents
        if operation == "document" and action in ["read", "status"]:
            result["efficiency_hint"] = {
                "message": "Document exists - use edit operations for changes",
                "important": "Avoid regenerating documents unless: corrupted, unreadable, needs complete rewrite, or user specifically requests it",
                "next_steps": [
                    {
                        "operation": "document",
                        "action": "edit",
                        "description": "Make specific changes to this document",
                        "command": "document(action='edit', path='...', changes=[...])"
                    }
                ]
            }
        
        # Add conversion hint when format change is needed
        if operation == "document" and action == "create" and result.get("format") == "markdown":
            if any(trigger in str(params.get("intent", "")).lower() 
                   for trigger in ["latex", "academic", "paper", "thesis"]):
                result["conversion_hint"] = {
                    "message": "Need LaTeX features? Convert your Markdown instead of rewriting",
                    "command": "document(action='convert', source='file.md', target_format='latex')"
                }
        
        # Hint to inspect after PDF export
        if operation == "output" and action == "export" and result.get("success"):
            if result.get("path") and str(result["path"]).endswith('.pdf'):
                result["workflow"] = {
                    "message": "PDF created successfully",
                    "suggested_next": [
                        {"description": "Preview the rendered output", "command": "document(action='inspect', path='filename.pdf', page=1)"},
                        {"description": "Send to printer", "command": "output(action='print', source='filename.pdf')"}
                    ]
                }
        
        # Hint after successful PDF inspection
        if operation == "document" and action == "inspect" and result.get("success"):
            result["workflow"] = {
                "message": "PDF page inspection complete",
                "suggested_next": [
                    {"description": "Print this document", "command": "output(action='print', source='filename.pdf')"},
                    {"description": "View next page", "command": "document(action='inspect', path='filename.pdf', page=2)"}
                ]
            }
        
        # Add reference hints for validation errors
        if operation == "document" and action == "validate" and not result.get("success"):
            if "error" in result:
                result["workflow"] = {
                    "message": "Validation failed - check the reference for help",
                    "suggested_next": [
                        {"description": "Get help for this error", "command": f"reference(action='error_help', error='{result['error'][:100]}...')"},
                        {"description": "Search for related commands", "command": "reference(action='search', query='command_name')"}
                    ]
                }
        
        # Hint when creating LaTeX documents
        if operation == "document" and action == "create" and result.get("format") == "latex":
            if "workflow" in result:
                result["workflow"]["suggested_next"].append({
                    "description": "Get LaTeX help and examples",
                    "command": "reference(action='search', query='topic')"
                })
        
        # Add warning for documents created outside projects
        if operation == "document" and action == "create" and params.get("_outside_project"):
            if result.get("path"):
                # Extract directory from path
                import os
                from pathlib import Path
                doc_path = Path(result["path"])
                doc_dir = doc_path.parent
                
                # Get relative path from workspace root for cleaner display
                workspace_root = Path(os.environ.get("TEXFLOW_WORKSPACE", Path.home() / "Documents" / "TeXFlow"))
                try:
                    relative_dir = doc_dir.relative_to(workspace_root)
                    dir_name = str(relative_dir) if str(relative_dir) != "." else workspace_root.name
                except ValueError:
                    # Path is outside workspace
                    dir_name = doc_dir.name
                
                # Suggest a project name based on the directory
                suggested_name = dir_name.replace("/", "-").replace(" ", "-").lower()
                
                result["project_hint"] = {
                    "message": f"⚠️  Document created in {doc_dir}",
                    "important": "To organize this document, import its directory as a project",
                    "next_steps": [
                        {
                            "operation": "project",
                            "action": "import", 
                            "description": f"Import '{dir_name}' as a TeXFlow project",
                            "command": f"project(action='import', name='{suggested_name}')"
                        },
                        {
                            "operation": "project",
                            "action": "create",
                            "description": "Or create a new project in a different location",
                            "command": "project(action='create', name='my-project')"
                        }
                    ]
                }
        
        return result
    
    def _format_suggestions(self, suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format workflow suggestions for clear presentation."""
        formatted = []
        for suggestion in suggestions:
            formatted.append({
                "operation": suggestion["operation"],
                "action": suggestion["action"],
                "description": suggestion["hint"],
                "example": suggestion.get("example", ""),
                "command": f"{suggestion['operation']}(action='{suggestion['action']}')"
            })
        return formatted
    
    def _check_format_triggers(self, content: str) -> List[str]:
        """Check for content that might benefit from LaTeX."""
        triggers = []
        
        trigger_patterns = {
            "equation": ["equation", "formula", "integral", "derivative"],
            "citation": ["cite", "reference", "bibliography"],
            "complex_table": ["\\begin{tabular}", "multicolumn"],
            "precise_layout": ["precise positioning", "exact margins"]
        }
        
        content_lower = content.lower()
        for trigger_type, patterns in trigger_patterns.items():
            if any(pattern in content_lower for pattern in patterns):
                triggers.append(trigger_type)
        
        return triggers
    
    def _get_format_escalation(self, triggers: List[str]) -> Dict[str, Any]:
        """Get format escalation suggestions."""
        escalation = self.workflows.get("format_escalation", {}).get("markdown_limitations_hit", {})
        return {
            "triggers": triggers,
            "message": escalation.get("message", "Consider using LaTeX for advanced features"),
            "suggestions": escalation.get("next_steps", [])
        }
    
    def _update_context(self, operation: str, action: str, result: Dict[str, Any]) -> None:
        """Update context based on operation results."""
        if not result.get("success", False):
            return
        
        # Update project context
        if operation == "project":
            if action == "create" or action == "switch":
                self.current_context["project"] = result.get("project_name", "")
            elif action == "info":
                self.current_context["project_info"] = result
        
        # Update document context
        elif operation == "document":
            if action == "create":
                self.current_context["last_document"] = result.get("path", "")
                self.current_context["last_format"] = result.get("format", "")
        
        # Update printer context
        elif operation == "printer":
            if action == "set_default":
                self.current_context["default_printer"] = result.get("printer", "")
    
    def _get_error_hint(self, operation: str, action: str, error: str) -> str:
        """Get helpful hints for common errors."""
        error_lower = error.lower()
        
        if "not found" in error_lower:
            if operation == "document":
                # Check if we're in a project context via texflow's SESSION_CONTEXT
                import texflow
                if texflow.SESSION_CONTEXT.get("current_project"):
                    return "File not found in current project. Use 'discover(action=\"documents\")' to list available files"
                else:
                    return "File not found. Are you working in a project? Use 'project(action=\"switch\")' to activate a project, or 'project(action=\"create\")' to create one"
            elif operation == "project":
                return "Use 'project(action=\"list\")' to see available projects"
            elif operation == "output":
                return "Source file not found. Use 'discover(action=\"documents\")' to list available documents"
        
        elif "permission" in error_lower:
            return "Check file permissions or try running with appropriate privileges"
        
        elif "format" in error_lower:
            if "cannot export from format" in error_lower:
                return "The 'format' parameter specifies the SOURCE format (not target). For .tex files, use format='latex' or omit for auto-detection"
            return "Use 'workflow(action=\"suggest\")' to get format recommendations"
        
        elif "validation" in error_lower or "compile" in error_lower:
            return "LaTeX compilation failed. Use 'document(action=\"validate\")' to check for syntax errors"
        
        return "Use 'workflow(action=\"guide\")' for help with this operation"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_personality_context(self, personality_name: str = "document-author") -> Dict[str, Any]:
        """Get context for a specific personality."""
        return self.personalities.get(personality_name, {}).get("context", {})