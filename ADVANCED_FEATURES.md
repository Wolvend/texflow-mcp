# TeXFlow Advanced Features Documentation

## Overview

TeXFlow now includes 11 powerful tools for comprehensive LaTeX document management, making it a complete solution for academic writing, book authoring, and technical documentation.

## Complete Tool Reference

### 1. Document Tool (Enhanced)
Manages document creation and editing with incremental writing support.

```json
{
  "name": "document",
  "arguments": {
    "action": "append",
    "path": "thesis/chapter3.tex",
    "content": "\\section{Results}\n\nThe experimental results show..."
  }
}
```

**Actions**:
- `create`: Start new document
- `read`: View existing content
- `edit`: Replace entire content
- `append`: Add to end (perfect for continuous writing)
- `insert`: Add at specific position

**Insert Positions**:
- `"position": "line:42"` - Insert at line 42
- `"position": "after:\\section{Methods}"` - Insert after text
- `"position": "before:\\section{Conclusion}"` - Insert before text

### 2. Output Tool
Export documents to PDF or DOCX format.

```json
{
  "name": "output",
  "arguments": {
    "action": "export",
    "path": "thesis/main.tex",
    "format": "pdf"
  }
}
```

### 3. Project Tool (Enhanced)
Create and manage projects with templates.

```json
{
  "name": "project",
  "arguments": {
    "action": "create",
    "name": "quantum-physics-thesis",
    "template": "thesis"
  }
}
```

**Templates**:
- `book`: Multi-chapter book structure
- `thesis`: Academic thesis/dissertation
- `article`: Journal article
- `report`: Technical report
- `math-heavy`: Mathematical document
- `novel`: Fiction writing

### 4. Compile Tool
Compile LaTeX with different engines.

```json
{
  "name": "compile",
  "arguments": {
    "path": "main.tex",
    "engine": "xelatex",
    "passes": 3
  }
}
```

**Engines**:
- `pdflatex`: Standard, fast
- `xelatex`: Unicode support, modern fonts
- `lualatex`: Advanced programming features

### 5. Diagnose Tool 🆕
Automatically diagnose and fix LaTeX errors.

```json
{
  "name": "diagnose",
  "arguments": {
    "path": "thesis.tex",
    "auto_fix": true,
    "install_missing": true
  }
}
```

**Features**:
- Parses compilation errors
- Suggests fixes for common issues
- Auto-installs missing packages
- Fixes unclosed braces, missing $, etc.

### 6. Bibliography Tool 🆕
Manage references and citations.

```json
{
  "name": "bibliography",
  "arguments": {
    "action": "import",
    "source": "10.1038/nature12373"
  }
}
```

**Actions**:
- `import`: Import from DOI, arXiv, ISBN
- `format`: Clean up bibliography formatting
- `check`: Find duplicate entries
- `convert`: Change citation styles
- `search`: Search for references

**Example - Import from arXiv**:
```json
{
  "name": "bibliography",
  "arguments": {
    "action": "import",
    "source": "arXiv:2301.00001"
  }
}
```

### 7. Version Control Tool 🆕
Track document changes without Git.

```json
{
  "name": "version",
  "arguments": {
    "action": "commit",
    "path": "thesis.tex",
    "message": "Added results section"
  }
}
```

**Actions**:
- `commit`: Save version snapshot
- `diff`: Show changes
- `rollback`: Restore previous version
- `history`: List all versions
- `branch`: Create alternate versions

### 8. Smart Edit Tool 🆕
LaTeX-aware search and replace.

```json
{
  "name": "smart_edit",
  "arguments": {
    "action": "search",
    "path": "thesis.tex",
    "pattern": "\\\\cite\\{smith2020\\}",
    "scope": "citations"
  }
}
```

**Scopes**:
- `all`: Entire document
- `equations`: Math environments only
- `figures`: Figure environments
- `tables`: Table environments
- `citations`: Citation commands
- `commands`: LaTeX commands

**Find Unused References**:
```json
{
  "name": "smart_edit",
  "arguments": {
    "action": "find_unused",
    "path": "thesis.tex"
  }
}
```

### 9. Analytics Tool 🆕
Track writing progress and statistics.

```json
{
  "name": "analytics",
  "arguments": {
    "action": "wordcount",
    "path": "thesis.tex",
    "by_section": true
  }
}
```

**Actions**:
- `wordcount`: Count words (total or by section)
- `velocity`: Writing speed over time
- `progress`: Track completion
- `structure`: Analyze document structure

### 10. Export Tool 🆕
Export to multiple formats.

