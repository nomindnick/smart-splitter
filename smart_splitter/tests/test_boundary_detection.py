"""Tests for boundary detection functionality."""

import unittest
from unittest.mock import Mock

from smart_splitter.boundary_detection.detector import BoundaryDetector, BoundaryConfig
from smart_splitter.pdf_processing.data_models import PageData, LayoutInfo, TextBlock
from smart_splitter.config.manager import ConfigManager


class TestBoundaryDetector(unittest.TestCase):
    """Test boundary detection functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.config_manager = Mock(spec=ConfigManager)
        self.config_manager.get_setting.side_effect = lambda key, default=None: {
            "processing.min_document_length": 1,
            "processing.confidence_threshold": 0.7
        }.get(key, default)
        
        self.detector = BoundaryDetector(self.config_manager)
        self.detector.pattern_manager.get_boundary_patterns = Mock(return_value={
            "email": [r"From:\s*.+@.+", r"Subject:\s*.+"],
            "payment_application": [r"PAYMENT APPLICATION\s*(?:NO|#)\.?\s*\d+"]
        })
        self.detector.config = BoundaryConfig(
            patterns=self.detector.pattern_manager.get_boundary_patterns(),
            min_document_length=1,
            confidence_threshold=0.7
        )
    
    def create_mock_page_data(self, page_num: int, text: str, has_large_text: bool = False) -> PageData:
        """Create mock page data for testing."""
        layout_info = LayoutInfo(
            has_header=False,
            has_footer=False,
            font_sizes=[12.0],
            text_blocks=[],
            page_width=612,
            page_height=792
        )
        
        return PageData(
            page_num=page_num,
            text=text,
            has_large_text=has_large_text,
            first_lines=text.split('\n')[:5],
            layout_info=layout_info
        )
    
    def test_detect_boundaries_empty_input(self):
        """Test boundary detection with empty input."""
        boundaries = self.detector.detect_boundaries([])
        self.assertEqual(boundaries, [])
    
    def test_detect_boundaries_single_page(self):
        """Test boundary detection with single page."""
        pages = [self.create_mock_page_data(0, "Regular document text")]
        boundaries = self.detector.detect_boundaries(pages)
        self.assertEqual(boundaries, [0])
    
    def test_detect_boundaries_with_email_pattern(self):
        """Test boundary detection with email pattern."""
        pages = [
            self.create_mock_page_data(0, "Regular document text"),
            self.create_mock_page_data(1, "From: john@example.com\nTo: jane@example.com\nSubject: Test Email"),
            self.create_mock_page_data(2, "More document text")
        ]
        
        boundaries = self.detector.detect_boundaries(pages)
        self.assertIn(0, boundaries)  # First page always included
        self.assertIn(1, boundaries)  # Email pattern detected
    
    def test_detect_boundaries_with_payment_application(self):
        """Test boundary detection with payment application pattern."""
        pages = [
            self.create_mock_page_data(0, "Regular document text"),
            self.create_mock_page_data(1, "PAYMENT APPLICATION NO. 5\nFor work completed"),
            self.create_mock_page_data(2, "More document text")
        ]
        
        boundaries = self.detector.detect_boundaries(pages)
        self.assertIn(0, boundaries)
        self.assertIn(1, boundaries)
    
    def test_validate_boundaries_minimum_length(self):
        """Test boundary validation with minimum document length."""
        self.detector.config.min_document_length = 2
        
        boundaries = [0, 1, 3, 5]  # Too short documents
        validated = self.detector.validate_boundaries(boundaries, 10)
        
        # Should keep 0, 3, 5 (documents of length 3, 2, 5)
        expected = [0, 3, 5]
        self.assertEqual(validated, expected)
    
    def test_get_document_sections(self):
        """Test converting boundaries to document sections."""
        boundaries = [0, 3, 7]
        sections = self.detector.get_document_sections(boundaries, 10)
        
        expected = [(0, 2), (3, 6), (7, 9)]
        self.assertEqual(sections, expected)
    
    def test_get_document_sections_empty(self):
        """Test document sections with empty boundaries."""
        sections = self.detector.get_document_sections([], 5)
        self.assertEqual(sections, [(0, 4)])
    
    def test_pattern_matching_case_insensitive(self):
        """Test that pattern matching is case insensitive."""
        page = self.create_mock_page_data(0, "from: john@example.com\nsubject: test")
        score = self.detector._check_boundary_patterns(page.text)
        self.assertGreater(score, 0)


if __name__ == "__main__":
    unittest.main()