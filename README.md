# Pattern File Recognizer

A Microsoft Presidio recognizer that identifies patterns from text and CSV files using fast keyword matching.

## Installation

```bash
pip install pattern-file-recognizer
```

## Usage

```python
from presidio_analyzer import AnalyzerEngine
from pattern_file_recognizer import PatternFileRecognizer

# Create recognizer with pattern files
recognizer = PatternFileRecognizer(
    patterns_files=['customers.txt', ('products.csv', 'product_name')],
    allowlist_files=['common_words.txt'],
    entity_type='CUSTOMER_ORG',
    csv_column='name',        # default column for CSV files
)

# Add to Presidio Analyzer
analyzer = AnalyzerEngine()
analyzer.registry.add_recognizer(recognizer)

# Analyze text
text = "Working with Acme Corp on a project."
results = analyzer.analyze(text=text, language="en")
```

## File Formats

### Plain Text (.txt)

- One pattern per line
- Blank lines ignored
- Lines starting with `#` are comments
- Leading/trailing whitespace stripped

```text
# Customer names
Acme Corp
Widget Inc
```

### CSV (.csv)

- Standard CSV with header row
- Specify column via `csv_column` parameter or tuple override

```csv
name,region
Acme Corp,West
Widget Inc,East
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `patterns_files` | list | Yes | - | List of pattern file paths |
| `entity_type` | str | Yes | - | Entity type for matches |
| `allowlist_files` | list | No | `[]` | Files with patterns to exclude |
| `csv_column` | str | No | `"name"` | Default column for CSV files |
| `case_sensitive` | bool | No | `False` | Case-sensitive matching |
