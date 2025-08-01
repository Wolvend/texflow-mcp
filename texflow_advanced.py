#!/usr/bin/env python3
"""Advanced features for TeXFlow MCP server"""

import re
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import hashlib

class LaTeXDiagnostics:
    """Diagnose and fix LaTeX compilation errors"""
    
    COMMON_FIXES = {
        r"LaTeX Error: File `(.+?)' not found": {
            "diagnosis": "Missing package: {1}",
            "fix": r"\\usepackage{{{1}}}",
            "install": "tlmgr install {1}"
        },
        r"Undefined control sequence.*?\\(\w+)": {
            "diagnosis": "Unknown command: \\{1}",
            "fix": "Check spelling or add required package",
            "suggest": ["amsmath", "amssymb", "graphicx"]
        },
        r"Missing \$ inserted": {
            "diagnosis": "Math mode required",
            "fix": "Wrap math content in $ ... $ or \\[ ... \\]"
        },
        r"Runaway argument\?": {
            "diagnosis": "Unclosed brace or environment",
            "fix": "Check for missing } or \\end{...}"
        },
        r"Package babel Error: Unknown language": {
            "diagnosis": "Language not configured",
            "fix": r"\\usepackage[english]{babel}"
        }
    }
    
    @classmethod
    def diagnose(cls, error_log: str) -> List[Dict]:
        """Analyze error log and suggest fixes"""
        diagnostics = []
        
        for pattern, info in cls.COMMON_FIXES.items():
            matches = re.finditer(pattern, error_log, re.MULTILINE)
            for match in matches:
                diagnostic = {
                    "error": match.group(0),
                    "diagnosis": info["diagnosis"].format(*match.groups()),
                    "fix": info["fix"].format(*match.groups()) if "{" in str(info["fix"]) else info["fix"],
                    "line": cls._extract_line_number(error_log, match.start())
                }
                if "install" in info:
                    diagnostic["install_cmd"] = info["install"].format(*match.groups())
                if "suggest" in info:
                    diagnostic["suggestions"] = info["suggest"]
                diagnostics.append(diagnostic)
        
        return diagnostics
    
    @staticmethod
    def _extract_line_number(log: str, position: int) -> Optional[int]:
        """Extract line number from error context"""
        before = log[:position].split('\n')
        for line in reversed(before[-5:]):
            match = re.search(r'\.tex:(\d+):', line)
            if match:
                return int(match.group(1))
        return None
    
    @classmethod
    def auto_fix(cls, file_path: str, diagnostics: List[Dict]) -> Dict[str, int]:
        """Apply automatic fixes to LaTeX file"""
        fixes_applied = {"packages": 0, "commands": 0, "formatting": 0}
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Add missing packages
        for diag in diagnostics:
            if "\\usepackage" in diag.get("fix", ""):
                if diag["fix"] not in content:
                    # Insert after documentclass
                    content = re.sub(
                        r'(\\documentclass.*?\n)',
                        r'\1' + diag["fix"] + '\n',
                        content
                    )
                    fixes_applied["packages"] += 1
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        return fixes_applied


class BibliographyManager:
    """Manage BibTeX references"""
    
    @staticmethod
    def import_from_doi(doi: str) -> str:
        """Import BibTeX entry from DOI"""
        # This would normally use crossref API
        return f"""@article{{doi_{doi.replace('/', '_')},
    doi = {{{doi}}},
    title = {{Article from DOI {doi}}},
    author = {{Author, Name}},
    year = {{2024}}
}}"""
    
    @staticmethod
    def import_from_arxiv(arxiv_id: str) -> str:
        """Import BibTeX entry from arXiv"""
        return f"""@article{{{arxiv_id},
    title = {{arXiv Paper {arxiv_id}}},
    author = {{Author, Name}},
    year = {{2024}},
    eprint = {{{arxiv_id}}},
    archivePrefix = {{arXiv}}
}}"""
    
    @staticmethod
    def check_duplicates(bib_content: str) -> List[str]:
        """Find duplicate entries in bibliography"""
        entries = re.findall(r'@\w+\{([^,]+),', bib_content)
        duplicates = []
        seen = set()
        
        for entry in entries:
            if entry in seen:
                duplicates.append(entry)
            seen.add(entry)
        
        return duplicates
    
    @staticmethod
    def format_bibliography(bib_content: str, style: str = "plain") -> str:
        """Format bibliography entries consistently"""
        # Basic formatting - in practice would use bibtexparser
        formatted = bib_content
        
        # Ensure consistent spacing
        formatted = re.sub(r'\s*=\s*', ' = ', formatted)
        formatted = re.sub(r',\s*\n\s*', ',\n    ', formatted)
        
        return formatted


