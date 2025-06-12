#!/usr/bin/env python3
"""
Integration tests for the TeXFlow semantic workflow.

Tests the complete document workflow from creation to printing,
verifying all the improvements made during development.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our tools
from texflow import document, output, project, workflow, archive, SESSION_CONTEXT


class TestSemanticWorkflow(unittest.TestCase):
    """Test the complete semantic workflow with all improvements."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary workspace
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = Path.cwd()
        os.chdir(self.temp_dir)
        
        # Reset session context
        SESSION_CONTEXT["current_project"] = None
        SESSION_CONTEXT["workspace_root"] = Path(self.temp_dir)
        
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
        
        # Clean up any test projects
        texflow_dir = Path.home() / "Documents" / "TeXFlow"
        if texflow_dir.exists():
            for project_name in ["test-project", "guided"]:
                project_path = texflow_dir / project_name
                if project_path.exists():
                    shutil.rmtree(project_path)
        
    def test_document_create_without_project(self):
        """Test document creation in workspace root."""
        result = document(
            action="create",
            content="# Test Document\n\nThis is a test.",
            path="test.md"
        )
        
        # Check file was created in workspace
        expected_path = Path(self.temp_dir) / "test.md"
        self.assertTrue(expected_path.exists())
        self.assertIn("✓ Document created:", result)
        self.assertIn("test.md", result)
        
        # Verify hints include multiple options
        self.assertIn("→ Read:", result)
        self.assertIn("→ Edit:", result)
        self.assertIn("→ Export:", result)
        
    def test_project_workflow(self):
        """Test complete project-based workflow."""
        # Create project
        result = project(action="create", name="test-project", description="Test project")
        self.assertIn("✓ Project created:", result)
        self.assertEqual(SESSION_CONTEXT["current_project"], "test-project")
        
        # Create document in project
        result = document(
            action="create",
            content="# Project Document",
            path="doc.md"
        )
        self.assertIn("(Project: test-project)", result)
        
        # Verify file is in project content directory
        project_base = Path.home() / "Documents" / "TeXFlow" / "test-project"
        doc_path = project_base / "content" / "doc.md"
        self.assertTrue(doc_path.exists())
        
    def test_edit_validate_loop(self):
        """Test the edit/validate feedback loop."""
        # Create LaTeX document
        result = document(
            action="create",
            content="\\documentclass{article}\n\\begin{document}\nHello\n\\end{document}",
            path="test.tex"
        )
        
        # Verify validate option is offered for LaTeX
        self.assertIn("→ Validate:", result)
        
        # Edit the document
        result = document(
            action="edit",
            path="test.tex",
            old_string="Hello",
            new_string="Hello World"
        )
        
        # Check multiple next steps are offered
        self.assertIn("→ Edit more:", result)
        self.assertIn("→ Review changes:", result)
        self.assertIn("→ Validate:", result)
        self.assertIn("→ Export:", result)
        
    def test_validate_action(self):
        """Test LaTeX validation."""
        # Create valid LaTeX
        document(
            action="create",
            content="\\documentclass{article}\n\\begin{document}\nTest\n\\end{document}",
            path="valid.tex"
        )
        
        result = document(action="validate", path="valid.tex")
        # Should pass or have warnings, not errors
        self.assertTrue(
            "✓ Validation passed" in result or 
            "✓ Validation passed with warnings" in result
        )
        
    def test_convert_workflow(self):
        """Test document conversion."""
        # Create markdown
        document(
            action="create",
            content="# Test\n\nThis is **bold** text.",
            path="test.md"
        )
        
        # Convert to LaTeX
        result = document(
            action="convert",
            source="test.md",
            target_format="latex"
        )
        
        self.assertIn("✓ Converted to LaTeX:", result)
        self.assertTrue(Path("test.tex").exists())
        
    def test_archive_workflow(self):
        """Test archive operations."""
        # Create a document
        document(action="create", content="Old content", path="old.md")
        
        # Archive it
        result = archive(action="archive", path="old.md")
        self.assertIn("✓ Archived:", result)
        self.assertFalse(Path("old.md").exists())
        
        # Verify archive directory was created
        archive_dir = Path(".texflow_archive")
        self.assertTrue(archive_dir.exists())
        
    def test_status_action(self):
        """Test status checking."""
        # Create a document
        document(action="create", content="Test", path="status.md")
        
        # Check status
        result = document(action="status", path="status.md")
        self.assertIn("📄 File:", result)
        self.assertIn("🕒 Modified:", result)
        self.assertIn("📏 Size:", result)
        
    def test_workflow_suggestions(self):
        """Test workflow guidance."""
        # Without project
        result = workflow(action="next_steps")
        self.assertIn("Getting started:", result)
        self.assertIn("Create project:", result)
        
        # With project
        project(action="create", name="guided", description="Test")
        # Make sure project was set
        self.assertEqual(SESSION_CONTEXT["current_project"], "guided")
        result = workflow(action="next_steps")
        self.assertIn("Next steps in project 'guided':", result)
        
        # Task-specific suggestions
        result = workflow(action="suggest", task="write academic paper")
        self.assertIn("Academic Paper Workflow:", result)
        self.assertIn("refs.bib", result)  # Check for bibliography file
        

class TestPathResolution(unittest.TestCase):
    """Test path resolution logic."""
    
    def setUp(self):
        """Set up for path tests."""
        self.temp_dir = tempfile.mkdtemp()
        SESSION_CONTEXT["workspace_root"] = Path(self.temp_dir)
        SESSION_CONTEXT["current_project"] = None
        
    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir)
        
    def test_workspace_paths(self):
        """Test paths resolve to workspace when no project."""
        from texflow import resolve_path
        
        # Relative path
        path = resolve_path("test.md")
        self.assertEqual(path, Path(self.temp_dir) / "test.md")
        
        # No path
        path = resolve_path(None, "default", ".tex")
        self.assertEqual(path, Path(self.temp_dir) / "default.tex")
        
    def test_project_paths(self):
        """Test paths resolve to project directories."""
        from texflow import resolve_path
        
        SESSION_CONTEXT["current_project"] = "myproject"
        
        # Simple filename goes to content/
        path = resolve_path("doc.md")
        expected = Path.home() / "Documents" / "TeXFlow" / "myproject" / "content" / "doc.md"
        self.assertEqual(path, expected)
        
        # Project subdirectory paths
        path = resolve_path("output/report.pdf")
        expected = Path.home() / "Documents" / "TeXFlow" / "myproject" / "output" / "report.pdf"
        self.assertEqual(path, expected)


if __name__ == "__main__":
    unittest.main()