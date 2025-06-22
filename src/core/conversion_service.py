"""
Centralized document conversion service.
Single implementation for all format conversions to eliminate duplication.
"""

import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import tempfile


class ConversionService:
    """Handles all document format conversions."""
    
    def __init__(self):
        """Initialize and check available tools."""
        self.pandoc_available = self._check_command("pandoc")
        self.xelatex_available = self._check_command("xelatex")
        self.pdflatex_available = self._check_command("pdflatex")
    
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
    
    def convert(self, source: Path, target_format: str, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Main conversion dispatcher.
        
        Args:
            source: Source file path
            target_format: Target format (latex, pdf, html, docx, etc.)
            output_path: Optional output path, auto-generated if not provided
            
        Returns:
            Dict with success status, output path, and any errors
        """
        source_format = source.suffix.lstrip('.')
        
        # Validate source exists
        if not source.exists():
            return {"success": False, "error": f"Source file not found: {source}"}
        
        # Auto-generate output path if not provided
        if output_path is None:
            # Use .tex for latex format, not .latex
            extension = '.tex' if target_format == 'latex' else f'.{target_format}'
            output_path = source.with_suffix(extension)
        
        # Store original format for later use
        original_format = source_format
        
        # Normalize source format for internal routing
        if source_format == 'markdown':
            source_format = 'md'
        elif source_format == 'latex':
            source_format = 'tex'
            
        # Route to appropriate converter - expanded support
        direct_converters = {
            ('md', 'latex'): self.markdown_to_latex,
            ('md', 'tex'): self.markdown_to_latex,
            ('md', 'pdf'): self.markdown_to_pdf,
            ('tex', 'pdf'): self.latex_to_pdf,
            ('latex', 'pdf'): self.latex_to_pdf,
        }
        
        converter_key = (source_format, target_format)
        
        # Check for direct converter first
        if converter_key in direct_converters:
            return direct_converters[converter_key](source, output_path)
        
        # Try generic pandoc conversion for other formats
        elif self.pandoc_available:
            # Use original format names for pandoc (it expects 'markdown' not 'md')
            pandoc_source_format = original_format
            if pandoc_source_format in ['md', 'tex']:
                pandoc_source_format = 'markdown' if pandoc_source_format == 'md' else 'latex'
            return self.pandoc_convert(source, output_path, pandoc_source_format, target_format)
        else:
            return {
                "success": False,
                "error": f"Conversion from {source_format} to {target_format} requires pandoc",
                "install_hint": "Install pandoc for extended format support: sudo apt install pandoc",
                "supported_formats": ["markdown", "latex", "pdf", "html", "docx", "odt", "rtf", "epub", "mediawiki", "rst"]
            }
    
    def markdown_to_latex(self, source_path: Path, output_path: Path) -> Dict[str, Any]:
        """Convert markdown to LaTeX using pandoc."""
        if not self.pandoc_available:
            return {
                "success": False,
                "error": "pandoc not found - install pandoc for format conversion",
                "install_hint": "Install with: sudo apt install pandoc (Linux) or brew install pandoc (Mac)"
            }
        
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Run pandoc with standalone flag for complete document
            subprocess.run([
                "pandoc",
                "-f", "markdown",
                "-t", "latex",
                "-s",  # Standalone document with proper headers
                "-o", str(output_path),
                str(source_path)
            ], check=True, capture_output=True, text=True)
            
            return {
                "success": True,
                "source": str(source_path),
                "output": str(output_path),
                "source_format": "markdown",
                "target_format": "latex",
                "message": f"Successfully converted to LaTeX: {output_path}"
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Pandoc conversion failed: {e}",
                "stderr": e.stderr if hasattr(e, 'stderr') else None
            }
    
    def latex_to_pdf(self, source_path: Path, output_path: Path) -> Dict[str, Any]:
        """
        Convert LaTeX to PDF using XeLaTeX (preferred) or PDFLaTeX.
        
        Runs multiple compilation passes to ensure:
        - Table of contents (TOC) is properly generated
        - Cross-references are resolved
        - Page numbers are correct (e.g., "Page X of Y")
        
        LaTeX needs multiple passes because:
        1. First pass: Collects section info and writes .aux files
        2. Second pass: Uses .aux files to build TOC and references
        3. Third pass: Finalizes any remaining references
        """
        # Choose engine
        if self.xelatex_available:
            engine = "xelatex"
        elif self.pdflatex_available:
            engine = "pdflatex"
        else:
            return {
                "success": False,
                "error": "No LaTeX engine found (XeLaTeX or PDFLaTeX required)",
                "install_hint": "Install TeX Live: sudo apt install texlive-xetex (Linux) or brew install --cask mactex (Mac)"
            }
        
        try:
            # Create a temporary directory for auxiliary files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Copy source file to temp directory
                temp_source = temp_path / source_path.name
                shutil.copy2(source_path, temp_source)
                
                # Copy any assets from the source directory (images, included files, etc.)
                # This ensures LaTeX can find all referenced files
                source_dir = source_path.parent
                for file in source_dir.iterdir():
                    if file.is_file() and file != source_path:
                        # Copy supporting files (images, .bib, .sty, etc.)
                        if file.suffix in ['.png', '.jpg', '.jpeg', '.pdf', '.eps', '.bib', '.sty', '.cls']:
                            shutil.copy2(file, temp_path / file.name)
                
                # Run LaTeX engine multiple times for TOC and cross-references
                # First pass: collect section information
                # Second pass: build TOC using collected info
                # Third pass: resolve any remaining references
                for pass_num in range(1, 4):
                    result = subprocess.run([
                        engine,
                        "-interaction=nonstopmode",
                        "-output-directory", str(temp_path),
                        str(temp_source)
                    ], 
                    capture_output=True,
                    text=True,
                    cwd=temp_path)
                    
                    if result.returncode != 0:
                        # Extract meaningful errors from output
                        errors = self._extract_latex_errors(result.stdout + result.stderr)
                        return {
                            "success": False,
                            "error": f"LaTeX compilation failed with {engine} (pass {pass_num})",
                            "latex_errors": errors,
                            "return_code": result.returncode,
                            "pass_failed": pass_num
                        }
                
                # Find generated PDF
                temp_pdf = temp_source.with_suffix('.pdf')
                if not temp_pdf.exists():
                    return {
                        "success": False,
                        "error": "PDF generation failed - no output file created"
                    }
                
                # Move to final location
                output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(temp_pdf), str(output_path))
                
                return {
                    "success": True,
                    "source": str(source_path),
                    "output": str(output_path),
                    "source_format": "latex",
                    "target_format": "pdf",
                    "engine": engine,
                    "message": f"Successfully created PDF: {output_path}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error during PDF generation: {str(e)}"
            }
    
    def markdown_to_pdf(self, source_path: Path, output_path: Path) -> Dict[str, Any]:
        """Convert markdown directly to PDF using pandoc."""
        if not self.pandoc_available:
            return {
                "success": False,
                "error": "pandoc not found - install pandoc for format conversion"
            }
        
        # Determine PDF engine
        pdf_engine = "xelatex" if self.xelatex_available else "pdflatex" if self.pdflatex_available else None
        
        if not pdf_engine:
            return {
                "success": False,
                "error": "No LaTeX engine found for PDF generation",
                "install_hint": "Install TeX Live for PDF support"
            }
        
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            subprocess.run([
                "pandoc",
                str(source_path),
                "-o", str(output_path),
                f"--pdf-engine={pdf_engine}"
            ], check=True, capture_output=True, text=True)
            
            return {
                "success": True,
                "source": str(source_path),
                "output": str(output_path),
                "source_format": "markdown",
                "target_format": "pdf",
                "engine": f"pandoc with {pdf_engine}",
                "message": f"Successfully created PDF: {output_path}"
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"PDF generation failed: {e}",
                "stderr": e.stderr if hasattr(e, 'stderr') else None
            }
    
    def pandoc_convert(self, source_path: Path, output_path: Path, source_format: str, target_format: str) -> Dict[str, Any]:
        """Generic pandoc conversion for any supported format."""
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Build pandoc command
            cmd = [
                "pandoc",
                "-f", source_format,
                "-t", target_format,
                "-o", str(output_path),
                str(source_path)
            ]
            
            # Add standalone flag for document formats
            if target_format in ['latex', 'tex', 'html', 'epub']:
                cmd.insert(3, "-s")  # Insert after -t target_format
            
            # Special handling for PDF output
            if target_format == 'pdf':
                # Determine PDF engine
                if self.xelatex_available:
                    cmd.extend(["--pdf-engine=xelatex"])
                elif self.pdflatex_available:
                    cmd.extend(["--pdf-engine=pdflatex"])
                else:
                    return {
                        "success": False,
                        "error": "PDF conversion requires a LaTeX engine (xelatex or pdflatex)",
                        "install_hint": "Install TeX Live: sudo apt install texlive-xetex"
                    }
            
            # Execute conversion
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "source": str(source_path),
                    "output": str(output_path),
                    "source_format": source_format,
                    "target_format": target_format,
                    "message": f"Successfully converted {source_format} to {target_format}: {output_path}",
                    "converter": "pandoc"
                }
            else:
                return {
                    "success": False,
                    "error": f"Pandoc conversion failed: {result.stderr}",
                    "stdout": result.stdout,
                    "command": ' '.join(cmd)
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Conversion error: {str(e)}"
            }
    
    def _extract_latex_errors(self, output: str) -> list:
        """Extract meaningful error messages from LaTeX output."""
        errors = []
        lines = output.split('\n')
        
        for i, line in enumerate(lines):
            # LaTeX errors start with !
            if line.startswith('!'):
                errors.append(line)
                # Try to get the next few lines for context
                for j in range(1, 4):
                    if i + j < len(lines):
                        errors.append(lines[i + j])
                errors.append('---')
        
        # Limit to first 5 errors
        return errors[:20] if errors else ["No specific errors found in output"]


# Singleton instance for reuse
_conversion_service = None

def get_conversion_service() -> ConversionService:
    """Get or create the conversion service singleton."""
    global _conversion_service
    if _conversion_service is None:
        _conversion_service = ConversionService()
    return _conversion_service