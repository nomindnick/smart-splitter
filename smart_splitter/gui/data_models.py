"""
Data models for GUI components.

This module defines the data structures used by the GUI to represent
document sections and their metadata.
"""

from dataclasses import dataclass
from typing import Optional
from PIL import Image


@dataclass
class DocumentSection:
    """Represents a detected document section within a PDF."""
    
    start_page: int
    end_page: int
    document_type: str
    filename: str
    classification_confidence: float
    text_sample: str = ""
    preview_image: Optional[Image.Image] = None
    selected: bool = False
    
    @property
    def page_count(self) -> int:
        """Get the number of pages in this document section."""
        return self.end_page - self.start_page + 1
    
    @property
    def page_range_str(self) -> str:
        """Get a formatted string representation of the page range."""
        if self.start_page == self.end_page:
            return f"Page {self.start_page}"
        return f"Pages {self.start_page}-{self.end_page}"
    
    @property
    def confidence_str(self) -> str:
        """Get a formatted confidence level string."""
        if self.classification_confidence >= 0.8:
            return "High"
        elif self.classification_confidence >= 0.6:
            return "Medium"
        else:
            return "Low"