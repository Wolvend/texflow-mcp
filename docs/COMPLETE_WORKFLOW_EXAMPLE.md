# TeXFlow Complete Workflow Example

This walkthrough demonstrates the complete TeXFlow pipeline from project creation to printing, using a family recipe book as an example.

## Overview

In this example, we:
1. Create a new project with organized structure
2. Write content in Markdown format
3. Convert to LaTeX for professional typesetting
4. Validate and fix any issues
5. Export to PDF
6. Send to a physical printer

## Step 1: Project Creation

```python
project(action='create', name='recipe-book', 
        description='A collection of favorite recipes with beautiful formatting')
```

**Output:**
```
✓ Project created: /home/aaron/Documents/TeXFlow/recipe-book
💡 Structure:
  - content/ (for source files)
  - output/pdf/ (for PDFs)
  - assets/ (for images/data)
💡 Next: document(action='create', content='...', path='content/intro.md')
```

The project automatically creates an organized directory structure. All subsequent operations use project-relative paths.

## Step 2: Creating Content

### Introduction Document

```python
document(action='create', 
         content='# Family Recipe Collection...', 
         path='content/intro.md')
```

### Individual Recipe Documents

We created multiple recipe documents:
- `content/pasta-sauce.md` - Grandma's Famous Pasta Sauce
- `content/sugar-cookies.md` - Holiday Sugar Cookies

### Combined Recipe Book

```python
document(action='create',
         content='# Our Family Recipe Book...',
         path='content/recipe-book.md')
```

This creates a complete recipe book combining all recipes with:
- Table of contents
- Formatted recipe sections
- Family stories and traditions
- Consistent styling

## Step 3: Converting to LaTeX

```python
document(action='convert',
         source='/home/aaron/Documents/TeXFlow/recipe-book/content/recipe-book.md',
         target_format='latex')
```

**Output:**
```
✓ Converted to LaTeX: /home/aaron/Documents/TeXFlow/recipe-book/content/recipe-book.tex
💡 Next: document(action='edit', path='/home/aaron/Documents/TeXFlow/recipe-book/content/recipe-book.tex')
```

## Step 4: Enhancing the LaTeX Document

The conversion creates a basic LaTeX file. We enhanced it with:

```latex
\documentclass[12pt,a4paper]{article}
\usepackage{xltxtra}
\usepackage{fontspec}
\usepackage{geometry}
\usepackage{fancyhdr}
\usepackage{titlesec}

% Custom formatting
\geometry{margin=1in}
\setmainfont{DejaVu Serif}

% Headers and footers
\pagestyle{fancy}
\fancyhead[C]{\textit{Our Family Recipe Book}}
\fancyfoot[C]{\thepage}
```

## Step 5: Validation

```python
document(action='validate',
         path='/home/aaron/Documents/TeXFlow/recipe-book/content/recipe-book.tex')
```

The validation:
- Checks LaTeX syntax with chktex
- Performs test compilation with XeLaTeX
- Reports specific errors with line numbers
- Suggests fixes for common issues

Initial validation found a font issue which we fixed by changing to an available font.

## Step 6: Export to PDF

```python
output(action='export',
       source='/home/aaron/Documents/TeXFlow/recipe-book/content/recipe-book.tex')
```

**Output:**
```
✓ PDF created: /home/aaron/Documents/TeXFlow/recipe-book/content/recipe-book.pdf
💡 Next: output(action='print', source='/home/aaron/Documents/TeXFlow/recipe-book/content/recipe-book.pdf')
```

## Step 7: Printing

First, check available printers:

```python
printer(action='list')
```

**Output:**
```
printer BrotherHL-L3295CDW is idle.  enabled since Wed 11 Jun 2025 06:46:58 PM CDT
printer CanonG3260 is idle.  enabled since Wed 07 May 2025 06:18:46 PM CDT
system default destination: BrotherHL-L3295CDW
```

Then send to printer:

```python
output(action='print',
       source='/home/aaron/Documents/TeXFlow/recipe-book/content/recipe-book.pdf',
       printer='BrotherHL-L3295CDW')
```

**Output:**
```
✓ Sent to printer: /home/aaron/Documents/TeXFlow/recipe-book/content/recipe-book.pdf
```

## Final Recipe Book Structure

The printed recipe book includes:

### Cover Page
- Centered title: "Our Family Recipe Book"
- Subtitle: "A Collection of Treasured Recipes"
- Professional typography with DejaVu Serif font

### Table of Contents
- Organized sections for Main Dishes and Desserts
- Clear navigation to each recipe

### Recipe Pages
Each recipe formatted with:
- Recipe name as heading
- Serving size, prep time, and cook time
- Ingredient lists with proper formatting
- Numbered instructions
- Family notes and traditions in italics
- Pull quotes for special family sayings

### Professional Touches
- Consistent headers on each page
- Page numbers centered at bottom
- Horizontal rules separating sections
- Proper typography for readability

## Key Workflow Features Demonstrated

1. **Project Organization**: All files automatically organized within project structure
2. **Format Flexibility**: Start with simple Markdown, convert to professional LaTeX
3. **Intelligent Hints**: Each step suggests logical next actions
4. **Validation Loop**: Catch and fix errors before printing
5. **Path Intelligence**: TeXFlow tracks file locations throughout the workflow
6. **Professional Output**: From simple text to beautifully typeset printed document

## Tips for Best Results

- Use the `convert` action to transform existing documents rather than rewriting
- Validate LaTeX documents before exporting to catch errors early
- The workflow supports iterative editing - make changes and re-validate as needed
- Projects keep all related files organized automatically
- Export creates PDFs in the project structure for easy access

This example shows how TeXFlow guides you through the complete document creation pipeline, from initial idea to printed output.