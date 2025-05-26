# CUPS MCP Server

An MCP (Model Context Protocol) server that enables printing documents via CUPS on Linux systems.

## Features

- List available CUPS printers
- Print plain text directly
- Print Markdown documents (rendered to PDF via pandoc)
- Print files from the filesystem
- Automatic file type detection

## Prerequisites

- Linux system with CUPS installed
- Python 3.10+
- `pandoc` (for Markdown printing)
- `texlive` or `xelatex` (for PDF generation from pandoc)

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