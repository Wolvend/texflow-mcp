"""Organizer operation for TeXFlow - manages document organization and lifecycle.

This operation handles:
- Moving documents between folders
- Archiving (soft delete) documents
- Restoring archived documents
- Finding document versions
- Cleaning up workspaces
- Managing LaTeX auxiliary files (TOC, bibliography, etc.)
- Refreshing compilation artifacts
"""

from typing import Dict, Any, Optional
import shutil
from pathlib import Path
from datetime import datetime
import json

from src.features.document.document_manager import document_manager


class OrganizerOperation:
    """Handles document organization and lifecycle management."""
    
    def get_info(self) -> Dict[str, Any]:
        """Get operation information."""
        return {
            "name": "organizer",
            "description": "Manage document organization and lifecycle",
            "version": "1.0.0",
            "actions": {
                "move": {
                    "description": "Move or rename document (like Unix mv)",
                    "params": {
                        "source": "Source file path",
                        "destination": "Destination (new path or new name)"
                    }
                },
                "archive": {
                    "description": "Soft delete - move to hidden archive folder",
                    "params": {
                        "path": "File to archive",
                        "reason": "Reason for archiving (optional)"
                    }
                },
                "restore": {
                    "description": "Restore archived document",
                    "params": {
                        "archive_path": "Path to archived file",
                        "restore_path": "Where to restore (optional)"
                    }
                },
                "list_archived": {
                    "description": "List all archived documents in directory",
                    "params": {
                        "directory": "Directory to check"
                    }
                },
                "find_versions": {
                    "description": "Find all versions of a document",
                    "params": {
                        "filename": "Base filename",
                        "directory": "Directory to search"
                    }
                },
                "clean": {
                    "description": "Archive multiple files matching pattern",
                    "params": {
                        "directory": "Directory to clean",
                        "pattern": "Glob pattern (default: *)"
                    }
                },
                "clean_aux": {
                    "description": "Clean LaTeX auxiliary files (keep .tex and .pdf)",
                    "params": {
                        "path": "LaTeX file or directory path",
                        "keep_bib": "Keep bibliography files (default: true)"
                    }
                },
                "refresh_aux": {
                    "description": "Force regeneration of TOC, bibliography, etc.",
                    "params": {
                        "path": "LaTeX file path",
                        "types": "Which aux files to remove (toc, bib, all)"
                    }
                },
                "list_aux": {
                    "description": "List all auxiliary files for a document",
                    "params": {
                        "path": "LaTeX file path"
                    }
                },
                "batch": {
                    "description": "Execute multiple operations in one call",
                    "params": {
                        "operations": "List of operations to execute",
                        "stop_on_error": "Stop if operation fails (default: false)"
                    },
                    "example": {
                        "operations": [
                            {"action": "archive", "params": {"path": "old_draft.tex"}},
                            {"action": "move", "params": {"source": "draft.tex", "destination": "final.tex"}},
                            {"action": "clean_aux", "params": {"path": "."}}
                        ]
                    }
                }
            }
        }
    
    def execute(self, action: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute organizer action or batch of actions."""
        # Check if this is a batch operation
        if action == "batch":
            return self._execute_batch(params, context)
        
        action_map = {
            "move": self._move_document,
            "archive": self._archive_document,
            "restore": self._restore_document,
            "list_archived": self._list_archived,
            "find_versions": self._find_versions,
            "clean": self._clean_workspace,
            "clean_aux": self._clean_auxiliary_files,
            "refresh_aux": self._refresh_auxiliary_files,
            "list_aux": self._list_auxiliary_files
        }
        
        if action not in action_map:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
                "available_actions": list(action_map.keys()) + ["batch"]
            }
        
        try:
            return action_map[action](params, context)
        except Exception as e:
            return {
                "success": False,
                "error": f"Organizer operation failed: {str(e)}"
            }
    
    def _execute_batch(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute multiple organizer actions in sequence.
        
        params should contain:
            operations: List of {"action": "...", "params": {...}} dicts
            stop_on_error: Whether to stop if an operation fails (default: False)
            dry_run: Whether to just validate without executing (default: False, auto-enabled)
        """
        operations = params.get("operations", [])
        stop_on_error = params.get("stop_on_error", False)
        explicit_dry_run = params.get("dry_run", False)
        
        if not operations:
            return {"success": False, "error": "No operations provided"}
        
        # Always validate first (implicit dry run)
        validation_errors = self._validate_batch(operations)
        if validation_errors:
            return {
                "success": False,
                "error": "Batch validation failed",
                "validation_errors": validation_errors,
                "message": f"Operation {validation_errors[0]['index']} ({validation_errors[0]['action']}) will fail: {validation_errors[0]['reason']}"
            }
        
        # If explicit dry run requested, return success
        if explicit_dry_run:
            return {
                "success": True,
                "message": "Dry run successful - all operations validated",
                "operations_validated": len(operations)
            }
        
        # Execute the batch
        results = []
        total_success = True
        
        for i, op in enumerate(operations):
            action = op.get("action")
            op_params = op.get("params", {})
            
            # Execute the operation
            result = self.execute(action, op_params, context)
            
            # Add operation info to result
            result["operation_index"] = i
            result["operation_action"] = action
            results.append(result)
            
            # Check if we should stop
            if not result.get("success", False):
                total_success = False
                if stop_on_error:
                    break
        
        # Summarize results
        successful = sum(1 for r in results if r.get("success", False))
        failed = len(results) - successful
        
        return {
            "success": total_success,
            "message": f"Batch completed: {successful} successful, {failed} failed",
            "total_operations": len(operations),
            "completed_operations": len(results),
            "results": results
        }
    
    def _validate_batch(self, operations: list) -> list:
        """Validate batch operations before execution.
        
        Returns list of validation errors, empty if all valid.
        """
        errors = []
        
        for i, op in enumerate(operations):
            action = op.get("action")
            params = op.get("params", {})
            
            # Check action exists
            valid_actions = ["move", "archive", "restore", "list_archived", 
                           "find_versions", "clean", "clean_aux", "refresh_aux", 
                           "list_aux"]
            
            if not action:
                errors.append({
                    "index": i,
                    "action": "undefined",
                    "reason": "No action specified"
                })
                continue
                
            if action not in valid_actions:
                errors.append({
                    "index": i,
                    "action": action,
                    "reason": f"Unknown action '{action}'"
                })
                continue
            
            # Validate specific actions
            if action == "move":
                if not params.get("source"):
                    errors.append({
                        "index": i,
                        "action": action,
                        "reason": "Missing required parameter 'source'"
                    })
                elif not Path(params["source"]).expanduser().exists():
                    errors.append({
                        "index": i,
                        "action": action,
                        "reason": f"Source file not found: {params['source']}"
                    })
                elif not params.get("destination"):
                    errors.append({
                        "index": i,
                        "action": action,
                        "reason": "Missing required parameter 'destination'"
                    })
                    
            elif action in ["archive", "list_aux", "refresh_aux"]:
                if not params.get("path"):
                    errors.append({
                        "index": i,
                        "action": action,
                        "reason": "Missing required parameter 'path'"
                    })
                elif not Path(params["path"]).expanduser().exists():
                    errors.append({
                        "index": i,
                        "action": action,
                        "reason": f"Path not found: {params['path']}"
                    })
                    
            elif action == "restore":
                if not params.get("archive_path"):
                    errors.append({
                        "index": i,
                        "action": action,
                        "reason": "Missing required parameter 'archive_path'"
                    })
                elif not Path(params["archive_path"]).expanduser().exists():
                    errors.append({
                        "index": i,
                        "action": action,
                        "reason": f"Archive not found: {params['archive_path']}"
                    })
                    
            elif action == "find_versions":
                if not params.get("filename"):
                    errors.append({
                        "index": i,
                        "action": action,
                        "reason": "Missing required parameter 'filename'"
                    })
        
        return errors
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return capabilities of the organizer operation."""
        return {
            "operation": "organizer",
            "description": "Manage document lifecycle and organization",
            "actions": {
                "move": {
                    "description": "Move documents to different locations",
                    "required_params": ["source", "destination"],
                    "optional_params": []
                },
                "archive": {
                    "description": "Archive (soft delete) documents",
                    "required_params": ["path"],
                    "optional_params": ["reason"]
                },
                "restore": {
                    "description": "Restore archived documents",
                    "required_params": ["archive_path"],
                    "optional_params": ["restore_path"]
                },
                "list_archived": {
                    "description": "List archived documents",
                    "required_params": [],
                    "optional_params": ["directory"]
                },
                "find_versions": {
                    "description": "Find all versions of a document",
                    "required_params": ["filename"],
                    "optional_params": ["directory"]
                },
                "clean": {
                    "description": "Archive multiple files by pattern",
                    "required_params": [],
                    "optional_params": ["directory", "pattern"]
                },
                "clean_aux": {
                    "description": "Clean LaTeX auxiliary files",
                    "required_params": [],
                    "optional_params": ["directory"]
                },
                "refresh_aux": {
                    "description": "Update auxiliary file definitions",
                    "required_params": ["extensions"],
                    "optional_params": []
                },
                "list_aux": {
                    "description": "List current auxiliary file patterns",
                    "required_params": [],
                    "optional_params": []
                },
                "batch": {
                    "description": "Execute multiple operations",
                    "required_params": ["operations"],
                    "optional_params": []
                }
            }
        }
    
    def _move_document(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Move document to new location."""
        source = Path(params.get("source", "")).expanduser()
        dest_param = params.get("destination", "")
        
        if not source.exists():
            return {"success": False, "error": f"Source not found: {source}"}
        
        # Parse destination
        dest = Path(dest_param).expanduser()
        
        # If destination is a directory, keep original filename
        if dest.is_dir() or dest_param.endswith('/'):
            dest = dest / source.name
            dest.parent.mkdir(parents=True, exist_ok=True)
        else:
            # Destination includes filename
            dest.parent.mkdir(parents=True, exist_ok=True)
        
        # Handle existing file at destination
        if dest.exists():
            # Archive the existing file first
            archive_result = document_manager.archive_document(
                str(dest), 
                reason=f"replaced by {source.name}"
            )
            if not archive_result["success"]:
                return {
                    "success": False,
                    "error": f"Failed to archive existing file: {archive_result['error']}"
                }
        
        try:
            shutil.move(str(source), str(dest))
            return {
                "success": True,
                "moved_from": str(source),
                "moved_to": str(dest),
                "message": f"Moved {source.name} to {dest}"
            }
        except Exception as e:
            return {"success": False, "error": f"Move failed: {str(e)}"}
    
    def _archive_document(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Archive (soft delete) a document."""
        path = params.get("path", "")
        reason = params.get("reason", "manual")
        
        result = document_manager.archive_document(path, reason)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Archived {Path(path).name} to {result['archive_name']}",
                "archive_path": result["archive_path"],
                "details": result
            }
        else:
            return result
    
    def _restore_document(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Restore an archived document."""
        archive_path = params.get("archive_path", "")
        restore_path = params.get("restore_path")
        
        result = document_manager.restore_document(archive_path, restore_path)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Restored document to {result['restored_to']}",
                "details": result
            }
        else:
            return result
    
    def _list_archived(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """List archived documents in a directory."""
        directory = params.get("directory", "")
        
        if not directory:
            # Use current project directory if available
            project = context.get("current_project")
            if project:
                directory = project.get("path", ".")
            else:
                directory = "."
        
        archives = document_manager.list_archived(directory)
        
        if not archives:
            return {
                "success": True,
                "message": "No archived documents found",
                "archives": []
            }
        
        # Format for display
        formatted = []
        for arch in archives:
            size_kb = arch.get("size", 0) / 1024
            formatted.append({
                "name": arch.get("original_name", Path(arch["current_path"]).name),
                "archived_at": arch.get("archived_at", arch.get("modified", "unknown")),
                "reason": arch.get("reason", "unknown"),
                "size": f"{size_kb:.1f} KB",
                "path": arch["current_path"]
            })
        
        return {
            "success": True,
            "message": f"Found {len(archives)} archived document(s)",
            "archives": formatted
        }
    
    def _find_versions(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Find all versions of a document."""
        filename = params.get("filename", "")
        directory = params.get("directory", "")
        
        if not directory:
            # Use current project directory if available
            project = context.get("current_project")
            if project:
                directory = project.get("path", ".")
            else:
                directory = "."
        
        versions = document_manager.find_versions(filename, directory)
        
        if not versions:
            return {
                "success": True,
                "message": f"No versions of '{filename}' found",
                "versions": []
            }
        
        # Format for display
        formatted = []
        for ver in versions:
            size_kb = ver["size"] / 1024
            formatted.append({
                "name": ver["name"],
                "type": ver["type"],
                "modified": ver["modified"],
                "size": f"{size_kb:.1f} KB",
                "path": ver["path"]
            })
        
        return {
            "success": True,
            "message": f"Found {len(versions)} version(s) of '{filename}'",
            "versions": formatted
        }
    
    def _clean_workspace(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Clean workspace by archiving files matching pattern."""
        directory = params.get("directory", "")
        pattern = params.get("pattern", "*")
        
        if not directory:
            # Use current project directory if available  
            project = context.get("current_project")
            if project:
                directory = project.get("path", ".")
            else:
                directory = "."
        
        result = document_manager.clean_workspace(directory, pattern)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Archived {result['archived_count']} file(s)",
                "details": result
            }
        else:
            return {
                "success": False,
                "message": f"Cleanup completed with errors",
                "details": result
            }
    
    def _clean_auxiliary_files(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Clean LaTeX auxiliary files while preserving source and output."""
        path = Path(params.get("path", "")).expanduser()
        keep_bib = params.get("keep_bib", True)
        
        if not path.exists():
            return {"success": False, "error": f"Path not found: {path}"}
        
        # Define auxiliary file extensions
        aux_extensions = [
            '.aux', '.log', '.out', '.toc', '.lof', '.lot',
            '.idx', '.ind', '.ilg', '.glo', '.gls', '.glg',
            '.dvi', '.fls', '.fdb_latexmk', '.synctex.gz',
            '.nav', '.snm', '.vrb',  # Beamer
            '.blg',  # Bibliography log
        ]
        
        if not keep_bib:
            aux_extensions.extend(['.bbl', '.bcf', '.run.xml'])
        
        cleaned = []
        errors = []
        
        # If path is a directory, clean all LaTeX files in it
        if path.is_dir():
            for tex_file in path.glob("*.tex"):
                stem = tex_file.stem
                for ext in aux_extensions:
                    aux_file = path / f"{stem}{ext}"
                    if aux_file.exists():
                        try:
                            # Archive instead of delete
                            result = document_manager.archive_document(
                                str(aux_file), 
                                reason="auxiliary_cleanup"
                            )
                            if result["success"]:
                                cleaned.append(aux_file.name)
                            else:
                                errors.append(f"{aux_file.name}: {result['error']}")
                        except Exception as e:
                            errors.append(f"{aux_file.name}: {str(e)}")
        else:
            # Clean auxiliary files for specific LaTeX file
            stem = path.stem
            parent = path.parent
            for ext in aux_extensions:
                aux_file = parent / f"{stem}{ext}"
                if aux_file.exists():
                    try:
                        result = document_manager.archive_document(
                            str(aux_file),
                            reason="auxiliary_cleanup"
                        )
                        if result["success"]:
                            cleaned.append(aux_file.name)
                        else:
                            errors.append(f"{aux_file.name}: {result['error']}")
                    except Exception as e:
                        errors.append(f"{aux_file.name}: {str(e)}")
        
        return {
            "success": len(errors) == 0,
            "message": f"Cleaned {len(cleaned)} auxiliary file(s)",
            "cleaned_files": cleaned,
            "errors": errors,
            "kept_bibliography": keep_bib
        }
    
    def _refresh_auxiliary_files(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Remove specific auxiliary files to force regeneration."""
        path = Path(params.get("path", "")).expanduser()
        types = params.get("types", "all")
        
        if not path.exists() or not path.suffix == '.tex':
            return {"success": False, "error": f"LaTeX file not found: {path}"}
        
        # Define file types to remove
        type_map = {
            "toc": ['.toc', '.lof', '.lot'],  # Table of contents, figures, tables
            "bib": ['.bbl', '.blg', '.bcf', '.run.xml'],  # Bibliography
            "idx": ['.idx', '.ind', '.ilg'],  # Index
            "all": []  # Will use all types
        }
        
        if types == "all":
            extensions = []
            for exts in type_map.values():
                if isinstance(exts, list):
                    extensions.extend(exts)
        else:
            extensions = type_map.get(types, [])
            if not extensions:
                return {"success": False, "error": f"Unknown type: {types}"}
        
        removed = []
        errors = []
        
        stem = path.stem
        parent = path.parent
        
        for ext in extensions:
            aux_file = parent / f"{stem}{ext}"
            if aux_file.exists():
                try:
                    aux_file.unlink()
                    removed.append(aux_file.name)
                except Exception as e:
                    errors.append(f"{aux_file.name}: {str(e)}")
        
        return {
            "success": len(errors) == 0,
            "message": f"Removed {len(removed)} file(s) for regeneration",
            "removed_files": removed,
            "errors": errors,
            "hint": "Run LaTeX compilation to regenerate these files"
        }
    
    def _list_auxiliary_files(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """List all auxiliary files for a LaTeX document."""
        path = Path(params.get("path", "")).expanduser()
        
        if not path.exists() or not path.suffix == '.tex':
            return {"success": False, "error": f"LaTeX file not found: {path}"}
        
        stem = path.stem
        parent = path.parent
        
        # Check for all possible auxiliary files
        aux_files = {
            "compilation": [],
            "bibliography": [],
            "index": [],
            "beamer": [],
            "other": []
        }
        
        file_categories = {
            "compilation": ['.aux', '.log', '.out', '.fls', '.fdb_latexmk'],
            "bibliography": ['.bbl', '.blg', '.bcf', '.run.xml'],
            "index": ['.idx', '.ind', '.ilg', '.glo', '.gls', '.glg'],
            "beamer": ['.nav', '.snm', '.vrb'],
            "other": ['.toc', '.lof', '.lot', '.dvi', '.synctex.gz']
        }
        
        total_size = 0
        
        for category, extensions in file_categories.items():
            for ext in extensions:
                aux_file = parent / f"{stem}{ext}"
                if aux_file.exists():
                    size = aux_file.stat().st_size
                    total_size += size
                    aux_files[category].append({
                        "name": aux_file.name,
                        "size": f"{size/1024:.1f} KB",
                        "modified": datetime.fromtimestamp(aux_file.stat().st_mtime).isoformat()
                    })
        
        # Count total files
        total_files = sum(len(files) for files in aux_files.values())
        
        return {
            "success": True,
            "message": f"Found {total_files} auxiliary file(s)",
            "total_size": f"{total_size/1024:.1f} KB",
            "files": aux_files,
            "latex_file": path.name
        }