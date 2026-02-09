from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class StepType(str, Enum):
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
    """A single executable step in the implementation workflow."""
    step_id: str = Field(..., description="Unique identifier for the step (e.g., 'step_01')")
    title: str = Field(..., description="Short title of the step")
    description: str = Field(..., description="Detailed description of what this step does")
    step_type: StepType = Field(..., description="Type of the step")
    inputs: List[str] = Field(default_factory=list, description="Data or variables required from previous steps")
    outputs: List[str] = Field(default_factory=list, description="Variables produced by this step")
    dependencies: List[str] = Field(default_factory=list, description="IDs of steps that must be completed first")
    code_prompt: str = Field(..., description="Specific instructions for the code generator to implement this step")

class ImplementationPlan(BaseModel):
    """Full plan for implementing an algorithm."""
    paper_title: str
    algorithm_name: str
    summary: str
    steps: List[WorkflowStep] = Field(..., description="Ordered list of steps to implement the algorithm")
