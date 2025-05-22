"""Document boundary detection for Smart-Splitter."""

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass

from ..pdf_processing.data_models import PageData
from ..config.manager import ConfigManager, PatternManager
from ..performance.monitor import monitor_performance
from ..error_handling.handlers import handle_errors
from ..error_handling.exceptions import PDFProcessingError


@dataclass
class BoundaryConfig:
    """Configuration for boundary detection."""
    patterns: Dict[str, List[str]]
    min_document_length: int = 1
    confidence_threshold: float = 0.7
    large_font_weight: float = 2.0
    header_change_weight: float = 1.5


class BoundaryDetector:
    """Detects document boundaries within a multi-document PDF."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.pattern_manager = PatternManager(config_manager)
        self.config = BoundaryConfig(
            patterns=self.pattern_manager.get_boundary_patterns(),
            min_document_length=config_manager.get_setting("processing.min_document_length", 1),
            confidence_threshold=config_manager.get_setting("processing.confidence_threshold", 0.7)
        )
    
    @monitor_performance("boundary_detection")
    @handle_errors()
    def detect_boundaries(self, pages_data: List[PageData]) -> List[int]:
        """Detect document boundaries and return list of starting page numbers."""
        if not pages_data:
            return []
        
        try:
            boundaries = [0]  # First page is always a boundary
            
            for i in range(1, len(pages_data)):
                if self._is_boundary_page(pages_data, i):
                    boundaries.append(i)
            
            return self.validate_boundaries(boundaries, len(pages_data))
        
        except Exception as e:
            raise PDFProcessingError(f"Boundary detection failed: {str(e)}", 
                                   details={"page_count": len(pages_data)})
    
    def _is_boundary_page(self, pages_data: List[PageData], page_index: int) -> bool:
        """Check if a page is likely a document boundary."""
        current_page = pages_data[page_index]
        previous_page = pages_data[page_index - 1] if page_index > 0 else None
        
        confidence = 0.0
        
        # Check for pattern matches
        pattern_score = self._check_boundary_patterns(current_page.text)
        confidence += pattern_score
        
        # Check for layout changes
        if previous_page:
            layout_score = self._check_layout_changes(previous_page, current_page)
            confidence += layout_score
        
        # Check for large text (potential titles/headers)
        if current_page.has_large_text:
            confidence += self.config.large_font_weight
        
        # Check for header format changes
        header_score = self._check_header_changes(pages_data, page_index)
        confidence += header_score
        
        return confidence >= self.config.confidence_threshold
    
    def _check_boundary_patterns(self, text: str) -> float:
        """Check for predefined boundary patterns in text."""
        text_upper = text.upper()
        max_score = 0.0
        
        for doc_type, patterns in self.config.patterns.items():
            for pattern in patterns:
                try:
                    if re.search(pattern, text_upper, re.IGNORECASE | re.MULTILINE):
                        max_score = max(max_score, 3.0)  # Strong pattern match
                except re.error:
                    continue
        
        return max_score
    
    def _check_layout_changes(self, prev_page: PageData, curr_page: PageData) -> float:
        """Check for significant layout changes between pages."""
        score = 0.0
        
        # Check font size changes
        prev_avg_font = sum(prev_page.layout_info.font_sizes) / len(prev_page.layout_info.font_sizes) if prev_page.layout_info.font_sizes else 12
        curr_avg_font = sum(curr_page.layout_info.font_sizes) / len(curr_page.layout_info.font_sizes) if curr_page.layout_info.font_sizes else 12
        
        font_change_ratio = abs(curr_avg_font - prev_avg_font) / prev_avg_font if prev_avg_font > 0 else 0
        if font_change_ratio > 0.2:  # 20% change
            score += 1.0
        
        # Check for significant text block position changes
        if self._has_layout_shift(prev_page, curr_page):
            score += 1.0
        
        return score
    
    def _has_layout_shift(self, prev_page: PageData, curr_page: PageData) -> bool:
        """Check if there's a significant layout shift between pages."""
        if not prev_page.layout_info.text_blocks or not curr_page.layout_info.text_blocks:
            return False
        
        # Calculate average Y positions of text blocks
        prev_avg_y = sum(block.y for block in prev_page.layout_info.text_blocks) / len(prev_page.layout_info.text_blocks)
        curr_avg_y = sum(block.y for block in curr_page.layout_info.text_blocks) / len(curr_page.layout_info.text_blocks)
        
        # Check if there's a significant vertical shift
        page_height = curr_page.layout_info.page_height
        shift_ratio = abs(curr_avg_y - prev_avg_y) / page_height if page_height > 0 else 0
        
        return shift_ratio > 0.3  # 30% of page height
    
    def _check_header_changes(self, pages_data: List[PageData], page_index: int) -> float:
        """Check for header format changes that might indicate new document."""
        if page_index < 2:  # Need at least 2 previous pages for comparison
            return 0.0
        
        current_page = pages_data[page_index]
        
        # Get first few lines as potential header
        current_header = current_page.first_lines[:3] if current_page.first_lines else []
        
        # Compare with previous pages' headers
        similar_headers = 0
        for i in range(max(0, page_index - 3), page_index):
            prev_header = pages_data[i].first_lines[:3] if pages_data[i].first_lines else []
            if self._headers_similar(current_header, prev_header):
                similar_headers += 1
        
        # If current header is very different from recent headers, it might be a new document
        if similar_headers == 0 and len(current_header) > 0:
            return self.config.header_change_weight
        
        return 0.0
    
    def _headers_similar(self, header1: List[str], header2: List[str]) -> bool:
        """Check if two headers are similar."""
        if not header1 or not header2:
            return False
        
        # Simple similarity check based on common words
        words1 = set(' '.join(header1).lower().split())
        words2 = set(' '.join(header2).lower().split())
        
        if not words1 or not words2:
            return False
        
        common_words = words1.intersection(words2)
        similarity = len(common_words) / max(len(words1), len(words2))
        
        return similarity > 0.3  # 30% word overlap
    
    def validate_boundaries(self, boundaries: List[int], total_pages: int) -> List[int]:
        """Validate and clean up detected boundaries."""
        if not boundaries:
            return [0]
        
        validated = [0]  # Always include first page
        
        for boundary in sorted(set(boundaries[1:])):  # Remove duplicates and sort
            if boundary >= total_pages:
                continue
            
            # Check minimum document length
            prev_boundary = validated[-1]
            if boundary - prev_boundary >= self.config.min_document_length:
                validated.append(boundary)
        
        return validated
    
    def add_custom_pattern(self, pattern: str, document_type: str):
        """Add a custom boundary detection pattern."""
        self.pattern_manager.add_custom_pattern(document_type, pattern, "boundary")
        # Reload patterns
        self.config.patterns = self.pattern_manager.get_boundary_patterns()
    
    def get_document_sections(self, boundaries: List[int], total_pages: int) -> List[Tuple[int, int]]:
        """Convert boundaries to document sections (start_page, end_page)."""
        if not boundaries:
            return [(0, total_pages - 1)] if total_pages > 0 else []
        
        sections = []
        for i in range(len(boundaries)):
            start_page = boundaries[i]
            end_page = boundaries[i + 1] - 1 if i + 1 < len(boundaries) else total_pages - 1
            
            if start_page <= end_page:
                sections.append((start_page, end_page))
        
        return sections