```json
{
  "name": "export",
  "arguments": {
    "path": "thesis.tex",
    "format": "epub",
    "options": {
      "epub_cover": "cover.jpg"
    }
  }
}
```

**Formats**:
- `pdf`: Standard PDF
- `docx`: Word with optional track changes
- `epub`: E-book format
- `html`: Web page with custom CSS
- `markdown`: GitHub-compatible
- `rtf`: Rich text format

### 11. Performance Tool 🆕
Optimize compilation speed.

```json
{
  "name": "performance",
  "arguments": {
    "action": "analyze",
    "path": "thesis/"
  }
}
```

**Actions**:
- `analyze`: Find compilation bottlenecks
- `cache`: Configure caching
- `optimize`: Apply optimizations
- `profile`: Detailed timing analysis

## Workflow Examples

### Academic Writing Workflow

1. **Create thesis project**:
```json
{
  "name": "project",
  "arguments": {
    "action": "create",
    "name": "phd-thesis",
    "template": "thesis"
  }
}
```

2. **Import references**:
```json
{
  "name": "bibliography",
  "arguments": {
    "action": "import",
    "source": "10.1038/nature12373"
  }
}
```

3. **Write incrementally**:
```json
{
  "name": "document",
  "arguments": {
    "action": "append",
    "path": "chapters/results.tex",
    "content": "\\subsection{Statistical Analysis}\n..."
  }
}
```

4. **Track progress**:
```json
{
  "name": "analytics",
  "arguments": {
    "action": "wordcount",
    "path": "thesis.tex",
    "by_section": true
  }
}
```

5. **Version before major changes**:
```json
{
  "name": "version",
  "arguments": {
    "action": "commit",
    "path": "thesis.tex",
    "message": "Before restructuring chapter 3"
  }
}
```

### Book Writing Workflow

1. **Create book project**:
```json
{
  "name": "project",
  "arguments": {
    "action": "create",
    "name": "my-novel",
    "template": "novel"
  }
}
```

2. **Write chapter by chapter**:
```json
{
  "name": "document",
  "arguments": {
    "action": "append",
    "path": "chapters/chapter5.tex",
    "content": "The hero faced a difficult choice..."
  }
}
```

3. **Track writing velocity**:
```json
{
  "name": "analytics",
  "arguments": {
    "action": "velocity",
    "path": "my-novel/",
    "period": "week"
  }
}
```

4. **Export to e-reader**:
```json
{
  "name": "export",
  "arguments": {
    "path": "main.tex",
    "format": "epub"
  }
}
```

### Mathematical Document Workflow

1. **Smart search in equations**:
```json
{
  "name": "smart_edit",
  "arguments": {
    "action": "search",
    "path": "paper.tex",
    "pattern": "\\\\nabla",
    "scope": "equations"
  }
}
```

2. **Diagnose compilation errors**:
```json
{
  "name": "diagnose",
  "arguments": {
    "path": "complex_math.tex",
    "auto_fix": true
  }
}
```

3. **Optimize performance**:
```json
{
  "name": "performance",
  "arguments": {
    "action": "cache",
    "path": "main.tex"
  }
}
```

## Best Practices

### 1. Error Recovery
Always run `diagnose` when compilation fails:
```json
{
  "name": "diagnose",
  "arguments": {
    "path": "document.tex",
    "auto_fix": true
  }
}
```

### 2. Bibliography Management
- Import references immediately when citing
- Run `check` periodically for duplicates
- Use consistent citation styles

### 3. Version Control
- Commit before major edits
- Use descriptive messages
- Create branches for experiments

### 4. Performance
- Use caching for large documents
- Analyze if compilation is slow
- Consider splitting very large files

### 5. Smart Editing
- Use scoped searches for precision
- Find unused references before submission
- Leverage regex for complex patterns

## Security Notes

All advanced features maintain security:
- Path validation ensures workspace isolation
- File size limits prevent resource exhaustion
- Safe handling of LaTeX commands
- No execution of arbitrary code

## Troubleshooting

### Compilation Fails
1. Run `diagnose` first
2. Check for missing packages
3. Verify file paths
4. Use appropriate engine

### Performance Issues
1. Run performance analysis
2. Enable caching
3. Split large files
4. Reduce image resolution

### Bibliography Problems
1. Check for duplicates
2. Verify citation keys
3. Ensure .bib file exists
4. Format consistently

## Future Enhancements

Planned features:
- Real-time collaboration
- Cloud backup integration
- AI-powered writing suggestions
- Automated citation formatting
- Grammar checking for academic style