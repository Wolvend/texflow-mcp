# CUPS MCP Server

An MCP (Model Context Protocol) server that enables printing documents via CUPS on Linux systems.

## Features

### Printing
- List available CUPS printers with status information
- Print plain text directly
- Print Markdown documents (rendered to PDF via pandoc)
- Print files from the filesystem
- Automatic file type detection

### Document Creation & Saving
- Convert Markdown to PDF without printing
- Save Markdown content to .md files
- Save LaTeX content to .tex files
- Print LaTeX documents with full XeLaTeX compilation
- Smart path handling with Documents folder default
- Automatic file renaming to avoid overwrites

### Printer Management
- Get detailed printer information
- Set default printer
- Enable/disable printers
- Update printer descriptions and locations

### Smart Features
- Dependency checking at startup
- Conditional tool registration based on available dependencies
- Clear feedback when dependencies are missing

## Prerequisites

### Required
- Linux system with CUPS installed
- Python 3.10+

### Optional (for additional features)
- `pandoc` - For markdown to PDF conversion
  - Debian/Ubuntu: `apt install pandoc`
  - Fedora: `dnf install pandoc`
  - Arch: `pacman -S pandoc`
- **LaTeX/XeLaTeX** - For PDF generation from markdown and LaTeX documents
  
  **Core Requirements:**
  - XeLaTeX engine for PDF compilation
  - Latin Modern fonts for proper text rendering
  - Standard LaTeX packages for document formatting
  
  **Installation by Distribution:**
  
  - **Debian/Ubuntu**: 
    ```bash
    # Essential packages
    apt install texlive-xetex texlive-fonts-recommended texlive-latex-recommended
    
    # For TikZ diagrams and graphics (if needed)
    apt install texlive-pictures
    ```
  
  - **Fedora**: 
    ```bash
    # Essential packages
    dnf install texlive-xetex texlive-collection-fontsrecommended
    
    # For TikZ diagrams and graphics (if needed)
    dnf install texlive-collection-pictures
    ```
  
  - **Arch**: 
    ```bash
    # Essential packages
    pacman -S texlive-xetex texlive-fontsrecommended
    
    # For TikZ diagrams and graphics (if needed)
    pacman -S texlive-pictures
    ```
  
  **What Each Package Provides:**
  - `texlive-xetex`: XeLaTeX engine and fontspec package
  - `texlive-fonts-recommended`: Latin Modern, Computer Modern, and other standard fonts
  - `texlive-latex-recommended`: Essential LaTeX packages (geometry, etc.)
  - `texlive-pictures`: TikZ package for creating diagrams and graphics

The server will check for these dependencies at startup and only enable features that have their requirements met. Missing dependencies will be reported with installation instructions.

## Installation

```bash
# Install system dependencies (choose your distribution)

# Debian/Ubuntu - Full installation with all features
sudo apt-get install cups pandoc texlive-xetex texlive-fonts-recommended \
                     texlive-latex-recommended texlive-pictures

# Fedora - Full installation with all features  
sudo dnf install cups pandoc texlive-xetex texlive-collection-fontsrecommended \
                 texlive-collection-pictures

# Arch - Full installation with all features
sudo pacman -S cups pandoc texlive-xetex texlive-fontsrecommended \
               texlive-pictures

# Clone and install
git clone https://github.com/yourusername/cups-mcp
cd cups-mcp
uv sync
```

## Usage

### Running the server

```bash
uv run cups-mcp
```

### Available Tools

#### `list_printers`
Lists all available CUPS printers.

```json
{
  "name": "list_printers"
}
```

#### `print_text`
Prints plain text content.

```json
{
  "name": "print_text",
  "arguments": {
    "content": "Hello, World!",
    "printer": "Brother_HL_L2350DW"  // optional
  }
}
```

#### `print_markdown`
Prints Markdown content rendered as PDF via pandoc and XeLaTeX.

**Supports:**
- Standard markdown formatting (headers, lists, tables, code blocks)
- LaTeX math expressions (inline with `$`, display with `$$`)
- Latin scripts including European languages
- Greek and Cyrillic alphabets
- Basic symbols and punctuation

**Limited support for:**
- Complex Unicode (emoji, box drawing characters)
- Right-to-left scripts (Arabic, Hebrew)
- CJK characters (Chinese, Japanese, Korean)

```json
{
  "name": "print_markdown",
  "arguments": {
    "content": "# My Document\n\nThis is **bold** text.\n\nMath: $E = mc^2$",
    "printer": "HP_LaserJet",  // optional
    "title": "My Document"     // optional
  }
}
```

#### `print_file`
Prints a file from the filesystem.

```json
{
  "name": "print_file",
  "arguments": {
    "path": "/path/to/document.pdf",
    "printer": "Canon_PIXMA"  // optional
  }
}
```

