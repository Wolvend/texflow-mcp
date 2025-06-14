"""
Project Operation implementation for TeXFlow.

Manages document projects with intelligent organization.
"""

from typing import Dict, Any, List, Optional
import sys
from pathlib import Path

# Import the texflow module to access the actual project functions
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
import texflow


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
            - import: Import an existing directory as a TeXFlow project
            - archive: Archive a project (future)
        """
        action_map = {
            "create": self._create_project,
            "switch": self._switch_project,
            "list": self._list_projects,
            "info": self._project_info,
            "close": self._close_project,
            "import": self._import_project,
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
                "import": {
                    "description": "Import an existing directory as a TeXFlow project",
                    "required_params": ["name"],
                    "optional_params": ["description"],
                    "features": ["auto_organization", "file_migration", "structure_creation"]
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
            result = self.texflow.project("create", name, description or template)
            
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
            # Call the actual texflow project function
            result = texflow.project("switch", name)
            
            # Check if it was successful (texflow functions return strings)
            if "❌" in result or "Error" in result:
                return {
                    "success": False,
                    "error": result,
                    "project_name": name,
                    "hint": "Use project(action='list') to see available projects"
                }
            
            return {
                "success": True,
                "action": "switch",
                "project_name": name,
                "message": result,
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
            # Call the actual texflow project function
            result = texflow.project("list")
            
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
            
            # Separate projects and importable directories
            active_projects = [p for p in projects if p.get("type") == "project"]
            importable_dirs = [p for p in projects if p.get("type") == "importable"]
            
            response = {
                "success": True,
                "action": "list",
                "projects": active_projects,
                "importable_directories": importable_dirs,
                "total_count": len(projects),
                "project_count": len(active_projects),
                "importable_count": len(importable_dirs),
                "filtered": bool(filter_term),
                "sorted_by": sort_by,
                "message": f"Found {len(active_projects)} project(s) and {len(importable_dirs)} importable directories"
            }
            
            return response
            
        except Exception as e:
            return {"error": str(e)}
    
    def _project_info(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about current project."""
        detailed = params.get("detailed", False)
        
        try:
            # Call the actual texflow project function
            result = texflow.project("info")
            
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
            result = self.texflow.project("close")
            
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
    
    def _import_project(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Import an existing directory as a TeXFlow project."""
        name = params.get("name")
        description = params.get("description", "")
        
        if not name:
            return {"error": "Directory name/path is required for import"}
        
        # Call the underlying import function
        try:
            # For nested paths like "projects/agent-attractor-states"
            result = self.texflow.project("import", name, description)
            
            # Parse result to extract import info
            import re
            name_match = re.search(r"Project imported: (.+?)(?:\n|$)", result)
            project_name = name_match.group(1) if name_match else name
            
            # Check if files were moved
            moved_match = re.search(r"Moved (\d+) files", result)
            files_moved = int(moved_match.group(1)) if moved_match else 0
            
            response = {
                "success": True,
                "action": "import",
                "project_name": project_name,
                "message": f"Successfully imported '{project_name}' as a TeXFlow project",
                "files_organized": files_moved,
                "structure_created": ["content/", "output/pdf/", "assets/"],
                "current_project": project_name,
                "next_steps": [
                    "Use document(action='read') to view existing files",
                    "Use document(action='convert') to transform between formats",
                    "Use output(action='export') to generate PDFs"
                ]
            }
            
            if files_moved > 0:
                response["organization_note"] = f"Moved {files_moved} document files to content/ directory"
                
            return response
            
        except Exception as e:
            # Check if it's because project already exists
            if "already a TeXFlow project" in str(e):
                return {
                    "error": f"Directory '{name}' is already a TeXFlow project",
                    "hint": f"Use project(action='switch', name='{name}') to activate it"
                }
            return {
                "error": str(e),
                "hint": "Check that the directory exists and contains document files"
            }
    
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
        importable = []
        in_projects_section = False
        in_importable_section = False
        
        lines = result.split('\n')
        
        for line in lines:
            line_stripped = line.strip()
            
            # Check section headers
            if line_stripped.startswith("Projects:"):
                in_projects_section = True
                in_importable_section = False
                continue
            elif "Directories available for import:" in line_stripped:
                in_projects_section = False
                in_importable_section = True
                continue
            
            # Parse entries
            if line_stripped.startswith('- '):
                item = line_stripped[2:].strip()
                
                if in_projects_section:
                    # Parse project entries
                    name = item.split(' (current)')[0].strip()
                    is_current = '(current)' in item
                    projects.append({
                        "name": name,
                        "type": "project",
                        "is_current": is_current
                    })
                elif in_importable_section:
                    # Parse importable directory entries
                    # Extract path from format: "path (use: project(action='import', name='path'))"
                    import re
                    path_match = re.match(r'^(.+?)\s*\(use:', item)
                    if path_match:
                        path = path_match.group(1).strip()
                        importable.append({
                            "name": path,
                            "type": "importable",
                            "action_hint": f"project(action='import', name='{path}')"
                        })
        
        # Combine results
        all_items = projects + importable
        return all_items
    
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