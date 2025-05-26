# CUPS MCP Server

An MCP (Model Context Protocol) server that enables printing documents via CUPS on Linux systems.

## Features

- List available CUPS printers
- Print plain text directly
- Print Markdown documents (rendered to PDF via pandoc)
- Print files from the filesystem
- Automatic file type detection

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
Prints Markdown content rendered as PDF.

```json
{
  "name": "print_markdown",
  "arguments": {
    "content": "# My Document\n\nThis is **bold** text.",
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