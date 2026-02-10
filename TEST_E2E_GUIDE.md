# End-to-End Test Guide

This guide explains how to test MathPilot with real data (no mocks).

## What Gets Tested

The `test_e2e.py` script tests the complete pipeline:

```
Phase 1: Search for Papers on arXiv
    ↓
Phase 2: Download PDF
    ↓
Phase 3: Parse Paper (Extract Algorithms via LLM)
    ↓
Phase 4: Generate Workflow Plan (Structure via LLM)
    ↓
Phase 5: Generate Python Code (Code generation via LLM)
    ↓
Phase 6: Create Workspace Project (Directory structure)
    ↓
Phase 7: Execute Generated Code (Run & validate)
```

## Prerequisites

1. **API Keys Set**: Ensure `GEMINI_API_KEY` is in your environment
   ```bash
   echo $GEMINI_API_KEY  # Should print your key
   ```

2. **Dependencies Installed**:
   ```bash
   pip install -e ".[dev]"
   ```

3. **Internet Connection**: Required for:
   - arXiv API calls (paper search)
   - Gemini API calls (LLM processing)
   - PDF downloads

## Running the Test

### Basic Run (Full Pipeline)
```bash
python test_e2e.py
```

This will:
- Search arXiv for "kalman filter sensor fusion"
- Download first 3 papers
- Parse the selected paper
- Generate a 5-8 step workflow
- Generate Python code for each step
- Create a project in `~/mathpilot_projects/test_kalman_filter_*`
- Execute the generated code

**Duration**: ~5-15 minutes (depends on LLM response times)

### Custom Search Query
```bash
python test_e2e.py --query "particle filter"
python test_e2e.py --query "LSTM neural network"
```

### Skip Expensive Operations
```bash
# Skip PDF download (use cached if available)
python test_e2e.py --skip-download

# Skip code execution
python test_e2e.py --skip-execute

# Both
python test_e2e.py --skip-download --skip-execute
```

### More Results
```bash
# Search for 5 papers instead of 3
python test_e2e.py --max-results 5
```

## Expected Output

### Success Output
```
════════════════════════════════════════════════════════════════════════════════
Phase 1: Search for Papers on arXiv
════════════════════════════════════════════════════════════════════════════════
Searching arXiv for: 'kalman filter sensor fusion'
Found 3 papers

┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ ID          ┃ Title                          ┃ Published     ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ 2103.12345  │ Kalman Filtering for Sensor... │ 2021-03-01    │
│ 2105.67890  │ Advanced Fusion Techniques... │ 2021-05-15    │
│ 2107.11111  │ Real-time Estimation with... │ 2021-07-22    │
└─────────────┴────────────────────────────────┴───────────────┘

... [continues through all phases] ...

════════════════════════════════════════════════════════════════════════════════
✓ End-to-End Test Complete!
════════════════════════════════════════════════════════════════════════════════

Project created at:
  /home/user/mathpilot_projects/test_kalman_filter_20260210_031500

Next steps:
  1. cd /home/user/mathpilot_projects/test_kalman_filter_20260210_031500
  2. pip install -r requirements.txt
  3. python src/main.py
  4. Edit step_*.py files to implement algorithm details
```

## What Each Phase Does

### Phase 1: Search
- Queries arXiv API with your search term
- Returns 3 matching papers
- You select the first one automatically

### Phase 2: Download PDF
- Downloads full PDF from arXiv
- Saves to `~/tmp/mathpilot_test/<arxiv_id>.pdf`
- File size: 1-10 MB typically

### Phase 3: Parse Paper
- Extracts abstract, methods, introduction sections
- Sends to Gemini API with structured prompt
- Extracts algorithm names, steps, inputs/outputs
- Returns `ParsedPaper` object

### Phase 4: Plan Workflow
- Takes first algorithm from parsed paper
- Generates structured workflow plan
- Creates 5-8 workflow steps with dependencies
- Returns `ImplementationPlan` object

### Phase 5: Generate Code
- For EACH step, calls Gemini to generate Python code
- Creates CodeTemplate with filename + code + dependencies
- Generates requirements.txt
- **Duration**: Longest phase (1-2 min if 6 steps)

