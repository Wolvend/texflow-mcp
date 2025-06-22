# LaTeX Reference Data Acquisition Strategy

## Overview

This document outlines strategies for building a comprehensive LaTeX reference database for TeXFlow, including data sources, extraction methods, and legal considerations.

## Data Sources

### 1. LaTeX2e-help-texinfo

**Source**: https://latexref.xyz/  
**License**: GNU Free Documentation License (GFDL)  
**Content**: Core LaTeX2e commands, environments, lengths, counters  
**Format**: Texinfo, HTML, PDF

**Extraction Strategy**:
```python
# Option 1: Parse HTML version
from bs4 import BeautifulSoup
import requests

def extract_from_latex2e_html():
    base_url = "https://latexref.xyz/"
    # Parse index page
    # Extract command definitions from each section
    # Structure: command -> syntax, description, examples
```

**Data Points**:
- ~500 core LaTeX commands
- ~50 environments
- ~100 counters and lengths
- Usage examples for each

### 2. The Comprehensive LaTeX Symbol List

**Source**: CTAN - symbols-a4.pdf  
**License**: LaTeX Project Public License (LPPL)  
**Content**: 14,000+ symbols from 200+ packages  
**Format**: PDF with structured tables

**Extraction Strategy**:
```python
# Option 1: PDF parsing with pdfplumber
import pdfplumber

def extract_symbols_from_pdf():
    with pdfplumber.open("symbols-a4.pdf") as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            # Parse symbol tables
            # Extract: symbol image, command, package
```

**Data Points**:
- Symbol visual representation
- LaTeX command(s)
- Required package
- Unicode mapping (where applicable)

### 3. Unicode-math Package Data

**Source**: unicode-math-table.tex  
**License**: LPPL  
**Content**: Unicode mathematical symbols with LaTeX mappings  
**Format**: TeX data file

**Extraction Strategy**:
```python
# Parse TeX data file
def parse_unicode_math():
    with open("unicode-math-table.tex") as f:
        for line in f:
            # Extract \UnicodeMathSymbol entries
            # Format: \UnicodeMathSymbol{"03B1}{\alpha}{\mathalpha}{greek small letter alpha}
```

**Data Points**:
- Unicode codepoint
- LaTeX command
- Symbol type
- Description

### 4. Package Documentation

**Sources**: 
- CTAN package documentation
- texdoc database
- Package source files (.sty, .dtx)

**Extraction Strategy**:
```python
# Option 1: Parse texdoc database
def get_package_list():
    # Run: texdoc -l --machine-readable
    # Parse JSON output
    
# Option 2: Parse .sty files
def extract_from_sty(package_name):
    # Find package with kpsewhich
    # Parse \newcommand, \def, \DeclareOption
    # Extract command signatures and descriptions
```

### 5. Common LaTeX Errors

**Sources**:
- TeX StackExchange data dump
- LaTeX error message documentation
- Community wikis

**Extraction Strategy**:
```python
# Parse StackExchange data
def extract_error_patterns():
    # Download data dump
    # Find questions tagged 'errors'
    # Extract error messages and accepted answers
    # Build pattern -> solution mapping
```

## Data Processing Pipeline

### 1. Collection Phase

```python
class DataCollector:
    def collect_all(self):
        self.collect_latex2e()      # Core commands
        self.collect_symbols()      # Symbol list
        self.collect_unicode()      # Unicode mappings
        self.collect_packages()     # Package docs
        self.collect_errors()       # Error patterns
```

### 2. Normalization Phase

```python
class DataNormalizer:
    def normalize(self, raw_data):
        # Standardize command names (\frac vs \frac{}{})
        # Merge duplicates from different sources
        # Resolve conflicts (prefer authoritative source)
        # Add cross-references
        # Validate data integrity
```

### 3. Enhancement Phase

```python
class DataEnhancer:
    def enhance(self, normalized_data):
        # Generate search keywords
        # Add category tags
        # Create inverse mappings (description -> command)
        # Add usage statistics (if available)
        # Generate examples where missing
```

### 4. Export Phase

```python
class DataExporter:
    def export(self, enhanced_data):
        # Split by category for efficient loading
        # Create search indices
        # Generate metadata
        # Compress for distribution
```

