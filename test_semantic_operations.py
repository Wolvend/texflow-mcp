#!/usr/bin/env python3
"""
Test script for semantic operations.

This demonstrates the new semantic API vs the old direct tool approach.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import semantic components
from src.core.semantic_router import SemanticRouter
from src.core.operation_registry import OperationRegistry
from src.core.format_detector import FormatDetector
from src.features.document import DocumentOperation
from src.features.output import OutputOperation
from src.features.project import ProjectOperation


def test_format_detection():
    """Test format detection logic."""
    print("\n=== Testing Format Detection ===")
    
    detector = FormatDetector()
    
    # Test cases
    test_cases = [
        {
            "content": "# My Quick Note\n\nThis is a simple note with a [link](http://example.com).",
            "intent": "quick note",
            "expected": "markdown"
        },
        {
            "content": "\\documentclass{article}\n\\begin{document}\nHello\\end{document}",
            "intent": None,
            "expected": "latex"
        },
        {
            "content": "I need to solve the equation $\\int_0^\\infty e^{-x^2} dx$",
            "intent": "math homework",
            "expected": "latex"
        },
        {
            "content": "TODO:\n- Buy milk\n- Call mom\n- Finish project",
            "intent": "todo list",
            "expected": "markdown"
        }
    ]
    
    for i, test in enumerate(test_cases):
        result = detector.detect(test["content"], test["intent"])
        status = "✓" if result["format"] == test["expected"] else "✗"
        print(f"\nTest {i+1}: {status}")
        print(f"  Intent: {test['intent'] or 'None'}")
        print(f"  Expected: {test['expected']}, Got: {result['format']}")
        print(f"  Confidence: {result['confidence']}")
        if result["reasons"]:
            print(f"  Reasons: {', '.join(result['reasons'])}")


def test_operation_registry():
    """Test operation registry and requirement checking."""
    print("\n\n=== Testing Operation Registry ===")
    
    registry = OperationRegistry()
    
    # Create mock operations for testing
    class MockDocumentOp:
        def execute(self, action, params, context):
            return {"success": True, "action": action}
        
        def get_capabilities(self):
            return {
                "system_requirements": {
                    "command": [
                        {"name": "pandoc", "required_for": ["convert"]},
                        {"name": "xelatex", "required_for": ["validate"], "user_install": True}
                    ],
                    "tex_package": [
                        {"name": "fontspec", "required_for": ["validate"]}
                    ]
                }
            }
    
    # Register operations
    registry.register("document", MockDocumentOp())
    
    print("\nRegistered operations:", registry.list_operations())
    
    # Check system requirements
    print("\nChecking system requirements...")
    requirements = registry.check_system_requirements()
    
    print(f"\nSatisfied requirements: {len(requirements['satisfied'])}")
    for req in requirements['satisfied'][:3]:  # Show first 3
        print(f"  ✓ {req['requirement']['name']} ({req['type']})")
    
    print(f"\nMissing requirements: {len(requirements['missing'])}")
    for req in requirements['missing'][:3]:  # Show first 3
        print(f"  ✗ {req['requirement']['name']} ({req['type']})")
        if req.get('install_hint'):
            print(f"    Hint: {req['install_hint']}")
    
    if requirements['warnings']:
        print(f"\nWarnings: {len(requirements['warnings'])}")
        for warning in requirements['warnings'][:3]:
            print(f"  ⚠ {warning}")


def test_semantic_routing():
    """Test semantic routing with workflow hints."""
    print("\n\n=== Testing Semantic Router ===")
    
    # Create router
    router = SemanticRouter()
    
    # Create mock texflow instance
    class MockTeXFlow:
        def save_markdown(self, content, filename):
            return f"Markdown saved to: {filename}"
        
        def save_latex(self, content, filename):
            return f"LaTeX saved to: {filename}"
    
    # Register operations
    texflow = MockTeXFlow()
    router.register_operation("document", DocumentOperation(texflow))
    
    # Test routing
    print("\nTest 1: Create a simple note")
    result = router.route("document", "create", {
        "content": "# Shopping List\n- Milk\n- Eggs",
        "intent": "quick shopping list"
    })
    print(f"  Format chosen: {result.get('format', 'unknown')}")
    print(f"  Success: {result.get('success', False)}")
    
    print("\nTest 2: Create academic content")
    result = router.route("document", "create", {
        "content": "The integral $\\int_0^1 x^2 dx = \\frac{1}{3}$",
        "intent": "math paper"
    })
    print(f"  Format chosen: {result.get('format', 'unknown')}")
    print(f"  Success: {result.get('success', False)}")
    
    # Test workflow hints
    if "workflow" in result:
        print(f"\n  Workflow hints:")
        print(f"    Message: {result['workflow']['message']}")
        if result['workflow'].get('suggested_next'):
            print(f"    Next steps:")
            for step in result['workflow']['suggested_next'][:2]:
                print(f"      - {step['description']}")


def main():
    """Run all tests."""
    print("TeXFlow Semantic Operations Test Suite")
    print("=" * 50)
    
    test_format_detection()
    test_operation_registry()
    test_semantic_routing()
    
    print("\n\nTest suite completed!")
    print("\nNext steps:")
    print("1. Complete remaining operations (printer, discover, workflow)")
    print("2. Create main semantic entry point")
    print("3. Integrate with texflow.py MCP server")
    print("4. Update MCP tool registrations to use semantic layer")


if __name__ == "__main__":
    main()