### Phase 6: Create Workspace
- Creates project directory structure:
  ```
  ~/mathpilot_projects/test_<algo>/
  ├── workflow.yaml
  ├── requirements.txt
  ├── src/
  │   ├── __init__.py
  │   ├── main.py
  │   ├── step_01_setup.py
  │   ├── step_02_data.py
  │   └── ...
  ├── tests/
  ├── data/
  └── logs/
  ```
- Writes all generated code to disk

### Phase 7: Execute
- Runs `src/main.py` in generated project
- Captures stdout/stderr
- Logs execution result
- Shows output to user

## Troubleshooting

### "No papers found"
- Your search query might be too specific
- Try: `--query "linear regression"` or `--query "clustering"`
- Check internet connection

### "Failed to download PDF"
- Some papers have access restrictions
- Try: `--query "simple linear regression"`
- The script will skip to Phase 4 automatically

### "Code generation failed"
- Gemini API might be rate limited
- Wait a few minutes and try again
- Check that `GEMINI_API_KEY` is set correctly
- Try: `--skip-execute` to just generate without running

### "Execution failed"
- Generated code might have bugs
- Check `stderr` output for Python errors
- This is expected! The generated code is a starter template
- Edit the `src/step_*.py` files to fix

### "Timeout"
- Phase 5 takes a long time (5-10 min for 6 steps)
- This is normal - be patient
- Gemini API calls are slow

## Environment Variables

Set these before running:

```bash
# Required
export GEMINI_API_KEY="your-key-here"

# Optional (defaults shown)
export MATHPILOT_CACHE_DIR="$HOME/.mathpilot/cache"
export MATHPILOT_LOG_DIR="$HOME/.mathpilot/logs"
```

## File Locations

After successful run, files are created at:

```
Project:     ~/mathpilot_projects/test_<algo>/
Cache:       ~/.mathpilot/cache/
Logs:        ~/.mathpilot/logs/
Temp PDFs:   /tmp/mathpilot_test/
```

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| API Key not found | `export GEMINI_API_KEY="..."` |
| Network error | Check internet, retry |
| PDF too complex | Try simpler query (e.g., "linear regression") |
| Code has bugs | Expected! Refine generated code in editor |
| Execution timeout | Increase timeout or skip execution |
| Out of memory | Project is too large; try fewer steps |

## Next Steps After Test

1. **Explore Generated Project**
   ```bash
   cd ~/mathpilot_projects/test_kalman_filter_*/
   ls -la
   cat requirements.txt
   cat src/main.py
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Review Generated Code**
   - Open `src/step_*.py` files
   - Check if they match the algorithm description
   - Fix any obvious bugs

4. **Run Full Project**
   ```bash
   python src/main.py
   ```

5. **Compare with Original Paper**
   - Check if implementation matches paper
   - Add test cases
   - Optimize performance

## Performance Notes

- **Phase 1-2**: ~1 minute
- **Phase 3**: ~30-60 seconds
- **Phase 4**: ~30-60 seconds
- **Phase 5**: ~5-10 minutes (1-2 per step)
- **Phase 6**: ~10 seconds
- **Phase 7**: Varies (usually <10 seconds)

**Total**: ~10-15 minutes for full pipeline

## Testing Tips

1. **Start with simple queries**: "linear regression", "clustering"
2. **Monitor GPU/API**: Some calls are slow
3. **Check logs**: See `~/.mathpilot/logs/` for detailed info
4. **Use --skip-download**: Faster iteration if you've tested before
5. **Check GEMINI_API_KEY**: Most failures are auth-related

## Success Criteria

✓ Phase 1: Found papers  
✓ Phase 2: Downloaded PDF (if not skipped)  
✓ Phase 3: Extracted algorithms  
✓ Phase 4: Generated workflow plan  
✓ Phase 5: Generated code files  
✓ Phase 6: Created project directory  
✓ Phase 7: Executed code (if not skipped)  

If all phases complete, your MathPilot installation works end-to-end!

## Questions?

- Check `IMPLEMENTATION_PARSER_PLANNER.md` for architecture
- Check `.github/copilot-instructions.md` for module details
- Review `plan.md` for implementation status
