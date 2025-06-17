#!/usr/bin/env python3
"""
Test script for system dependency checker.

This script tests the system dependency checker functionality
without requiring the full MCP server to be running.
"""

import json
from pathlib import Path
from src.core.system_checker import SystemDependencyChecker


def main():
    """Test the system dependency checker."""
    print("🔍 Testing TeXFlow System Dependency Checker")
    print("=" * 50)
    
    try:
        # Initialize checker
        checker = SystemDependencyChecker()
        print(f"✅ Loaded manifest from: {checker.manifest_path}")
        print(f"🖥️  Platform detected: {checker.platform_name}")
        print()
        
        # Check all dependencies
        print("📋 Checking all dependencies...")
        report = checker.check_all_dependencies()
        
        # Print summary
        summary = report["summary"]
        print(f"📊 SUMMARY:")
        print(f"   Total dependencies: {summary['total_dependencies']}")
        print(f"   Essential: {summary['essential_available']}/{summary['essential_total']} available")
        print(f"   Optional: {summary['optional_available']}/{summary['optional_total']} available")
        print(f"   Overall status: {summary['overall_status']}")
        print()
        
        # Print essential dependencies status
        print("🚨 ESSENTIAL DEPENDENCIES:")
        for dep_name, dep_status in report["dependencies"]["essential"].items():
            status_icon = "✅" if dep_status["available"] else "❌"
            version_info = f" (v{dep_status['version']})" if dep_status["version"] else ""
            print(f"   {status_icon} {dep_name}{version_info}")
            if not dep_status["available"]:
                print(f"      Status: {dep_status['status']}")
                print(f"      Message: {dep_status['message']}")
                if dep_status.get("installation_options"):
                    print(f"      Install options: {dep_status['installation_options']}")
        print()
        
        # Print optional dependencies status
        print("💡 OPTIONAL DEPENDENCIES:")
        for dep_name, dep_status in report["dependencies"]["optional"].items():
            status_icon = "✅" if dep_status["available"] else "❌"
            version_info = f" (v{dep_status['version']})" if dep_status["version"] else ""
            print(f"   {status_icon} {dep_name}{version_info}")
            if not dep_status["available"]:
                print(f"      Status: {dep_status['status']}")
                print(f"      Message: {dep_status['message']}")
        print()
        
        # Print categories
        print("📂 CATEGORIES:")
        for cat_name, cat_info in report["categories"].items():
            status_icon = "✅" if cat_info["status"] == "available" else "⚠️" if cat_info["status"] == "partial" else "❌"
            essential_mark = " (ESSENTIAL)" if cat_info["essential"] else ""
            print(f"   {status_icon} {cat_name}: {cat_info['available_count']}/{cat_info['dependencies_count']}{essential_mark}")
            print(f"      {cat_info['description']}")
        print()
        
        # Get missing dependencies
        missing_essential = checker.get_missing_essential_dependencies()
        if missing_essential:
            print("⚠️  MISSING ESSENTIAL DEPENDENCIES:")
            for dep in missing_essential:
                print(f"   - {dep}")
            print()
        
        # Get installation suggestions
        suggestions = checker.get_installation_suggestions()
        if suggestions["missing_essential"] or suggestions["missing_optional"]:
            print("💻 INSTALLATION SUGGESTIONS:")
            print(f"Platform: {suggestions['platform']}")
            
            if suggestions["missing_essential"]:
                print("\n🚨 Essential (install these first):")
                for dep in suggestions["missing_essential"]:
                    print(f"   • {dep['name']}: {dep['description']}")
                    if dep.get("installation_options"):
                        for pkg_mgr, pkg_name in dep["installation_options"].items():
                            print(f"     {pkg_mgr} install {pkg_name}")
                    if dep.get("platform_note"):
                        print(f"     Note: {dep['platform_note']}")
            
            if suggestions["missing_optional"]:
                print("\n💡 Optional (enhanced functionality):")
                for dep in suggestions["missing_optional"]:
                    print(f"   • {dep['name']}: {dep['description']}")
                    if dep.get("installation_options"):
                        for pkg_mgr, pkg_name in dep["installation_options"].items():
                            print(f"     {pkg_mgr} install {pkg_name}")
                    if dep.get("platform_note"):
                        print(f"     Note: {dep['platform_note']}")
        else:
            print("🎉 All dependencies are available!")
        
        print()
        print("💾 Full report available as JSON in report.json")
        
        # Save full report to file
        with open("system_dependencies_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        # Test individual dependency checks
        print("\n🔬 INDIVIDUAL DEPENDENCY TESTS:")
        test_deps = ["pandoc", "xelatex", "fc-list"]
        
        for dep_name in test_deps:
            # Find the dependency in the manifest
            dep_config = None
            for section in ["essential", "optional"]:
                deps = checker.manifest.get("dependencies", {}).get(section, {})
                for manifest_name, config in deps.items():
                    if manifest_name == dep_name or dep_name in config.get("commands", []):
                        dep_config = config
                        break
                if dep_config:
                    break
            
            if dep_config:
                result = checker.check_dependency(dep_name, dep_config)
                status_icon = "✅" if result["available"] else "❌"
                print(f"   {status_icon} {dep_name}: {result['message']}")
            else:
                print(f"   ❓ {dep_name}: Not found in manifest")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()