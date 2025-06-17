"""
Example of how to create a unified conversion service to eliminate duplication.
This would replace the multiple implementations of pandoc/xelatex calls.
"""

import subprocess
from pathlib import Path
from typing import Dict, Any, Optional


class ConversionService:
    """Centralized document conversion service."""
    
    def __init__(self):
        self.pandoc_available = self._check_command("pandoc")
        self.xelatex_available = self._check_command("xelatex")
    
    def _check_command(self, command: str) -> bool:
        """Check if a command is available."""
        try:
            subprocess.run([command, "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def markdown_to_latex(self, source_path: Path, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """Convert markdown to LaTeX with consistent parameters."""
        if not self.pandoc_available:
            return {"error": "pandoc not found - install pandoc for format conversion"}
        
        if not source_path.exists():
            return {"error": f"Source file not found: {source_path}"}
        
        if output_path is None:
            output_path = source_path.with_suffix('.tex')
        
        try:
            # Single implementation with -s flag for standalone document
            subprocess.run([
                "pandoc", 
                "-f", "markdown", 
                "-t", "latex", 
                "-s",  # Standalone document with headers
                "-o", str(output_path), 
                str(source_path)
            ], check=True)
            
            return {
                "success": True,
                "source": str(source_path),
                "output": str(output_path),
                "source_format": "markdown",
                "target_format": "latex"
            }
        except subprocess.CalledProcessError as e:
            return {"error": f"Conversion failed: {e}"}
    
    def latex_to_pdf(self, source_path: Path, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """Convert LaTeX to PDF with consistent parameters."""
        if not self.xelatex_available:
            return {"error": "XeLaTeX not found - install TeX Live for LaTeX support"}
        
        if not source_path.exists():
            return {"error": f"Source file not found: {source_path}"}
        
        try:
            # Run XeLaTeX in the source directory
            result = subprocess.run([
                "xelatex", 
                "-interaction=nonstopmode",
                source_path.name
            ], 
            cwd=source_path.parent,
            capture_output=True,
            text=True,
            check=True)
            
            # XeLaTeX creates PDF in same directory as source
            actual_pdf = source_path.with_suffix('.pdf')
            
            # Move to desired location if different
            if output_path and output_path != actual_pdf:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                actual_pdf.rename(output_path)
                final_path = output_path
            else:
                final_path = actual_pdf
            
            return {
                "success": True,
                "source": str(source_path),
                "output": str(final_path),
                "source_format": "latex",
                "target_format": "pdf"
            }
            
        except subprocess.CalledProcessError as e:
            # Extract meaningful error from XeLaTeX output
            errors = []
            for line in result.stderr.split('\n') if 'result' in locals() else []:
                if line.startswith('!'):
                    errors.append(line)
            
            error_msg = "\n".join(errors[:3]) if errors else str(e)
            return {"error": f"LaTeX compilation failed: {error_msg}"}
    
    def markdown_to_pdf(self, source_path: Path, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """Convert markdown directly to PDF using pandoc."""
        if not self.pandoc_available:
            return {"error": "pandoc not found - install pandoc for format conversion"}
        
        if not source_path.exists():
            return {"error": f"Source file not found: {source_path}"}
        
        if output_path is None:
            output_path = source_path.with_suffix('.pdf')
        
        try:
            subprocess.run([
                "pandoc",
                str(source_path),
                "-o", str(output_path),
                "--pdf-engine=xelatex"
            ], check=True)
            
            return {
                "success": True,
                "source": str(source_path),
                "output": str(output_path),
                "source_format": "markdown",
                "target_format": "pdf"
            }
        except subprocess.CalledProcessError as e:
            return {"error": f"PDF generation failed: {e}"}


# Usage example - how both semantic layer and texflow.py would use this:

# In document_operation.py:
def _convert_document(self, params, context):
    """Semantic wrapper around conversion service."""
    conversion_service = ConversionService()
    
    source = params.get("source")
    target_format = params.get("target_format")
    
    source_path = Path(source)
    
    # Use the unified service
    if source_path.suffix == '.md' and target_format == 'latex':
        result = conversion_service.markdown_to_latex(source_path)
    else:
        result = {"error": f"Conversion from {source_path.suffix} to {target_format} not supported"}
    
    # Add semantic enhancements
    if result.get("success"):
        result["workflow"] = {
            "message": "Document converted successfully",
            "next_steps": [
                {"action": "validate", "description": "Check LaTeX syntax"},
                {"action": "export", "description": "Generate PDF"}
            ]
        }
    
    return result


# In texflow.py:
def document(action, **kwargs):
    """Original document function using the service."""
    if action == "convert":
        conversion_service = ConversionService()
        
        source = kwargs.get("source")
        target_format = kwargs.get("target_format")
        
        # Use the same service
        if Path(source).suffix == '.md' and target_format == 'latex':
            result = conversion_service.markdown_to_latex(Path(source))
            if result.get("success"):
                return f"✓ Converted to LaTeX: {result['output']}"
            else:
                return f"❌ Error: {result['error']}"