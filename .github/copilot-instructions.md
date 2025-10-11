# GitHub Copilot Instructions for WireViz

## Project Overview

WireViz is a tool for easily documenting cables, wiring harnesses and connector pinouts. It takes plain text, YAML-formatted files as input and produces beautiful graphical output (SVG, PNG, HTML) using GraphViz.

## Key Technologies

- **Python 3.12+** - Main programming language
- **GraphViz** - Graph visualization for generating wiring diagrams
- **YAML** - Input format for wiring specifications
- **Pillow (PIL)** - Image processing
- **Typer** - CLI framework

## Code Style Guidelines

- Follow **PEP 8** Python style guidelines
- Use **isort** for import sorting
- Use **black** for code formatting (line length: 100 characters)
- Use Google Style for documentation strings ([examples](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html))
- UTF-8 encoding for all input and output files

## Project Structure

```
src/wireviz/          # Main source code
  __init__.py         # App metadata (version, name, URL)
  wireviz.py          # Main parsing logic
  harness.py          # Harness data model
  bom.py              # Bill of Materials generation
  colors.py           # Color handling (IEC 60757, DIN 47100, etc.)
  data.py             # Data structures (Metadata, Options, Tweak)
  helper.py           # Utility functions
  html.py             # HTML output generation
  graphviz_html.py    # GraphViz HTML table generation
  svgembed.py         # SVG embedding
  build_examples.py   # Script to build examples
  main.py             # CLI entry point
  templates/          # HTML output templates
docs/                 # Documentation
  README.md           # Main documentation
  syntax.md           # YAML syntax reference
  CONTRIBUTING.md     # Contribution guidelines
examples/             # Example wiring diagrams
tutorial/             # Tutorial files
```

## Core Concepts

### YAML Input Format

WireViz uses YAML files with these main sections:

1. **connectors**: Dictionary of connector definitions (type, pins, pinlabels, etc.)
2. **cables**: Dictionary of cable/wire definitions (gauge, length, colors, shield, etc.)
3. **connections**: List of connection mappings between connectors and cables
4. **additional_bom_items**: Custom BOM entries
5. **metadata**: Harness metadata (title, description, notes, etc.)
6. **options**: Global options (fontname, bgcolor, template, etc.)
7. **tweak**: GraphViz output tweaking

### Color Handling

WireViz supports multiple color coding standards:
- IEC 60757 (BK, RD, OR, YE, GN, BU, VT, GY, WT, etc.)
- DIN 47100 (WT, BN, GN, YE, GY, PK, BU, RD, BK, VT, etc.)
- 25 Pair Color Code
- TIA/EIA 568 A/B

### Output Formats

- `.gv` - GraphViz source
- `.svg` - Vector diagram
- `.png` - Raster diagram
- `.bom.tsv` - Bill of Materials (tab-separated)
- `.html` - HTML page with embedded diagram and BOM

## Important Patterns

### Parsing Flow

1. Parse YAML input (file, string, or dict)
2. Validate and expand data structures
3. Create Harness object
4. Generate GraphViz output
5. Render to requested formats (PNG, SVG, HTML)
6. Generate BOM

### Template System

HTML templates use placeholders like:
- `<!-- %generator% -->` - App name, version, URL
- `<!-- %bom% -->` - BOM table
- `<!-- %diagram% -->` - SVG diagram
- `<!-- %metadata_{item}_{category}_{key}% -->` - Custom metadata

Templates can be:
1. Specified in YAML: `metadata.template.name: din-6771`
2. Placed in same directory as input file
3. Stored in `src/wireviz/templates/`
4. Default: `simple.html`

## Testing and Building

### Build Examples

```bash
python -m wireviz.build_examples build
```

### CLI Usage

```bash
wireviz path/to/file.yml
wireviz path/to/files/*.yml  # Wildcards supported
```

## Common Tasks

### Adding a New Color Scheme

1. Update `colors.py` with color definitions
2. Add color code mapping
3. Update documentation in `docs/syntax.md`

### Adding a New Connector Type

1. Modify connector parsing in `harness.py`
2. Update YAML schema validation
3. Add example in `examples/`
4. Document in `docs/syntax.md`

### Modifying HTML Output

1. Edit templates in `src/wireviz/templates/`
2. Update placeholder handling in `html.py`
3. Document in `src/wireviz/templates/README.md`

## Contribution Guidelines

- Always create a feature branch from `dev` branch
- Submit issues before PRs to discuss changes
- Prefix issue titles: `[bug]`, `[feature]`, `[internal]`, `[doc]`, `[meta]`
- Format code with `isort` and `black` before submitting
- Update `docs/syntax.md` if changing YAML syntax
- Avoid committing generated files (examples, etc.) to reduce merge conflicts
- Consider interactive rebasing for complex PRs to clean commit history
- Reference issue numbers in PR descriptions

## Important Notes

- WireViz is designed for documenting individual wires and harnesses, not complete system wiring
- Wire gauge can be specified in mm² or AWG with auto-conversion
- The tool handles automatic BOM creation from connector and cable definitions
- Unicode/UTF-8 support for special characters in labels and text
- Auto-routing supported for 1-to-1 wiring connections

## Version Information

- Current version: 0.4.1
- Command name: `wireviz` (lowercase)
- Application name: `WireViz` (camelcase for human-readable text)
- Repository: https://github.com/wireviz/WireViz
