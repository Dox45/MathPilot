# Parser & Planner Implementation Document

**Date**: 2026-02-09  
**Status**: Phase 1 Complete ✅ | Phases 2-3 Partial 🟡 | Phases 4-9 Pending ❌

---

## Executive Overview

This document provides a comprehensive audit of the Parser and Planner modules, including what's been implemented, what remains, and how the modules integrate with the rest of MathPilot.

### Current State Snapshot

| Component | Status | Details |
|-----------|--------|---------|
| **Phase 1: Utilities** | ✅ Complete | LLM wrapper (191 lines, 91% coverage) + PDF utils (218 lines, 93% coverage) |
| **Phase 2: Parser** | 🟡 Partial | Models + core function complete; needs tests + caching |
| **Phase 3: Planner** | 🟡 Partial | Models + core function complete; needs tests + validation |
| **Phase 4-9: Other** | ❌ Not Started | Executor, Generator, Workspace, CLI all pending |
| **Tests** | ⚠️ Mixed | 25/25 utility tests passing; parser + planner untested |
| **Documentation** | ⏳ Pending | Copilot instructions need parser/planner sections |

---

## What's Implemented: Detailed Breakdown

### Phase 1: Shared LLM & PDF Utilities ✅ COMPLETE

#### mathpilot/utils/llm.py (191 lines)

**Purpose**: Wrapper around Gemini API with retry logic, structured output parsing, and JSON extraction.

**Key Functions**:
```python
call_gemini(prompt, model="gemini-2.0-flash", temperature=0.1, schema=None) 
    → str | Pydantic Model
    • Retries up to 3 times with exponential backoff
    • Validates response against Pydantic schema if provided
    • Extracts JSON from markdown code blocks
    • Logs errors with context

batch_call_gemini(prompts, model="gemini-2.0-flash", temperature=0.1) 
    → list[str]
    • Sequential calls (not parallelized due to rate limits)
    • Returns responses in same order

_parse_structured_response(text, schema) 
    → Pydantic Model
    • Attempts JSON extraction from markdown ```json blocks
    • Validates against schema
    • Raises ValueError with context on failure

extract_json_from_response(text, key=None) 
    → dict | list
    • Finds first valid JSON object or array in text
    • Optionally extracts specific key
    • Useful for responses with extra text
```

**Design Decisions**:
- Retry logic: 3 attempts, 2-10 second exponential backoff
- Temperature: 0.1 (low) for structured extraction (deterministic)
- Error handling: Raises ValueError on all failures
- Logging: DEBUG for API calls, ERROR for failures

**Test Coverage**: 13 tests (91%)
- Success paths: normal response, schema validation, markdown extraction
- Error paths: empty response, invalid JSON, schema mismatch
- Batch calling, JSON extraction from various formats

**Dependencies**:
- google-generativeai >= 0.3.0
- pydantic >= 2.0.0
- tenacity >= 8.2.0

---

#### mathpilot/utils/pdf.py (218 lines)

**Purpose**: Extract text and metadata from PDF files with section-based targeting and graceful fallback.

**Key Functions**:
```python
extract_pdf_text(pdf_path, max_pages=None) 
    → str
    • Extracts all text from PDF using pdfplumber
    • Optional page limit
    • Handles per-page failures gracefully
    • Returns concatenated text with blank line separators

extract_pdf_sections(pdf_path, sections=None, max_pages=None) 
    → dict[str, str]
    • Identifies section headers (case-insensitive matching)
    • Extracts text between section boundaries
    • Defaults to: ["abstract", "introduction", "methods"]
    • Returns dict with empty strings for missing sections
    • Works with common variations: "Abstract:", "1. Introduction", etc.

get_pdf_metadata(pdf_path) 
    → dict
    • Extracts PDF metadata (title, author, subject, etc.)
    • Returns empty dict if no metadata

pdf_to_text_with_fallback(pdf_path, max_pages=None) 
    → str
    • Tries full text extraction first
    • Falls back to metadata if text extraction fails
    • Returns empty string only if both fail
