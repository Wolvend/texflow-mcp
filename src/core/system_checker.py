"""
System Dependencies Checker for TeXFlow MCP Server.

This module checks system-level dependencies defined in the manifest
and provides status information via MCP resources.
"""

import json
import subprocess
import shutil
import re
import platform
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


class SystemDependencyChecker:
    """Checks system dependencies and provides status reporting."""
    
    def __init__(self, manifest_path: Optional[Path] = None):
        """
        Initialize the dependency checker.
        
        Args:
            manifest_path: Path to system dependencies manifest JSON file.
                          Defaults to config/system_dependencies.json
        """
        if manifest_path is None:
            # Default to manifest in config directory relative to this file
            self.manifest_path = Path(__file__).parent.parent.parent / "config" / "system_dependencies.json"
        else:
            self.manifest_path = Path(manifest_path)
        
        self.platform_name = self._detect_platform()
        self.manifest = self._load_manifest()
        self._check_cache = {}  # Cache results for performance
        
    def _detect_platform(self) -> str:
        """Detect the current platform."""
        system = platform.system().lower()
        if system == "darwin":
            return "macos"
        elif system == "windows":
            return "windows"
        else:
            return "linux"  # Default for Unix-like systems
    
    def _load_manifest(self) -> Dict[str, Any]:
        """Load the system dependencies manifest."""
        try:
            with open(self.manifest_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"System dependencies manifest not found: {self.manifest_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in manifest file: {e}")
    
    def check_dependency(self, dep_name: str, dep_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check a single dependency.
        
        Args:
            dep_name: Name of the dependency
            dep_config: Configuration for the dependency from manifest
            
        Returns:
            Status dictionary with availability, version, and details
        """
        # Check cache first
        cache_key = f"{dep_name}_{self.platform_name}"
        if cache_key in self._check_cache:
            return self._check_cache[cache_key]
        
        result = {
            "name": dep_name,
            "display_name": dep_config.get("name", dep_name),
            "description": dep_config.get("description", ""),
            "required_for": dep_config.get("required_for", []),
            "category": dep_config.get("category", "unknown"),
            "available": False,
            "version": None,
            "executable_path": None,
            "status": "not_found",
            "message": "",
            "platform_supported": True,
            "checked_at": datetime.now().isoformat()
        }
        
        # Check if dependency is supported on current platform
        platform_info = dep_config.get("platforms", {}).get(self.platform_name, {})
        if not platform_info and self.platform_name not in dep_config.get("platforms", {}):
            result["platform_supported"] = False
            result["status"] = "platform_not_supported"
            result["message"] = f"Not supported on {self.platform_name}"
            self._check_cache[cache_key] = result
            return result
        
        # Check for special platform notes
        platform_note = platform_info.get("note")
        if platform_note:
            result["platform_note"] = platform_note
        
        # Try to find the executable
        commands = dep_config.get("commands", [dep_name])
        executable_path = None
        
        for cmd in commands:
            executable_path = shutil.which(cmd)
            if executable_path:
                result["executable_path"] = executable_path
                result["command_used"] = cmd
                break
        
        if not executable_path:
            result["status"] = "not_found"
            result["message"] = f"Command not found in PATH: {', '.join(commands)}"
            # Add installation hints
            if platform_info and "package_managers" in platform_info:
                result["installation_options"] = platform_info["package_managers"]
            self._check_cache[cache_key] = result
            return result
        
        # Executable found, now check version
        result["available"] = True
        result["status"] = "available"
        
        version_info = self._get_version(dep_config, executable_path)
        if version_info:
            result["version"] = version_info["version"]
            result["version_raw"] = version_info["raw_output"]
            result["message"] = f"Available (v{version_info['version']})"
        else:
            result["message"] = "Available (version unknown)"
        
        self._check_cache[cache_key] = result
        return result
    
    def _get_version(self, dep_config: Dict[str, Any], executable_path: str) -> Optional[Dict[str, str]]:
        """
        Get version information for a dependency.
        
        Args:
            dep_config: Dependency configuration
            executable_path: Path to the executable
            
        Returns:
            Version information dict or None if unavailable
        """
        version_command = dep_config.get("version_command")
        if not version_command:
            return None
        
        try:
            # Replace the command name with the full path
            cmd_parts = version_command.split()
            cmd_parts[0] = executable_path
            
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            raw_output = result.stdout + result.stderr
            
            # Extract version using pattern if provided
            version_pattern = dep_config.get("version_pattern")
            if version_pattern:
                match = re.search(version_pattern, raw_output, re.IGNORECASE)
                if match:
                    return {
                        "version": match.group(1),
                        "raw_output": raw_output.strip()
                    }
            
            # Fallback: return first line that contains digits
            for line in raw_output.split('\n'):
                if re.search(r'\d+\.\d+', line):
                    version_match = re.search(r'(\d+\.\d+(?:\.\d+)*)', line)
                    if version_match:
                        return {
                            "version": version_match.group(1),
                            "raw_output": raw_output.strip()
                        }
            
            return {
                "version": "unknown",
                "raw_output": raw_output.strip()
            }
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return None
    
    def check_all_dependencies(self) -> Dict[str, Any]:
        """
        Check all dependencies defined in the manifest.
        
        Returns:
            Complete status report for all dependencies
        """
        report = {
            "metadata": {
                "manifest_version": self.manifest.get("metadata", {}).get("version", "unknown"),
                "platform": self.platform_name,
                "checked_at": datetime.now().isoformat(),
                "manifest_path": str(self.manifest_path)
            },
            "summary": {
                "total_dependencies": 0,
                "essential_available": 0,
                "essential_total": 0,
                "optional_available": 0,
                "optional_total": 0,
                "overall_status": "unknown"
            },
            "dependencies": {
                "essential": {},
                "optional": {}
            },
            "categories": {}
        }
        
        # Check essential dependencies
        essential_deps = self.manifest.get("dependencies", {}).get("essential", {})
        for dep_name, dep_config in essential_deps.items():
            status = self.check_dependency(dep_name, dep_config)
            report["dependencies"]["essential"][dep_name] = status
            
            if status["available"]:
                report["summary"]["essential_available"] += 1
            report["summary"]["essential_total"] += 1
        
        # Check optional dependencies
        optional_deps = self.manifest.get("dependencies", {}).get("optional", {})
        for dep_name, dep_config in optional_deps.items():
            status = self.check_dependency(dep_name, dep_config)
            report["dependencies"]["optional"][dep_name] = status
            
            if status["available"]:
                report["summary"]["optional_available"] += 1
            report["summary"]["optional_total"] += 1
        
        # Calculate totals
        report["summary"]["total_dependencies"] = (
            report["summary"]["essential_total"] + 
            report["summary"]["optional_total"]
        )
        
        # Determine overall status
        if report["summary"]["essential_available"] == report["summary"]["essential_total"]:
            if report["summary"]["optional_available"] == report["summary"]["optional_total"]:
                report["summary"]["overall_status"] = "fully_operational"
            else:
                report["summary"]["overall_status"] = "operational"
        else:
            report["summary"]["overall_status"] = "degraded"
        
        # Generate category summaries
        categories = self.manifest.get("categories", {})
        for category_name, category_info in categories.items():
            category_deps = []
            
            # Find all dependencies in this category
            for section in ["essential", "optional"]:
                for dep_name, dep_status in report["dependencies"][section].items():
                    if dep_status["category"] == category_name:
                        category_deps.append(dep_status)
            
            if category_deps:
                available_count = sum(1 for dep in category_deps if dep["available"])
                report["categories"][category_name] = {
                    "description": category_info.get("description", ""),
                    "essential": category_info.get("essential", False),
                    "platform_specific": category_info.get("platform_specific", False),
                    "dependencies_count": len(category_deps),
                    "available_count": available_count,
                    "status": "available" if available_count == len(category_deps) else "partial" if available_count > 0 else "unavailable"
                }
        
        return report
    
    def get_missing_essential_dependencies(self) -> List[str]:
        """Get list of missing essential dependencies."""
        report = self.check_all_dependencies()
        missing = []
        
        for dep_name, dep_status in report["dependencies"]["essential"].items():
            if not dep_status["available"]:
                missing.append(dep_name)
        
        return missing
    
    def get_installation_suggestions(self) -> Dict[str, Any]:
        """Get installation suggestions for missing dependencies."""
        report = self.check_all_dependencies()
        suggestions = {
            "platform": self.platform_name,
            "missing_essential": [],
            "missing_optional": [],
            "platform_commands": {}
        }
        
        for section in ["essential", "optional"]:
            for dep_name, dep_status in report["dependencies"][section].items():
                if not dep_status["available"] and dep_status["platform_supported"]:
                    suggestion = {
                        "name": dep_name,
                        "description": dep_status["description"],
                        "installation_options": dep_status.get("installation_options", {}),
                        "platform_note": dep_status.get("platform_note")
                    }
                    
                    if section == "essential":
                        suggestions["missing_essential"].append(suggestion)
                    else:
                        suggestions["missing_optional"].append(suggestion)
        
        return suggestions
    
    def clear_cache(self):
        """Clear the dependency check cache."""
        self._check_cache.clear()