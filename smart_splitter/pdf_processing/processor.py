"""PDF processing engine for Smart-Splitter."""

import fitz  # PyMuPDF
from PIL import Image
from typing import List, Optional
import io

from .data_models import PageData, LayoutInfo, TextBlock


class PDFProcessor:
    """Core PDF processing functionality."""
    
    def __init__(self):
        self.document: Optional[fitz.Document] = None
        self.file_path: Optional[str] = None
    
    def load_pdf(self, file_path: str) -> bool:
        """Load a PDF file for processing."""
        try:
            self.document = fitz.open(file_path)
            self.file_path = file_path
            return True
        except Exception as e:
            print(f"Error loading PDF: {e}")
            return False
    
    def get_page_count(self) -> int:
        """Get the total number of pages in the PDF."""
        if not self.document:
            return 0
        return len(self.document)
    
    def extract_page_text(self, page_num: int) -> str:
        """Extract text from a specific page."""
        if not self.document or page_num >= len(self.document):
            return ""
        
        page = self.document[page_num]
        return page.get_text()
    
    def get_page_layout_info(self, page_num: int) -> LayoutInfo:
        """Extract layout information from a page."""
        if not self.document or page_num >= len(self.document):
            return LayoutInfo(False, False, [], [], 0, 0)
        
        page = self.document[page_num]
        rect = page.rect
        text_dict = page.get_text("dict")
        
        text_blocks = []
        font_sizes = []
        
        for block in text_dict.get("blocks", []):
            if "lines" not in block:
                continue
                
            for line in block["lines"]:
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if text:
                        bbox = span.get("bbox", [0, 0, 0, 0])
                        font_size = span.get("size", 12)
                        font_name = span.get("font", "")
                        
                        text_blocks.append(TextBlock(
                            text=text,
                            x=bbox[0],
                            y=bbox[1],
                            width=bbox[2] - bbox[0],
                            height=bbox[3] - bbox[1],
                            font_size=font_size,
                            font_name=font_name
                        ))
                        font_sizes.append(font_size)
        
        has_header = any(block.y < rect.height * 0.1 for block in text_blocks)
        has_footer = any(block.y > rect.height * 0.9 for block in text_blocks)
        
        return LayoutInfo(
            has_header=has_header,
            has_footer=has_footer,
            font_sizes=font_sizes,
            text_blocks=text_blocks,
            page_width=rect.width,
            page_height=rect.height
        )
    
    def get_page_preview(self, page_num: int, max_size: int = 300) -> Optional[Image.Image]:
        """Generate a preview image for a page."""
        if not self.document or page_num >= len(self.document):
            return None
        
        try:
            page = self.document[page_num]
            
            zoom = max_size / max(page.rect.width, page.rect.height)
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            img_data = pix.tobytes("png")
            return Image.open(io.BytesIO(img_data))
        except Exception as e:
            print(f"Error generating preview for page {page_num}: {e}")
            return None
    
    def extract_page_data(self) -> List[PageData]:
        """Extract comprehensive data from all pages."""
        if not self.document:
            return []
        
        pages_data = []
        
        for page_num in range(len(self.document)):
            text = self.extract_page_text(page_num)
            layout_info = self.get_page_layout_info(page_num)
            
            first_lines = []
            lines = text.split('\n')
            for line in lines[:10]:
                line = line.strip()
                if line:
                    first_lines.append(line)
            
            large_font_threshold = 16
            has_large_text = any(
                size > large_font_threshold 
                for size in layout_info.font_sizes
            )
            
            page_data = PageData(
                page_num=page_num,
                text=text,
                has_large_text=has_large_text,
                first_lines=first_lines,
                layout_info=layout_info
            )
            
            pages_data.append(page_data)
        
        return pages_data
    
    def close(self):
        """Close the PDF document."""
        if self.document:
            self.document.close()
            self.document = None
            self.file_path = None