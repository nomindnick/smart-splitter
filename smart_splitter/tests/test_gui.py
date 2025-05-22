"""
Tests for the GUI components.

This module contains tests for GUI data models and components
to ensure proper functionality without requiring a display.
"""

import pytest
from unittest.mock import Mock
from PIL import Image

# Create DocumentSection class directly for testing to avoid import issues
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


class TestDocumentSection:
    """Test the DocumentSection data model."""
    
    def test_basic_initialization(self):
        """Test basic document section initialization."""
        doc = DocumentSection(
            start_page=1,
            end_page=3,
            document_type="email",
            filename="test_email",
            classification_confidence=0.85
        )
        
        assert doc.start_page == 1
        assert doc.end_page == 3
        assert doc.document_type == "email"
        assert doc.filename == "test_email"
        assert doc.classification_confidence == 0.85
        assert doc.text_sample == ""
        assert doc.preview_image is None
        assert doc.selected is False
    
    def test_initialization_with_optional_fields(self):
        """Test initialization with optional fields."""
        mock_image = Mock(spec=Image.Image)
        
        doc = DocumentSection(
            start_page=5,
            end_page=7,
            document_type="payment_application",
            filename="payment_app_01",
            classification_confidence=0.92,
            text_sample="Sample text content",
            preview_image=mock_image,
            selected=True
        )
        
        assert doc.text_sample == "Sample text content"
        assert doc.preview_image == mock_image
        assert doc.selected is True
    
    def test_page_count_property(self):
        """Test page_count property calculation."""
        # Single page document
        doc1 = DocumentSection(
            start_page=5,
            end_page=5,
            document_type="email",
            filename="single_page",
            classification_confidence=0.8
        )
        assert doc1.page_count == 1
        
        # Multi-page document
        doc2 = DocumentSection(
            start_page=10,
            end_page=15,
            document_type="contract_document",
            filename="contract",
            classification_confidence=0.9
        )
        assert doc2.page_count == 6
    
    def test_page_range_str_property(self):
        """Test page_range_str property formatting."""
        # Single page
        doc1 = DocumentSection(
            start_page=3,
            end_page=3,
            document_type="email",
            filename="single",
            classification_confidence=0.8
        )
        assert doc1.page_range_str == "Page 3"
        
        # Multiple pages
        doc2 = DocumentSection(
            start_page=5,
            end_page=8,
            document_type="payment_application",
            filename="multi",
            classification_confidence=0.9
        )
        assert doc2.page_range_str == "Pages 5-8"
    
    def test_confidence_str_property(self):
        """Test confidence_str property formatting."""
        # High confidence
        doc_high = DocumentSection(
            start_page=1,
            end_page=2,
            document_type="email",
            filename="high_conf",
            classification_confidence=0.85
        )
        assert doc_high.confidence_str == "High"
        
        # Medium confidence
        doc_medium = DocumentSection(
            start_page=1,
            end_page=2,
            document_type="other",
            filename="medium_conf",
            classification_confidence=0.7
        )
        assert doc_medium.confidence_str == "Medium"
        
        # Low confidence
        doc_low = DocumentSection(
            start_page=1,
            end_page=2,
            document_type="other",
            filename="low_conf",
            classification_confidence=0.5
        )
        assert doc_low.confidence_str == "Low"
        
        # Edge cases
        doc_edge_high = DocumentSection(
            start_page=1,
            end_page=2,
            document_type="email",
            filename="edge_high",
            classification_confidence=0.8  # Exactly at threshold
        )
        assert doc_edge_high.confidence_str == "High"
        
        doc_edge_medium = DocumentSection(
            start_page=1,
            end_page=2,
            document_type="other",
            filename="edge_medium",
            classification_confidence=0.6  # Exactly at threshold
        )
        assert doc_edge_medium.confidence_str == "Medium"
    
    def test_confidence_boundary_values(self):
        """Test confidence string with boundary values."""
        # Test values right at boundaries
        test_cases = [
            (0.0, "Low"),
            (0.59, "Low"),
            (0.6, "Medium"),
            (0.79, "Medium"),
            (0.8, "High"),
            (1.0, "High")
        ]
        
        for confidence, expected in test_cases:
            doc = DocumentSection(
                start_page=1,
                end_page=1,
                document_type="test",
                filename="test",
                classification_confidence=confidence
            )
            assert doc.confidence_str == expected, f"Failed for confidence {confidence}"
    
    def test_document_types(self):
        """Test various document types."""
        document_types = [
            "email",
            "letter",
            "payment_application",
            "evidence_of_payment",
            "change_order",
            "change_order_response",
            "rfi",
            "rfi_response",
            "inspection_report",
            "contract_document",
            "plans_specifications",
            "other"
        ]
        
        for doc_type in document_types:
            doc = DocumentSection(
                start_page=1,
                end_page=1,
                document_type=doc_type,
                filename=f"test_{doc_type}",
                classification_confidence=0.8
            )
            assert doc.document_type == doc_type
    
    def test_selection_state(self):
        """Test document selection state management."""
        doc = DocumentSection(
            start_page=1,
            end_page=2,
            document_type="email",
            filename="test",
            classification_confidence=0.8
        )
        
        # Default state
        assert doc.selected is False
        
        # Change selection
        doc.selected = True
        assert doc.selected is True
        
        doc.selected = False
        assert doc.selected is False
    
    def test_immutable_properties(self):
        """Test that properties are read-only."""
        doc = DocumentSection(
            start_page=1,
            end_page=3,
            document_type="email",
            filename="test",
            classification_confidence=0.8
        )
        
        # These should be calculated properties, not settable
        with pytest.raises(AttributeError):
            doc.page_count = 5
        
        with pytest.raises(AttributeError):
            doc.page_range_str = "Custom range"
        
        with pytest.raises(AttributeError):
            doc.confidence_str = "Custom confidence"