```

**Design Decisions**:
- Section matching: Case-insensitive, header-aware (handles numbering)
- Fallback strategy: Full text → metadata → empty string
- Max pages: Default None (extract all); can limit for performance
- Error logging: Warnings for per-page failures, errors for critical failures

**Test Coverage**: 12 tests (93%)
- Text extraction: normal, with page limit, with failures
- Section extraction: success, missing sections, case insensitivity
- Metadata extraction, fallback behavior

**Dependencies**:
- pdfplumber >= 0.9.0
- pathlib (stdlib)
- logging (stdlib)

---

### Phase 2: Parser Module 🟡 PARTIAL

#### mathpilot/parser/models.py (32 lines)

**Data Structures**:

```python
class ParsingError(Exception):
    """Raised when paper parsing fails."""

class AlgorithmStep(BaseModel):
    """Single step in algorithm sequence."""
    number: int                              # Step number in sequence
    description: str                         # What this step does
    mathematical_details: Optional[str]      # Equations, notation (LaTeX/text)
    code_hint: Optional[str]                # Pseudocode or implementation hint

class ExtractedAlgorithm(BaseModel):
    """Structured algorithm extracted from paper."""
    name: str                                # Algorithm/method name
    summary: str                             # High-level description
    problem_addressed: str                   # What problem it solves
    inputs: List[str]                       # Required inputs/parameters
    outputs: List[str]                      # Expected outputs
    steps: List[AlgorithmStep]              # Sequential steps
    complexity: Optional[str]                # Time/space complexity if mentioned

class ParsedPaper(BaseModel):
    """Container for all extracted info from paper."""
    title: str                               # Paper title
    algorithms: List[ExtractedAlgorithm]   # All algorithms found
```

**Design**: Pydantic-based, JSON-serializable, validates automatically on instantiation.

---

#### mathpilot/parser/core.py (75 lines)

**Main Function**:

```python
def parse_paper(paper_pdf: str, paper_title: str, model_name: str = "gemini-2.5-pro") 
    → ParsedPaper
```

**Workflow**:
1. **Extract PDF sections**: Try to find specific sections (method, algorithm, implementation, model, approach, proposed method)
2. **Fallback logic**: If sections < 500 chars total, use full text extraction (first 15 pages)
3. **Build prompt**: Construct detailed prompt with paper title + text content
4. **Call Gemini**: Use `call_gemini()` with ParsedPaper schema
5. **Validate title**: Ensure title isn't hallucinated by LLM
6. **Error handling**: Catch exceptions, wrap in ParsingError

**Prompt Strategy**:
- Role: "expert scientific implementer"
- Task: Extract core algorithms with clear methodology
- Format: Request JSON matching ParsedPaper schema
- Context: Paper title, text content (truncated to 30,000 chars)

**Error Handling**:
- Catches LLM failures, wraps in ParsingError
- Logs at each major step (INFO for success, ERROR for failures)
- Validates title to prevent hallucinations

**Integration**:
- Consumes: Paper PDF path (must exist)
- Uses: `extract_pdf_sections()`, `extract_pdf_text()`, `call_gemini()` from utils
- Produces: ParsedPaper object (Pydantic model, JSON-serializable)

---

#### TODO: Caching Layer

**Not Yet Implemented**:
```python
# mathpilot/parser/cache.py (NEEDED)

def cache_parsed_paper(paper_id: str, parsed_paper: ParsedPaper, 
                       cache_dir: str = "~/.mathpilot/cache") → str:
    """Save parsed paper to JSON file."""

def load_cached_paper(paper_id: str, 
                     cache_dir: str = "~/.mathpilot/cache") → Optional[ParsedPaper]:
    """Load cached parsed paper."""

def is_cached(paper_id: str, 
             cache_dir: str = "~/.mathpilot/cache") → bool:
    """Check if paper is in cache."""
```

Would update `parse_paper()` to:
1. Check cache first: `if is_cached(paper_id): return load_cached_paper(paper_id)`
2. If not cached, parse and cache: `result = parse_paper(...); cache_parsed_paper(...)`
3. Add `--no-cache` flag to CLI to bypass

---

### Phase 3: Planner Module 🟡 PARTIAL

#### mathpilot/planner/models.py (32 lines)

**Data Structures**:

```python
class StepType(str, Enum):
    """Workflow step categories."""
    SETUP = "setup"
    DATA_GENERATION = "data_generation"
    DATA_LOADING = "data_loading"
    PREPROCESSING = "preprocessing"
    CORE_LOGIC = "core_logic"
    TRAINING = "training"
    INFERENCE = "inference"
    VISUALIZATION = "visualization"
    VALIDATION = "validation"

