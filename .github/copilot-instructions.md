# MathPilot Copilot Instructions

## Project Overview

**MathPilot** is a scientific workflow assistant that transforms research papers into structured implementation plans and starter Python code. The system bridges academic research and practical implementation by automating the extraction, planning, and code generation phases.

**Stack**: Python 3.10+, Typer (CLI), async patterns, Pydantic for validation

## Build, Test & Lint Commands

### Installation
```bash
pip install -e .              # Minimal installation
pip install -e ".[dev,llm]"   # Full dev + LLM providers
```

### Running
```bash
mathpilot --help              # Show CLI help
mathpilot implement "task"    # Main workflow
mathpilot --debug implement   # With debug logging
```

### Testing
```bash
pytest                                    # Run all tests
pytest tests/test_search.py -v           # Single test file
pytest -k test_extract --cov=mathpilot   # Tests matching pattern with coverage
pytest --cov=mathpilot --cov-report=html # HTML coverage report
```

### Code Quality
```bash
black mathpilot tests              # Format code
ruff check mathpilot tests --fix   # Lint + auto-fix
mypy mathpilot                     # Type checking
```

## Architecture & Data Flow

### Module Responsibilities

| Module | Role | Key Functions |
|--------|------|---|
| **cli** | Entry point & command routing | Typer app, argument parsing, delegates to other modules |
| **search** | Paper discovery & caching | Query arXiv API, cache PDFs, metadata management |
| **parser** | Extract algorithms from papers | PDF parsing, extract equations, methods, pseudocode using LLM |
| **planner** | Convert methods → workflow | Structure algorithms into ordered steps, identify dependencies |
| **generator** | Generate Python code | Create starter code for each step, generate requirements.txt |
| **executor** | Run generated code safely | Execute with timeout, capture logs, handle sandbox (optional) |
| **workspace** | Project management | Create project dirs, load/list projects, archive |
| **utils** | Cross-cutting concerns | Logging, config management, file I/O |

### Data Flow

```
User Input (CLI)
    ↓
[cli.implement] Parse args, load config
    ↓
[search] Find papers on arXiv (query from task)
    ↓
[parser] Extract algorithms from PDF
    ↓
[planner] Structure into Workflow with WorkflowStep objects
    ↓
[generator] Generate CodeTemplate for each step
    ↓
[workspace] Create project directory, save workflow + code
    ↓
[executor] (optional --execute flag) Run code, log results
```

### Key Data Structures

**search.Paper**: arXiv metadata (id, title, authors, abstract, pdf_url)

**parser.Algorithm**: Extracted algorithm (name, description, pseudocode, equations, inputs, outputs)

**planner.Workflow**: Complete plan with WorkflowStep list, overview, difficulty estimate

**planner.WorkflowStep**: Single implementation step (id, name, type, inputs, outputs, dependencies)

**generator.CodeTemplate**: Generated Python code for a step (step_id, filename, code, dependencies)

**workspace.Project**: Managed project (id, name, task, paper_title, root_dir, workflow_file, code_dir, logs_dir)

## Key Conventions

### Configuration
- Configuration file: `.mathpilot.yaml` in project root or home directory
- Sections: `llm`, `arxiv`, `executor`
- Config class loads with fallbacks: file → defaults
- Example in README.md

### Logging
- Use `get_logger(__name__)` in all modules
- Levels: DEBUG (--debug flag), INFO (default), WARNING, ERROR
- Logs go to stderr to keep stdout clean for CLI output

### Async Patterns
- `search_arxiv()` uses `async def` (can be called with `asyncio.run()`)
- Use `httpx` for async HTTP requests
- Generator/executor functions should be async-ready for future Jupyter integration

### File Organization
- Generated projects saved to `~/mathpilot_projects/{project_name}/`
- Standardized structure: `src/`, `tests/`, `data/`, `logs/`, `workflow.yaml`
- Cache arXiv papers in `~/.mathpilot/cache/`

### Type Hints
- All public functions use type hints
- Use `Optional[X]` from typing for optional values
- Use `list[X]` syntax (Python 3.10+) instead of `List[X]`

### Error Handling
- Custom exceptions in each module if needed (e.g., `ParserError`, `SearchError`)
- Log errors with context before raising
- Executor: catch timeout, subprocess errors gracefully

### CLI Patterns (Typer)
- Commands use `@app.command()` decorator
- Arguments use `typer.Argument(..., help="...")`
- Options use `typer.Option(..., help="...")`
- Debug callback: `@app.callback()` for global flags like `--debug`

### Testing
- Test files in `tests/` directory mirror module structure
- Use pytest fixtures for common setup
- Mocking: mock `httpx` calls in search tests, file I/O in workspace tests
- No external API calls in unit tests (use mocks)

### Dependencies
- **Core**: typer, httpx, pydantic, tenacity
- **LLM** (optional extra): anthropic, openai
- **Executor** (optional extra): jupyter, ipykernel
- **Dev**: pytest, pytest-cov, black, ruff, mypy

## Common Development Tasks

### Adding a New CLI Command
1. Define function in `cli/__init__.py` with `@app.command()` decorator
2. Use `typer.Argument()` and `typer.Option()` for parameters
3. Import helper function from relevant module (e.g., `search.search_arxiv`)
4. Log progress with `logger.info()`
5. Use `typer.echo()` for user-facing output

### Implementing a Module Function
1. Add function signature with docstring and type hints in `mathpilot/{module}/__init__.py`
2. Add `# TODO:` comments for implementation steps
3. Use `get_logger(__name__)` for logging
4. Validate inputs using Pydantic models where applicable
5. Return strongly-typed objects (Algorithm, Workflow, CodeTemplate, etc.)

### Adding a New Dependency
1. Add to appropriate section in `pyproject.toml` (dependencies, optional)
2. Run `pip install -e ".[extra_name]"` to test
3. Update README.md if it's a user-facing feature

### Integrating LLM Provider
- Use config system to switch between Anthropic/OpenAI
- Instantiate in relevant module (e.g., `parser` for extraction, `generator` for code)
- Handle API errors with tenacity retries
- Pass structured data to LLM, parse response into dataclass

## Project Guidelines

### MVP Focus
- Core workflow: search → parse → plan → generate
- Execution is optional and experimental
- Prioritize paper parsing accuracy over fancy UI
- One LLM provider (Anthropic preferred for best prompt control)

### Code Generation Quality
- Include type hints in generated code
- Add docstrings to generated functions
- Include error handling examples
- Suggest test structure
- Generated code should be copy-paste-ready

### Performance Considerations
- Cache arXiv PDFs to avoid re-downloads
- Use async for HTTP requests (potential batching)
- Lazy-load LLM clients (only instantiate when needed)
- Generator: template-based approach is faster than full LLM generation per file

### Safety First
- Executor: mandatory timeout on user code
- Config sandbox flag can restrict execution (future: use containerization)
- Never execute untrusted code without user confirmation
- Log all execution results for audit trail
