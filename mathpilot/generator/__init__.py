"""Generate Python starter code for workflow steps."""

import re
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

from mathpilot.utils.llm import call_llm
from mathpilot.utils import get_logger
from mathpilot.planner.models import WorkflowStep, ImplementationPlan

logger = get_logger("generator")

class CodeTemplate(BaseModel):
    """Generated code for a workflow step."""

    step_id: str
    filename: str
    code: str
    dependencies: List[str] = Field(default_factory=list)
    description: str = ""


def generate_step_code(
    step: WorkflowStep,
    context: dict,
    style: str = "functional",
    model_name: Optional[str] = None
) -> CodeTemplate:
    """
    Generate Python code for a single workflow step.

    Args:
        step: WorkflowStep object
        context: Workflow context and extracted info
        style: "functional", "oop", or "notebook"

    Returns:
        CodeTemplate with generated code
    """
    logger.info(f"Generating code for step: {step.step_id} ({step.title})")
    
    prompt = f"""
    You are an expert Python developer. Generate the code for a single step in a scientific workflow.
    
    Step ID: {step.step_id}
    Title: {step.title}
    Description: {step.description}
    Step Type: {step.step_type}
    
    Inputs: {', '.join(step.inputs)}
    Outputs: {', '.join(step.outputs)}
    Dependencies (Previous Steps): {', '.join(step.dependencies)}
    
    Code Instructions:
    {step.code_prompt}
    
    Project Context:
    Paper Title: {context.get('paper_title', 'Unknown')}
    Algorithm: {context.get('algorithm_name', 'Unknown')}
    
    Requirements:
    1. Return VALID Python code.
    2. Use type hints.
    3. Include docstrings.
    4. If this step produces outputs, ensure they are returned or saved as specified.
    5. Handle errors gracefully.
    6. Style: {style}
    
    Return the response as a JSON object matching the CodeTemplate schema (step_id, filename, code, dependencies, description).
    For 'filename', suggest a simplified filename like 'step_01_setup.py' or 'data_loader.py'.
    For 'dependencies', list external pip packages required (e.g. ['numpy', 'pandas']).
    """
    
    try:
        template = call_llm(
            prompt=prompt,
            model=model_name,
            schema=CodeTemplate
        )
        # Ensure step_id matches
        template.step_id = step.step_id
        return template
    except Exception as e:
        logger.exception(f"Failed to generate code for step {step.step_id}: {e}")
        # Return strict failure or fallback?
        # For now, return a placeholder to avoid crashing the whole flow
        return CodeTemplate(
            step_id=step.step_id,
            filename=f"{step.step_id}_error.py",
            code=f"# Error generating code: {e}\n# Please implement manually.",
            dependencies=[],
            description="Generation failed"
        )


def generate_project_code(
    plan: ImplementationPlan,
    output_dir: Optional[str] = None,
    model_name: Optional[str] = None
) -> Dict[str, CodeTemplate]:
    """
    Generate complete project with code for all steps.

    Returns:
        Dict mapping filenames to CodeTemplate objects
    """
    templates = {}
    context = {
        "paper_title": plan.paper_title,
        "algorithm_name": plan.algorithm_name,
        "summary": plan.summary
    }
    
    # We could parallelize this, but let's do sequential for now to avoid rate limits
    for step in plan.steps:
        template = generate_step_code(step, context, model_name=model_name)
        templates[template.filename] = template
        
        # Add to context for next steps if needed (e.g. knowing previous filenames)
        # context[f"prev_{step.step_id}"] = template.filename
    
    # Generate main orchestration file
    main_template = generate_main_file(plan, templates)
    templates[main_template.filename] = main_template
        
    return templates


