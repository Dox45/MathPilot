from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime

class Paper(BaseModel):
    """
    Represents a research paper from arXiv.
    """
    id: str
    title: str
    authors: List[str]
    summary: str
    published: datetime
    updated: datetime
    pdf_url: Optional[HttpUrl] = None
    category: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
