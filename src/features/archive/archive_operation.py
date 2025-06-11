"""
Archive Operation - Document version and history management

Manages document archiving, versioning, and cleanup operations.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path


class ArchiveOperation:
    """
    Handles all archive-related operations including:
    - Archiving (soft deleting) documents
    - Listing archived documents
    - Restoring archived documents
    - Finding document versions
    - Bulk cleanup operations
    """
    
    def __init__(self, texflow_instance):
        """
        Initialize with TeXFlow instance.
        
        Args:
            texflow_instance: TeXFlow instance with archive tools
        """
        self.texflow = texflow_instance
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an archive operation.
        
        Args:
            action: The action to perform (archive, restore, list, versions, cleanup)
            params: Parameters for the action
            
        Returns:
            Result dictionary with operation results
        """
        if action == "archive":
            return self._archive_document(params)
        elif action == "restore":
            return self._restore_document(params)
        elif action == "list":
            return self._list_archived(params)
        elif action == "versions":
            return self._find_versions(params)
        elif action == "cleanup":
            return self._cleanup_workspace(params)
        else:
            return {
                "error": f"Unknown archive action: {action}",
                "available_actions": ["archive", "restore", "list", "versions", "cleanup"]
            }
    
    def _archive_document(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Archive (soft delete) a document."""
        path = params.get("path")
        reason = params.get("reason", "manual")
        
        if not path:
            return {"error": "Document path is required"}
        
        try:
            result = self.texflow.archive_document(path, reason)
            
            return {
                "success": True,
                "message": f"Document archived: {path}",
                "archive_path": result.get("archive_path"),
                "reason": reason,
                "suggested_next": [
                    {
                        "operation": "archive",
                        "action": "list",
                        "hint": "View archived documents"
                    },
                    {
                        "operation": "archive",
                        "action": "restore",
                        "hint": "Restore if needed",
                        "params": {"archive_path": result.get("archive_path")}
                    }
                ]
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _restore_document(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Restore an archived document."""
        archive_path = params.get("archive_path")
        restore_path = params.get("restore_path")
        
        if not archive_path:
            return {"error": "Archive path is required"}
        
        try:
            result = self.texflow.restore_archived_document(archive_path, restore_path)
            
            return {
                "success": True,
                "message": "Document restored successfully",
                "restored_path": result.get("restored_path"),
                "suggested_next": [
                    {
                        "operation": "document",
                        "action": "read",
                        "hint": "Read the restored document",
                        "params": {"path": result.get("restored_path")}
                    },
                    {
                        "operation": "document",
                        "action": "edit",
                        "hint": "Edit the restored document"
                    }
                ]
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _list_archived(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List archived documents in a directory."""
        directory = params.get("directory", "")
        
        try:
            result = self.texflow.list_archived_documents(directory)
            
            archived_docs = result.get("archived_documents", [])
            
            return {
                "success": True,
                "directory": directory or "current directory",
                "archived_count": len(archived_docs),
                "archived_documents": archived_docs,
                "suggested_next": [
                    {
                        "operation": "archive",
                        "action": "restore",
                        "hint": "Restore a document"
                    } if archived_docs else None,
                    {
                        "operation": "archive",
                        "action": "cleanup",
                        "hint": "Archive more old files"
                    }
                ]
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _find_versions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find all versions of a document."""
        filename = params.get("filename")
        directory = params.get("directory", "")
        
        if not filename:
            return {"error": "Filename is required"}
        
        try:
            result = self.texflow.find_document_versions(filename, directory)
            
            versions = result.get("versions", {})
            current = versions.get("current")
            archived = versions.get("archived", [])
            
            return {
                "success": True,
                "filename": filename,
                "current_version": current,
                "archived_versions": archived,
                "total_versions": 1 + len(archived) if current else len(archived),
                "suggested_next": [
                    {
                        "operation": "archive",
                        "action": "restore",
                        "hint": "Restore an older version"
                    } if archived else None,
                    {
                        "operation": "document",
                        "action": "read",
                        "hint": "Read current version",
                        "params": {"path": current}
                    } if current else None
                ]
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _cleanup_workspace(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Archive multiple files matching a pattern."""
        directory = params.get("directory", "")
        pattern = params.get("pattern", "*_old*")
        
        try:
            result = self.texflow.clean_workspace(directory, pattern)
            
            archived_files = result.get("archived_files", [])
            
            return {
                "success": True,
                "directory": directory or "current directory",
                "pattern": pattern,
                "archived_count": len(archived_files),
                "archived_files": archived_files,
                "message": f"Archived {len(archived_files)} files matching '{pattern}'",
                "suggested_next": [
                    {
                        "operation": "archive",
                        "action": "list",
                        "hint": "View all archived documents"
                    },
                    {
                        "operation": "discover",
                        "action": "documents",
                        "hint": "See remaining documents"
                    }
                ]
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return capabilities of the archive operation."""
        return {
            "operation": "archive",
            "description": "Manage document versions and history",
            "actions": {
                "archive": {
                    "description": "Archive (soft delete) a document",
                    "required_params": ["path"],
                    "optional_params": ["reason"]
                },
                "restore": {
                    "description": "Restore an archived document",
                    "required_params": ["archive_path"],
                    "optional_params": ["restore_path"]
                },
                "list": {
                    "description": "List archived documents",
                    "required_params": [],
                    "optional_params": ["directory"]
                },
                "versions": {
                    "description": "Find all versions of a document",
                    "required_params": ["filename"],
                    "optional_params": ["directory"]
                },
                "cleanup": {
                    "description": "Archive multiple files by pattern",
                    "required_params": [],
                    "optional_params": ["directory", "pattern"]
                }
            },
            "examples": [
                {
                    "description": "Archive an old draft",
                    "operation": "archive",
                    "action": "archive",
                    "params": {"path": "draft_v1.md", "reason": "outdated"}
                },
                {
                    "description": "Find all versions of a document",
                    "operation": "archive",
                    "action": "versions",
                    "params": {"filename": "report.tex"}
                },
                {
                    "description": "Clean up old files",
                    "operation": "archive",
                    "action": "cleanup",
                    "params": {"pattern": "*_backup*"}
                }
            ]
        }