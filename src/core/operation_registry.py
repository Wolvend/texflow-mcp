"""
Operation Registry for TeXFlow

Manages registration and discovery of semantic operations.
"""

from typing import Dict, Any, List, Optional, Protocol
from abc import abstractmethod


class Operation(Protocol):
    """Protocol for semantic operations."""
    
    @abstractmethod
    def execute(self, action: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an operation action."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get operation capabilities and requirements."""
        pass


class OperationRegistry:
    """Registry for semantic operations."""
    
    def __init__(self):
        self.operations: Dict[str, Operation] = {}
        self.capabilities_cache: Dict[str, Dict[str, Any]] = {}
        
    def register(self, name: str, operation: Operation) -> None:
        """Register a semantic operation."""
        self.operations[name] = operation
        # Cache capabilities
        self.capabilities_cache[name] = operation.get_capabilities()
        
    def get(self, name: str) -> Optional[Operation]:
        """Get an operation by name."""
        return self.operations.get(name)
    
    def list_operations(self) -> List[str]:
        """List all registered operations."""
        return list(self.operations.keys())
    
    def get_capabilities(self, name: str) -> Optional[Dict[str, Any]]:
        """Get capabilities for an operation."""
        return self.capabilities_cache.get(name)
    
    def check_system_requirements(self) -> Dict[str, Any]:
        """Check system requirements for all operations."""
        requirements = {
            "satisfied": [],
            "missing": [],
            "warnings": []
        }
        
        for op_name, capabilities in self.capabilities_cache.items():
            if "system_requirements" in capabilities:
                for req_type, req_list in capabilities["system_requirements"].items():
                    for requirement in req_list:
                        status = self._check_requirement(req_type, requirement)
                        
                        if status["available"]:
                            requirements["satisfied"].append({
                                "operation": op_name,
                                "requirement": requirement,
                                "type": req_type
                            })
                        else:
                            requirements["missing"].append({
                                "operation": op_name,
                                "requirement": requirement,
                                "type": req_type,
                                "install_hint": status.get("install_hint", ""),
                                "user_action_required": status.get("user_action_required", False)
                            })
                            
                            if status.get("user_action_required"):
                                requirements["warnings"].append(
                                    f"{requirement} requires user action: {status.get('install_hint', '')}"
                                )
        
        return requirements
    
    def _check_requirement(self, req_type: str, requirement: Dict[str, Any]) -> Dict[str, Any]:
        """Check a specific system requirement."""
        # This would integrate with the existing dependency checking
        # from texflow.py's DEPENDENCIES system
        
        if req_type == "command":
            # Check if command exists in PATH
            import shutil
            return {
                "available": shutil.which(requirement["name"]) is not None,
                "install_hint": requirement.get("install_hint", ""),
                "user_action_required": requirement.get("user_install", False)
            }
        
        elif req_type == "python_package":
            # Check Python package
            try:
                __import__(requirement["name"])
                return {"available": True}
            except ImportError:
                return {
                    "available": False,
                    "install_hint": f"pip install {requirement['name']}",
                    "user_action_required": True
                }
        
        elif req_type == "tex_package":
            # Check TeX package availability
            # This requires running kpsewhich or similar
            import subprocess
            try:
                result = subprocess.run(
                    ["kpsewhich", f"{requirement['name']}.sty"],
                    capture_output=True,
                    text=True
                )
                return {
                    "available": result.returncode == 0,
                    "install_hint": requirement.get("install_hint", f"Install TeX package: {requirement['name']}"),
                    "user_action_required": True
                }
            except:
                return {
                    "available": False,
                    "install_hint": "TeX installation not found",
                    "user_action_required": True
                }
        
        elif req_type == "font":
            # Check font availability
            import subprocess
            try:
                result = subprocess.run(
                    ["fc-list", f":family={requirement['name']}"],
                    capture_output=True,
                    text=True
                )
                return {
                    "available": bool(result.stdout.strip()),
                    "install_hint": requirement.get("install_hint", f"Install font: {requirement['name']}"),
                    "user_action_required": True
                }
            except:
                return {
                    "available": False,
                    "install_hint": "Font configuration tools not found",
                    "user_action_required": True
                }
        
        return {"available": False, "install_hint": "Unknown requirement type"}
    
    def get_operation_requirements(self, operation: str, action: str = None) -> Dict[str, Any]:
        """Get specific requirements for an operation/action."""
        capabilities = self.get_capabilities(operation)
        if not capabilities:
            return {"error": f"Unknown operation: {operation}"}
        
        requirements = {
            "operation": operation,
            "system_requirements": [],
            "optional_features": []
        }
        
        # Get general operation requirements
        if "system_requirements" in capabilities:
            for req_type, req_list in capabilities["system_requirements"].items():
                for req in req_list:
                    status = self._check_requirement(req_type, req)
                    requirements["system_requirements"].append({
                        "name": req["name"],
                        "type": req_type,
                        "status": "available" if status["available"] else "missing",
                        "required_for": req.get("required_for", ["all"]),
                        "install_hint": status.get("install_hint", "")
                    })
        
        # Get action-specific requirements if provided
        if action and "action_requirements" in capabilities:
            if action in capabilities["action_requirements"]:
                action_reqs = capabilities["action_requirements"][action]
                for req in action_reqs:
                    requirements["system_requirements"].append(req)
        
        # Get optional features
        if "optional_features" in capabilities:
            for feature in capabilities["optional_features"]:
                feature_available = all(
                    self._check_requirement(req["type"], req)["available"]
                    for req in feature.get("requirements", [])
                )
                requirements["optional_features"].append({
                    "name": feature["name"],
                    "description": feature["description"],
                    "available": feature_available,
                    "requirements": feature.get("requirements", [])
                })
        
        return requirements