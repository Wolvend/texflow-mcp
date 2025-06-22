# LaTeX Reference Search Implementation Design

## Overview

The TeXFlow LaTeX reference tool needs an efficient search system to help users find commands, symbols, packages, and solutions among thousands of LaTeX-related items. This document outlines the current implementation and proposes improvements for production use.

## Current Implementation

### Architecture
- **Storage**: JSON files organized by category
- **Loading**: All data loaded into memory at startup
- **Search**: Linear iteration through dictionaries
- **Matching**: Simple substring matching (case-insensitive)

### Data Structure
```python
{
  "\\command": {
    "syntax": "\\command[options]{args}",
    "description": "What it does",
    "package": "package-name",
    "category": "category",
    "examples": [...],
    "related": [...]
  }
}
```

### Search Algorithm
```python
for item_name, item_info in database.items():
    if (query in item_name.lower() or 
        query in item_info.get("description", "").lower() or
        query in item_info.get("category", "").lower()):
        results.append(item)
```

### Performance Characteristics
- **Time Complexity**: O(n) where n = number of items
- **Space Complexity**: O(n) all data in memory
- **Startup Time**: Proportional to data size
- **Search Time**: ~1-10ms for 1000 items, ~10-100ms for 10,000 items

## Search Requirements

### Functional Requirements
1. **Fast Response**: < 100ms for searches
2. **Fuzzy Matching**: Handle typos and variations
3. **Relevance Ranking**: Best matches first
4. **Multi-field Search**: Search across names, descriptions, categories
5. **Contextual Results**: Boost results based on user's current document
6. **Incremental Search**: Support as-you-type functionality

### Non-Functional Requirements
1. **Scalability**: Handle 50,000+ items
2. **Low Memory**: Reasonable memory usage
3. **Easy Updates**: Simple to add new data
4. **No External Services**: Work offline
5. **Cross-Platform**: Work on all operating systems

## Proposed Search Implementations

### Option 1: Enhanced In-Memory Search (Short Term)

Improve the current system with minimal changes:

```python
import rapidfuzz
from collections import defaultdict

class EnhancedSearch:
    def __init__(self):
        # Build inverted index
        self.index = defaultdict(set)
        self.items = {}
        
    def add_item(self, id, item):
        self.items[id] = item
        # Tokenize and index
        tokens = self._tokenize(item['name'], item['description'])
        for token in tokens:
            self.index[token].add(id)
    
    def search(self, query, limit=20):
        # Fuzzy match against all items
        results = rapidfuzz.process.extract(
            query,
            self.items.keys(),
            scorer=rapidfuzz.fuzz.WRatio,
            limit=limit
        )
        return results
```

**Pros**:
- Minimal changes to existing code
- Adds fuzzy matching
- Still simple to understand

**Cons**:
- Still O(n) complexity
- Limited to simple ranking

### Option 2: SQLite Full-Text Search (Medium Term)

Use SQLite's FTS5 extension for professional full-text search:

```python
import sqlite3

class SQLiteSearch:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
    
    def _create_tables(self):
        self.conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS latex_ref USING fts5(
            type, name, syntax, description, package, category,
            content=latex_ref,
            tokenize = 'porter unicode61'
        )
        """)
        
        # Auxiliary table for exact data
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS latex_ref_data (
            id INTEGER PRIMARY KEY,
            type TEXT,
            name TEXT,
            data TEXT  -- JSON blob
        )
        """)
    
    def search(self, query, limit=20):
        # Use FTS5 ranking
        cursor = self.conn.execute("""
        SELECT *, rank FROM latex_ref 
        WHERE latex_ref MATCH ?
        ORDER BY rank
        LIMIT ?
        """, [query, limit])
        return cursor.fetchall()
```

**Pros**:
- Professional-grade full-text search
- Built-in relevance ranking
- Supports phrase searches, boolean operators
- Efficient even with 100k+ items
- No external dependencies

**Cons**:
- Requires building index
- More complex than in-memory

### Option 3: Dedicated Search Index (Long Term)

Use a dedicated search library like Whoosh:

