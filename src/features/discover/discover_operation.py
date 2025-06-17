"""
Discover Operation implementation for TeXFlow.

Provides semantic enhancements for document and resource discovery.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

# Import the main texflow module
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
import texflow


class DiscoverOperation:
    """Handles discovery operations with semantic understanding."""
    
    def __init__(self, texflow_instance):
        """
        Initialize with reference to TeXFlow instance.
        
        Args:
            texflow_instance: Instance of TeXFlow with discover functionality
        """
        self.texflow = texflow_instance
        self._discovery_cache = {}
        
    def execute(self, action: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a discover operation with semantic enhancements.
        
        Actions:
            - documents: Find documents with smart recommendations
            - recent: Show recently modified documents
            - fonts: Browse available fonts with usage hints
            - capabilities: Check system dependencies with setup guidance
        """
        action_map = {
            "documents": self._discover_documents,
            "recent": self._discover_recent,
            "fonts": self._discover_fonts,
            "capabilities": self._check_capabilities
        }
        
        if action not in action_map:
            return {
                "error": f"Unknown discover action: {action}",
                "available_actions": list(action_map.keys())
            }
        
        return action_map[action](params, context)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get discover operation capabilities."""
        return {
            "actions": {
                "documents": {
                    "description": "List documents in project or folder",
                    "optional_params": ["folder"],
                    "workflow_hints": "Shows relative paths for easy reference"
                },
                "recent": {
                    "description": "Show recently modified documents across all projects",
                    "optional_params": ["limit", "format"],
                    "workflow_hints": "Helps resume work on recent documents"
                },
                "fonts": {
                    "description": "Browse available fonts for LaTeX",
                    "optional_params": ["style"],
                    "workflow_hints": "Find fonts for professional documents"
                },
                "capabilities": {
                    "description": "Check system dependencies and tools",
                    "workflow_hints": "Identifies missing tools and provides installation guidance"
                }
            }
        }
    
    def _discover_documents(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Discover documents with semantic enhancements."""
        folder = params.get("folder")
        
        try:
            # Call original implementation
            result = self.texflow.discover("documents", folder)
            
            # Parse documents from result
            documents = self._parse_document_list(result)
            
            # Categorize documents
            categorized = {
                "latex": [],
                "markdown": [],
                "other": []
            }
            
            for doc in documents:
                if doc["path"].endswith('.tex'):
                    categorized["latex"].append(doc)
                elif doc["path"].endswith('.md'):
                    categorized["markdown"].append(doc)
                else:
                    categorized["other"].append(doc)
            
            # Add workflow recommendations
            workflow_hints = []
            if categorized["latex"]:
                workflow_hints.append({
                    "category": "LaTeX documents",
                    "count": len(categorized["latex"]),
                    "suggestion": "Use document(action='validate') before exporting to PDF"
                })
            
            if categorized["markdown"]:
                workflow_hints.append({
                    "category": "Markdown documents",
                    "count": len(categorized["markdown"]),
                    "suggestion": "Can be converted to LaTeX for advanced formatting"
                })
            
            return {
                "success": True,
                "folder": folder or "current directory",
                "total_documents": len(documents),
                "documents": documents,
                "categorized": categorized,
                "workflow": {
                    "message": f"Found {len(documents)} document(s)",
                    "hints": workflow_hints,
                    "next_steps": self._get_document_next_steps(documents, context)
                }
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _discover_recent(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Discover recent documents with workflow hints."""
        limit = params.get("limit", 10)
        format_filter = params.get("format")
        
        try:
            # Call original implementation
            result = self.texflow.discover("recent")
            
            # Parse recent documents
            recent_docs = self._parse_recent_list(result)
            
            # Apply format filter if specified
            if format_filter:
                recent_docs = [doc for doc in recent_docs 
                             if doc.get("format") == format_filter]
            
            # Limit results
            recent_docs = recent_docs[:limit]
            
            # Group by project
            by_project = {}
            for doc in recent_docs:
                project = doc.get("project", "No Project")
                if project not in by_project:
                    by_project[project] = []
                by_project[project].append(doc)
            
            return {
                "success": True,
                "recent_documents": recent_docs,
                "count": len(recent_docs),
                "by_project": by_project,
                "workflow": {
                    "message": f"Found {len(recent_docs)} recent document(s)",
                    "next_steps": [
                        {"action": "read", "description": "Open a recent document"},
                        {"action": "edit", "description": "Continue working on a document"}
                    ]
                }
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _discover_fonts(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Discover fonts with usage recommendations."""
        style = params.get("style")
        
        try:
            # Call original implementation
            result = self.texflow.discover("fonts", style=style)
            
            # Parse font list
            fonts = self._parse_font_list(result)
            
            # Categorize fonts
            recommendations = {
                "serif": [],
                "sans-serif": [],
                "monospace": [],
                "special": []
            }
            
            # Add font recommendations based on usage
            font_hints = []
            if any("Computer Modern" in f["name"] for f in fonts):
                font_hints.append({
                    "font": "Computer Modern",
                    "usage": "Default LaTeX font, excellent for academic papers"
                })
            
            if any("Liberation" in f["name"] for f in fonts):
                font_hints.append({
                    "font": "Liberation family",
                    "usage": "Open-source alternatives to Times, Arial, and Courier"
                })
            
            return {
                "success": True,
                "fonts": fonts,
                "total_fonts": len(fonts),
                "style_filter": style,
                "recommendations": font_hints,
                "workflow": {
                    "message": f"Found {len(fonts)} font(s)",
                    "usage_example": "\\setmainfont{Font Name} in LaTeX preamble",
                    "next_steps": [
                        {"action": "create", "description": "Create document with custom font"},
                        {"action": "validate", "description": "Check if fonts work in your document"}
                    ]
                }
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _check_capabilities(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Check system capabilities with setup guidance."""
        try:
            # Call original implementation
            result = self.texflow.discover("capabilities")
            
            # Parse capabilities
            capabilities = self._parse_capabilities(result)
            
            # Categorize by status
            ready_tools = []
            missing_tools = []
            
            for tool, status in capabilities.items():
                if status.get("available", False):
                    ready_tools.append(tool)
                else:
                    missing_tools.append({
                        "tool": tool,
                        "purpose": status.get("purpose", ""),
                        "install_hint": status.get("install_hint", "")
                    })
            
            # Workflow recommendations based on missing tools
            workflow_priority = []
            if any(t["tool"] == "xelatex" for t in missing_tools):
                workflow_priority.append({
                    "priority": "high",
                    "action": "Install XeLaTeX for PDF generation",
                    "impact": "Cannot create PDFs from LaTeX documents"
                })
            
            if any(t["tool"] == "pandoc" for t in missing_tools):
                workflow_priority.append({
                    "priority": "medium",
                    "action": "Install pandoc for format conversion",
                    "impact": "Cannot convert between document formats"
                })
            
            return {
                "success": True,
                "ready_tools": ready_tools,
                "missing_tools": missing_tools,
                "system_ready": len(missing_tools) == 0,
                "workflow": {
                    "message": f"{len(ready_tools)} tools ready, {len(missing_tools)} missing",
                    "priorities": workflow_priority,
                    "next_steps": self._get_capability_next_steps(missing_tools)
                }
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _get_document_next_steps(self, documents: List[Dict], context: Dict) -> List[Dict]:
        """Generate next steps based on discovered documents."""
        steps = []
        
        if documents:
            # Suggest actions based on document types
            has_latex = any(d["path"].endswith('.tex') for d in documents)
            has_markdown = any(d["path"].endswith('.md') for d in documents)
            
            if has_latex:
                steps.append({
                    "action": "validate",
                    "description": "Check LaTeX documents for errors"
                })
            
            if has_markdown:
                steps.append({
                    "action": "convert",
                    "description": "Convert Markdown to LaTeX for advanced features"
                })
            
            steps.append({
                "action": "export",
                "description": "Generate PDFs from documents"
            })
        else:
            steps.append({
                "action": "create",
                "description": "Create a new document"
            })
        
        return steps
    
    def _get_capability_next_steps(self, missing_tools: List[Dict]) -> List[Dict]:
        """Generate next steps for missing capabilities."""
        steps = []
        
        if missing_tools:
            steps.append({
                "action": "install",
                "description": "Install missing tools using provided hints"
            })
        
        steps.append({
            "action": "check",
            "description": "Re-run capabilities check after installation"
        })
        
        return steps
    
    def _parse_document_list(self, result_str: str) -> List[Dict[str, Any]]:
        """Parse document list from string result."""
        documents = []
        lines = result_str.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line.endswith('.tex') or line.endswith('.md') or 
                        line.endswith('.txt') or line.endswith('.pdf')):
                # Extract path and other info
                if '│' in line:
                    parts = line.split('│')
                    if len(parts) >= 2:
                        documents.append({
                            "path": parts[0].strip().strip('•'),
                            "info": parts[1].strip() if len(parts) > 1 else ""
                        })
                else:
                    documents.append({
                        "path": line.strip('•').strip(),
                        "info": ""
                    })
        
        return documents
    
    def _parse_recent_list(self, result_str: str) -> List[Dict[str, Any]]:
        """Parse recent documents from string result."""
        # Similar to document parsing but might include timestamps
        documents = self._parse_document_list(result_str)
        
        # Add format detection
        for doc in documents:
            path = doc["path"]
            if path.endswith('.tex'):
                doc["format"] = "latex"
            elif path.endswith('.md'):
                doc["format"] = "markdown"
            else:
                doc["format"] = "other"
        
        return documents
    
    def _parse_font_list(self, result_str: str) -> List[Dict[str, Any]]:
        """Parse font list from string result."""
        fonts = []
        lines = result_str.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('Available fonts'):
                # Basic font parsing
                fonts.append({
                    "name": line.strip('•').strip(),
                    "type": "system"  # Could be enhanced to detect font type
                })
        
        return fonts
    
    def _parse_capabilities(self, result_str: str) -> Dict[str, Dict[str, Any]]:
        """Parse capabilities from string result."""
        capabilities = {}
        lines = result_str.split('\n')
        
        for line in lines:
            if '✓' in line:
                # Tool is available
                tool_name = line.split('✓')[1].strip().split()[0].lower()
                capabilities[tool_name] = {"available": True}
            elif '✗' in line or 'Missing' in line:
                # Tool is missing
                parts = line.split('✗' if '✗' in line else 'Missing')
                if len(parts) > 1:
                    tool_info = parts[1].strip()
                    tool_name = tool_info.split()[0].lower()
                    capabilities[tool_name] = {
                        "available": False,
                        "install_hint": tool_info
                    }
        
        return capabilities