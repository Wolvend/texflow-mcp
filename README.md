# CUPS MCP Server

An MCP (Model Context Protocol) server that enables printing documents via CUPS on Linux systems.

## Features

### Printing
- List available CUPS printers with status information
- Print plain text directly
- Print Markdown documents (rendered to PDF via pandoc)
- Convert Markdown to PDF without printing
- Print files from the filesystem
- Automatic file type detection

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
- `xelatex` - For PDF generation from pandoc (requires XeLaTeX and fonts)
  - **Debian/Ubuntu**: 
    ```bash
    apt install texlive-xetex texlive-fonts-recommended texlive-latex-recommended
    ```
  - **Fedora**: 
    ```bash
    dnf install texlive-xetex texlive-collection-fontsrecommended
    ```
  - **Arch**: 
    ```bash
    pacman -S texlive-xetex texlive-fontsrecommended
    ```
  - Note: Basic texlive packages alone are not sufficient. You need:
    - XeLaTeX format files (`texlive-xetex`)
    - Latin Modern and other standard fonts (`texlive-fonts-recommended` or equivalent)
    - LaTeX packages for pandoc (`texlive-latex-recommended` on Debian/Ubuntu)

The server will check for these dependencies at startup and only enable features that have their requirements met. Missing dependencies will be reported with installation instructions.

## Installation

```bash
# Install system dependencies
sudo apt-get install cups pandoc texlive-xetex  # Debian/Ubuntu
# or
sudo dnf install cups pandoc texlive-xetex      # Fedora
# or
sudo pacman -S cups pandoc texlive-xetex        # Arch

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
    "printer_name": "BrotherHL-L3295CDW"
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
    "printer_name": "BrotherHL-L3295CDW"
  }
}
```

#### `update_printer_info`
Update printer description and/or location.

```json
{
  "name": "update_printer_info",
  "arguments": {
    "printer_name": "BrotherHL-L3295CDW",
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

**Path handling:**
- Simple filename (e.g., `report.pdf`) → Saves to `~/Documents/report.pdf`
- Full path (e.g., `/home/user/Documents/report.pdf`) → Uses exact path
- Path with `~` (e.g., `~/Downloads/report.pdf`) → Expands to home directory

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