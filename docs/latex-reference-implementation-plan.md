# LaTeX Reference Tool - Full Implementation Plan

## Overview

The LaTeX reference tool is a comprehensive documentation system for LaTeX, designed as a full application with an MCP interface. It should provide instant, accurate help for commands, packages, symbols, and errors.

## Data Architecture

### 1. Primary Data Sources

#### latex2e-help-texinfo (Core LaTeX)
- **Source**: https://latexref.xyz/ or https://gitlab.com/latexref/latexref
- **License**: GFDL (GNU Free Documentation License)
- **Integration**: Git submodule or build-time fetch
- **Content**: ~500 core commands, environments, counters

#### The Comprehensive LaTeX Symbol List
- **Source**: CTAN mirrors
- **License**: LPPL
- **Integration**: Download during build
- **Content**: 14,000+ symbols from 200+ packages

#### CTAN Package Database
- **Source**: https://ctan.org/xml/1.3/packages
- **License**: Public
- **Integration**: API/XML fetch
- **Content**: All CTAN packages with metadata

### 2. Build System Design

```yaml
# build.yaml - Build configuration
sources:
  latex2e:
    type: git
    url: https://gitlab.com/latexref/latexref
    branch: main
    parser: texinfo
    
  symbols:
    type: http
    url: https://mirror.ctan.org/info/symbols/comprehensive/symbols-a4.pdf
    parser: pdf_tables
    
  ctan:
    type: api
    url: https://ctan.org/xml/1.3/packages
    parser: xml
    
  package_docs:
    type: texdoc
    packages: [amsmath, tikz, beamer, biblatex, hyperref, ...]
    parser: tex_comments

output:
  format: sqlite
  database: latex_reference.db
  indexes: [command, package, symbol, description]
```

### 3. Database Schema

```sql
-- Core tables
CREATE TABLE commands (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    syntax TEXT,
    description TEXT,
    package_id INTEGER,
    category TEXT,
    added_version TEXT,
    FOREIGN KEY (package_id) REFERENCES packages(id)
);

CREATE TABLE packages (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    ctan_path TEXT,
    version TEXT,
    license TEXT,
    dependencies TEXT -- JSON array
);

CREATE TABLE symbols (
    id INTEGER PRIMARY KEY,
    unicode TEXT,
    command TEXT NOT NULL,
    description TEXT,
    package_id INTEGER,
    category TEXT,
    image_base64 TEXT,
    FOREIGN KEY (package_id) REFERENCES packages(id)
);

CREATE TABLE errors (
    id INTEGER PRIMARY KEY,
    pattern TEXT NOT NULL,
    description TEXT,
    solution TEXT,
    related_package_id INTEGER,
    related_command_id INTEGER
);

-- Full-text search tables
CREATE VIRTUAL TABLE commands_fts USING fts5(
    name, description, syntax, 
    content=commands
);

CREATE VIRTUAL TABLE symbols_fts USING fts5(
    command, description,
    content=symbols
);

-- Indexes for performance
CREATE INDEX idx_commands_package ON commands(package_id);
CREATE INDEX idx_commands_name ON commands(name);
CREATE INDEX idx_symbols_command ON symbols(command);
```

### 4. Build Pipeline

```python
# build_reference_db.py
class ReferenceBuilder:
    def __init__(self, config_path):
        self.config = load_config(config_path)
        self.db = sqlite3.connect('latex_reference.db')
        
    def build(self):
        # 1. Fetch sources
        self.fetch_latex2e()
        self.fetch_symbols()
        self.fetch_ctan_data()
        
        # 2. Parse data
        commands = self.parse_latex2e()
        symbols = self.parse_symbol_list()
        packages = self.parse_ctan()
        
        # 3. Build relationships
        self.link_commands_to_packages()
        self.extract_error_patterns()
        
        # 4. Create search indexes
        self.build_fts_indexes()
        
        # 5. Generate statistics
        self.generate_stats()
```

## Search Implementation

### 1. Smart Search with Context

