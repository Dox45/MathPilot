# MathPilot

A scientific workflow assistant that transforms research papers into structured implementation plans and starter code.

## Overview

MathPilot bridges the gap between academic research and practical implementation. Given a natural language request like "implement a Kalman filter from this paper," the system:

1. **Searches** for relevant research papers (arXiv API)
2. **Parses** papers to extract core algorithms and methods
3. **Plans** a structured workflow with implementation steps
4. **Generates** Python starter code for each step
5. **Executes** (optionally) and logs results

## Quick Start

```bash
pip install -e .
mathpilot "implement a Kalman filter for sensor fusion"
```

## Project Structure

```
mathpilot/
├── cli/              # CLI commands (Typer-based)
├── search/           # Paper retrieval & caching
├── parser/           # Extract methods from papers
├── planner/          # Convert methods → workflow steps
├── generator/        # Generate Python starter code
├── executor/         # Execute & log generated code
├── workspace/        # Store generated projects
└── utils/            # Logging, file handling, etc.
```

## Module Responsibilities

| Module | Purpose |
|--------|---------|
| `cli` | Entry point, argument parsing, command routing |
| `search` | Query arXiv, cache papers, metadata |
| `parser` | Extract algorithms, methods, equations from PDFs |
| `planner` | Structure methods into logical workflow steps |
| `generator` | Create Python code templates for each step |
| `executor` | Safe execution of generated code with logging |
| `workspace` | Manage project directories and artifacts |
| `utils` | Logging, config, file I/O helpers |

## Development

### Install

```bash
pip install -e ".[dev,llm]"
```

### Run Tests

```bash
pytest                    # Full suite
pytest tests/test_search.py -v    # Single module
pytest -k test_parse --cov=mathpilot.parser  # Single test with coverage
```

### Lint & Format

```bash
black mathpilot tests
ruff check mathpilot tests --fix
mypy mathpilot
```

## Data Flow

```
User Input
    ↓
[CLI] Parses command
    ↓
[Search] Retrieves papers from arXiv
    ↓
[Parser] Extracts algorithms from PDF
    ↓
[Planner] Structures into workflow
    ↓
[Generator] Produces Python code
    ↓
[Workspace] Saves project
    ↓
[Executor] (Optional) Runs & logs
```

## Configuration

Create a `.mathpilot.yaml` in your project root or home directory:

```yaml
llm:
  provider: anthropic  # or openai
  model: claude-3-sonnet-20240229
arxiv:
  cache_dir: ~/.mathpilot/cache
  max_results: 10
executor:
  sandbox: true
  timeout_seconds: 300
```

## License

MIT
