#!/usr/bin/env python3
"""
Integration tests for the TeXFlow templates tool.

Tests template creation, management, and integration with projects.
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
from texflow import templates, project, document, SESSION_CONTEXT, TEMPLATES_DIR


class TestTemplates(unittest.TestCase):
    """Test the templates tool functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary workspace
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = Path.cwd()
        os.chdir(self.temp_dir)
        
        # Reset session context
        SESSION_CONTEXT["current_project"] = None
        SESSION_CONTEXT["workspace_root"] = Path(self.temp_dir)
        
        # Backup existing templates directory if it exists
        self.templates_backup = None
        if TEMPLATES_DIR.exists():
            self.templates_backup = TEMPLATES_DIR.parent / "templates_backup"
            if self.templates_backup.exists():
                shutil.rmtree(self.templates_backup)
            shutil.move(str(TEMPLATES_DIR), str(self.templates_backup))
            
        # Re-initialize default template for tests
        from texflow import initialize_default_template
        initialize_default_template()
            
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
        
        # Clean up test templates
        if TEMPLATES_DIR.exists():
            shutil.rmtree(TEMPLATES_DIR)
            
        # Restore original templates if they existed
        if self.templates_backup and self.templates_backup.exists():
            shutil.move(str(self.templates_backup), str(TEMPLATES_DIR))
            
        # Clean up any test projects
        texflow_dir = Path.home() / "Documents" / "TeXFlow"
        for project_name in ["template-test-project"]:
            project_path = texflow_dir / project_name
            if project_path.exists():
                shutil.rmtree(project_path)

    def test_default_template_initialization(self):
        """Test that default template is created on initialization."""
        # The default template should already exist from initialization
        self.assertTrue(TEMPLATES_DIR.exists())
        default_template = TEMPLATES_DIR / "default" / "minimal"
        self.assertTrue(default_template.exists())
        
        # Check default template files
        self.assertTrue((default_template / "main.tex").exists())
        self.assertTrue((default_template / "references.bib").exists())
        self.assertTrue((default_template / "README.md").exists())
        
    def test_list_templates(self):
        """Test listing templates."""
        result = templates(action="list")
        self.assertIn("default/minimal", result)
        self.assertIn("Available templates:", result)
        
    def test_template_info(self):
        """Test getting template information."""
        result = templates(action="info", category="default", name="minimal")
        self.assertIn("Template: default/minimal", result)
        self.assertIn("TeX files: 1", result)
        self.assertIn("Bibliography: 1", result)
        
    def test_create_template_with_content(self):
        """Test creating a new template with content."""
        content = r"""\documentclass{article}
\begin{document}
Test template
\end{document}"""
        
        result = templates(action="create", category="test", name="simple", content=content)
        self.assertIn("✓ Template created: test/simple", result)
        
        # Verify template was created
        template_path = TEMPLATES_DIR / "test" / "simple"
        self.assertTrue(template_path.exists())
        self.assertTrue((template_path / "main.tex").exists())
        
        # Verify content
        saved_content = (template_path / "main.tex").read_text()
        self.assertEqual(saved_content, content)
        
    def test_create_template_from_source(self):
        """Test creating a template from an existing file."""
        # Create a source file
        source_file = Path(self.temp_dir) / "source.tex"
        source_file.write_text(r"\documentclass{book}\begin{document}Book\end{document}")
        
        result = templates(action="create", category="book", name="mybook", 
                         source=str(source_file))
        self.assertIn("✓ Template created: book/mybook", result)
        
        # Verify template was created
        template_path = TEMPLATES_DIR / "book" / "mybook"
        self.assertTrue((template_path / "source.tex").exists())
        
    def test_use_template_in_project(self):
        """Test using a template in a project."""
        # Create a project
        project_result = project(action="create", name="template-test-project", 
                               description="Testing templates")
        self.assertIn("✓ Project created", project_result)
        
        # Use the default template
        result = templates(action="use", category="default", name="minimal")
        self.assertIn("✓ Template copied to:", result)
        self.assertIn("minimal-from-template", result)
        
        # Verify files were copied
        project_path = Path.home() / "Documents" / "TeXFlow" / "template-test-project"
        template_copy = project_path / "content" / "minimal-from-template"
        self.assertTrue(template_copy.exists())
        self.assertTrue((template_copy / "main.tex").exists())
        
    def test_copy_template(self):
        """Test copying a template."""
        # First create a template to copy
        templates(action="create", category="test", name="original", 
                 content=r"\documentclass{article}")
        
        # Copy it
        result = templates(action="copy", category="test", name="original", 
                         target="copy")
        self.assertIn("✓ Template copied: test/original → test/copy", result)
        
        # Verify copy exists
        self.assertTrue((TEMPLATES_DIR / "test" / "copy").exists())
        
    def test_copy_template_cross_category(self):
        """Test copying a template to a different category."""
        # Copy default template to a new category
        result = templates(action="copy", category="default", name="minimal", 
                         target="mycategory/mytemplate")
        self.assertIn("✓ Template copied: default/minimal → mycategory/mytemplate", result)
        
        # Verify copy exists
        self.assertTrue((TEMPLATES_DIR / "mycategory" / "mytemplate").exists())
        
    def test_rename_template(self):
        """Test renaming a template."""
        # Create a template to rename
        templates(action="create", category="test", name="oldname", 
                 content=r"\documentclass{article}")
        
        # Rename it
        result = templates(action="rename", category="test", name="oldname", 
                         target="newname")
        self.assertIn("✓ Template renamed: test/oldname → test/newname", result)
        
        # Verify old doesn't exist and new does
        self.assertFalse((TEMPLATES_DIR / "test" / "oldname").exists())
        self.assertTrue((TEMPLATES_DIR / "test" / "newname").exists())
        
    def test_delete_template(self):
        """Test deleting a template."""
        # Create a template to delete
        templates(action="create", category="test", name="deleteme", 
                 content=r"\documentclass{article}")
        
        # Delete it
        result = templates(action="delete", category="test", name="deleteme")
        self.assertIn("✓ Template deleted: test/deleteme", result)
        
        # Verify it's gone
        self.assertFalse((TEMPLATES_DIR / "test" / "deleteme").exists())
        
    def test_edit_template_location(self):
        """Test getting edit location for a template."""
        result = templates(action="edit", category="default", name="minimal")
        self.assertIn("Template location:", result)
        self.assertIn("main.tex", result)
        self.assertIn("document(action='edit'", result)
        
    def test_error_handling(self):
        """Test error cases."""
        # Non-existent template
        result = templates(action="info", category="fake", name="nothere")
        self.assertIn("❌ Error: Template 'fake/nothere' not found", result)
        
        # Missing required parameters
        result = templates(action="create", category="test")
        self.assertIn("❌ Error: Both category and name required", result)
        
        # Invalid action
        result = templates(action="invalid")
        self.assertIn("❌ Error: Unknown templates action", result)
        
    def test_no_templates_message(self):
        """Test message when no templates exist."""
        # Remove all templates
        if TEMPLATES_DIR.exists():
            shutil.rmtree(TEMPLATES_DIR)
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)  # Create empty dir
        
        result = templates(action="list")
        self.assertIn("No templates found", result)
        self.assertIn("Clone template repository", result)


if __name__ == "__main__":
    unittest.main()