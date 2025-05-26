# CUPS MCP Server Project Memory

## Development Workflow

We're using a rapid iteration pattern for MCP server development:

1. **Add to Claude Desktop**: Use `claude mcp add` to add the server
2. **Restart Claude Code**: After adding, restart Claude Code to test the server
3. **Iterate**: Make changes, then restart Claude Code to test again
4. **Test Tools**: 
   - Use MCP Inspector for interactive testing
   - Add regular test code as needed

## Project Overview

This is an MCP server that connects to CUPS on Linux for printing documents. The architecture uses lightweight tools:
- **pandoc** for Markdown → PDF conversion
- **weasyprint** for HTML → PDF (planned)
- **rsvg-convert** for SVG → PDF (planned)
- **convert** (ImageMagick) for image handling (planned)
- Direct `lp/lpr` commands for CUPS interaction

## Current Implementation

### Completed Tools
- `list_printers` - Lists all available CUPS printers
- `print_text` - Prints plain text content
- `print_markdown` - Renders Markdown to PDF via pandoc and prints
- `print_file` - Prints files from filesystem with MIME type detection

### Handler Architecture
We use a handler-based approach where each content type has its own conversion pipeline:
```
Input → Detector → Handler → PDF/PostScript → CUPS → Printer
```

## Testing Notes

To test the server locally:
```bash
uv run python main.py
```

For Claude Desktop integration:
```json
{
  "mcpServers": {
    "cups-mcp": {
      "command": "uv",
      "args": ["--directory", "/home/aaron/Projects/ai/mcp/cups-mcp", "run", "python", "main.py"]
    }
  }
}
```

## Known Issues & TODOs

- Need to handle pandoc installation check gracefully
- Add error handling for missing system dependencies
- Implement remaining handlers (HTML, SVG, images)
- Add print job status tracking
- Add printer options (paper size, orientation, etc.)