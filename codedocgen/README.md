# CodeDocGen: Automatic Code Documentation Generator

CodeDocGen is a Python package that uses AutoGen with Ollama to automatically generate comprehensive documentation for your codebase. It analyzes your code files and creates well-formatted documentation that explains the purpose, structure, and functionality of each file.

## Features

- **Automated Documentation**: Generate comprehensive documentation for your entire codebase with a single command
- **AI-Powered Analysis**: Uses Ollama's language models to understand and document your code
- **Multi-language Support**: Works with Python, JavaScript, TypeScript, Java, C/C++, and many other languages
- **Multiple Output Formats**: Generate documentation in Markdown, HTML, or JSON
- **Easy Configuration**: Interactive setup and configuration using simple CLI commands
- **Error Handling**: Robust error recovery and detailed reporting
- **Customizable**: Exclude directories, filter by file type, set size limits, and more

## Installation

```bash
# Install from PyPI
pip install codedocgen

# Or install from source
git clone https://github.com/yourusername/codedocgen.git
cd codedocgen
pip install -e .
```

## Prerequisites

- Python 3.7 or higher
- [Ollama](https://ollama.ai/) running locally
- A supported Ollama model (e.g., mistral, llama2, codellama)

## Quick Start

```bash
# Configure settings (only needed once)
codedocgen settings

# Generate documentation for current directory
codedocgen run

# Generate documentation for a specific directory
codedocgen run /path/to/your/project
```

## Commands

### Settings

Configure CodeDocGen settings interactively:

```bash
# Interactive configuration
codedocgen settings

# Show current configuration
codedocgen settings --show

# Reset configuration to defaults
codedocgen settings --reset
```

### Run

Generate documentation:

```bash
# Document current directory
codedocgen run

# Document specific directory
codedocgen run /path/to/project

# Document with specific settings
codedocgen run --model codellama --format html --exclude node_modules build
```

#### Run Options

| Option | Description |
|--------|-------------|
| `--model MODEL` | Ollama model to use (overrides config) |
| `--port PORT` | Ollama API port (overrides config) |
| `--format {markdown,html,json}` | Output format (overrides config) |
| `--output DIR` | Output directory for documentation |
| `--exclude [DIR/FILE ...]` | Directories or files to exclude |
| `--max-size SIZE` | Maximum file size in KB to process |
| `--extensions [EXT ...]` | File extensions to include (e.g., py js ts) |
| `--timeout SECONDS` | Timeout for API calls in seconds |
| `--verbose` | Enable verbose output |

## Output Structure

The documentation is organized as follows:

```
code_docs/
├── index.md (or .html/.json)
├── file1.md
├── file2.md
└── subdir/
    ├── file3.md
    └── file4.md
```

The index file contains:
- Overall statistics
- Language breakdown
- Links to all documentation files
- List of any errors encountered

## Troubleshooting

### Ollama Connection Issues

If you encounter connection errors:

1. Ensure Ollama is running: `ollama serve`
2. Check if the API is accessible: `curl http://localhost:11434/api/version`
3. Configure a different port if needed: `codedocgen settings`

### Memory Issues with Large Files

If the tool crashes with large files:

1. Reduce the maximum file size: `codedocgen run --max-size 200`
2. Exclude problematic directories: `codedocgen run --exclude path/to/large/files`

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