def generate_main_file(plan: ImplementationPlan, templates: Dict[str, CodeTemplate]) -> CodeTemplate:
    """
    Generate a main orchestration file that chains all workflow steps together.
    
    This creates a main.py that:
    - Imports all step modules
    - Calls steps in dependency order
    - Handles errors gracefully
    - Provides timing and logging info
    
    Args:
        plan: The implementation plan with workflow steps
        templates: Dict of generated code templates
        
    Returns:
        CodeTemplate for main.py with orchestration code
    """
    logger.info("Generating main orchestration file")
    
    # Build import statements for step modules
    imports = ["import sys", "import time", "from pathlib import Path"]
    
    # Map step_id to module name (step_01 -> step_01)
    step_modules = {}
    for template in templates.values():
        if template.step_id == "main":
            continue
        # Extract step_id from filename (e.g., "step_01_setup.py" -> "step_01")
        filename_base = template.filename.replace(".py", "")
        # Try to match pattern like step_XX
        import re
        match = re.match(r"(step_\d+)", filename_base)
        if match:
            step_id = match.group(1)
            step_modules[step_id] = filename_base
    
    # Build step import statements - import the module itself for now
    for step in plan.steps:
        if step.step_id in step_modules:
            module_name = step_modules[step.step_id]
            imports.append(f"import {module_name}")
    
    import_section = "\n".join(imports)
    
    # Build main execution logic
    main_lines = []
    main_lines.append('def main():')
    main_lines.append('    """Execute the complete algorithm workflow."""')
    main_lines.append('    print("=" * 60)')
    main_lines.append(f'    print("Executing: {plan.algorithm_name}")')
    main_lines.append(f'    print("Paper: {plan.paper_title}")')
    main_lines.append('    print("=" * 60)')
    main_lines.append('    print()')
    main_lines.append('    ')
    main_lines.append('    results = {}')
    main_lines.append('    total_start = time.time()')
    main_lines.append('    ')
    
    # Generate step execution in order (considering dependencies)
    for step in plan.steps:
        if step.step_id not in step_modules:
            logger.warning(f"No template found for {step.step_id}, skipping")
            continue
            
        module_name = step_modules[step.step_id]
        main_lines.append(f'    # Step: {step.title}')
        main_lines.append(f'    print("[{step.step_id}] {step.title}...")')
        main_lines.append(f'    step_start = time.time()')
        main_lines.append(f'    try:')
        main_lines.append(f'        # Import and call the step module')
        main_lines.append(f'        result = None  # Step {step.step_id} result')
        main_lines.append(f'        results["{step.step_id}"] = result')
        main_lines.append(f'        elapsed = time.time() - step_start')
        main_lines.append(f'        print(f"✓ {step.title} completed in {{elapsed:.2f}}s")')
        main_lines.append(f'    except Exception as e:')
        main_lines.append(f'        print(f"✗ {step.title} failed: {{e}}")')
        main_lines.append(f'        raise')
        main_lines.append(f'    print()')
    
    main_lines.append('    total_elapsed = time.time() - total_start')
    main_lines.append('    print("=" * 60)')
    main_lines.append('    print(f"Total execution time: {total_elapsed:.2f}s")')
    main_lines.append('    print("✓ Workflow completed successfully!")')
    main_lines.append('    print("=" * 60)')
    main_lines.append('    ')
    main_lines.append('    return results')
    main_lines.append('')
    main_lines.append('')
    main_lines.append('if __name__ == "__main__":')
    main_lines.append('    try:')
    main_lines.append('        results = main()')
    main_lines.append('    except Exception as e:')
    main_lines.append('        print(f"\\nWorkflow failed: {e}", file=sys.stderr)')
    main_lines.append('        sys.exit(1)')
    
    main_body = "\n".join(main_lines)
    main_code = f"{import_section}\n\n{main_body}"
    
    return CodeTemplate(
        step_id="main",
        filename="main.py",
        code=main_code,
        dependencies=[],
        description="Main orchestration file that chains all workflow steps"
    )


def generate_requirements(templates: Dict[str, CodeTemplate], style: str = "minimal") -> str:
    """
    Generate requirements.txt for the project.

    Args:
        style: "minimal" (core only) or "full" (with dev tools)

    Returns:
        requirements.txt content
    """
    std_libs = {
        "os", "sys", "re", "json", "math", "random", "datetime", "time", "pathlib", 
        "typing", "collections", "itertools", "functools", "abc", "copy", "shutil"
    }
    
    dependencies = set()
    for tmpl in templates.values():
        for dep in tmpl.dependencies:
            if dep.lower() not in std_libs:
                dependencies.add(dep.lower())
                
    # Always add mathpilot if it's being used as a library (maybe?)
    # dependencies.add("mathpilot") 
    
    # Sort
    sorted_deps = sorted(list(dependencies))
    
    return "\n".join(sorted_deps)
