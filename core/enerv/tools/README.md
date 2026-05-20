# facet-indexing — Phase 0 MVP

CLI for faceted project/knowledge folder indexing.

## Quick Start

### Dev Setup

```bash
cd tools
pip install -e ".[dev]"
```

### First Use

```bash
# Audit existing structure (read-only)
facet audit --root "C:\telo"

# Initialize .facets in a root
facet init --root "E:\" --type knowledge

# Create a new project
facet new project ai active my-project --root "C:\telo" --apply

# Rebuild index
facet index --root "C:\telo" --force
```

### Testing

```bash
pytest tests/ -v
pytest tests/test_cli.py -k "test_new" -v  # Single test
```

## Architecture

- `cli.py` — Click command dispatch
- `commands/` — Individual commands (audit, validate, new, index, migrate, init)
- `core/` — Shared logic (config, meta, index, journal, file_ops)
- `schemas/` — JSON Schemas (tech.schema.json, knowledge.schema.json)
- `tests/` — TDD test suite

## Phases

- **Phase 0 (MVP)**: Core tooling, pilot migration (this)
- **Phase 1**: Full tech migration + Claude Code plugin
- **Phase 2**: Semantic embeddings
- **Phase 3**: Bulk knowledge migration

## Entry Points

The package installs a `facet` command available after installation:

```bash
facet --version
facet --help
```

## Development

### File Structure

```
tools/
├── tools/
│   ├── __init__.py
│   ├── cli.py              # Main Click group
│   ├── commands/           # Command modules
│   ├── core/              # Core logic
│   └── schemas/           # JSON Schema files
├── tests/
│   └── test_*.py          # Test suite
├── pyproject.toml         # Package config + entry point
└── README.md              # This file
```

### Running Tests

```bash
# All tests with coverage
pytest tests/ -v --cov=tools

# Specific test
pytest tests/test_cli.py::test_audit -v

# Watch mode (requires pytest-watch)
ptw
```

### Integration Tests

```bash
bash tools/integration_test.sh
```

This validates:
- Init creates `.facets/` directories
- New projects register in meta
- Index rebuilds correctly
- Audit reports structure

## Deployment

### GitHub Actions (CI)

See `.github/workflows/test.yml` for automated test runs on push.

### Manual Installation

```bash
pip install -e .
```

This installs the `facet` command globally in your Python environment.

## Troubleshooting

**"facet: command not found"**

```bash
# Reinstall editable
cd tools
pip install -e .

# Verify entry point
python -m pip show facet-indexing
```

**Tests fail on Windows path**

The codebase is cross-platform. If tests fail on path handling:

```python
# Use pathlib.Path, not string manipulation
from pathlib import Path
root = Path(args.root)
```

**Schema validation errors**

Ensure `.facets/meta.json` matches the schema:

```bash
facet validate --root "C:\telo"
```

## Next Steps

1. **Phase 1**: Migrate full tech stack, create Claude Code plugin
2. **Phase 2**: Add semantic embeddings for cross-project discovery
3. **Phase 3**: Migrate knowledge folders with content-based faceting
