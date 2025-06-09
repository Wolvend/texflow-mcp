# TeXFlow Semantic API Usage Examples

This document shows how to use the new semantic API compared to the old direct tool approach.

## Document Management

### Creating Documents

**Old way (need to know format):**
```python
# For Markdown
save_markdown(
    content="# My Document\n\nHello world",
    filename="mydoc.md"
)

# For LaTeX
save_latex(
    content="\\documentclass{article}...",
    filename="mydoc.tex"
)
```

**New way (auto-detects format):**
```python
# System automatically chooses format based on content and intent
document(
    action="create",
    content="# My Document\n\nHello world",
    intent="quick note"  # Optional hint
)

# For academic content, it auto-selects LaTeX
document(
    action="create", 
    content="We prove that $\\int_0^1 x^2 dx = \\frac{1}{3}$",
    intent="math proof"
)
```

### Reading and Editing

**Old way:**
```python
# Read
content = read_document(file_path="/path/to/doc.md", offset=1, limit=50)

# Edit
edit_document(
    file_path="/path/to/doc.md",
    old_string="Hello",
    new_string="Hi",
    expected_replacements=1
)
```

**New way:**
```python
# Read
document(action="read", path="doc.md")

# Edit with multiple changes
document(
    action="edit",
    path="doc.md",
    changes=[
        {"old": "Hello", "new": "Hi"},
        {"old": "world", "new": "everyone"}
    ]
)
```

## Output Operations

### Printing Documents

**Old way (need to know format and printer):**
```python
# Need different tools for different formats
print_text(content="Hello", printer="HP_Printer")
print_markdown(file_path="doc.md", printer="HP_Printer")
print_latex(file_path="doc.tex", printer="HP_Printer")
print_file(path="/path/to/file.pdf", printer="HP_Printer")
```

**New way (unified interface):**
```python
# Auto-detects format and remembers printer preference
output(action="print", source="doc.md")
output(action="print", content="Quick text to print")

# First time asks: "Would you like to print or save as PDF?"
# Remembers choice for session
```

### Exporting to PDF

**Old way:**
```python
# Different tools for different formats
markdown_to_pdf(
    file_path="doc.md",
    output_path="output.pdf",
    title="My Document"
)

latex_to_pdf(
    file_path="doc.tex",
    output_path="output.pdf"
)
```

**New way:**
```python
# Single export action handles all formats
output(
    action="export",
    source="doc.md"  # Auto-detects markdown
)

output(
    action="export",
    source="thesis.tex",  # Auto-detects LaTeX
    output_path="~/Documents/thesis_final.pdf"
)
```

## Project Management

### Creating Projects

**Old way:**
```python
create_project(
    name="my-thesis",
    description="PhD thesis on quantum computing"
)
```

**New way (with AI-powered structure):**
```python
project(
    action="create",
    name="my-thesis",
    description="PhD thesis on quantum computing with 5 chapters, needs figures and bibliography"
)
# AI creates: chapters/, figures/, references/, output/
```

### Working with Projects

**Old way:**
```python
# List projects
list_projects()

# Switch project
use_project(name="my-thesis")

# Get info
project_info()
```

**New way:**
```python
# Same actions, cleaner interface
project(action="list")
project(action="switch", name="my-thesis")
project(action="info", detailed=True)
```

## Workflow Examples

### Example 1: Write and Print a Letter

```python
# 1. Create the letter (auto-detects simple format)
doc = document(
    action="create",
    content="""
Dear Sir/Madam,

I am writing to inquire about...

Sincerely,
John Doe
""",
    intent="formal letter"
)

# 2. System suggests next steps:
# - "Edit the letter": document(action='edit')
# - "Print the letter": output(action='print')
# - "Save as PDF": output(action='export')

# 3. Print it
output(action="print", source=doc["path"])
```

### Example 2: Academic Paper Workflow

```python
# 1. Create project
project(
    action="create",
    name="ieee-paper-2025",
    description="IEEE conference paper on machine learning, 8 pages, needs abstract, intro, methodology, results, conclusion"
)

# 2. Create main document (AI suggests LaTeX for academic paper)
document(
    action="create",
    content="\\documentclass[conference]{IEEEtran}...",
    filename="main.tex",
    intent="IEEE conference paper"
)

# 3. Validate before submission
document(action="validate", path="main.tex")

# 4. Export final PDF
output(action="export", source="main.tex", output_path="final_submission.pdf")
```

### Example 3: Quick Notes to PDF

```python
# Simple markdown note
document(
    action="create",
    content="""
# Meeting Notes - Jan 8, 2025

## Attendees
- Alice
- Bob

## Action Items
1. Review proposal
2. Schedule follow-up
""",
    filename="meeting_notes.md"
)

# Direct to PDF without printing
output(action="export", source="meeting_notes.md")
```

## Getting Help

```python
# Check what you can do
texflow_help(topic="suggest_workflow", context="I want to write a thesis")

# Check system requirements
texflow_help(topic="check_requirements")

# Get format guidance
texflow_help(topic="format_help")

# Get next step suggestions
texflow_help(topic="next_steps")
```

## Key Benefits

1. **No format knowledge needed** - System detects optimal format
2. **Unified interface** - One command for all similar operations  
3. **Smart defaults** - Remembers preferences, suggests next steps
4. **Flexible input** - Multiple ways to specify the same thing
5. **AI assistance** - Understands intent and creates appropriate structure

## Migration Tips

- Start using semantic operations for new documents
- Old tools still work if needed
- Let auto-detection choose formats
- Use `intent` parameter to help the system understand your needs
- Check `texflow_help` when unsure