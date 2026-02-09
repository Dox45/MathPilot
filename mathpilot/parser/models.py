from typing import List, Optional
from pydantic import BaseModel, Field

class ParsingError(Exception):
    """Raised when parsing fails."""
    pass

class AlgorithmStep(BaseModel):
    """A single step in an algorithm."""
    number: int
    description: str = Field(..., description="Description of the step")
    mathematical_details: Optional[str] = Field(None, description="Mathematical formulas or notation")
    code_hint: Optional[str] = Field(None, description="Pseudocode or implementation hint")

class ExtractedAlgorithm(BaseModel):
    """
    Structured representation of an algorithm extracted from a paper.
    """
    name: str = Field(..., description="Name of the algorithm or method")
    summary: str = Field(..., description="High-level summary of what the algorithm does")
    problem_addressed: str = Field(..., description="The specific problem this algorithm solves")
    inputs: List[str] = Field(..., description="Required inputs/parameters")
    outputs: List[str] = Field(..., description="Expected outputs/results")
    steps: List[AlgorithmStep] = Field(..., description="Sequential steps of the algorithm")
    complexity: Optional[str] = Field(None, description="Time/space complexity if mentioned")
    
class ParsedPaper(BaseModel):
    """
    Container for all extracted information from a paper.
    """
    title: str
    algorithms: List[ExtractedAlgorithm] = Field(..., description="List of algorithms found in the paper")