#### `get_printer_info`
Get detailed information about a specific printer including status, make/model, location, and URI.

```json
{
  "name": "get_printer_info",
  "arguments": {
    "printer_name": "My_Printer"
  }
}
```

#### `set_default_printer`
Change the default printer.

```json
{
  "name": "set_default_printer",
  "arguments": {
    "printer_name": "CanonG3260"
  }
}
```

#### `enable_printer` / `disable_printer`
Control printer availability for accepting jobs.

```json
{
  "name": "enable_printer",
  "arguments": {
    "printer_name": "My_Printer"
  }
}
```

#### `update_printer_info`
Update printer description and/or location.

```json
{
  "name": "update_printer_info",
  "arguments": {
    "printer_name": "My_Printer",
    "description": "Office Color Laser",
    "location": "Room 201"
  }
}
```

#### `markdown_to_pdf`
Convert markdown to PDF and save to a file (without printing).

**Supports:**
- Same markdown features as `print_markdown`
- Saves PDF to specified path instead of printing

```json
{
  "name": "markdown_to_pdf",
  "arguments": {
    "content": "# My Document\n\nSave this as PDF.",
    "output_path": "report.pdf",  // Saves to ~/Documents/report.pdf by default
    "title": "My Document"
  }
}
```

#### `print_latex`
Print LaTeX content (compiled to PDF via XeLaTeX).

**Supports:**
- Full LaTeX syntax and packages
- Mathematical formulas and equations
- TikZ diagrams and graphics
- Bibliography and citations
- Custom document classes

```json
{
  "name": "print_latex",
  "arguments": {
    "content": "\\documentclass{article}\n\\begin{document}\nHello LaTeX!\n\\end{document}",
    "printer": "My_Printer",  // optional
    "title": "My LaTeX Doc"  // optional
  }
}
```

#### `save_markdown`
Save markdown content to a .md file.

```json
{
  "name": "save_markdown",
  "arguments": {
    "content": "# My Document\n\nThis is my markdown content.",
    "filename": "notes.md"  // Saves to ~/Documents/notes.md by default
  }
}
```

#### `save_latex`
Save LaTeX content to a .tex file.

```json
{
  "name": "save_latex",
  "arguments": {
    "content": "\\documentclass{article}\n\\begin{document}\nHello LaTeX!\n\\end{document}",
    "filename": "document.tex"  // Saves to ~/Documents/document.tex by default
  }
}
```

#### `list_documents`
List PDF and Markdown files in the Documents folder.

```json
{
  "name": "list_documents",
  "arguments": {
    "folder": "reports"  // Optional: list files in ~/Documents/reports
  }
}
```

#### `print_from_documents`
Print a PDF or Markdown file from the Documents folder.

```json
{
  "name": "print_from_documents",
  "arguments": {
    "filename": "report.pdf",     // or just "report" - will find .pdf or .md
    "printer": "My_Printer",  // optional
    "folder": "reports"           // optional subfolder
  }
}
```

**Features:**
- Automatically finds .pdf or .md extension if not specified
- Converts Markdown files to PDF before printing
- Works with subfolders in Documents

**Path handling for save tools:**
- Simple filename (e.g., `report.pdf`) → Saves to `~/Documents/`
- Full path (e.g., `/home/user/Documents/report.pdf`) → Uses exact path
- Path with `~` (e.g., `~/Downloads/report.pdf`) → Expands to home directory

**Automatic features:**
- Creates Documents directory if it doesn't exist
- Generates unique filename if file already exists (adds _1, _2, etc.)
- Returns clear error messages for permission issues or other failures

### AI Agent Guidelines

#### Printer Selection Logic

When using the printing tools, AI agents should follow this logic:

1. **First print request:**
   - If user doesn't specify, ask: "Would you like to print or save as PDF?"
   - If printing and no default printer exists, ask which printer to use
   - Remember the chosen printer for the session

2. **Subsequent requests:**
   - Use the remembered printer from the first request
   - Only change if user explicitly specifies a different printer

#### File Paths

When saving PDFs with `markdown_to_pdf`:
- Use simple filenames (e.g., `report.pdf`) which save to `~/Documents/`
- Don't assume the user's home directory path
- Let the tool handle path expansion

This ensures users aren't repeatedly asked about printer selection and files are saved to predictable locations.

## Claude Desktop Configuration

Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "cups-mcp": {
      "command": "uv",
      "args": ["--directory", "/path/to/cups-mcp", "run", "cups-mcp"]
    }
  }
}
```

## Future Enhancements

- [ ] HTML to PDF printing (via weasyprint)
- [ ] SVG to PDF printing (via rsvg-convert)
- [ ] Image format handling and scaling
- [ ] Print job status tracking
- [ ] Print job cancellation
- [ ] Printer options (paper size, orientation, etc.)
- [ ] Base64 encoded content support

## License

MIT