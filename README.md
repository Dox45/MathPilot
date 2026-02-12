# MathPilot 🚀

**Scientific Workflow Assistant - AI-Powered Algorithm Implementation**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

MathPilot is an intelligent agent capable of transforming natural language requests into fully functional, executable Python projects. It bridges the gap between academic research and practical implementation by automating the discovery, understanding, and coding of complex algorithms from scientific papers.

---

## 🌟 Key Features

*   **🔍 arXiv Paper Search**: Instantly find relevant research papers using natural language queries.
*   **🧠 Intelligent Parsing**: Extracts core algorithms, methods, and equations from PDFs using advanced LLMs (Gemini Pro, Claude 3, etc.).
*   **📋 Automated Planning**: Generates structured, step-by-step implementation plans (workflows) derived directly from the paper's methodology.
*   **💻 Code Generation**: Produces high-quality, documented Python code for each step of the workflow, including verification tests.
*   **📂 Project Management**: Automatically creates organized project directories with `requirements.txt`, source code, and data folders.
*   **🛡️ Safe Execution**: Runs generated code in a controlled environment to verify correctness (supports sandboxing).
*   **⚡ Interactive CLI**: A rich terminal interface for seamless searching, planning, and coding.

---

## 🚀 Quick Start

Get up and running in minutes.

### Prerequisites

*   Python 3.7+ (3.12+ Recommended)
*   **Gemini API Key** (for parsing and code generation) or **Anthropic/Groq API Key**.

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/mathpilot.git
cd mathpilot

# Install in editable mode
pip install -e .
```

### The 5-Minute Test

Verify your installation by implementing a classic algorithm:

```bash
# Set your API key
export GEMINI_API_KEY="your_api_key_here"

# Run the end-to-end test
mathpilot implement "linear regression" --execute
```

This command will:
1.  Search arXiv for "linear regression".
2.  Download and parse a relevant paper.
3.  Generate an implementation plan.
4.  Write the Python code.
5.  Execute the result!

---

## 📖 Usage Guide

MathPilot offers a powerful Command Line Interface (CLI) built with `Typer` and `Rich`.

### 1. Interactive Mode (Recommended)
The easiest way to use MathPilot is the interactive REPL.

```bash
mathpilot interactive
```
Follow the on-screen prompts to search for papers, browse local PDFs, and generate code.

### 2. Search for Papers
Find papers on arXiv without leaving your terminal.

```bash
mathpilot search "kalman filter sensor fusion" --max-results 5
```

### 3. Generate a Plan
Create an implementation plan from a specific paper (by arXiv ID or local PDF).

```bash
# From arXiv ID
mathpilot plan 2103.12345 --output plan.json

# From local PDF
mathpilot plan ./papers/my_research.pdf
```

### 4. Compiling to Code
Turn a plan into a working project.

```bash
mathpilot generate plan.json --project-name my_kalman_filter
```
This creates a folder `~/mathpilot_projects/my_kalman_filter` with the generated source code.

### 5. The "Do It All" Command
The `implement` command combines all steps into one.

```bash
mathpilot implement "implement the algorithm from this paper" --paper-id 2103.12345
```

---

## ⚙️ Configuration

MathPilot is configurable via environment variables or a `.mathpilot.yaml` file in your home directory.

### Environment Variables

| Variable | Description |
| :--- | :--- |
| `GEMINI_API_KEY` | **Required.** API key for Google Gemini models. |
| `ANTHROPIC_API_KEY`| Optional. For using Claude models. |
| `GROQ_API_KEY` | Optional. For using Groq-hosted open source models. |
| `LLM_PROVIDER` | Default LLM provider (e.g., `gemini`, `anthropic`, `groq`). |
| `LLM_MODEL` | Specific model name (e.g., `gemini-1.5-pro-latest`). |

### Configuration File (`~/.mathpilot.yaml`)

```yaml
llm:
  provider: gemini
  model: gemini-1.5-pro-latest

arxiv:
  cache_dir: ~/.mathpilot/cache
  max_results: 10

executor:
  sandbox: true
  timeout_seconds: 300
```

---

## 🏗️ Project Architecture

When MathPilot generates a project, it creates a clean, standard structure:

```
~/mathpilot_projects/my_project/
├── workflow.yaml              # The implementation plan metadata
├── requirements.txt           # Detected Python dependencies
├── src/                       # Source code directory
│   ├── __init__.py
│   ├── main.py                # Entry point
│   ├── step_01_setup.py       # Modular implementation steps
│   ├── step_02_data.py
│   └── ...
├── tests/                     # Generated tests (if requested)
├── data/                      # Data storage
└── logs/                      # Execution logs
```

### Module Overview

*   **`mathpilot.search`**: Handles arXiv API interactions and caching.
*   **`mathpilot.parser`**: Uses Vision-Language Models (VLMs) to "read" PDFs and extract algorithmic details.
*   **`mathpilot.planner`**: Breaks down complex algorithms into logical coding tasks.
*   **`mathpilot.generator`**: The coding engine. Writes modular, documented Python code.
*   **`mathpilot.executor`**: Safely runs generated code and captures output/errors.

---

## 🛠️ Development

We welcome contributions!

### Setup for Contributors

```bash
# Install dev dependencies
pip install -e ".[dev,llm]"

# Install pre-commit hooks (optional but recommended)
pre-commit install
```

### Running Tests

```bash
# Run the full test suite
pytest

# Run specific tests
pytest tests/test_search.py
```

### Linting

```bash
# Format code
black mathpilot tests

# Check types
mypy mathpilot
```

---

## 🤝 Troubleshooting

**Q: "Paper not found" error?**
A: Try using the exact arXiv title in quotes or the specific arXiv ID (e.g., `2103.12345`).

**Q: API Errors / Rate Limits?**
A: Ensure your `GEMINI_API_KEY` is set and valid. If using the free tier, you may hit rate limits; wait a minute and try again.

**Q: Generated code has bugs?**
A: MathPilot creates *starter* code. While often functional, complex algorithms may require manual fine-tuning. Check the `src/` files and debug as you would any other project.

---

## 📄 License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.
