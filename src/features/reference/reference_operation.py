"""LaTeX Reference Operation

Provides intelligent documentation search and help for LaTeX commands,
packages, symbols, and error messages.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class SearchResult:
    """Represents a search result from the reference database."""
    type: str  # command, symbol, package, error
    name: str
    description: str
    syntax: Optional[str] = None
    package: Optional[str] = None
    examples: Optional[List[str]] = None
    related: Optional[List[str]] = None
    category: Optional[str] = None


class ReferenceOperation:
    """LaTeX reference and documentation search."""
    
    def __init__(self):
        # Get data directory relative to this file
        self.data_dir = Path(__file__).parent.parent.parent / "data" / "latex_reference"
        
        # Ensure data directory exists
        if not self.data_dir.exists():
            print(f"Warning: Reference data directory not found: {self.data_dir}")
            self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.commands_db = self._load_commands()
        self.symbols_db = self._load_symbols()
        self.packages_db = self._load_packages()
        self.errors_db = self._load_errors()
    
    def _load_json_file(self, filepath: Path) -> Dict[str, Any]:
        """Load a JSON file, returning empty dict if not found."""
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                print(f"Warning: Invalid JSON in {filepath}: {e}")
                return {}
            except Exception as e:
                print(f"Warning: Error reading {filepath}: {e}")
                return {}
        return {}
    
    def _load_commands(self) -> Dict[str, Any]:
        """Load command database."""
        commands = {}
        commands_dir = self.data_dir / "commands"
        
        # Load all command JSON files
        for json_file in commands_dir.glob("*.json"):
            data = self._load_json_file(json_file)
            commands.update(data)
        
        return commands
    
    def _load_symbols(self) -> Dict[str, Any]:
        """Load symbol database."""
        symbols = {}
        symbols_dir = self.data_dir / "symbols"
        
        # Load all symbol JSON files
        for json_file in symbols_dir.glob("*.json"):
            data = self._load_json_file(json_file)
            symbols.update(data)
        
        return symbols
    
    def _load_packages(self) -> Dict[str, Any]:
        """Load package documentation."""
        packages = {}
        packages_dir = self.data_dir / "packages"
        
        # Load all package JSON files
        for json_file in packages_dir.glob("*.json"):
            data = self._load_json_file(json_file)
            package_name = json_file.stem
            packages[package_name] = data
        
        return packages
    
    def _load_errors(self) -> Dict[str, Any]:
        """Load error patterns and solutions."""
        errors_file = self.data_dir / "errors" / "patterns.json"
        return self._load_json_file(errors_file)
    
    def execute(self, action: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a reference operation."""
        try:
            if action == "search":
                return self._search(params)
            elif action == "symbol":
                return self._find_symbol(params)
            elif action == "package":
                return self._get_package_info(params)
            elif action == "check_style":
                return self._check_style(params, context)
            elif action == "error_help":
                return self._get_error_help(params)
            elif action == "example":
                return self._get_example(params)
            else:
                return {
                    "error": f"Unknown action: {action}",
                    "available_actions": ["search", "symbol", "package", "check_style", "error_help", "example"]
                }
        except Exception as e:
            return {"error": str(e)}
    
    def _search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for LaTeX commands, environments, or general queries."""
        query = params.get("query", "").lower()
        if not query:
            return {"error": "Query parameter required"}
        
        results = []
        
        # Search commands
        for cmd_name, cmd_info in self.commands_db.items():
            if (query in cmd_name.lower() or 
                query in cmd_info.get("description", "").lower() or
                query in cmd_info.get("category", "").lower()):
                results.append(SearchResult(
                    type="command",
                    name=cmd_name,
                    description=cmd_info.get("description", ""),
                    syntax=cmd_info.get("syntax"),
                    package=cmd_info.get("package"),
                    examples=cmd_info.get("examples"),
                    related=cmd_info.get("related"),
                    category=cmd_info.get("category")
                ))
        
        # Search symbols
        for sym_name, sym_info in self.symbols_db.items():
            if (query in sym_name.lower() or 
                query in sym_info.get("description", "").lower()):
                results.append(SearchResult(
                    type="symbol",
                    name=sym_name,
                    description=sym_info.get("description", ""),
                    syntax=sym_info.get("command"),
                    package=sym_info.get("package"),
                    category=sym_info.get("category")
                ))
        
        # Limit results
        results = results[:20]
        
        return {
            "success": True,
            "query": query,
            "results": [
                {
                    "type": r.type,
                    "name": r.name,
                    "description": r.description,
                    "syntax": r.syntax,
                    "package": r.package,
                    "examples": r.examples,
                    "related": r.related,
                    "category": r.category
                }
                for r in results
            ],
            "count": len(results),
            "message": f"Found {len(results)} results for '{query}'"
        }
    
    def _find_symbol(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find symbols by description."""
        description = params.get("description", "").lower()
        if not description:
            return {"error": "Description parameter required"}
        
        matches = []
        
        for sym_name, sym_info in self.symbols_db.items():
            sym_desc = sym_info.get("description", "").lower()
            if any(word in sym_desc for word in description.split()):
                matches.append({
                    "symbol": sym_name,
                    "command": sym_info.get("command", sym_name),
                    "description": sym_info.get("description", ""),
                    "package": sym_info.get("package", "built-in"),
                    "unicode": sym_info.get("unicode"),
                    "category": sym_info.get("category", "")
                })
        
        # Sort by relevance (more matching words = higher relevance)
        words = description.split()
        matches.sort(key=lambda m: sum(1 for w in words if w in m["description"].lower()), reverse=True)
        
        return {
            "success": True,
            "description": description,
            "symbols": matches[:15],  # Limit to top 15
            "count": len(matches),
            "message": f"Found {len(matches)} symbols matching '{description}'"
        }
    
    def _get_package_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about a LaTeX package."""
        package_name = params.get("name", "").lower()
        if not package_name:
            return {"error": "Package name parameter required"}
        
        if package_name not in self.packages_db:
            # Try to find similar packages
            similar = [p for p in self.packages_db.keys() if package_name in p]
            return {
                "success": False,
                "error": f"Package '{package_name}' not found",
                "suggestions": similar[:5] if similar else None,
                "message": "Try 'reference(action=\"search\", query=\"package_name\")' for broader search"
            }
        
        package_info = self.packages_db[package_name]
        
        return {
            "success": True,
            "package": package_name,
            "description": package_info.get("description", ""),
            "usage": package_info.get("usage", f"\\usepackage{{{package_name}}}"),
            "options": package_info.get("options", []),
            "commands": package_info.get("commands", []),
            "examples": package_info.get("examples", []),
            "documentation": package_info.get("documentation", f"texdoc {package_name}"),
            "message": f"Package information for '{package_name}'"
        }
    
    def _check_style(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Check document for LaTeX style best practices."""
        path = params.get("path")
        if not path:
            return {"error": "Path parameter required"}
        
        # Resolve path relative to project if needed
        filepath = Path(path)
        if not filepath.is_absolute() and context.get("project"):
            project_root = context.get("workspace_root", Path.home() / "Documents" / "TeXFlow")
            project_dir = project_root / context["project"]
            filepath = project_dir / filepath
        
        if not filepath.exists():
            return {"error": f"File not found: {filepath}"}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}
        
        # Style checks
        warnings = []
        line_num = 0
        
        for line in content.split('\n'):
            line_num += 1
            
            # Check for math operators without backslash
            math_ops = ['sin', 'cos', 'tan', 'log', 'ln', 'exp', 'min', 'max', 'lim']
            for op in math_ops:
                # Look for operator not preceded by backslash
                pattern = rf'(?<!\\){op}\s*\('
                if re.search(pattern, line):
                    warnings.append({
                        "line": line_num,
                        "type": "math_operator",
                        "message": f"Use \\{op} instead of {op} for mathematical operators",
                        "suggestion": f"Replace '{op}' with '\\{op}'"
                    })
            
            # Check for deprecated commands
            deprecated = {
                '\\rm': '\\textrm or \\mathrm',
                '\\bf': '\\textbf or \\mathbf',
                '\\it': '\\textit or \\mathit',
                '\\sc': '\\textsc',
                '\\tt': '\\texttt or \\mathtt'
            }
            
            for old_cmd, new_cmd in deprecated.items():
                if old_cmd in line:
                    warnings.append({
                        "line": line_num,
                        "type": "deprecated",
                        "message": f"Command '{old_cmd}' is deprecated",
                        "suggestion": f"Use '{new_cmd}' instead"
                    })
            
            # Check for spacing issues
            if '\\\\\\\\' in line:
                warnings.append({
                    "line": line_num,
                    "type": "spacing",
                    "message": "Multiple line breaks detected",
                    "suggestion": "Consider using \\vspace{} for vertical spacing"
                })
        
        # Check for missing packages based on commands used
        suggestions = []
        
        if '\\SI' in content and '\\usepackage{siunitx}' not in content:
            suggestions.append({
                "type": "package",
                "message": "Consider using siunitx package for units",
                "suggestion": "Add \\usepackage{siunitx} to preamble"
            })
        
        if any(cmd in content for cmd in ['\\toprule', '\\midrule', '\\bottomrule']) and '\\usepackage{booktabs}' not in content:
            suggestions.append({
                "type": "package",
                "message": "Using booktabs commands without package",
                "suggestion": "Add \\usepackage{booktabs} to preamble"
            })
        
        return {
            "success": True,
            "file": str(filepath),
            "warnings": warnings,
            "suggestions": suggestions,
            "summary": {
                "total_warnings": len(warnings),
                "total_suggestions": len(suggestions)
            },
            "message": f"Style check complete: {len(warnings)} warnings, {len(suggestions)} suggestions"
        }
    
    def _get_error_help(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get help for LaTeX error messages."""
        error_msg = params.get("error", "")
        if not error_msg:
            return {"error": "Error message parameter required"}
        
        # Normalize error message
        error_lower = error_msg.lower()
        
        # Search for matching error patterns
        matches = []
        
        for pattern, solution in self.errors_db.items():
            if pattern.lower() in error_lower or re.search(pattern, error_msg, re.IGNORECASE):
                matches.append({
                    "pattern": pattern,
                    "explanation": solution.get("explanation", ""),
                    "solution": solution.get("solution", ""),
                    "example": solution.get("example", ""),
                    "common_causes": solution.get("common_causes", [])
                })
        
        if not matches:
            # Provide generic help based on error type
            generic_help = self._get_generic_error_help(error_msg)
            if generic_help:
                matches.append(generic_help)
        
        return {
            "success": True,
            "error_message": error_msg,
            "solutions": matches,
            "count": len(matches),
            "message": f"Found {len(matches)} solutions for your error"
        }
    
    def _get_generic_error_help(self, error_msg: str) -> Optional[Dict[str, Any]]:
        """Provide generic help for common error types."""
        error_lower = error_msg.lower()
        
        if "undefined control sequence" in error_lower:
            # Extract the undefined command if possible
            match = re.search(r'undefined control sequence.*?\\(\w+)', error_msg, re.IGNORECASE)
            cmd = match.group(1) if match else "command"
            
            return {
                "pattern": "Undefined control sequence",
                "explanation": f"LaTeX doesn't recognize the command \\{cmd}",
                "solution": f"Check spelling, ensure required package is loaded, or define the command",
                "common_causes": [
                    "Typo in command name",
                    "Missing \\usepackage{} declaration",
                    "Command from a package that isn't loaded",
                    "Custom command that hasn't been defined"
                ]
            }
        
        elif "missing $ inserted" in error_lower:
            return {
                "pattern": "Missing $ inserted",
                "explanation": "Math mode content found outside math environment",
                "solution": "Wrap math content in $ ... $ or \\[ ... \\]",
                "example": "Change: x^2 + y^2 = z^2\nTo: $x^2 + y^2 = z^2$",
                "common_causes": [
                    "Using ^ or _ outside math mode",
                    "Math commands like \\frac outside math mode",
                    "Forgetting to close a math environment"
                ]
            }
        
        elif "file not found" in error_lower:
            return {
                "pattern": "File not found",
                "explanation": "LaTeX cannot find a required file",
                "solution": "Check file path, ensure file exists, or install missing package",
                "common_causes": [
                    "Incorrect file path in \\input or \\include",
                    "Missing image file for \\includegraphics",
                    "Package not installed on system",
                    "Typo in filename"
                ]
            }
        
        return None
    
    def _get_example(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get working examples for a topic."""
        topic = params.get("topic", "").lower()
        if not topic:
            return {"error": "Topic parameter required"}
        
        # This would be expanded with a proper examples database
        examples = {
            "table": {
                "basic": """\\begin{tabular}{|l|c|r|}
\\hline
Left & Center & Right \\\\
\\hline
1 & 2 & 3 \\\\
4 & 5 & 6 \\\\
\\hline
\\end{tabular}""",
                "description": "Basic table with borders"
            },
            "equation": {
                "basic": """\\begin{equation}
E = mc^2
\\end{equation}""",
                "description": "Numbered equation"
            },
            "figure": {
                "basic": """\\begin{figure}[htbp]
\\centering
\\includegraphics[width=0.8\\textwidth]{image.png}
\\caption{Figure caption}
\\label{fig:example}
\\end{figure}""",
                "description": "Figure with caption and label"
            }
        }
        
        # Search for matching examples
        matches = []
        for ex_name, ex_info in examples.items():
            if topic in ex_name:
                matches.append({
                    "name": ex_name,
                    "code": ex_info["basic"],
                    "description": ex_info["description"]
                })
        
        if not matches:
            return {
                "success": False,
                "error": f"No examples found for topic '{topic}'",
                "suggestion": "Try searching with 'reference(action=\"search\", query=\"topic\")'"
            }
        
        return {
            "success": True,
            "topic": topic,
            "examples": matches,
            "message": f"Found {len(matches)} examples for '{topic}'"
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get operation capabilities and requirements."""
        return {
            "actions": {
                "search": {
                    "description": "Search for LaTeX commands, environments, or general topics",
                    "required_params": ["query"],
                    "examples": [
                        "reference(action='search', query='section')",
                        "reference(action='search', query='math environments')"
                    ]
                },
                "symbol": {
                    "description": "Find symbols by description",
                    "required_params": ["description"],
                    "examples": [
                        "reference(action='symbol', description='approximately equal')",
                        "reference(action='symbol', description='infinity')"
                    ]
                },
                "package": {
                    "description": "Get information about a LaTeX package",
                    "required_params": ["name"],
                    "examples": [
                        "reference(action='package', name='amsmath')",
                        "reference(action='package', name='graphicx')"
                    ]
                },
                "check_style": {
                    "description": "Check document for LaTeX style best practices",
                    "required_params": ["path"],
                    "examples": [
                        "reference(action='check_style', path='document.tex')",
                        "reference(action='check_style', path='chapter1.tex')"
                    ]
                },
                "error_help": {
                    "description": "Get help for LaTeX error messages",
                    "required_params": ["error"],
                    "examples": [
                        "reference(action='error_help', error='Undefined control sequence')",
                        "reference(action='error_help', error='Missing $ inserted')"
                    ]
                },
                "example": {
                    "description": "Get working examples for a topic",
                    "required_params": ["topic"],
                    "examples": [
                        "reference(action='example', topic='table')",
                        "reference(action='example', topic='equation')"
                    ]
                }
            },
            "system_requirements": {
                "command": [
                    {
                        "name": "texdoc",
                        "required_for": ["package"],
                        "install_hint": "Part of TeX Live distribution"
                    }
                ]
            },
            "optional_features": [
                {
                    "name": "Extended symbol search",
                    "description": "Visual symbol rendering",
                    "requirements": [
                        {"type": "command", "name": "pdflatex"}
                    ]
                }
            ],
            "data_sources": {
                "commands": "LaTeX2e reference",
                "symbols": "Comprehensive LaTeX Symbol List",
                "packages": "Package documentation",
                "errors": "Community knowledge"
            }
        }