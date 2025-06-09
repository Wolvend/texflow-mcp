"""Document management operations for TeXFlow.

Provides soft delete, archiving, and version management without external dependencies.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any


class DocumentManager:
    """Manages document lifecycle with soft delete and archiving."""
    
    ARCHIVE_DIR = ".texflow_archive"
    
    def __init__(self):
        """Initialize document manager."""
        pass
    
    def archive_document(self, file_path: str, reason: str = "manual") -> Dict[str, Any]:
        """Archive (soft delete) a document by moving it to hidden archive folder.
        
        Args:
            file_path: Path to document to archive
            reason: Reason for archiving (manual, replaced, outdated, etc.)
            
        Returns:
            Dict with archive details
        """
        source = Path(file_path).expanduser()
        
        if not source.exists():
            return {"success": False, "error": f"File not found: {source}"}
        
        # Create archive directory in the same folder as the file
        archive_dir = source.parent / self.ARCHIVE_DIR
        archive_dir.mkdir(exist_ok=True)
        
        # Generate archived filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = source.stem
        extension = source.suffix
        
        # Check for existing archived versions and increment sequence
        sequence = 1
        while True:
            archived_name = f"{base_name}_{timestamp}_{sequence:03d}{extension}"
            dest = archive_dir / archived_name
            if not dest.exists():
                break
            sequence += 1
        
        try:
            # Move file to archive
            shutil.move(str(source), str(dest))
            
            # Create metadata file
            metadata_path = dest.with_suffix(dest.suffix + ".meta")
            metadata = {
                "original_path": str(source),
                "archived_at": datetime.now().isoformat(),
                "reason": reason,
                "original_name": source.name,
                "sequence": sequence
            }
            
            with open(metadata_path, 'w') as f:
                import json
                json.dump(metadata, f, indent=2)
            
            return {
                "success": True,
                "original_path": str(source),
                "archive_path": str(dest),
                "archive_name": archived_name,
                "timestamp": timestamp,
                "sequence": sequence,
                "reason": reason
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to archive: {str(e)}"}
    
    def list_archived(self, directory: str) -> List[Dict[str, Any]]:
        """List all archived documents in a directory.
        
        Args:
            directory: Directory to check for archives
            
        Returns:
            List of archived documents with metadata
        """
        dir_path = Path(directory).expanduser()
        archive_dir = dir_path / self.ARCHIVE_DIR
        
        if not archive_dir.exists():
            return []
        
        archives = []
        for item in archive_dir.iterdir():
            if item.suffix == ".meta":
                continue
                
            # Look for metadata file
            meta_path = Path(str(item) + ".meta")
            if meta_path.exists():
                try:
                    with open(meta_path, 'r') as f:
                        import json
                        metadata = json.load(f)
                    
                    # Add file info
                    metadata["current_path"] = str(item)
                    metadata["size"] = item.stat().st_size
                    metadata["modified"] = datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                    
                    archives.append(metadata)
                except:
                    # If metadata is corrupted, still list the file
                    archives.append({
                        "current_path": str(item),
                        "original_name": item.name,
                        "size": item.stat().st_size,
                        "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                    })
            else:
                # No metadata file
                archives.append({
                    "current_path": str(item),
                    "original_name": item.name,
                    "size": item.stat().st_size,
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                })
        
        # Sort by modification time, newest first
        archives.sort(key=lambda x: x.get('archived_at', x.get('modified', '')), reverse=True)
        
        return archives
    
    def restore_document(self, archive_path: str, restore_path: Optional[str] = None) -> Dict[str, Any]:
        """Restore an archived document.
        
        Args:
            archive_path: Path to archived document
            restore_path: Where to restore (defaults to original location)
            
        Returns:
            Dict with restore details
        """
        source = Path(archive_path).expanduser()
        
        if not source.exists():
            return {"success": False, "error": f"Archive not found: {source}"}
        
        # Try to read metadata
        meta_path = Path(str(source) + ".meta")
        original_path = None
        if meta_path.exists():
            try:
                with open(meta_path, 'r') as f:
                    import json
                    metadata = json.load(f)
                    original_path = metadata.get('original_path')
            except:
                pass
        
        # Determine restore path
        if restore_path:
            dest = Path(restore_path).expanduser()
        elif original_path:
            dest = Path(original_path)
        else:
            # Restore to parent directory with original-ish name
            parent = source.parent.parent  # Go up from .texflow_archive
            # Remove timestamp and sequence from name
            name_parts = source.stem.split('_')
            if len(name_parts) > 3:
                # Assume format: originalname_YYYYMMDD_HHMMSS_###
                original_stem = '_'.join(name_parts[:-3])
            else:
                original_stem = source.stem
            dest = parent / (original_stem + source.suffix)
        
        # Handle existing file at destination
        if dest.exists():
            base = dest.stem
            suffix = dest.suffix
            counter = 1
            while dest.exists():
                dest = dest.parent / f"{base}_{counter}{suffix}"
                counter += 1
        
        try:
            # Move file back
            shutil.move(str(source), str(dest))
            
            # Remove metadata file
            if meta_path.exists():
                meta_path.unlink()
            
            return {
                "success": True,
                "restored_from": str(source),
                "restored_to": str(dest),
                "original_path": original_path
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to restore: {str(e)}"}
    
    def clean_workspace(self, directory: str, pattern: str = "*") -> Dict[str, Any]:
        """Archive multiple files matching a pattern.
        
        Args:
            directory: Directory to clean
            pattern: Glob pattern for files to archive
            
        Returns:
            Summary of archived files
        """
        dir_path = Path(directory).expanduser()
        
        if not dir_path.exists():
            return {"success": False, "error": f"Directory not found: {directory}"}
        
        archived = []
        errors = []
        
        for file_path in dir_path.glob(pattern):
            if file_path.is_file() and not file_path.name.startswith('.'):
                result = self.archive_document(str(file_path), reason="cleanup")
                if result["success"]:
                    archived.append(result["archive_name"])
                else:
                    errors.append(f"{file_path.name}: {result['error']}")
        
        return {
            "success": len(errors) == 0,
            "archived_count": len(archived),
            "archived_files": archived,
            "errors": errors
        }
    
    def find_versions(self, filename: str, directory: str) -> List[Dict[str, Any]]:
        """Find all versions of a document (current and archived).
        
        Args:
            filename: Base filename to search for
            directory: Directory to search in
            
        Returns:
            List of all versions found
        """
        dir_path = Path(directory).expanduser()
        base_name = Path(filename).stem
        
        versions = []
        
        # Check current directory
        for file_path in dir_path.glob(f"{base_name}*"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                versions.append({
                    "path": str(file_path),
                    "name": file_path.name,
                    "type": "current",
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    "size": file_path.stat().st_size
                })
        
        # Check archive
        archive_dir = dir_path / self.ARCHIVE_DIR
        if archive_dir.exists():
            for file_path in archive_dir.glob(f"{base_name}*"):
                if file_path.suffix != ".meta":
                    versions.append({
                        "path": str(file_path),
                        "name": file_path.name,
                        "type": "archived",
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                        "size": file_path.stat().st_size
                    })
        
        # Sort by modification time
        versions.sort(key=lambda x: x["modified"], reverse=True)
        
        return versions


# Singleton instance
document_manager = DocumentManager()