"""
Example of how document_operation.py should be refactored to use core services.
This shows the key changes needed to eliminate duplication.
"""

# Key changes to make in document_operation.py:

# 1. In __init__ method, add:
def __init__(self, texflow_instance):
    self.texflow = texflow_instance
    # Initialize core services
    self.conversion_service = get_conversion_service()
    self.validation_service = get_validation_service()
    self.format_detector = get_format_detector()

# 2. Replace _detect_format method:
def _detect_format(self, content: str, intent: str) -> str:
    """Detect optimal format based on content and intent using core service."""
    result = self.format_detector.detect(content, intent)
    return result["format"]

# 3. Replace _detect_format_from_path method:
def _detect_format_from_path(self, path: str) -> str:
    """Detect format from file extension using core service."""
    return self.format_detector.detect_from_path(path)

# 4. Replace _convert_document method:
def _convert_document(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Convert document between formats using core conversion service."""
    source = params.get("source")
    target_format = params.get("target_format", "latex")
    output_path = params.get("output_path")
    
    if not source:
        return {"error": "Source parameter is required"}
    
    try:
        # Resolve paths
        source_path = texflow.resolve_path(source)
        if output_path:
            output_path = texflow.resolve_path(output_path)
        
        # Use core conversion service
        result = self.conversion_service.convert(source_path, target_format, output_path)
        
        # Add semantic enhancements on success
        if result.get("success"):
            result["workflow"] = {
                "message": f"Document converted to {target_format} successfully",
                "next_steps": []
            }
            
            # Add format-specific suggestions
            if target_format == "latex":
                result["workflow"]["next_steps"].extend([
                    {"action": "validate", "description": "Check LaTeX syntax before compiling"},
                    {"action": "export", "description": "Generate PDF from LaTeX"}
                ])
            elif target_format == "pdf":
                result["workflow"]["next_steps"].extend([
                    {"action": "inspect", "description": "Preview the generated PDF"},
                    {"action": "print", "description": "Send to printer"}
                ])
            
        return result
            
    except Exception as e:
        return {"error": str(e)}

# 5. Replace _validate_document method:
def _validate_document(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Validate document syntax using core validation service."""
    content_or_path = params.get("content_or_path")
    format_hint = params.get("format", "auto")
    
    if not content_or_path:
        return {"error": "content_or_path parameter is required"}
    
    try:
        # Use core validation service
        result = self.validation_service.validate(content_or_path, format_hint)
        
        # Add semantic enhancements
        if result.get("success"):
            result["workflow"] = {
                "message": "Validation completed successfully",
                "next_steps": [
                    {"action": "export", "description": "Generate PDF from validated document"}
                ]
            }
        else:
            result["workflow"] = {
                "message": "Validation found issues",
                "next_steps": [
                    {"action": "edit", "description": "Fix the reported errors"},
                    {"action": "read", "description": "Review the document content"}
                ]
            }
        
        return result
        
    except Exception as e:
        return {"error": str(e)}

# The pattern is clear:
# 1. Core services handle the actual implementation
# 2. Document operation adds semantic workflow hints
# 3. No duplication of conversion/validation/detection logic