"""
TeXFlow Semantic Entry Point

This module provides the main entry point for semantic operations,
integrating all components and exposing a unified API for MCP tools.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path

from .core.semantic_router import SemanticRouter
from .core.operation_registry import OperationRegistry
from .core.format_detector import FormatDetector
from .features.document import DocumentOperation
from .features.output import OutputOperation
from .features.project import ProjectOperation
from .features.organizer import OrganizerOperation


class TeXFlowSemantic:
    """
    Main semantic interface for TeXFlow.
    
    This class provides a unified API that:
    1. Accepts high-level semantic operations
    2. Routes to appropriate handlers
    3. Provides workflow guidance
    4. Manages system requirements
    """
    
    def __init__(self, texflow_instance):
        """
        Initialize semantic layer with TeXFlow instance.
        
        Args:
            texflow_instance: Instance of TeXFlow with all original tools
        """
        self.texflow = texflow_instance
        self.router = SemanticRouter()
        self.registry = OperationRegistry()
        self.format_detector = FormatDetector()
        
        # Initialize and register operations
        self._register_operations()
        
        # Track current session context
        self.session_context = {
            "personality": "document-author",
            "workflow_hints_enabled": True
        }
    
    def _register_operations(self):
        """Register all semantic operations."""
        # Document operation
        doc_op = DocumentOperation(self.texflow)
        self.registry.register("document", doc_op)
        self.router.register_operation("document", doc_op)
        
        # Output operation
        output_op = OutputOperation(self.texflow)
        self.registry.register("output", output_op)
        self.router.register_operation("output", output_op)
        
        # Project operation
        project_op = ProjectOperation(self.texflow)
        self.registry.register("project", project_op)
        self.router.register_operation("project", project_op)
        
        # Organizer operation
        organizer_op = OrganizerOperation()
        self.registry.register("organizer", organizer_op)
        self.router.register_operation("organizer", organizer_op)
        
        # TODO: Register remaining operations when implemented
        # - printer
        # - discover
        # - workflow
    
    def execute(self, operation: str, action: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a semantic operation.
        
        This is the main entry point for all semantic operations.
        
        Args:
            operation: The semantic operation (document, output, project, etc.)
            action: The action within the operation (create, print, etc.)
            params: Parameters for the operation
            
        Returns:
            Result dictionary with operation results and workflow hints
        """
        params = params or {}
        
        # Add session context
        context = self.session_context.copy()
        
        # Route the operation
        result = self.router.route(operation, action, params)
        
        # Add system capability info if there was an error
        if "error" in result and "requirement" in result.get("error", "").lower():
            result["system_check"] = self.check_requirements(operation, action)
        
        return result
    
    def check_requirements(self, operation: Optional[str] = None, 
                         action: Optional[str] = None) -> Dict[str, Any]:
        """
        Check system requirements for operations.
        
        Args:
            operation: Specific operation to check (None for all)
            action: Specific action to check (None for all)
            
        Returns:
            Requirement status and installation hints
        """
        if operation:
            return self.registry.get_operation_requirements(operation, action)
        else:
            return self.registry.check_system_requirements()
    
    def get_capabilities(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        Get capabilities for operations.
        
        Args:
            operation: Specific operation (None for all)
            
        Returns:
            Capability information
        """
        if operation:
            return self.registry.get_capabilities(operation)
        else:
            # Return all capabilities
            capabilities = {}
            for op_name in self.registry.list_operations():
                capabilities[op_name] = self.registry.get_capabilities(op_name)
            return capabilities
    
    def suggest_format(self, content: str, intent: Optional[str] = None) -> Dict[str, Any]:
        """
        Suggest optimal document format.
        
        Args:
            content: Document content
            intent: User's stated intent
            
        Returns:
            Format recommendation with reasoning
        """
        return self.format_detector.detect(content, intent, self.session_context)
    
    def set_personality(self, personality: str) -> Dict[str, Any]:
        """
        Set the active personality (for future expansion).
        
        Args:
            personality: Personality name
            
        Returns:
            Confirmation or error
        """
        # Currently only document-author is supported
        if personality != "document-author":
            return {
                "error": f"Unknown personality: {personality}",
                "available": ["document-author"]
            }
        
        self.session_context["personality"] = personality
        return {
            "success": True,
            "personality": personality,
            "message": f"Active personality: {personality}"
        }
    
    def enable_workflow_hints(self, enabled: bool = True) -> Dict[str, Any]:
        """
        Enable or disable workflow hints.
        
        Args:
            enabled: Whether to show workflow hints
            
        Returns:
            Confirmation
        """
        self.session_context["workflow_hints_enabled"] = enabled
        return {
            "success": True,
            "workflow_hints": enabled,
            "message": f"Workflow hints {'enabled' if enabled else 'disabled'}"
        }
    
    # Convenience methods for common operations
    
    def create_document(self, content: str, **kwargs) -> Dict[str, Any]:
        """Convenience method for document creation."""
        params = {"content": content}
        params.update(kwargs)
        return self.execute("document", "create", params)
    
    def print_document(self, source: str, **kwargs) -> Dict[str, Any]:
        """Convenience method for printing."""
        params = {"source": source}
        params.update(kwargs)
        return self.execute("output", "print", params)
    
    def export_pdf(self, source: str, **kwargs) -> Dict[str, Any]:
        """Convenience method for PDF export."""
        params = {"source": source}
        params.update(kwargs)
        return self.execute("output", "export", params)
    
    def create_project(self, name: str, description: str = "", **kwargs) -> Dict[str, Any]:
        """Convenience method for project creation."""
        params = {"name": name, "description": description}
        params.update(kwargs)
        return self.execute("project", "create", params)
    
    def list_projects(self, **kwargs) -> Dict[str, Any]:
        """Convenience method for listing projects."""
        return self.execute("project", "list", kwargs)


def create_semantic_tools(texflow_instance) -> List[Dict[str, Any]]:
    """
    Create MCP tool definitions for semantic operations.
    
    This function generates the tool definitions that will be registered
    with the MCP server, replacing the 27+ individual tools with
    6 semantic operations.
    
    Args:
        texflow_instance: Instance of TeXFlow
        
    Returns:
        List of MCP tool definitions
    """
    # Create semantic instance
    semantic = TeXFlowSemantic(texflow_instance)
    
    # Define the semantic tools
    tools = [
        {
            "name": "document",
            "description": "Manage documents - create, edit, convert, and validate content",
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "read", "edit", "convert", "validate", "status"],
                        "description": "Action to perform"
                    },
                    "content": {
                        "type": "string",
                        "description": "Document content (for create/validate)"
                    },
                    "path": {
                        "type": "string",
                        "description": "Document path (for read/edit/status)"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["auto", "markdown", "latex"],
                        "description": "Document format (auto-detected if not specified)"
                    },
                    "intent": {
                        "type": "string",
                        "description": "Document purpose (helps format selection)"
                    },
                    "changes": {
                        "type": "array",
                        "description": "Edit changes to apply"
                    }
                },
                "required": ["action"]
            },
            "handler": lambda args: semantic.execute("document", args["action"], args)
        },
        {
            "name": "output",
            "description": "Output documents - print or export to PDF",
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["print", "export", "preview"],
                        "description": "Output action"
                    },
                    "source": {
                        "type": "string",
                        "description": "Document source path"
                    },
                    "content": {
                        "type": "string",
                        "description": "Direct content to output"
                    },
                    "printer": {
                        "type": "string",
                        "description": "Printer name (auto-selected if not specified)"
                    },
                    "format": {
                        "type": "string",
                        "description": "Output format"
                    }
                },
                "required": ["action"]
            },
            "handler": lambda args: semantic.execute("output", args["action"], args)
        },
        {
            "name": "project",
            "description": "Manage document projects for organized work",
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "switch", "list", "info"],
                        "description": "Project action"
                    },
                    "name": {
                        "type": "string",
                        "description": "Project name"
                    },
                    "description": {
                        "type": "string",
                        "description": "Project description (AI uses this to create structure)"
                    }
                },
                "required": ["action"]
            },
            "handler": lambda args: semantic.execute("project", args["action"], args)
        },
        {
            "name": "organizer",
            "description": "Organize documents - move, archive, manage versions, clean auxiliary files",
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["move", "archive", "restore", "list_archived", "find_versions", 
                                "clean", "clean_aux", "refresh_aux", "list_aux", "batch"],
                        "description": "Organizer action"
                    },
                    "source": {
                        "type": "string",
                        "description": "Source path (for move)"
                    },
                    "destination": {
                        "type": "string",
                        "description": "Destination path (for move)"
                    },
                    "path": {
                        "type": "string",
                        "description": "File/directory path"
                    },
                    "operations": {
                        "type": "array",
                        "description": "Batch operations list"
                    }
                },
                "required": ["action"]
            },
            "handler": lambda args: semantic.execute("organizer", args["action"], args)
        }
    ]
    
    # Add workflow suggestion tool
    tools.append({
        "name": "texflow_help",
        "description": "Get help with TeXFlow - suggest workflows, check requirements, or get guidance",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "enum": ["suggest_workflow", "check_requirements", "format_help", "next_steps"],
                    "description": "Help topic"
                },
                "context": {
                    "type": "string",
                    "description": "Additional context for help"
                }
            },
            "required": ["topic"]
        },
        "handler": lambda args: _handle_help(semantic, args)
    })
    
    return tools


def _handle_help(semantic: TeXFlowSemantic, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle help requests."""
    topic = args["topic"]
    context = args.get("context", "")
    
    if topic == "suggest_workflow":
        # Analyze context and suggest workflow
        return {
            "suggestions": [
                "To write a document: document(action='create', content='...', intent='your purpose')",
                "To print: output(action='print', source='document_name')",
                "To organize work: project(action='create', name='...', description='...')"
            ],
            "tip": "TeXFlow auto-detects the best format based on your content"
        }
    
    elif topic == "check_requirements":
        return semantic.check_requirements()
    
    elif topic == "format_help":
        return {
            "formats": {
                "markdown": "Best for: notes, documentation, simple documents",
                "latex": "Best for: academic papers, math, precise formatting"
            },
            "auto_detection": "TeXFlow automatically chooses based on your content",
            "escalation": "Start with Markdown - TeXFlow suggests LaTeX when needed"
        }
    
    elif topic == "next_steps":
        # Get workflow suggestions based on current context
        return {
            "next_steps": [
                {"action": "project(action='list')", "description": "See your projects"},
                {"action": "document(action='create')", "description": "Create a new document"},
                {"action": "output(action='export')", "description": "Generate PDF from document"}
            ]
        }
    
    return {"error": f"Unknown help topic: {topic}"}