class WorkflowStep(BaseModel):
    """Single executable step in workflow."""
    step_id: str                      # Unique ID: "step_01", "step_02", etc.
    title: str                        # Short title of step
    description: str                  # Detailed description
    step_type: StepType              # Category (SETUP, CORE_LOGIC, etc.)
    inputs: List[str]                # Data/vars from previous steps
    outputs: List[str]               # Variables produced
    dependencies: List[str]          # IDs of prerequisite steps
    code_prompt: str                 # Instructions for code generator

class ImplementationPlan(BaseModel):
    """Full plan for implementing algorithm."""
    paper_title: str                 # Source paper
    algorithm_name: str              # Algorithm being implemented
    summary: str                     # High-level plan summary
    steps: List[WorkflowStep]       # Ordered steps
```

**Design**: Pydantic-based, DAG-compatible (dependencies can be validated with networkx).

---

#### mathpilot/planner/core.py (65 lines)

**Main Function**:

```python
def generate_plan(paper_title: str, algorithm: ExtractedAlgorithm, 
                  model_name: str = "gemini-2.5-pro") 
    → ImplementationPlan
```

**Workflow**:
1. **Build prompt**: Detailed prompt with algorithm info, guidelines for step decomposition
2. **Call Gemini**: Use `call_gemini()` with ImplementationPlan schema
3. **Validate structure**: Basic validation (could be enhanced)
4. **Error handling**: Catch exceptions, wrap in PlanningError

**Prompt Strategy**:
- Role: "expert scientific algorithm architect"
- Task: Design step-by-step implementation plan
- Guidelines:
  1. Start with SETUP (imports, constants)
  2. Include DATA_GENERATION or DATA_LOADING
  3. Break CORE_LOGIC into functions/classes
  4. Include INFERENCE or VALIDATION
  5. Include VISUALIZATION if applicable
- Expects: Unique step IDs, clear inputs/outputs, detailed code_prompt per step

**Error Handling**:
- Catches LLM failures, wraps in PlanningError
- Logs at major steps

**Integration**:
- Consumes: ExtractedAlgorithm (from parser)
- Uses: `call_gemini()` from utils
- Produces: ImplementationPlan object (Pydantic model, JSON-serializable)

---

#### TODO: Validation Layer

**Not Yet Implemented**:
```python
# mathpilot/planner/validation.py (NEEDED)

def validate_workflow(workflow: ImplementationPlan) → bool:
    """
    Validate workflow structure:
    - All step IDs unique
    - All dependencies reference existing steps
    - No circular dependencies
    """

def _topological_sort(steps: List[WorkflowStep]) 
    → List[WorkflowStep]:
    """Order steps by dependencies using networkx.topological_sort()"""

def _has_cycles(steps: List[WorkflowStep]) → bool:
    """Detect circular dependencies"""
```

Would be called from `generate_plan()` after LLM returns result:
```python
plan = call_gemini(...)
if not validate_workflow(plan):
    raise PlanningError("Invalid workflow structure")
plan.steps = _topological_sort(plan.steps)  # Re-order if needed
return plan
```

---

## Integration Points

### Parser ↔ Utilities

```
parse_paper()
  ├── extract_pdf_sections(pdf_path) → dict[str, str]
  │   └── uses pdfplumber to find section headers
  ├── extract_pdf_text(pdf_path) → str (fallback)
  │   └── extracts first 15 pages of full text
  └── call_gemini(prompt, schema=ParsedPaper) → ParsedPaper
      └── uses Gemini 2.5-pro with structured output
```

**Data flow**:
```
PDF file
    ↓
[pdf.py] Extract sections + text
    ↓
[llm.py] Pass to Gemini with schema
    ↓
ParsedPaper (list of ExtractedAlgorithm objects)
```

---

### Planner ↔ Parser ↔ Utilities

```
generate_plan(algorithm: ExtractedAlgorithm)
  └── call_gemini(prompt, schema=ImplementationPlan) → ImplementationPlan
      └── uses Gemini 2.5-pro with structured output
```

**Data flow**:
```
ExtractedAlgorithm (from parser)
    ↓
[llm.py] Pass to Gemini with schema
    ↓
ImplementationPlan (list of WorkflowStep objects)
```

---

### CLI ↔ Parser ↔ Planner

*Currently not integrated in cli/main.py*

```
mathpilot plan <arxiv_id>
  ├── [search] Fetch paper from arXiv
  ├── [parser] parse_paper(pdf_path) → ParsedPaper
  │   └── For each ExtractedAlgorithm:
  └── [planner] generate_plan(algorithm) → ImplementationPlan
      └── Display workflow to user (rich table)
