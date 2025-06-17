"""
LaTeX Package Discovery Module for TeXFlow MCP Server.

This module detects installed LaTeX packages through system package managers
and provides structured data about available packages.
"""

import subprocess
import platform
import re
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PackageDiscovery:
    """Discovers installed LaTeX packages through system package managers."""
    
    def __init__(self):
        """Initialize the package discovery system."""
        self.distro_info = self._detect_distribution()
        self.package_manager = self._detect_package_manager()
        self._cache = {}  # Cache for package queries
        
    def _detect_distribution(self) -> Dict[str, str]:
        """Detect the Linux distribution."""
        distro_info = {
            "name": "unknown",
            "version": "unknown",
            "id": "unknown",
            "id_like": []
        }
        
        # Try to read /etc/os-release
        os_release_path = Path("/etc/os-release")
        if os_release_path.exists():
            try:
                with open(os_release_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line:
                            key, value = line.split('=', 1)
                            value = value.strip('"')
                            
                            if key == "NAME":
                                distro_info["name"] = value
                            elif key == "VERSION":
                                distro_info["version"] = value
                            elif key == "ID":
                                distro_info["id"] = value.lower()
                            elif key == "ID_LIKE":
                                distro_info["id_like"] = value.lower().split()
            except Exception as e:
                logger.warning(f"Failed to read /etc/os-release: {e}")
        
        return distro_info
    
    def _detect_package_manager(self) -> Optional[str]:
        """Detect the system package manager."""
        # Check for package managers in order of preference
        package_managers = [
            ("apt", ["apt", "--version"]),
            ("dpkg", ["dpkg", "--version"]),
            ("pacman", ["pacman", "--version"]),
            ("dnf", ["dnf", "--version"]),
            ("yum", ["yum", "--version"]),
            ("rpm", ["rpm", "--version"]),
            ("zypper", ["zypper", "--version"]),
        ]
        
        for pm_name, check_cmd in package_managers:
            try:
                subprocess.run(check_cmd, capture_output=True, check=True)
                return pm_name
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        return None
    
    def _query_apt_packages(self) -> List[Dict[str, Any]]:
        """Query LaTeX packages using apt/dpkg."""
        packages = []
        
        try:
            # Use dpkg to list installed packages
            result = subprocess.run(
                ["dpkg", "-l", "*tex*", "*latex*"],
                capture_output=True,
                text=True,
                check=False  # Don't fail if no matches
            )
            
            # Parse dpkg output
            for line in result.stdout.split('\n'):
                if line.startswith('ii'):  # 'ii' means installed
                    parts = line.split()
                    if len(parts) >= 3:
                        package_name = parts[1]
                        version = parts[2]
                        
                        # Get package description
                        desc_result = subprocess.run(
                            ["dpkg", "-s", package_name],
                            capture_output=True,
                            text=True,
                            check=False
                        )
                        
                        description = ""
                        for desc_line in desc_result.stdout.split('\n'):
                            if desc_line.startswith('Description:'):
                                description = desc_line[12:].strip()
                                break
                        
                        # Categorize package
                        category = self._categorize_package(package_name, description)
                        
                        packages.append({
                            "name": package_name,
                            "version": version,
                            "description": description,
                            "category": category,
                            "installed": True,
                            "source": "dpkg"
                        })
            
        except Exception as e:
            logger.error(f"Failed to query apt/dpkg packages: {e}")
        
        return packages
    
    def _query_pacman_packages(self) -> List[Dict[str, Any]]:
        """Query LaTeX packages using pacman."""
        packages = []
        
        try:
            # Query installed texlive packages
            result = subprocess.run(
                ["pacman", "-Qs", "texlive"],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Parse pacman output
            lines = result.stdout.strip().split('\n')
            i = 0
            while i < len(lines):
                if lines[i].startswith('local/'):
                    # Extract package info
                    package_line = lines[i]
                    package_info = package_line.replace('local/', '').strip()
                    
                    # Split name and version
                    parts = package_info.split(' ', 1)
                    package_name = parts[0]
                    version = parts[1] if len(parts) > 1 else "unknown"
                    
                    # Next line is description
                    description = ""
                    if i + 1 < len(lines):
                        description = lines[i + 1].strip()
                    
                    category = self._categorize_package(package_name, description)
                    
                    packages.append({
                        "name": package_name,
                        "version": version,
                        "description": description,
                        "category": category,
                        "installed": True,
                        "source": "pacman"
                    })
                    
                    i += 2
                else:
                    i += 1
        
        except Exception as e:
            logger.error(f"Failed to query pacman packages: {e}")
        
        return packages
    
    def _query_rpm_packages(self) -> List[Dict[str, Any]]:
        """Query LaTeX packages using rpm/dnf/yum."""
        packages = []
        
        try:
            # Query installed texlive packages
            result = subprocess.run(
                ["rpm", "-qa", "--queryformat", "%{NAME}|%{VERSION}|%{SUMMARY}\n", "*texlive*", "*latex*"],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Parse rpm output
            for line in result.stdout.strip().split('\n'):
                if '|' in line:
                    parts = line.split('|', 2)
                    if len(parts) >= 3:
                        package_name = parts[0]
                        version = parts[1]
                        description = parts[2]
                        
                        category = self._categorize_package(package_name, description)
                        
                        packages.append({
                            "name": package_name,
                            "version": version,
                            "description": description,
                            "category": category,
                            "installed": True,
                            "source": "rpm"
                        })
        
        except Exception as e:
            logger.error(f"Failed to query rpm packages: {e}")
        
        return packages
    
    def _categorize_package(self, name: str, description: str) -> str:
        """Categorize a LaTeX package based on its name and description."""
        name_lower = name.lower()
        desc_lower = description.lower()
        combined = f"{name_lower} {desc_lower}"
        
        # Define category patterns
        categories = {
            "languages": [
                "babel", "polyglossia", "language", "lang-", "hyphen",
                "chinese", "japanese", "korean", "arabic", "hebrew",
                "greek", "cyrillic", "devanagari"
            ],
            "templates": [
                "template", "class", "beamer", "thesis", "article",
                "book", "report", "letter", "cv", "resume", "poster"
            ],
            "fonts": [
                "font", "ttf", "otf", "type1", "truetype", "opentype",
                "libertine", "dejavu", "lato", "roboto", "fira"
            ],
            "graphics": [
                "tikz", "pgf", "graphics", "graphicx", "picture",
                "diagram", "plot", "chart", "svg", "eps"
            ],
            "math": [
                "math", "ams", "equation", "theorem", "proof",
                "algebra", "calculus", "geometry"
            ],
            "bibliography": [
                "bib", "biblatex", "bibtex", "natbib", "citation",
                "reference", "bibliography"
            ],
            "formatting": [
                "format", "layout", "geometry", "margin", "spacing",
                "indent", "paragraph", "section", "chapter"
            ],
            "science": [
                "science", "physics", "chemistry", "biology",
                "engineering", "units", "siunitx"
            ],
            "utilities": [
                "tool", "util", "helper", "macro", "package",
                "extension", "extra"
            ],
            "documentation": [
                "doc", "manual", "guide", "documentation",
                "example", "tutorial"
            ]
        }
        
        # Check each category
        for category, patterns in categories.items():
            for pattern in patterns:
                if pattern in combined:
                    return category
        
        # Default category
        if "texlive" in name_lower:
            return "core"
        
        return "other"
    
    def discover_packages(self) -> Dict[str, Any]:
        """
        Discover all installed LaTeX packages.
        
        Returns:
            Dictionary containing discovered packages and metadata
        """
        packages = []
        
        # Query packages based on package manager
        if self.package_manager in ["apt", "dpkg"]:
            packages = self._query_apt_packages()
        elif self.package_manager == "pacman":
            packages = self._query_pacman_packages()
        elif self.package_manager in ["rpm", "dnf", "yum"]:
            packages = self._query_rpm_packages()
        
        # Remove duplicates
        seen = set()
        unique_packages = []
        for pkg in packages:
            if pkg["name"] not in seen:
                seen.add(pkg["name"])
                unique_packages.append(pkg)
        
        # Sort by category and name
        unique_packages.sort(key=lambda x: (x["category"], x["name"]))
        
        # Build category summaries
        categories_summary = {}
        for pkg in unique_packages:
            cat = pkg["category"]
            if cat not in categories_summary:
                categories_summary[cat] = {
                    "count": 0,
                    "packages": []
                }
            categories_summary[cat]["count"] += 1
            categories_summary[cat]["packages"].append(pkg["name"])
        
        return {
            "distribution": self.distro_info,
            "package_manager": self.package_manager,
            "total_packages": len(unique_packages),
            "categories": categories_summary,
            "packages": unique_packages,
            "warnings": [
                "Package availability depends on your TeX distribution installation.",
                "Some packages may be installed but not detected by the package manager.",
                "Use 'tlmgr list --only-installed' for TeX Live specific packages."
            ]
        }
    
    def get_package_info(self, package_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific package.
        
        Args:
            package_name: Name of the package to query
            
        Returns:
            Package information or None if not found
        """
        # Use cache if available
        if package_name in self._cache:
            return self._cache[package_name]
        
        # Discover all packages if not already done
        discovery = self.discover_packages()
        
        # Find the package
        for pkg in discovery["packages"]:
            if pkg["name"] == package_name:
                self._cache[package_name] = pkg
                return pkg
        
        return None
    
    def search_packages(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for packages matching a query.
        
        Args:
            query: Search term (searches in name and description)
            
        Returns:
            List of matching packages
        """
        query_lower = query.lower()
        discovery = self.discover_packages()
        
        matches = []
        for pkg in discovery["packages"]:
            if (query_lower in pkg["name"].lower() or 
                query_lower in pkg["description"].lower()):
                matches.append(pkg)
        
        return matches