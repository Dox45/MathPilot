"""Safe execution of generated code with logging."""

import subprocess
import sys
import time
import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger("mathpilot.executor")

@dataclass
class ExecutionResult:
    """Result of code execution."""

    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float


def execute_script(
    script_path: str,
    timeout: int = 300,
    sandbox: bool = True,
) -> ExecutionResult:
    """
    Execute a Python script safely.

    Args:
        script_path: Path to .py file
        timeout: Max execution time (seconds)
        sandbox: Whether to restrict access (experimental - currently ignored)

    Returns:
        ExecutionResult with output and status
    """
    path = Path(script_path)
    if not path.exists():
        return ExecutionResult(
            success=False,
            stdout="",
            stderr=f"Script not found: {script_path}",
            exit_code=-1,
            execution_time=0.0
        )

    start_time = time.time()
    
    try:
        # Run in a separate process
        # We capture output and set a timeout
        result = subprocess.run(
            [sys.executable, str(path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=path.parent # Run in script's directory so relative paths work
        )
        
        execution_time = time.time() - start_time
        
        return ExecutionResult(
            success=(result.returncode == 0),
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            execution_time=execution_time
        )
        
    except subprocess.TimeoutExpired as e:
        execution_time = time.time() - start_time
        return ExecutionResult(
            success=False,
            stdout=e.stdout or "",
            stderr=f"Execution timed out after {timeout} seconds",
            exit_code=124, # Standard timeout exit code
            execution_time=execution_time
        )
    except Exception as e:
        execution_time = time.time() - start_time
        return ExecutionResult(
            success=False,
            stdout="",
            stderr=str(e),
            exit_code=-1,
            execution_time=execution_time
        )


def execute_notebook(
    notebook_path: str,
    timeout: int = 600,
) -> ExecutionResult:
    """Execute a Jupyter notebook."""
    # Placeholder for future implementation using nbconvert
    return ExecutionResult(
        success=False,
        stdout="",
        stderr="Notebook execution not yet implemented",
        exit_code=-1,
        execution_time=0.0
    )


def log_execution(
    workflow_id: str,
    step_id: str,
    result: ExecutionResult,
    log_dir: str = "~/.mathpilot/logs",
) -> None:
    """Log execution results."""
    log_path = Path(log_dir).expanduser()
    log_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = int(time.time())
    filename = f"{workflow_id}_{step_id}_{timestamp}.json"
    
    log_data = {
        "workflow_id": workflow_id,
        "step_id": step_id,
        "timestamp": timestamp,
        "result": asdict(result)
    }
    
    try:
        with open(log_path / filename, "w") as f:
            json.dump(log_data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to write execution log: {e}")
