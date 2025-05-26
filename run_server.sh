#!/bin/bash
cd /home/aaron/Projects/ai/mcp/cups-mcp
exec /usr/bin/uv run python -c "from main import server; server.run()"