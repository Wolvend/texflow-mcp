"""
Printer Operation implementation for TeXFlow.

Provides semantic enhancements for printer management operations.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

# Import the main texflow module for printer access
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
import texflow


class PrinterOperation:
    """Handles printer-related operations with semantic understanding."""
    
    def __init__(self, texflow_instance):
        """
        Initialize with reference to TeXFlow instance.
        
        Args:
            texflow_instance: Instance of TeXFlow with printer functionality
        """
        self.texflow = texflow_instance
        self._printer_cache = {}  # Cache printer info to reduce queries
        
    def execute(self, action: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a printer operation with semantic enhancements.
        
        Actions:
            - list: Show available printers with recommendations
            - info: Get detailed printer information
            - set_default: Change default printer with workflow hints
            - enable/disable: Manage printer availability
            - update: Update printer metadata
        """
        # Map actions to handler methods
        action_map = {
            "list": self._list_printers,
            "info": self._get_printer_info,
            "set_default": self._set_default_printer,
            "enable": self._enable_printer,
            "disable": self._disable_printer,
            "update": self._update_printer
        }
        
        if action not in action_map:
            return {
                "error": f"Unknown printer action: {action}",
                "available_actions": list(action_map.keys())
            }
        
        return action_map[action](params, context)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get printer operation capabilities."""
        return {
            "actions": {
                "list": {
                    "description": "List all available printers with status",
                    "required_params": [],
                    "workflow_hints": "Shows printer recommendations based on document type"
                },
                "info": {
                    "description": "Get detailed printer information",
                    "required_params": ["name"],
                    "optional_params": []
                },
                "set_default": {
                    "description": "Change the default printer",
                    "required_params": ["name"],
                    "workflow_hints": "Updates printer preference for future jobs"
                },
                "enable": {
                    "description": "Enable printer to accept jobs",
                    "required_params": ["name"]
                },
                "disable": {
                    "description": "Disable printer from accepting jobs",
                    "required_params": ["name"]
                },
                "update": {
                    "description": "Update printer description/location",
                    "required_params": ["name"],
                    "optional_params": ["description", "location"]
                }
            },
            "system_requirements": {
                "command": [
                    {
                        "name": "lpstat",
                        "required_for": ["list", "info"],
                        "install_hint": "CUPS printing system required"
                    },
                    {
                        "name": "lpadmin",
                        "required_for": ["set_default", "enable", "disable", "update"],
                        "install_hint": "CUPS admin tools required"
                    }
                ]
            }
        }
    
    def _list_printers(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """List printers with semantic enhancements."""
        try:
            # Call original implementation
            result = self.texflow.printer("list")
            
            # Parse the string result to add semantic enhancements
            printers = self._parse_printer_list(result)
            
            # Add workflow hints
            if printers:
                # Check if we have a document context
                doc_format = context.get("document_format", "unknown")
                recommendations = []
                
                # Find suitable printers
                for printer in printers:
                    if printer.get("accepting", True):
                        if doc_format == "latex" and "laser" in printer.get("name", "").lower():
                            recommendations.append({
                                "name": printer["name"],
                                "reason": "Laser printer recommended for LaTeX documents"
                            })
                        elif "default" in printer.get("status", ""):
                            recommendations.append({
                                "name": printer["name"],
                                "reason": "System default printer"
                            })
                
                return {
                    "success": True,
                    "printers": printers,
                    "count": len(printers),
                    "recommendations": recommendations,
                    "workflow": {
                        "message": f"Found {len(printers)} printer(s)",
                        "next_steps": [
                            {"action": "set_default", "description": "Change default printer"},
                            {"action": "print", "description": "Send document to printer"}
                        ]
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "No printers found",
                    "workflow": {
                        "message": "No printers configured",
                        "next_steps": [
                            {"action": "setup", "description": "Configure a printer using system settings"}
                        ]
                    }
                }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _get_printer_info(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Get printer info with semantic enhancements."""
        name = params.get("name")
        if not name:
            return {"error": "Printer name is required"}
        
        try:
            # Call original implementation
            result = self.texflow.printer("info", name)
            
            # Add semantic enhancements
            info = self._parse_printer_info(result)
            
            return {
                "success": True,
                "printer": name,
                "info": info,
                "workflow": {
                    "message": f"Printer '{name}' information retrieved",
                    "next_steps": []
                }
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _set_default_printer(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Set default printer with workflow hints."""
        name = params.get("name")
        if not name:
            return {"error": "Printer name is required"}
        
        try:
            # Call original implementation
            result = self.texflow.printer("set_default", name)
            
            return {
                "success": True,
                "printer": name,
                "message": f"Default printer set to '{name}'",
                "workflow": {
                    "message": "Default printer updated",
                    "next_steps": [
                        {"action": "print", "description": f"Print documents using {name}"},
                        {"action": "list", "description": "View all printers"}
                    ]
                }
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _enable_printer(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Enable printer with workflow hints."""
        name = params.get("name")
        if not name:
            return {"error": "Printer name is required"}
        
        try:
            result = self.texflow.printer("enable", name)
            
            return {
                "success": True,
                "printer": name,
                "message": f"Printer '{name}' enabled",
                "workflow": {
                    "message": "Printer is now accepting jobs",
                    "next_steps": [
                        {"action": "print", "description": f"Send jobs to {name}"}
                    ]
                }
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _disable_printer(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Disable printer with workflow hints."""
        name = params.get("name")
        if not name:
            return {"error": "Printer name is required"}
        
        try:
            result = self.texflow.printer("disable", name)
            
            return {
                "success": True,
                "printer": name,
                "message": f"Printer '{name}' disabled",
                "workflow": {
                    "message": "Printer will not accept new jobs",
                    "next_steps": [
                        {"action": "list", "description": "Find alternative printers"},
                        {"action": "enable", "description": f"Re-enable {name} when ready"}
                    ]
                }
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _update_printer(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Update printer metadata."""
        name = params.get("name")
        if not name:
            return {"error": "Printer name is required"}
        
        description = params.get("description")
        location = params.get("location")
        
        try:
            result = self.texflow.printer("update", name, description, location)
            
            updates = []
            if description:
                updates.append(f"description: {description}")
            if location:
                updates.append(f"location: {location}")
            
            return {
                "success": True,
                "printer": name,
                "updates": updates,
                "message": f"Printer '{name}' updated",
                "workflow": {
                    "message": "Printer metadata updated",
                    "next_steps": [
                        {"action": "info", "description": "View updated printer info"}
                    ]
                }
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _parse_printer_list(self, result_str: str) -> List[Dict[str, Any]]:
        """Parse printer list from string result."""
        # This is a simplified parser - actual implementation would be more robust
        printers = []
        lines = result_str.split('\n')
        
        for line in lines:
            if line.strip() and not line.startswith('Printers:'):
                # Basic parsing - would need enhancement for real use
                parts = line.split()
                if parts:
                    printer = {
                        "name": parts[0].strip('•'),
                        "status": "ready" if "Ready" in line else "offline",
                        "accepting": "accepting" in line.lower(),
                        "default": "default" in line.lower()
                    }
                    printers.append(printer)
        
        return printers
    
    def _parse_printer_info(self, result_str: str) -> Dict[str, Any]:
        """Parse printer info from string result."""
        # Simplified parser for printer info
        info = {}
        lines = result_str.split('\n')
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip().lower()] = value.strip()
        
        return info