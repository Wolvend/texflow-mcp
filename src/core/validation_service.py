"""
Centralized document validation service.
Single implementation for syntax checking and validation.
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Union
import re


class ValidationService:
    """Handles document validation for various formats."""
    
    def __init__(self):
        """Initialize and check available validation tools."""
        self.chktex_available = self._check_command("chktex")
        self.xelatex_available = self._check_command("xelatex")
        self.aspell_available = self._check_command("aspell")
    
    def _check_command(self, command: str) -> bool:
        """Check if a command is available in the system."""
        try:
            subprocess.run([command, "--version"], 
                         capture_output=True, 
                         check=True,
                         timeout=5)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def validate(self, content_or_path: Union[str, Path], format: str = "auto") -> Dict[str, Any]:
        """
        Validate document content or file.
        
        Args:
            content_or_path: Either document content (str) or path to file (Path/str)
            format: Document format (auto, latex, markdown)
            
        Returns:
            Dict with validation results, errors, and warnings
        """
        # Determine if input is content or path
        is_content = isinstance(content_or_path, str) and not Path(content_or_path).exists()
        
        if format == "auto":
            if is_content:
                format = self._detect_format_from_content(content_or_path)
            else:
                path = Path(content_or_path)
                format = self._detect_format_from_path(path)
        
        # Route to appropriate validator
        validators = {
            'latex': self.validate_latex,
            'tex': self.validate_latex,
            'markdown': self.validate_markdown,
            'md': self.validate_markdown,
        }
        
        if format in validators:
            return validators[format](content_or_path)
        else:
            return {
                "success": False,
                "error": f"No validation available for {format} format",
                "supported_formats": list(set(validators.values()))
            }
    
    def validate_latex(self, content_or_path: Union[str, Path]) -> Dict[str, Any]:
        """Validate LaTeX document using chktex and test compilation."""
        errors = []
        warnings = []
        
        # Prepare content and path
        if isinstance(content_or_path, str) and not Path(content_or_path).exists():
            # Content provided - write to temp file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False)
            temp_file.write(content_or_path)
            temp_file.close()
            file_path = Path(temp_file.name)
            is_temp = True
        else:
            file_path = Path(content_or_path)
            is_temp = False
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }
        
        try:
            # Step 1: Check with chktex if available
            if self.chktex_available:
                try:
                    result = subprocess.run(
                        ["chktex", str(file_path)],
                        capture_output=True,
                        text=True
                    )
                    
                    # Parse chktex output
                    for line in result.stdout.split('\n'):
                        if "Warning" in line:
                            warnings.append(line.strip())
                        elif "Error" in line:
                            errors.append(line.strip())
                except Exception as e:
                    warnings.append(f"chktex check failed: {str(e)}")
            
            # Step 2: Test compilation with XeLaTeX
            if self.xelatex_available:
                with tempfile.TemporaryDirectory() as temp_dir:
                    try:
                        result = subprocess.run([
                            "xelatex",
                            "-interaction=nonstopmode",
                            "-halt-on-error",
                            "-output-directory", temp_dir,
                            str(file_path)
                        ],
                        capture_output=True,
                        text=True,
                        cwd=file_path.parent if not is_temp else None)
                        
                        if result.returncode != 0:
                            # Extract LaTeX errors
                            latex_errors = self._extract_latex_errors(result.stdout)
                            errors.extend(latex_errors)
                    except Exception as e:
                        errors.append(f"Compilation test failed: {str(e)}")
            else:
                warnings.append("XeLaTeX not available - skipping compilation test")
            
            # Determine overall success
            success = len(errors) == 0
            
            return {
                "success": True,  # Validation process succeeded
                "valid": success,  # Document is valid (no errors)
                "format": "latex",
                "errors": errors,
                "warnings": warnings,
                "error_count": len(errors),
                "warning_count": len(warnings),
                "message": "LaTeX validation completed" if success else "LaTeX validation failed"
            }
            
        finally:
            # Clean up temp file
            if is_temp and file_path.exists():
                file_path.unlink()
    
    def validate_markdown(self, content_or_path: Union[str, Path]) -> Dict[str, Any]:
        """Basic validation for Markdown documents."""
        # For now, markdown validation is minimal
        # Could add spell checking with aspell, link checking, etc.
        
        if isinstance(content_or_path, str) and not Path(content_or_path).exists():
            content = content_or_path
        else:
            path = Path(content_or_path)
            if not path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {path}"
                }
            content = path.read_text()
        
        warnings = []
        
        # Basic checks
        if len(content.strip()) == 0:
            warnings.append("Document is empty")
        
        # Check for common issues
        if '\t' in content:
            warnings.append("Document contains tabs - consider using spaces for consistency")
        
        # Check for broken reference links
        ref_pattern = r'\[([^\]]+)\]\[([^\]]+)\]'
        refs_used = re.findall(ref_pattern, content)
        ref_defs = re.findall(r'^\[([^\]]+)\]:', content, re.MULTILINE)
        
        for _, ref_id in refs_used:
            if ref_id not in ref_defs:
                warnings.append(f"Undefined reference: [{ref_id}]")
        
        return {
            "success": True,
            "valid": True,  # Markdown has no errors, only warnings
            "format": "markdown",
            "errors": [],
            "warnings": warnings,
            "error_count": 0,
            "warning_count": len(warnings),
            "message": "Markdown validation completed"
        }
    
    def _detect_format_from_content(self, content: str) -> str:
        """Detect format from content patterns."""
        # LaTeX patterns
        latex_patterns = [
            r'\\documentclass',
            r'\\begin{document}',
            r'\\usepackage',
            r'\\section{',
            r'\\chapter{'
        ]
        
        for pattern in latex_patterns:
            if re.search(pattern, content):
                return 'latex'
        
        # Default to markdown
        return 'markdown'
    
    def _detect_format_from_path(self, path: Path) -> str:
        """Detect format from file extension."""
        ext_map = {
            '.tex': 'latex',
            '.latex': 'latex',
            '.md': 'markdown',
            '.markdown': 'markdown',
            '.mdown': 'markdown',
            '.mkd': 'markdown',
        }
        
        return ext_map.get(path.suffix.lower(), 'auto')
    
    def _extract_latex_errors(self, output: str) -> List[str]:
        """Extract error messages from LaTeX output."""
        errors = []
        lines = output.split('\n')
        
        for i, line in enumerate(lines):
            if line.startswith('!'):
                error_msg = line
                # Get context lines
                if i + 1 < len(lines) and lines[i + 1].startswith('l.'):
                    error_msg += ' ' + lines[i + 1]
                errors.append(error_msg)
        
        return errors[:5]  # Limit to first 5 errors


# Singleton instance
_validation_service = None

def get_validation_service() -> ValidationService:
    """Get or create the validation service singleton."""
    global _validation_service
    if _validation_service is None:
        _validation_service = ValidationService()
    return _validation_service