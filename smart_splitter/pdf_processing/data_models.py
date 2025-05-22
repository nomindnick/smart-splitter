"""Data models for PDF processing."""

from dataclasses import dataclass
from typing import List, Optional
from PIL import Image


@dataclass
class TextBlock:
    """Represents a block of text with position and formatting info."""
    text: str
    x: float
    y: float
    width: float
    height: float
    font_size: float
    font_name: str


@dataclass
class LayoutInfo:
    """Layout information for a PDF page."""
    has_header: bool
    has_footer: bool
    font_sizes: List[float]
    text_blocks: List[TextBlock]
    page_width: float
    page_height: float


@dataclass
class PageData:
    """Data extracted from a PDF page."""
    page_num: int
    text: str
    has_large_text: bool
    first_lines: List[str]
    layout_info: LayoutInfo
    preview_image: Optional[Image.Image] = None