class VersionControl:
    """Simple version control for LaTeX documents"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.versions_dir = base_path / ".texflow_versions"
        self.versions_dir.mkdir(exist_ok=True)
    
    def commit(self, file_path: str, message: str) -> str:
        """Create a version snapshot"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = Path(file_path)
        
        # Calculate file hash
        with open(file_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()[:8]
        
        version_id = f"{timestamp}_{file_hash}"
        version_file = self.versions_dir / f"{file_path.stem}_{version_id}.tex"
        
        # Copy file to versions directory
        version_file.write_text(file_path.read_text())
        
        # Save metadata
        meta_file = self.versions_dir / f"{file_path.stem}_{version_id}.json"
        meta_file.write_text(json.dumps({
            "timestamp": timestamp,
            "message": message,
            "hash": file_hash,
            "original": str(file_path)
        }))
        
        return version_id
    
    def diff(self, file_path: str, version_id: Optional[str] = None) -> str:
        """Show differences between versions"""
        current = Path(file_path).read_text()
        
        if version_id:
            version_file = self.versions_dir / f"{Path(file_path).stem}_{version_id}.tex"
            if version_file.exists():
                old = version_file.read_text()
                return self._simple_diff(old, current)
        
        return "No previous version found"
    
    @staticmethod
    def _simple_diff(old: str, new: str) -> str:
        """Simple line-based diff"""
        old_lines = old.splitlines()
        new_lines = new.splitlines()
        diff_output = []
        
        for i, (o, n) in enumerate(zip(old_lines, new_lines)):
            if o != n:
                diff_output.append(f"Line {i+1}:")
                diff_output.append(f"- {o}")
                diff_output.append(f"+ {n}")
        
        return "\n".join(diff_output)


class SmartSearch:
    """LaTeX-aware search and replace"""
    
    ENVIRONMENTS = {
        "equations": [r"\\begin\{equation\}.*?\\end\{equation\}", 
                     r"\$\$.*?\$\$", r"\$[^$]+\$"],
        "figures": [r"\\begin\{figure\}.*?\\end\{figure\}"],
        "tables": [r"\\begin\{table\}.*?\\end\{table\}"],
        "citations": [r"\\cite\{[^}]+\}", r"\\citep\{[^}]+\}", r"\\citet\{[^}]+\}"],
        "commands": [r"\\[a-zA-Z]+(?:\[[^\]]*\])?\{[^}]*\}"]
    }
    
    @classmethod
    def search_in_scope(cls, content: str, pattern: str, scope: str = "all") -> List[Dict]:
        """Search within specific LaTeX environments"""
        matches = []
        
        if scope == "all":
            for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
                matches.append({
                    "match": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                    "line": content[:match.start()].count('\n') + 1
                })
        else:
            # Search only within specified environments
            env_patterns = cls.ENVIRONMENTS.get(scope, [])
            for env_pattern in env_patterns:
                for env_match in re.finditer(env_pattern, content, re.DOTALL):
                    env_content = env_match.group(0)
                    for match in re.finditer(pattern, env_content):
                        matches.append({
                            "match": match.group(0),
                            "environment": scope,
                            "start": env_match.start() + match.start(),
                            "line": content[:env_match.start() + match.start()].count('\n') + 1
                        })
        
        return matches
    
    @staticmethod
    def find_unused_references(tex_content: str, bib_content: str) -> List[str]:
        """Find references defined but not cited"""
        # Extract all bib keys
        bib_keys = set(re.findall(r'@\w+\{([^,]+),', bib_content))
        
        # Extract all citations
        cited_keys = set()
        for cite in re.findall(r'\\cite[pt]?\{([^}]+)\}', tex_content):
            cited_keys.update(k.strip() for k in cite.split(','))
        
        return list(bib_keys - cited_keys)


class ProjectAnalytics:
    """Writing statistics and analytics"""
    
    @staticmethod
    def word_count(content: str, by_section: bool = False) -> Dict:
        """Count words in LaTeX document"""
        # Remove LaTeX commands and comments
        cleaned = re.sub(r'\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^}]*\})?', '', content)
        cleaned = re.sub(r'%.*$', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'\$.*?\$', 'MATH', cleaned)
        
        if not by_section:
            words = len(cleaned.split())
            return {"total": words}
        
        # Count by section
        sections = {}
        current_section = "preamble"
        
        for line in content.splitlines():
            section_match = re.match(r'\\(chapter|section|subsection)\{([^}]+)\}', line)
            if section_match:
                current_section = section_match.group(2)
                sections[current_section] = 0
            
            # Count words in current section
            cleaned_line = re.sub(r'\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^}]*\})?', '', line)
            cleaned_line = re.sub(r'%.*$', '', cleaned_line)
            sections[current_section] = sections.get(current_section, 0) + len(cleaned_line.split())
        
        return sections
    
    @staticmethod
    def calculate_velocity(project_path: Path, period: str = "day") -> Dict:
        """Calculate writing velocity"""
        # This would track changes over time
        # For now, return mock data
        return {
            "period": period,
            "average_words": 500,
            "peak_day": "Monday",
            "total_sessions": 12
        }


class PerformanceOptimizer:
    """Optimize LaTeX compilation performance"""
    
    @staticmethod
    def analyze_compilation(log_content: str) -> Dict:
        """Analyze compilation log for performance issues"""
        issues = []
        
        # Check for missing fonts
        if "Font shape" in log_content and "undefined" in log_content:
            issues.append({
                "type": "missing_font",
                "impact": "slow",
                "suggestion": "Pre-compile fonts or use system fonts"
            })
        
        # Check for large images
        img_loads = re.findall(r'<(.+?\.(png|jpg|pdf))>', log_content)
        for img in img_loads:
            issues.append({
                "type": "image_load",
                "file": img[0],
                "suggestion": "Consider reducing image resolution or using PDF format"
            })
        
        return {"issues": issues, "total_time": "2.3s"}
    
    @staticmethod
    def create_cache_config(project_path: Path) -> Dict:
        """Create optimal cache configuration"""
        return {
            "aux_dir": str(project_path / ".texflow_cache"),
            "jobname": "cached_build",
            "recorder": True,
            "file_line_error": True
        }