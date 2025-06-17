"""
Templates Operation implementation for TeXFlow.

Manages document templates for quick project starts with semantic enhancements.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

# Import the resolve_path function and session context from the main texflow module
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
import texflow


class TemplatesOperation:
    """Handles template management with workflow intelligence."""
    
    def __init__(self, texflow_instance):
        """
        Initialize with reference to TeXFlow instance for tool access.
        
        Args:
            texflow_instance: Instance of TeXFlow with all original tools
        """
        self.texflow = texflow_instance
        
    def execute(self, action: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a templates operation action.
        
        Actions:
            - list: Show available templates (optionally filtered by category)
            - use: Copy a template to current project or specified location
            - activate: Convert current project into a template
            - create: Create a new template from content or existing document
            - rename: Rename a template
            - delete: Remove a template
            - info: Get details about a specific template
        """
        action_map = {
            "list": self._list_templates,
            "use": self._use_template,
            "activate": self._activate_template,
            "create": self._create_template,
            "rename": self._rename_template,
            "delete": self._delete_template,
            "info": self._get_template_info
        }
        
        if action not in action_map:
            return {
                "error": f"Unknown templates action: {action}",
                "available_actions": list(action_map.keys())
            }
        
        # For templates tool, we pass through to the original implementation
        # but add semantic enhancements to the results
        # Only pass the parameters that the original function expects
        template_params = {}
        if "category" in params:
            template_params["category"] = params["category"]
        if "name" in params:
            template_params["name"] = params["name"]
        if "source" in params:
            template_params["source"] = params["source"]
        if "target" in params:
            template_params["target"] = params["target"]
        if "content" in params:
            template_params["content"] = params["content"]
            
        result = self.texflow.templates(action=action, **template_params)
        
        # Convert string result to dict format for consistency
        if isinstance(result, str):
            result = {
                "success": True,
                "message": result,
                "action": action
            }
        
        # Add semantic layer enhancements
        if isinstance(result, dict) and not result.get("error"):
            result = self._enhance_template_result(action, result, params, context)
        
        return result
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get operation capabilities and requirements."""
        return {
            "actions": {
                "list": {
                    "description": "Show available templates with smart categorization",
                    "optional_params": ["category"],
                    "categories": ["academic", "technical", "creative", "business"],
                    "examples": [
                        "templates(action='list')",
                        "templates(action='list', category='academic')"
                    ]
                },
                "use": {
                    "description": "Instantiate a template in your project",
                    "required_params": ["name"],
                    "optional_params": ["target"],
                    "examples": [
                        "templates(action='use', name='research_paper')",
                        "templates(action='use', name='thesis', target='dissertation.tex')"
                    ]
                },
                "activate": {
                    "description": "Convert current project into a reusable template",
                    "required_params": ["name"],
                    "optional_params": ["category"],
                    "examples": [
                        "templates(action='activate', name='my_report_template', category='business')"
                    ]
                },
                "create": {
                    "description": "Create a new template from content or document",
                    "required_params": ["name"],
                    "optional_params": ["content", "source", "category"],
                    "examples": [
                        "templates(action='create', name='letter', content='...', category='business')",
                        "templates(action='create', name='slides', source='presentation.tex')"
                    ]
                },
                "rename": {
                    "description": "Rename an existing template",
                    "required_params": ["name", "target"],
                    "examples": [
                        "templates(action='rename', name='old_name', target='new_name')"
                    ]
                },
                "delete": {
                    "description": "Remove a template",
                    "required_params": ["name"],
                    "examples": [
                        "templates(action='delete', name='unused_template')"
                    ]
                },
                "info": {
                    "description": "Get detailed information about a template",
                    "required_params": ["name"],
                    "examples": [
                        "templates(action='info', name='research_paper')"
                    ]
                }
            },
            "template_categories": {
                "academic": {
                    "description": "Academic documents and papers",
                    "templates": ["research_paper", "thesis", "dissertation", "literature_review", "conference_paper"]
                },
                "technical": {
                    "description": "Technical documentation",
                    "templates": ["api_docs", "user_manual", "technical_report", "architecture_doc", "readme"]
                },
                "creative": {
                    "description": "Creative writing templates",
                    "templates": ["novel", "short_story", "screenplay", "poetry_collection", "blog_post"]
                },
                "business": {
                    "description": "Business documents",
                    "templates": ["business_letter", "report", "proposal", "invoice", "memo"]
                }
            },
            "best_practices": [
                "Start projects from templates to ensure consistency",
                "Create templates from successful projects for reuse",
                "Organize templates by category for easy discovery",
                "Include placeholder content and comments in templates"
            ]
        }
    
    def _list_templates(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """List available templates."""
        # This is handled by the original tool, we just enhance the result
        return {}
    
    def _use_template(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Use a template."""
        # This is handled by the original tool, we just enhance the result
        return {}
    
    def _activate_template(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Activate current project as template."""
        # This is handled by the original tool, we just enhance the result
        return {}
    
    def _create_template(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new template."""
        # This is handled by the original tool, we just enhance the result
        return {}
    
    def _rename_template(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Rename a template."""
        # This is handled by the original tool, we just enhance the result
        return {}
    
    def _delete_template(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a template."""
        # This is handled by the original tool, we just enhance the result
        return {}
    
    def _get_template_info(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Get template information."""
        # This is handled by the original tool, we just enhance the result
        return {}
    
    def _enhance_template_result(self, action: str, result: Dict[str, Any], params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Add semantic layer enhancements to template results."""
        
        # Enhance list results with usage hints
        if action == "list" and "templates" in result:
            for template in result.get("templates", []):
                # Add quick start commands
                template["quick_start"] = f"templates(action='use', name='{template.get('name', '')}')"
                
                # Add description based on name patterns
                name = template.get("name", "").lower()
                if "thesis" in name or "dissertation" in name:
                    template["ideal_for"] = "Graduate students writing thesis or dissertation"
                elif "paper" in name or "article" in name:
                    template["ideal_for"] = "Academic papers and journal articles"
                elif "report" in name:
                    template["ideal_for"] = "Technical or business reports"
                elif "letter" in name:
                    template["ideal_for"] = "Formal correspondence"
                elif "slides" in name or "presentation" in name:
                    template["ideal_for"] = "Conference or meeting presentations"
        
        # Enhance use results with next steps
        if action == "use" and result.get("success"):
            result["workflow"] = {
                "message": "Template instantiated successfully",
                "next_steps": [
                    {
                        "action": "edit",
                        "description": "Customize the template content",
                        "command": f"document(action='edit', path='{result.get('target', 'document.tex')}', old_string='...', new_string='...')"
                    },
                    {
                        "action": "validate", 
                        "description": "Check document syntax",
                        "command": f"document(action='validate', path='{result.get('target', 'document.tex')}')"
                    },
                    {
                        "action": "export",
                        "description": "Generate output when ready",
                        "command": f"output(action='export', source='{result.get('target', 'document.tex')}', output_path='output/document.pdf')"
                    }
                ]
            }
        
        # Enhance create/activate results
        if action in ["create", "activate"] and result.get("success"):
            result["template_tips"] = [
                "Include clear placeholders for user content",
                "Add comments explaining complex formatting",
                "Use descriptive variable names for easy customization",
                "Test the template before sharing"
            ]
        
        # Add category recommendations for uncategorized templates
        if action == "list" and not params.get("category"):
            result["category_guide"] = {
                "academic": "Research papers, theses, dissertations",
                "technical": "Documentation, manuals, reports",
                "creative": "Stories, scripts, creative writing",
                "business": "Letters, proposals, invoices",
                "hint": "Filter by category for more focused results"
            }
        
        # Add project context awareness
        if context.get("current_project") and action == "use":
            result["project_tip"] = "Template will be copied to your current project's content directory"
        elif not context.get("current_project") and action == "use":
            result["project_tip"] = "Consider creating a project first for better organization"
        
        return result