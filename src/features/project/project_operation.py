"""
Project Operation implementation for TeXFlow.

Manages document projects with intelligent organization.
"""

from typing import Dict, Any, List, Optional


class ProjectOperation:
    """Handles all project management operations."""
    
    def __init__(self, texflow_instance):
        """
        Initialize with reference to TeXFlow instance for tool access.
        
        Args:
            texflow_instance: Instance of TeXFlow with all original tools
        """
        self.texflow = texflow_instance
        
    def execute(self, action: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a project operation action.
        
        Actions:
            - create: Create new project with AI-guided structure
            - switch: Switch to different project
            - list: List all projects
            - info: Get current project info
            - close: Close current project and return to Documents mode
            - archive: Archive a project (future)
        """
        action_map = {
            "create": self._create_project,
            "switch": self._switch_project,
            "list": self._list_projects,
            "info": self._project_info,
            "close": self._close_project,
            "archive": self._archive_project
        }
        
        if action not in action_map:
            return {
                "error": f"Unknown project action: {action}",
                "available_actions": list(action_map.keys())
            }
        
        return action_map[action](params, context)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get operation capabilities and requirements."""
        return {
            "actions": {
                "create": {
                    "description": "Create a new project with AI-guided structure",
                    "required_params": ["name"],
                    "optional_params": ["description", "template"],
                    "ai_features": ["structure_generation", "intent_analysis"]
                },
                "switch": {
                    "description": "Switch to a different project",
                    "required_params": ["name"],
                    "optional_params": []
                },
                "list": {
                    "description": "List all available projects",
                    "required_params": [],
                    "optional_params": ["filter", "sort_by"]
                },
                "info": {
                    "description": "Get information about current project",
                    "required_params": [],
                    "optional_params": ["detailed"]
                },
                "close": {
                    "description": "Close current project and return to Documents mode",
                    "required_params": [],
                    "optional_params": []
                },
                "archive": {
                    "description": "Archive a project",
                    "required_params": ["name"],
                    "optional_params": ["keep_exports"],
                    "status": "planned"
                }
            },
            "system_requirements": {
                "command": []  # No special requirements
            },
            "features": {
                "ai_structure": "AI analyzes project description to create optimal directory structure",
                "flexible_organization": "Projects are optional - work ad-hoc or organized",
                "metadata_tracking": "Tracks project creation date, last modified, and description"
            }
        }
    
    def _create_project(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project with AI-guided structure."""
        name = params.get("name")
        description = params.get("description", "")
        template = params.get("template")  # For backward compatibility
        
        if not name:
            return {"error": "Project name is required"}
        
        try:
            # Use the original create_project function
            result = self.texflow.create_project(name, description or template)
            
            # Parse result to extract project info
            project_path = self._extract_project_path(result)
            
            return {
                "success": True,
                "action": "create",
                "project_name": name,
                "project_path": project_path,
                "description": description or "No description provided",
                "message": f"Project '{name}' created successfully",
                "structure_created": self._infer_structure(description),
                "next_step": "Use document(action='create') to start writing"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "project_name": name,
                "hint": "Check if project already exists with project(action='list')"
            }
    
    def _switch_project(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Switch to a different project."""
        name = params.get("name")
        
        if not name:
            return {"error": "Project name is required"}
        
        try:
            result = self.texflow.use_project(name)
            
            return {
                "success": True,
                "action": "switch",
                "project_name": name,
                "message": f"Switched to project: {name}",
                "hint": "All document operations will now use this project"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "project_name": name,
                "hint": "Use project(action='list') to see available projects"
            }
    
    def _list_projects(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """List all available projects."""
        filter_term = params.get("filter", "")
        sort_by = params.get("sort_by", "modified")  # name, created, modified
        
        try:
            result = self.texflow.list_projects()
            
            # Parse the result to extract project list
            projects = self._parse_project_list(result)
            
            # Apply filter if provided
            if filter_term:
                projects = [p for p in projects if filter_term.lower() in p["name"].lower()]
            
            # Sort projects
            if sort_by == "name":
                projects.sort(key=lambda p: p["name"])
            elif sort_by == "created":
                projects.sort(key=lambda p: p.get("created", ""), reverse=True)
            else:  # modified
                projects.sort(key=lambda p: p.get("modified", ""), reverse=True)
            
            return {
                "success": True,
                "action": "list",
                "projects": projects,
                "count": len(projects),
                "filtered": bool(filter_term),
                "sorted_by": sort_by,
                "message": f"Found {len(projects)} project(s)"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _project_info(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about current project."""
        detailed = params.get("detailed", False)
        
        try:
            result = self.texflow.project_info()
            
            # Check if no project is active
            if "no project" in result.lower() or "not in a project" in result.lower():
                return {
                    "success": True,
                    "action": "info",
                    "active_project": None,
                    "message": "No project currently active",
                    "hint": "Use project(action='create') or project(action='switch') to work with projects"
                }
            
            # Parse project info
            info = self._parse_project_info(result)
            
            response = {
                "success": True,
                "action": "info",
                "active_project": info.get("name", "Unknown"),
                "path": info.get("path", ""),
                "description": info.get("description", ""),
                "created": info.get("created", ""),
                "modified": info.get("modified", "")
            }
            
            if detailed:
                # Add more details like file count, structure, etc.
                response["details"] = {
                    "document_count": info.get("document_count", 0),
                    "output_count": info.get("output_count", 0),
                    "structure": info.get("structure", [])
                }
            
            return response
            
        except Exception as e:
            return {"error": str(e)}
    
    def _close_project(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Close the current project."""
        try:
            result = self.texflow.close_project()
            
            # Check if no project was active
            if "no project is currently active" in result.lower():
                return {
                    "success": True,
                    "action": "close",
                    "message": "No project was active",
                    "hint": "File operations already use ~/Documents/ by default"
                }
            
            # Extract closed project name from result
            import re
            name_match = re.search(r"Closed project '(.+?)'", result)
            project_name = name_match.group(1) if name_match else "Unknown"
            
            return {
                "success": True,
                "action": "close",
                "closed_project": project_name,
                "message": f"Project '{project_name}' closed successfully",
                "hint": "File operations will now use ~/Documents/ by default"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _archive_project(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Archive a project (future feature)."""
        return {
            "error": "Archive feature not yet implemented",
            "hint": "Projects can be manually moved to an archive folder"
        }
    
    def _extract_project_path(self, result: str) -> str:
        """Extract project path from result string."""
        import re
        patterns = [
            r'created at:\s*(.+?)(?:\n|$)',
            r'Project created:\s*(.+?)(?:\n|$)',
            r'at:\s*(.+?)(?:\n|$)',
            r'(/[\w/.-]+/TeXFlow/[\w-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, result, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "~/Documents/TeXFlow/" + result.split()[0] if result else "unknown"
    
    def _infer_structure(self, description: str) -> List[str]:
        """Infer what structure was created based on description."""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ["thesis", "dissertation"]):
            return ["chapters/", "figures/", "references/", "output/"]
        elif any(word in desc_lower for word in ["paper", "article", "journal"]):
            return ["content/", "figures/", "output/"]
        elif any(word in desc_lower for word in ["book", "manual"]):
            return ["chapters/", "appendices/", "figures/", "output/"]
        else:
            return ["content/", "output/"]
    
    def _parse_project_list(self, result: str) -> List[Dict[str, Any]]:
        """Parse project list from tool result."""
        projects = []
        
        # Simple parsing - look for project entries
        lines = result.split('\n')
        current_project = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_project:
                    projects.append(current_project)
                    current_project = {}
                continue
            
            # Parse different formats
            if line.startswith('- ') or line.startswith('* '):
                # Bullet list format
                name = line[2:].split(':')[0].strip()
                current_project = {"name": name}
            elif ':' in line:
                # Key: value format
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                current_project[key] = value.strip()
        
        # Add last project if exists
        if current_project:
            projects.append(current_project)
        
        # If no structured data found, try simple parsing
        if not projects and result:
            # Look for project names in the result
            for line in lines:
                if line and not line.startswith(' '):
                    projects.append({"name": line.strip()})
        
        return projects
    
    def _parse_project_info(self, result: str) -> Dict[str, Any]:
        """Parse project info from tool result."""
        info = {}
        
        lines = result.split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                info[key] = value.strip()
        
        # Extract common patterns
        import re
        
        # Project name
        name_match = re.search(r'Project:\s*(.+)', result, re.IGNORECASE)
        if name_match:
            info['name'] = name_match.group(1).strip()
        
        # Path
        path_match = re.search(r'Path:\s*(.+)', result, re.IGNORECASE)
        if path_match:
            info['path'] = path_match.group(1).strip()
        
        return info