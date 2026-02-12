"""Tests for code generator module."""

import pytest
from mathpilot.generator import generate_main_file, CodeTemplate
from mathpilot.planner.models import ImplementationPlan, WorkflowStep, StepType


def test_generate_main_file_basic():
    """Test generating a main orchestration file."""
    # Create a simple plan
    steps = [
        WorkflowStep(
            step_id="step_01",
            title="Setup",
            description="Setup imports",
            step_type=StepType.SETUP,
            inputs=[],
            outputs=["np", "torch"],
            dependencies=[],
            code_prompt="import numpy as np"
        ),
        WorkflowStep(
            step_id="step_02",
            title="Generate Data",
            description="Create test data",
            step_type=StepType.DATA_GENERATION,
            inputs=["np"],
            outputs=["data"],
            dependencies=["step_01"],
            code_prompt="data = np.random.rand(10)"
        ),
        WorkflowStep(
            step_id="step_03",
            title="Process Data",
            description="Process the data",
            step_type=StepType.CORE_LOGIC,
            inputs=["data"],
            outputs=["result"],
            dependencies=["step_02"],
            code_prompt="result = data * 2"
        ),
    ]
    
    plan = ImplementationPlan(
        paper_title="Test Paper",
        algorithm_name="Test Algorithm",
        summary="A test algorithm",
        steps=steps
    )
    
    # Create corresponding templates
    templates = {}
    for step in steps:
        templates[f"{step.step_id}_test.py"] = CodeTemplate(
            step_id=step.step_id,
            filename=f"{step.step_id}_test.py",
            code=f"def {step.step_id}():\n    pass",
            dependencies=[]
        )
    
    # Generate main file
    main = generate_main_file(plan, templates)
    
    # Assertions
    assert main.step_id == "main"
    assert main.filename == "main.py"
    assert "import sys" in main.code
    assert "import time" in main.code
    assert "def main():" in main.code
    assert "Test Algorithm" in main.code
    assert "Test Paper" in main.code
    assert "Setup" in main.code
    assert "Generate Data" in main.code
    assert "Process Data" in main.code
    assert "step_01" in main.code
    assert "step_02" in main.code
    assert "step_03" in main.code
    assert 'if __name__ == "__main__":' in main.code
    assert "results" in main.code
    assert "total_elapsed" in main.code


def test_generate_main_file_imports():
    """Test that main file generates correct imports."""
    steps = [
        WorkflowStep(
            step_id="step_01",
            title="Init",
            description="Initialize",
            step_type=StepType.SETUP,
            inputs=[],
            outputs=[],
            dependencies=[],
            code_prompt="pass"
        ),
    ]
    
    plan = ImplementationPlan(
        paper_title="Test",
        algorithm_name="Test",
        summary="Test",
        steps=steps
    )
    
    templates = {
        "step_01_init.py": CodeTemplate(
            step_id="step_01",
            filename="step_01_init.py",
            code="pass",
            dependencies=[]
        )
    }
    
    main = generate_main_file(plan, templates)
    
    # Check imports are present
    assert "import sys" in main.code
    assert "import time" in main.code
    assert "import step_01_init" in main.code


def test_generate_main_file_error_handling():
    """Test that main file includes error handling."""
    steps = [
        WorkflowStep(
            step_id="step_01",
            title="Test Step",
            description="Test",
            step_type=StepType.SETUP,
            inputs=[],
            outputs=[],
            dependencies=[],
            code_prompt="pass"
        ),
    ]
    
    plan = ImplementationPlan(
        paper_title="Test",
        algorithm_name="Test",
        summary="Test",
        steps=steps
    )
    
    templates = {
        "step_01_test.py": CodeTemplate(
            step_id="step_01",
            filename="step_01_test.py",
            code="pass",
            dependencies=[]
        )
    }
    
    main = generate_main_file(plan, templates)
    
    # Check error handling
    assert "try:" in main.code
    assert "except Exception as e:" in main.code
    assert "raise" in main.code
    assert "sys.exit(1)" in main.code


def test_generate_main_file_timing():
    """Test that main file includes timing information."""
    steps = [
        WorkflowStep(
            step_id="step_01",
            title="Timed Step",
            description="Test timing",
            step_type=StepType.SETUP,
            inputs=[],
            outputs=[],
            dependencies=[],
            code_prompt="pass"
        ),
    ]
    
    plan = ImplementationPlan(
        paper_title="Test",
        algorithm_name="Test",
        summary="Test",
        steps=steps
    )
    
    templates = {
        "step_01_timed.py": CodeTemplate(
            step_id="step_01",
            filename="step_01_timed.py",
            code="pass",
            dependencies=[]
        )
    }
    
    main = generate_main_file(plan, templates)
    
    # Check timing
    assert "time.time()" in main.code
    assert "elapsed" in main.code
    assert "total_elapsed" in main.code
    assert "{elapsed:.2f}s" in main.code


def test_generate_main_file_empty_templates():
    """Test generating main file with no matching templates."""
    steps = [
        WorkflowStep(
            step_id="step_01",
            title="Missing Step",
            description="Test",
            step_type=StepType.SETUP,
            inputs=[],
            outputs=[],
            dependencies=[],
            code_prompt="pass"
        ),
    ]
    
    plan = ImplementationPlan(
        paper_title="Test",
        algorithm_name="Test",
        summary="Test",
        steps=steps
    )
    
    # No templates provided
    templates = {}
    
    main = generate_main_file(plan, templates)
    
    # Should still generate a valid structure
    assert main.filename == "main.py"
    assert "def main():" in main.code
    assert 'if __name__ == "__main__":' in main.code
