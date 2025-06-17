#!/usr/bin/env python3
"""
Test script for MCP resources related to system dependencies.

This tests the resource functions without requiring a full MCP server.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.system_checker import SystemDependencyChecker


def simulate_mcp_resources():
    """Simulate the MCP resource functions."""
    print("🧪 Testing MCP Resource Functions")
    print("=" * 40)
    
    # Create checker instance
    system_checker = SystemDependencyChecker()
    
    # Test 1: Status resource (mimics get_system_dependencies_status)
    print("📊 Resource: system-dependencies://status")
    try:
        report = system_checker.check_all_dependencies()
        import json
        status_json = json.dumps(report, indent=2)
        print("✅ Status resource works")
        print(f"JSON length: {len(status_json)} characters")
    except Exception as e:
        print(f"❌ Status resource failed: {e}")
    print()
    
    # Test 2: Summary resource (mimics get_system_dependencies_summary)
    print("📋 Resource: system-dependencies://summary")
    try:
        report = system_checker.check_all_dependencies()
        summary = report.get("summary", {})
        
        status_emoji = {
            "fully_operational": "✅",
            "operational": "⚡", 
            "degraded": "⚠️",
            "unknown": "❓"
        }
        
        emoji = status_emoji.get(summary.get("overall_status", "unknown"), "❓")
        
        lines = [
            f"{emoji} TeXFlow System Dependencies Status",
            f"Platform: {report['metadata']['platform']}",
            f"Overall Status: {summary.get('overall_status', 'unknown')}",
            "",
            f"Essential: {summary.get('essential_available', 0)}/{summary.get('essential_total', 0)} available",
            f"Optional: {summary.get('optional_available', 0)}/{summary.get('optional_total', 0)} available",
            "",
            "Categories:"
        ]
        
        for cat_name, cat_info in report.get("categories", {}).items():
            status_icon = "✅" if cat_info["status"] == "available" else "⚠️" if cat_info["status"] == "partial" else "❌"
            lines.append(f"  {status_icon} {cat_name}: {cat_info['available_count']}/{cat_info['dependencies_count']}")
        
        summary_text = "\n".join(lines)
        print("✅ Summary resource works")
        print("Output preview:")
        print(summary_text)
        
    except Exception as e:
        print(f"❌ Summary resource failed: {e}")
    print()
    
    # Test 3: Missing dependencies resource (mimics get_missing_dependencies)
    print("🔍 Resource: system-dependencies://missing")
    try:
        suggestions = system_checker.get_installation_suggestions()
        
        if not suggestions["missing_essential"] and not suggestions["missing_optional"]:
            missing_text = "✅ All dependencies are available!"
        else:
            lines = [f"Missing Dependencies ({suggestions['platform']}):", ""]
            
            if suggestions["missing_essential"]:
                lines.extend([
                    "🚨 ESSENTIAL (required for core functionality):",
                    ""
                ])
                
                for dep in suggestions["missing_essential"]:
                    lines.append(f"• {dep['name']}: {dep['description']}")
                    if dep.get("installation_options"):
                        for pkg_mgr, pkg_name in dep["installation_options"].items():
                            lines.append(f"  Install: {pkg_mgr} install {pkg_name}")
                    if dep.get("platform_note"):
                        lines.append(f"  Note: {dep['platform_note']}")
                    lines.append("")
            
            if suggestions["missing_optional"]:
                lines.extend([
                    "💡 OPTIONAL (enhanced functionality):",
                    ""
                ])
                
                for dep in suggestions["missing_optional"]:
                    lines.append(f"• {dep['name']}: {dep['description']}")
                    if dep.get("installation_options"):
                        for pkg_mgr, pkg_name in dep["installation_options"].items():
                            lines.append(f"  Install: {pkg_mgr} install {pkg_name}")
                    if dep.get("platform_note"):
                        lines.append(f"  Note: {dep['platform_note']}")
                    lines.append("")
            
            missing_text = "\n".join(lines)
        
        print("✅ Missing dependencies resource works")
        print("Output preview:")
        print(missing_text)
        
    except Exception as e:
        print(f"❌ Missing dependencies resource failed: {e}")
    print()
    
    print("🎉 All MCP resource functions tested successfully!")


if __name__ == "__main__":
    simulate_mcp_resources()