## Legal Considerations

### License Compatibility

| Source | License | Usage in TeXFlow | Attribution Required |
|--------|---------|------------------|---------------------|
| latex2e-help-texinfo | GFDL | ✓ Allowed | Yes |
| Comprehensive Symbol List | LPPL | ✓ Allowed | Yes |
| unicode-math | LPPL | ✓ Allowed | Yes |
| CTAN packages | Various (mostly LPPL) | Check each | Yes |
| StackExchange | CC BY-SA | ✓ Allowed | Yes |

### Attribution Template

```json
{
  "source": "latex2e-help-texinfo",
  "version": "2024.05",
  "license": "GFDL",
  "url": "https://latexref.xyz/",
  "attribution": "Copyright (C) 2024 Karl Berry, et al."
}
```

## Data Quality Assurance

### Validation Rules

1. **Completeness**: Every command has syntax and description
2. **Accuracy**: Commands tested with actual LaTeX compilation
3. **Consistency**: Naming conventions followed
4. **Coverage**: Common use cases covered

### Quality Metrics

```python
def calculate_quality_score(dataset):
    scores = {
        'completeness': check_required_fields(dataset),
        'accuracy': run_latex_tests(dataset),
        'coverage': measure_command_coverage(dataset),
        'freshness': check_last_updated(dataset)
    }
    return sum(scores.values()) / len(scores)
```

## Update Strategy

### Automated Updates

```yaml
# .github/workflows/update-reference-data.yml
name: Update Reference Data
on:
  schedule:
    - cron: '0 0 1 * *'  # Monthly
  workflow_dispatch:

jobs:
  update:
    steps:
      - name: Fetch latest sources
      - name: Run extraction pipeline
      - name: Validate data quality
      - name: Create PR if changes
```

### Manual Curation

- Community contributions via PR
- Expert review for new packages
- User feedback integration
- Error pattern updates from support

## Data Schema

### Command Schema
```json
{
  "name": "\\frac",
  "syntax": "\\frac{numerator}{denominator}",
  "description": "Creates a fraction",
  "package": "built-in",
  "category": ["math", "fractions"],
  "examples": [
    {
      "code": "\\frac{1}{2}",
      "description": "Simple fraction"
    }
  ],
  "related": ["\\dfrac", "\\tfrac", "\\nicefrac"],
  "see_also": ["amsmath"],
  "added": "1994-01-01",
  "updated": "2024-01-01",
  "source": {
    "name": "latex2e-help-texinfo",
    "url": "https://latexref.xyz/frac.html"
  }
}
```

### Symbol Schema
```json
{
  "symbol": "≈",
  "commands": ["\\approx"],
  "packages": ["built-in"],
  "unicode": "U+2248",
  "description": "Approximately equal to",
  "category": ["relations", "math"],
  "variants": ["\\thickapprox", "\\approxeq"],
  "image": "base64:...",  // Optional rendered image
  "source": {
    "name": "comprehensive-symbol-list",
    "page": 45
  }
}
```

## Implementation Timeline

### Phase 1: Core Data (Week 1-2)
- Extract latex2e-help-texinfo
- Basic command/environment data
- Manual entry of common symbols

### Phase 2: Symbol Expansion (Week 3-4)
- Parse Comprehensive Symbol List
- Unicode-math integration
- Symbol categorization

### Phase 3: Package Data (Week 5-6)
- Top 20 packages documentation
- Command extraction from .sty files
- Cross-reference with CTAN

### Phase 4: Error Patterns (Week 7-8)
- Common error collection
- Solution documentation
- Pattern matching rules

### Phase 5: Production Pipeline (Week 9-10)
- Automated extraction scripts
- Quality validation
- Update mechanisms

## Success Metrics

1. **Coverage**: 95% of commands in typical LaTeX documents
2. **Accuracy**: < 1% error rate in command syntax
3. **Freshness**: Updated within 30 days of package releases
4. **Usability**: 90% of searches return relevant results

## Conclusion

Building a comprehensive LaTeX reference requires combining multiple authoritative sources, careful data processing, and ongoing maintenance. The phased approach allows for incremental value delivery while building toward a complete reference system.