```python
from whoosh import index, fields, qparser
from whoosh.analysis import StemmingAnalyzer

class WhooshSearch:
    def __init__(self, index_dir):
        self.schema = fields.Schema(
            type=fields.ID(stored=True),
            name=fields.TEXT(stored=True, analyzer=StemmingAnalyzer()),
            syntax=fields.TEXT(stored=True),
            description=fields.TEXT(analyzer=StemmingAnalyzer()),
            package=fields.KEYWORD(stored=True),
            category=fields.KEYWORD(stored=True, commas=True),
            examples=fields.TEXT,
            boost=fields.NUMERIC(stored=True)
        )
        self.ix = index.create_in(index_dir, self.schema)
    
    def search(self, query_str, limit=20):
        with self.ix.searcher() as searcher:
            # Multi-field search with boosting
            parser = qparser.MultifieldParser(
                ["name", "description", "category"],
                self.ix.schema,
                fieldboosts={"name": 2.0, "category": 1.5}
            )
            query = parser.parse(query_str)
            results = searcher.search(query, limit=limit)
            return [dict(r) for r in results]
```

**Pros**:
- Purpose-built for search
- Advanced features (stemming, boosting, facets)
- Highly customizable
- Good for complex search requirements

**Cons**:
- External dependency
- More complex setup
- Larger footprint

## Implementation Roadmap

### Phase 1: Quick Improvements (1-2 days)
1. Add fuzzy matching with rapidfuzz
2. Implement simple caching
3. Add search result highlighting
4. Basic relevance scoring

### Phase 2: SQLite FTS Integration (1 week)
1. Design SQLite schema
2. Build data import pipeline
3. Implement FTS5 search
4. Add search operators (AND, OR, phrases)
5. Performance testing

### Phase 3: Advanced Features (2-3 weeks)
1. Context-aware ranking (boost based on current document)
2. Search suggestions/autocomplete
3. Synonym support
4. Search analytics
5. Incremental index updates

## Performance Targets

| Dataset Size | Search Time | Memory Usage | Index Size |
|--------------|-------------|--------------|------------|
| 1,000 items  | < 10ms      | < 10MB       | < 1MB      |
| 10,000 items | < 50ms      | < 50MB       | < 10MB     |
| 50,000 items | < 100ms     | < 200MB      | < 50MB     |

## Search Quality Metrics

1. **Precision**: % of returned results that are relevant
2. **Recall**: % of relevant results that are returned  
3. **F1 Score**: Harmonic mean of precision and recall
4. **Mean Reciprocal Rank**: Average of 1/rank of first relevant result
5. **User Satisfaction**: Time to find desired result

## Testing Strategy

### Unit Tests
```python
def test_fuzzy_search():
    # Test typo tolerance
    results = search.find("\\fracc")  # typo in \frac
    assert "\\frac" in [r.name for r in results[:5]]

def test_relevance_ranking():
    # Test that exact matches rank higher
    results = search.find("section")
    assert results[0].name == "\\section"
```

### Performance Tests
```python
def test_search_performance():
    # Load 10k items
    search.load_bulk_data(generate_items(10000))
    
    # Measure search time
    start = time.time()
    results = search.find("equation")
    duration = time.time() - start
    
    assert duration < 0.05  # 50ms
```

### Quality Tests
- Create test sets of queries with expected results
- Measure precision/recall for common searches
- A/B test different ranking algorithms

## Future Enhancements

### Machine Learning Integration
- Learn from user clicks to improve ranking
- Suggest related commands based on usage patterns
- Auto-generate synonyms from documentation

### Natural Language Queries
- "How do I make a table?" → table-related commands
- "Symbol for approximately equal" → ≈, \approx
- Integration with LLMs for query understanding

### Visual Search
- Draw a symbol to find its LaTeX command
- Screenshot → LaTeX code suggestions
- Visual similarity search for symbols

## Conclusion

The current simple search works well for proof-of-concept but will need enhancement as the dataset grows. The recommended path is:

1. **Immediate**: Add fuzzy matching to improve user experience
2. **Short term**: Migrate to SQLite FTS5 for scalability
3. **Long term**: Consider dedicated search infrastructure if needed

The key is to maintain simplicity while providing a good search experience. SQLite FTS5 offers the best balance of features, performance, and simplicity for TeXFlow's needs.