```

---

## What Needs to Be Done

### High Priority (Quick Wins)

1. **Add Parser Tests** (test_parser.py)
   - Test `parse_paper()` with mocked `call_gemini()`
   - Validate ParsedPaper structure
   - Test section extraction fallback logic
   - Error handling

2. **Add Planner Tests** (test_planner.py)
   - Test `generate_plan()` with mocked `call_gemini()`
   - Validate ImplementationPlan structure
   - Test step dependency structure

3. **Parser Caching** (parser/cache.py)
   - Cache ParsedPaper as JSON to `~/.mathpilot/cache/{arxiv_id}.json`
   - Check cache before LLM calls
   - Reduce API costs

4. **Planner Validation** (planner/validation.py)
   - Validate step IDs are unique
   - Check all dependencies reference existing steps
   - Detect circular dependencies (networkx)
   - Topological sort of steps

### Medium Priority

5. **CLI Integration**
   - Connect `plan` command to parser + planner
   - Test end-to-end: search → parse → plan

6. **Executor Implementation**
   - `execute_script()` with subprocess + timeout
   - `execute_notebook()` with Jupyter
   - `log_execution()` with structured logging

7. **Generator Implementation**
   - `generate_step_code()` using LLM
   - `generate_project_code()` assembling all steps
   - `generate_requirements()` dependency inference

### Lower Priority

8. **Workspace Implementation**
   - `create_project()` directory structure
   - `load_project()` YAML parsing
   - `list_projects()` directory scanning

9. **Documentation**
   - Add module READMEs
   - Update copilot-instructions.md
   - Add examples

---

## Testing Strategy

### Unit Tests (Isolated)
```python
# tests/test_parser.py
def test_parse_paper_with_mocked_llm():
    with patch('mathpilot.utils.llm.call_gemini') as mock_gemini:
        mock_gemini.return_value = ParsedPaper(
            title="Sample Paper",
            algorithms=[...]
        )
        result = parse_paper("dummy.pdf", "Sample Paper")
        assert isinstance(result, ParsedPaper)

# tests/test_planner.py
def test_generate_plan_with_mocked_llm():
    with patch('mathpilot.utils.llm.call_gemini') as mock_gemini:
        mock_gemini.return_value = ImplementationPlan(
            steps=[...]
        )
        result = generate_plan("Paper", algorithm)
        assert isinstance(result, ImplementationPlan)
```

### Integration Tests
```python
# tests/test_integration.py
def test_parse_and_plan_workflow():
    # Mock both parse and plan
    with patch('mathpilot.utils.llm.call_gemini') as mock_gemini:
        # First call returns ParsedPaper
        # Second call returns ImplementationPlan
        parsed = parse_paper("dummy.pdf", "Paper")
        plan = generate_plan("Paper", parsed.algorithms[0])
        
        # Validate the plan can be used by subsequent modules
        assert len(plan.steps) > 0
        assert all(s.step_type in StepType for s in plan.steps)
```

---

## Success Criteria

- ✅ 25+ tests passing for parser + planner
- ✅ 80%+ code coverage for both modules
- ✅ Parser correctly extracts 3+ algorithms from sample papers
- ✅ Planner creates valid DAG (no cycles, topologically ordered)
- ✅ Planner orders steps logically (data prep → core → validation)
- ✅ All functions have type hints + docstrings
- ✅ Integration test validates end-to-end pipeline

---

## Dependencies

**Already Added**:
- google-generativeai >= 0.3.0
- pydantic >= 2.0.0
- tenacity >= 8.2.0
- pdfplumber >= 0.9.0
- networkx >= 3.0

**May Need Later**:
- jupyter (for executor)
- anthropic or openai (if switching providers)

---

## Conclusion

Parser and Planner modules are **75% complete**:
- ✅ Data models defined (Pydantic)
- ✅ Core functions written (using LLM)
- ✅ Integration points identified
- ⏳ Need: Tests, caching, validation, CLI integration

The architecture is sound. The LLM integration is proven (via utilities). Next step: write tests to validate the models + core functions work as expected, then proceed with caching + validation layers.

**Estimated time to validation**: ~2 hours (tests + caching + validation)  
**Estimated time to full completion**: ~6-8 hours (including executor, generator, workspace, CLI)