```python
class SmartSearch:
    def search(self, query, context=None):
        # 1. Detect query type
        query_type = self.detect_type(query)
        
        # 2. Apply context boost
        if context:
            # Boost results from packages used in current doc
            # Boost based on document type (math, presentation, etc.)
            pass
            
        # 3. Multi-strategy search
        results = []
        results.extend(self.exact_match(query))
        results.extend(self.fuzzy_match(query))
        results.extend(self.semantic_search(query))
        
        # 4. Rank and deduplicate
        return self.rank_results(results)
```

### 2. Query Understanding

```python
class QueryParser:
    patterns = [
        # "how to make a table" -> table environments
        (r'how to (?:make|create|draw) (?:a |an )?(\w+)', 'tutorial'),
        
        # "error undefined control sequence" -> error help
        (r'error:?\s*(.*)', 'error'),
        
        # "symbol for approximately" -> symbol search
        (r'symbol (?:for |of )?(.+)', 'symbol'),
        
        # "\frac" -> command lookup
        (r'\\(\w+)', 'command'),
        
        # "amsmath" -> package info
        (r'^[a-z]+[a-z0-9-]*$', 'package')
    ]
```

## Real-World Usage Integration

### 1. Usage Analytics

```python
# Track actual usage from documents
class UsageTracker:
    def analyze_document(self, tex_content):
        # Extract used packages, commands, environments
        # Store in usage_stats table
        # Use for ranking search results
```

### 2. Error Learning

```python
# Learn from compilation errors
class ErrorLearner:
    def learn_from_error(self, error_text, solution):
        # Extract pattern
        # Store successful solutions
        # Build error->solution mappings
```

## Practical Features

### 1. Package Availability Check

```python
def check_package_availability(package_name):
    # Try multiple methods
    methods = [
        lambda: subprocess.check_output(['kpsewhich', f'{package_name}.sty']),
        lambda: check_tlmgr_list(package_name),
        lambda: check_miktex_installed(package_name)
    ]
    
    for method in methods:
        try:
            return method()
        except:
            continue
    return None
```

### 2. Installation Guidance

```python
def get_install_command(package_name, context):
    system = detect_tex_system()
    
    if system == 'texlive':
        return f'tlmgr install {package_name}'
    elif system == 'miktex':
        return f'miktex packages install {package_name}'
    elif system == 'debian':
        return f'apt-get install texlive-{guess_debian_package(package_name)}'
```

### 3. Alternative Suggestions

```python
alternatives = {
    'qtree': ['forest', 'tikz-qtree'],
    'subfigure': ['subcaption', 'subfig'],
    'glossary': ['glossaries', 'nomencl']
}
```

## MCP Interface Enhancements

```python
@mcp.tool()
def reference(
    action: str,
    query: Optional[str] = None,
    # ... existing params ...
    context: Optional[Dict] = None,  # Current document context
    interactive: bool = False         # Enable follow-up questions
) -> str:
    """Enhanced reference tool with context awareness."""
    
    if context:
        # Use current document's packages, style, etc.
        enhancer = ContextEnhancer(context)
        results = enhancer.enhance_search(results)
```

## Deployment Strategy

### 1. Distribution Options

- **Option A**: Include pre-built SQLite database (~50MB)
- **Option B**: Build on first run with caching
- **Option C**: Hybrid - basic data included, extended data on demand

### 2. Update Mechanism

```python
class ReferenceUpdater:
    def check_updates(self):
        # Check CTAN for package updates
        # Check latex2e for new versions
        # Incremental updates only
```

## Success Metrics

1. **Coverage**: 95% of commands in typical documents found
2. **Speed**: < 50ms for any search
3. **Accuracy**: Correct package for command 99% of time
4. **Helpfulness**: Error solutions work 90% of time

## Key Insights from Usage

From creating real LaTeX documents, we learned:

1. **Command → Package mapping is critical**: When `\rowcolor` failed, we needed to know it requires `colortbl`
2. **Package availability matters**: `qtree.sty not found` needs installation guidance
3. **Context helps**: Knowing we're making tables could prioritize table-related packages
4. **Real errors teach best**: Actual compilation errors show what help is needed

This is a real application that will significantly improve the LaTeX authoring experience!