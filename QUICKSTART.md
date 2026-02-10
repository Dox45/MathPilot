# MathPilot Quick Start Guide

**Status**: ✅ MVP Complete and Ready for End-to-End Testing

## What is MathPilot?

MathPilot is an AI-powered tool that:
1. Searches for research papers on arXiv
2. Extracts algorithms and methods from papers
3. Generates implementation plans (workflows)
4. Generates Python starter code
5. Creates organized project directories
6. Executes generated code safely

**Full workflow: Paper → Algorithm → Plan → Code → Project**

## Quick Test (5 minutes)

```bash
cd /home/ace/gitfiles/cobio
python test_e2e.py --query "linear regression" --skip-download
```

## Full Test (15 minutes)

```bash
cd /home/ace/gitfiles/cobio
export GEMINI_API_KEY="your-key"  # If not set
python test_e2e.py
```

This will:
- Search arXiv for papers
- Download and parse a paper
- Generate workflow steps
- Generate Python code for each step
- Create a project in `~/mathpilot_projects/`
- Execute the generated code

## Test Options

```bash
# Search for different papers
python test_e2e.py --query "particle filter"

# Get more results
python test_e2e.py --max-results 5

# Skip PDF download (faster if you've run before)
python test_e2e.py --skip-download

# Skip code execution
python test_e2e.py --skip-execute

# Combine flags
python test_e2e.py --query "kmeans clustering" --skip-download --skip-execute
```

## Use MathPilot CLI

After running the test, you can also use the CLI directly:

```bash
# Search for papers
mathpilot search "kalman filter"

# Generate plan from a paper ID
mathpilot plan 2103.12345

# Generate code from a plan
mathpilot generate plan.json --project-name my_algorithm

# Run generated code
mathpilot run ~/mathpilot_projects/my_algorithm/src/main.py

# See all options
mathpilot --help
```

## Expected Test Output

When you run `test_e2e.py`, you'll see:

```
════════════════════════════════════════════════════════════════════════════════
Phase 1: Search for Papers on arXiv
════════════════════════════════════════════════════════════════════════════════
Searching arXiv for: 'linear regression'
Found 3 papers

[Table with paper titles, IDs, publication dates]

════════════════════════════════════════════════════════════════════════════════
Phase 2: Download PDF
════════════════════════════════════════════════════════════════════════════════
Downloading from: https://arxiv.org/pdf/...

[... more phases ...]

════════════════════════════════════════════════════════════════════════════════
✓ End-to-End Test Complete!
════════════════════════════════════════════════════════════════════════════════

Project created at:
  /home/user/mathpilot_projects/test_linear_regression_20260210_031500

Next steps:
  1. cd /home/user/mathpilot_projects/test_linear_regression_*
  2. pip install -r requirements.txt
  3. python src/main.py
```

## Project Structure After Test

```
~/mathpilot_projects/test_linear_regression_*/
├── workflow.yaml              # Plan metadata
├── requirements.txt           # Python dependencies
├── src/
│   ├── __init__.py
│   ├── main.py               # Entry point
│   ├── step_01_setup.py      # Generated code
│   ├── step_02_data.py       # Generated code
│   └── ...
├── tests/                     # Test directory (empty)
├── data/                      # Data directory (empty)
└── logs/                      # Execution logs
```

## Documentation

- **TEST_E2E_GUIDE.md** - Detailed testing guide with troubleshooting
- **README.md** - Project overview
- **IMPLEMENTATION_PARSER_PLANNER.md** - Technical deep dive
- **.github/copilot-instructions.md** - Architecture for future development
- **plan.md** - Implementation status and phases

## Requirements

- Python 3.10+
- `GEMINI_API_KEY` environment variable set
- Internet connection (for arXiv API + Gemini API)
- Dependencies: `pip install -e ".[dev]"`

## Troubleshooting

**API Key not set?**
```bash
export GEMINI_API_KEY="your-gemini-key-here"
```

**PDF download fails?**
```bash
python test_e2e.py --skip-download
```

**Code generation times out?**
```bash
python test_e2e.py --skip-execute
```

**Want to see all options?**
```bash
python test_e2e.py --help
```

See **TEST_E2E_GUIDE.md** for more detailed troubleshooting.

## Architecture

```
User Input (CLI)
    ↓
Search arXiv → [ArxivClient]
    ↓
Download PDF → [requests/urllib]
    ↓
Parse Paper → [Parser + Gemini API]
    ↓
Generate Plan → [Planner + Gemini API]
    ↓
Generate Code → [Generator + Gemini API]
    ↓
Create Project → [Workspace]
    ↓
Execute Code → [Executor]
    ↓
User Gets: Working Python Project ✓
```

## What Gets Tested

✅ **Phase 1: Search** - Find papers on arXiv  
✅ **Phase 2: Download** - Get PDF from arXiv  
✅ **Phase 3: Parse** - Extract algorithms via LLM  
✅ **Phase 4: Plan** - Generate workflow via LLM  
✅ **Phase 5: Generate** - Create Python code via LLM  
✅ **Phase 6: Workspace** - Organize project files  
✅ **Phase 7: Execute** - Run generated code  

## Performance

| Phase | Duration | Notes |
|-------|----------|-------|
| 1 Search | 10s | Quick arXiv API call |
| 2 Download | 30-60s | Depends on PDF size (1-10 MB) |
| 3 Parse | 30-60s | LLM API call with PDF text |
| 4 Plan | 30-60s | LLM API call for workflow |
| 5 Generate | 5-10 min | **Longest phase** - 1-2 min per step |
| 6 Workspace | 10s | File creation |
| 7 Execute | <10s | Run main.py |
| **Total** | **10-15 min** | Typical end-to-end run |

## Next Steps

1. **Run the test**: `python test_e2e.py`
2. **Review output**: Check `~/mathpilot_projects/test_*/`
3. **Explore code**: Look at generated `step_*.py` files
4. **Customize**: Edit code to match your needs
5. **Deploy**: Use as template for production code

## Questions?

- Technical details: See `IMPLEMENTATION_PARSER_PLANNER.md`
- Testing help: See `TEST_E2E_GUIDE.md`
- Architecture: See `.github/copilot-instructions.md`
- Status: See `plan.md`

## Ready?

```bash
python test_e2e.py
```

Go! 🚀
