#!/usr/bin/env python3
"""Test script for LaTeX package discovery functionality."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.package_discovery import PackageDiscovery
from src.core.system_checker import SystemDependencyChecker

def test_package_discovery():
    """Test the package discovery functionality."""
    print("Testing LaTeX Package Discovery\n" + "="*50)
    
    # Test direct package discovery
    print("\n1. Testing Direct Package Discovery:")
    try:
        pd = PackageDiscovery()
        print(f"   Distribution: {pd.distro_info}")
        print(f"   Package Manager: {pd.package_manager}")
        
        packages = pd.discover_packages()
        print(f"\n   Total packages found: {packages['total_packages']}")
        print(f"   Categories: {list(packages['categories'].keys())}")
        
        # Show sample packages
        print("\n   Sample packages by category:")
        for cat, info in list(packages['categories'].items())[:3]:
            print(f"   - {cat}: {info['count']} packages")
            sample = info['packages'][:3]
            for pkg in sample:
                print(f"     • {pkg}")
            
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test system checker integration
    print("\n\n2. Testing System Checker Integration:")
    try:
        checker = SystemDependencyChecker()
        report = checker.check_all_dependencies()
        
        if "discovered_packages" in report:
            dp = report["discovered_packages"]
            print(f"   Package discovery available: {dp.get('available', False)}")
            if dp.get('available'):
                print(f"   Total packages: {dp.get('total_packages', 0)}")
                print(f"   Package manager: {dp.get('package_manager', 'unknown')}")
            else:
                print(f"   Reason: {dp.get('message', 'Unknown')}")
        else:
            print("   No discovered_packages section in report")
            
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test discover action
    print("\n\n3. Testing Discover Action (texflow.py):")
    try:
        # Import the discover function
        import texflow
        result = texflow.discover("packages")
        print(result)
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Save full report
    print("\n\n4. Saving Full Report:")
    try:
        checker = SystemDependencyChecker()
        report = checker.check_all_dependencies()
        
        output_file = Path("package_discovery_report.json")
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"   Full report saved to: {output_file}")
        
    except Exception as e:
        print(f"   ERROR: {e}")

if __name__ == "__main__":
    test_package_discovery()