from typing import List, Optional
from mathpilot.utils import get_logger
from mathpilot.utils.llm import call_gemini
from mathpilot.parser.models import ExtractedAlgorithm
from mathpilot.planner.models import ImplementationPlan, WorkflowStep, StepType

logger = get_logger("planner")

class PlanningError(Exception):
    pass

def generate_plan(paper_title: str, algorithm: ExtractedAlgorithm, model_name: Optional[str] = None) -> ImplementationPlan:
    """
    Generate an implementation plan from an extracted algorithm.
    
    Args:
        paper_title: Title of the source paper
        algorithm: The extracted algorithm details
        model_name: Gemini model to use
        
    Returns:
        ImplementationPlan containing workflow steps
    """
    logger.info(f"Generating plan for algorithm: {algorithm.name}")
    
    prompt = f"""
    You are an expert scientific algorithm architect.
    Your task is to design a step-by-step implementation plan for the algorithm described below.
    This plan will be used to generate executable Python code.
    
    Paper Title: {paper_title}
    Algorithm: {algorithm.name}
    Summary: {algorithm.summary}
    
    Algorithm Steps from Paper:
    {algorithm.model_dump_json(indent=2)}
    
    Create a modular workflow. Follow these guidelines:
    1. Start with a SETUP step (imports, constants).
    2. Include a DATA_GENERATION or DATA_LOADING step (create synthetic data to test the algorithm if no dataset is specified).
    3. Break the CORE_LOGIC into logical functions or classes.
    4. Include an INFERENCE or VALIDATION step to demonstrate it works.
    5. Include a VISUALIZATION step to plot results if applicable.
    
    Each step must have a unique ID (step_01, step_02, etc.), clear inputs/outputs, and a detailed `code_prompt` that tells a code generator exactly what to write for that step.
    
    Return a JSON matching the ImplementationPlan schema.
    """
        
    try:
        plan = call_gemini(
            prompt=prompt,
            model=model_name,
            schema=ImplementationPlan
        )
        
        # Validation: Ensure step IDs are unique and dependencies differ
        # (Basic validation could be added here)
        
        logger.info(f"Generated plan with {len(plan.steps)} steps.")
        return plan
        
    except Exception as e:
        logger.error(f"Planning failed: {e}")
        raise PlanningError(f"Failed to generate plan: {e}") from e
