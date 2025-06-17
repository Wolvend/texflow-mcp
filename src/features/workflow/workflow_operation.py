"""
Workflow Operation implementation for TeXFlow.

Provides intelligent workflow guidance and task recommendations.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

# Import the resolve_path function and session context from the main texflow module
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
import texflow


class WorkflowOperation:
    """Handles workflow guidance and intelligent recommendations."""
    
    def __init__(self, texflow_instance):
        """
        Initialize with reference to TeXFlow instance for tool access.
        
        Args:
            texflow_instance: Instance of TeXFlow with all original tools
        """
        self.texflow = texflow_instance
        
    def execute(self, action: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow operation action.
        
        Actions:
            - suggest: Get workflow recommendations for a task
            - guide: Get comprehensive guidance for a workflow
            - next_steps: See contextual next actions based on current state
        """
        action_map = {
            "suggest": self._suggest_workflow,
            "guide": self._guide_workflow,
            "next_steps": self._get_next_steps
        }
        
        if action not in action_map:
            return {
                "error": f"Unknown workflow action: {action}",
                "available_actions": list(action_map.keys())
            }
        
        # For workflow tool, we pass through to the original implementation
        # but add semantic enhancements to the results
        result = self.texflow.workflow(action=action, **params)
        
        # Add semantic layer enhancements
        if isinstance(result, dict) and not result.get("error"):
            result = self._enhance_workflow_result(action, result, params, context)
        
        return result
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get operation capabilities and requirements."""
        return {
            "actions": {
                "suggest": {
                    "description": "Get workflow recommendations for a specific task",
                    "required_params": ["task"],
                    "examples": [
                        "workflow(action='suggest', task='write a research paper')",
                        "workflow(action='suggest', task='create presentation slides')"
                    ]
                },
                "guide": {
                    "description": "Get comprehensive guidance for a complete workflow",
                    "required_params": ["task"],
                    "examples": [
                        "workflow(action='guide', task='dissertation')",
                        "workflow(action='guide', task='technical documentation')"
                    ]
                },
                "next_steps": {
                    "description": "Get contextual next actions based on current project state",
                    "optional_params": ["context"],
                    "examples": [
                        "workflow(action='next_steps')",
                        "workflow(action='next_steps', context='just created latex document')"
                    ]
                }
            },
            "features": [
                "Context-aware recommendations",
                "Task-specific workflow patterns",
                "Integration with all TeXFlow tools",
                "Progressive disclosure of complexity"
            ],
            "workflow_patterns": {
                "academic": [
                    "Research paper",
                    "Thesis/Dissertation", 
                    "Conference presentation",
                    "Literature review"
                ],
                "technical": [
                    "API documentation",
                    "User manual",
                    "Technical report",
                    "Architecture document"
                ],
                "creative": [
                    "Novel/Book",
                    "Poetry collection",
                    "Screenplay",
                    "Blog series"
                ]
            }
        }
    
    def _suggest_workflow(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Get workflow suggestions for a task."""
        # This is handled by the original tool, we just enhance the result
        return {}
    
    def _guide_workflow(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive workflow guidance."""
        # This is handled by the original tool, we just enhance the result
        return {}
    
    def _get_next_steps(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Get contextual next steps."""
        # This is handled by the original tool, we just enhance the result
        return {}
    
    def _enhance_workflow_result(self, action: str, result: Dict[str, Any], params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Add semantic layer enhancements to workflow results."""
        
        # Add cross-tool integration hints
        if "steps" in result:
            enhanced_steps = []
            for step in result.get("steps", []):
                enhanced_step = dict(step)  # Copy original step
                
                # Add tool command examples based on step description
                if "create" in str(step.get("description", "")).lower():
                    enhanced_step["examples"] = [
                        "document(action='create', content='...', format='latex')",
                        "project(action='create', name='my_project')"
                    ]
                elif "validate" in str(step.get("description", "")).lower():
                    enhanced_step["examples"] = [
                        "document(action='validate', path='document.tex')"
                    ]
                elif "export" in str(step.get("description", "")).lower():
                    enhanced_step["examples"] = [
                        "output(action='export', source='document.tex', output_path='output/document.pdf')"
                    ]
                elif "organize" in str(step.get("description", "")).lower():
                    enhanced_step["examples"] = [
                        "organizer(action='archive', path='old_draft.tex', reason='Superseded by v2')"
                    ]
                
                enhanced_steps.append(enhanced_step)
            
            result["steps"] = enhanced_steps
        
        # Add efficiency tips based on action
        if action == "suggest":
            result["efficiency_tips"] = [
                "Use 'edit' action on existing documents instead of recreating",
                "Convert between formats instead of rewriting content",
                "Validate LaTeX before attempting to export to PDF",
                "Work within projects for better organization"
            ]
        
        # Add contextual awareness
        if context.get("current_project"):
            result["project_context"] = {
                "current_project": context["current_project"],
                "hint": "You're already in a project context - great for organization!"
            }
        
        # Add common pitfalls to avoid
        result["avoid_these_mistakes"] = [
            "Don't use format='pdf' when exporting (format is for source, not target)",
            "Don't forget to validate LaTeX before compiling",
            "Don't recreate documents when you can edit them",
            "Don't work with loose files when projects provide better organization"
        ]
        
        return result