# md2map

[English](./README.md) | [日本語](./README_ja.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)

A CLI tool that transforms large markdown documents into "semantic maps (index + document parts)" for AI analysis and review.

## Use Cases

- **AI Document Review**: Split large markdown files into AI-friendly semantic units to improve review accuracy
- **Document Structure Visualization**: Output heading hierarchy and section summaries as an index
- **Line Number Mapping**: Reliably map AI feedback to original file line numbers
- **Documentation Management**: Manage large specification documents by splitting them into maintainable parts

## Features

- **Heading-Based Splitting**: Split documents by H1, H2, H3 (and deeper) heading levels
- **Markdown Index Generation**: Auto-generate INDEX.md with structure tree and section details
- **Line Number Mapping**: Provide correspondence between parts and original file in MAP.json (machine-readable)
- **Japanese Support**: Full support for Japanese document processing and character counting
- **Code Block Awareness**: Correctly handle headings inside code blocks (skip them)
- **Dry Run**: Preview generation plan before actual output

## Setup

### Requirements

- Python 3.9 or higher
- [uv](https://docs.astral.sh/uv/) (recommended package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/md2map.git
cd md2map

# Install dependencies with uv (virtual environment created automatically)
uv sync --all-extras

# Verify installation
uv run md2map --help
```

## Usage

### Basic Execution

```bash
# Analyze a markdown file
uv run md2map build document.md --out ./output

# Analyze with custom depth (H1-H2 only)
uv run md2map build document.md --out ./output --max-depth 2
```

### Check Output

```bash
# View the index
cat output/INDEX.md

# View the split document parts
ls output/parts/

# View the line number mapping
cat output/MAP.json
```

### Dry Run (Preview)

```bash
# Preview the plan without generating files
uv run md2map build document.md --dry-run
```

## Main Options

| Option | Default | Description |
|--------|---------|-------------|
| `--out <DIR>` | `./md2map-out` | Output directory |
| `--max-depth <N>` | `3` | Maximum heading depth to process (1-6) |
| `--verbose` | false | Output detailed logs |
| `--dry-run` | false | Preview only, no file generation |

For details, see `uv run md2map build --help`.

## Output Examples

### INDEX.md

```markdown
# Index: specification.md

## Structure Tree

- specification.md
  - Introduction
    - Background
    - Purpose
  - Requirements
    - Functional Requirements
    - Non-Functional Requirements
  - Design

## Section Details

### Introduction
- **Path**: specification.md > Introduction
- **Lines**: 1-25
- **Summary**: This document describes the system specification...
- **Keywords**: system, specification, overview
```

### MAP.json

```json
[
  {
    "section": "Introduction",
    "level": 1,
    "path": "Introduction",
    "original_file": "specification.md",
    "original_start_line": 1,
    "original_end_line": 25,
    "word_count": 150,
    "part_file": "parts/Introduction.md",
    "checksum": "a1b2c3d4..."
  }
]
```

### Part Files

Each part file includes a metadata header:

```markdown
<!--
md2map fragment
original: specification.md
lines: 1-25
section: Introduction
level: 1
-->
# Introduction

This document describes the system specification...
```

## Directory Structure

```text
md2map/
├── md2map/                # Main package
│   ├── cli.py             # CLI entry point
│   ├── generators/        # Output generation modules
│   │   ├── index_generator.py   # INDEX.md generation
│   │   ├── map_generator.py     # MAP.json generation
│   │   └── parts_generator.py   # parts/ generation
│   ├── models/            # Data models
│   │   └── section.py     # Section information class
│   ├── parsers/           # Document parsers
│   │   ├── base_parser.py       # Base class
│   │   └── markdown_parser.py   # Markdown parser
│   └── utils/             # Utilities
│       ├── file_utils.py  # File operations
│       └── logger.py      # Log configuration
├── tests/                 # Test code
│   └── fixtures/          # Test fixtures
├── docs/                  # Documentation
├── README.md              # This file (English)
├── README_ja.md           # Japanese README
├── spec.md                # Technical specification
└── pyproject.toml         # Project configuration
```

## Limitations

- **Single File Processing**: Currently processes one file at a time
- **ATX Headings Only**: Setext-style headings (underline) are not supported
- **No Link Correction**: Internal links are detected but not automatically corrected in parts

For details, see [spec.md](spec.md).

## Related Projects

- [code2map](https://github.com/elvezjp/code2map) - Similar tool for source code analysis

## License

MIT License - For details, see [LICENSE](LICENSE).
