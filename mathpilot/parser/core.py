from typing import List, Optional
from mathpilot.utils import get_logger
from mathpilot.utils.pdf import extract_pdf_sections, extract_pdf_text
from mathpilot.utils.llm import call_gemini
from mathpilot.parser.models import ParsedPaper, ParsingError

logger = get_logger("parser")

def parse_paper(pdf_path: str, title: Optional[str] = None, model_name: Optional[str] = None) -> ParsedPaper:
    """
    Parse a scientific paper PDF and extract algorithm implementation details.
    
    Args:
        model_name: Gemini model to use
        
    Returns:
        ParsedPaper object with extracted algorithms
    """
    logger.info(f"Parsing paper: {title}")
    
    # 1. Extract text, prioritizing Method/Algorithm sections
    # Try multiple common headers for methods
    sections = extract_pdf_sections(pdf_path, sections=["method", "algorithm", "implementation", "model", "approach", "proposed method"])
    
    # Combine extracted sections or fall back to full text if specific sections missing
    context_text = ""
    for sec_name, text in sections.items():
        if text:
            context_text += f"\n\n--- SECTION: {sec_name.upper()} ---\n{text}"
    
    if len(context_text) < 500: # Heuristic: if implementation sections are too short, use full text
         logger.info("Specific sections too short or missing, using full text extraction.")
         # Extract first N pages, usually enough for main algorithm description
         all_text = extract_pdf_text(pdf_path, max_pages=15) 
         context_text = all_text # Overwrite
         
    if not context_text:
        raise ParsingError("Could not extract any text from the PDF.")

    # 2. Use LLM to extract structured algorithm details
    # We construct a prompt that asks to populate the Pydantic structure
    prompt = f"""
    You are an expert scientific implementer. Your task is to extract the core algorithm(s) described in this paper text.
    
    Paper Title: {title}
    
    Focus on the methodology, mathematical steps, and implementation details necessary to reproduce the work.
    Extract the algorithm into clear, sequential steps that can be implemented in Python code.
    If multiple algorithms are presented, list all of them.
    Identify the logic, include key equations in the mathematical_details (latex format preferred but readable text ok), inputs, and outputs.
    
    Return the result as a JSON matching the ParsedPaper schema.
    
    Text content from paper:
    {context_text[:30000]} 
    """

    try:
        parsed_paper = call_gemini(
            prompt=prompt,
            model=model_name,
            schema=ParsedPaper
        )
        # Ensure title matches input if LLM hallucinates or omits it
        if title and (not parsed_paper.title or parsed_paper.title == "Algorithm"):
            parsed_paper.title = title
            
        logger.info(f"Successfully extracted {len(parsed_paper.algorithms)} algorithms for '{title}'.")
        return parsed_paper

    except Exception as e:
        logger.error(f"Failed to parse paper: {e}")
        raise ParsingError(f"LLM parsing failed: {e}") from e
