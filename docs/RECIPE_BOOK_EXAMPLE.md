# Recipe Book Example

This example demonstrates creating a family recipe book using TeXFlow's complete workflow.

## How an AI Agent Operates TeXFlow

As an AI agent using TeXFlow, I navigate the document creation process through semantic tool operations. Here's how I work:

### 1. Following Semantic Operations
Instead of needing to memorize a large toolset, I use 7 semantic operations (document, output, project, etc.) with action parameters. The consistent pattern `tool(action='...', parameters)` makes navigation intuitive.

### 2. Using Tool Hints
Each tool response includes `💡 Next:` suggestions that guide my next actions:
- After creating content → suggests read, edit, or export
- After validation failure → suggests edit to fix specific errors
- After export → suggests print or archive

### 3. Project Context Awareness
Once I create a project, TeXFlow maintains context. I don't track exact file paths - the system handles path resolution within the project structure.

### 4. Validation Feedback Loops
When validation fails, I receive specific error information rather than generic messages. This allows targeted fixes without guessing.

### 5. Conversion Over Recreation
I use the `convert` action to transform existing documents between formats, preserving content while changing presentation.

### 6. Modular Content Strategy
I create individual documents (intro, recipes) then combine them, making content reusable and maintainable.

## Project Setup

```python
# Create a new project
mcp__texflow__project(action='create', name='recipe-book', 
                      description='A collection of favorite recipes with beautiful formatting')
```

## Content Creation

Created three Markdown documents in the project:
- `content/intro.md` - Welcome and introduction
- `content/pasta-sauce.md` - Grandma's pasta sauce recipe  
- `content/sugar-cookies.md` - Holiday cookie recipe
- `content/recipe-book.md` - Combined book with all recipes

## Document Processing

```python
# Convert Markdown to LaTeX
mcp__texflow__document(action='convert', 
                       source='content/recipe-book.md',
                       target_format='latex')

# Enhance LaTeX with custom formatting
mcp__texflow__document(action='edit',
                       path='content/recipe-book.tex',
                       old_string='...', 
                       new_string='...')

# Validate the document
mcp__texflow__document(action='validate',
                       path='content/recipe-book.tex')
```

## Output Generation

```python
# Export to PDF
mcp__texflow__output(action='export',
                     source='content/recipe-book.tex')

# Print the recipe book
mcp__texflow__output(action='print',
                     source='content/recipe-book.pdf',
                     printer='BrotherHL-L3295CDW')
```

## Result

A professionally typeset recipe book with:
- Custom fonts and formatting
- Table of contents
- Consistent styling throughout
- Family stories and traditions preserved
- Ready for printing and sharing

The complete workflow took the content from simple Markdown files through LaTeX processing to a beautifully printed document.