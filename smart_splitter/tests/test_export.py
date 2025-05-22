"""
Tests for the export functionality.

This module contains tests for PDF export operations including
document splitting, filename collision handling, and export results.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from smart_splitter.export.exporter import PDFExporter
from smart_splitter.export.data_models import ExportConfig, ExportResult

# Create a simple DocumentSection for testing
from dataclasses import dataclass

@dataclass
class DocumentSection:
    start_page: int
    end_page: int
    document_type: str
    filename: str
    classification_confidence: float


class TestExportResult:
    """Test the ExportResult data model."""
    
    def test_empty_result(self):
        """Test empty export result."""
        result = ExportResult()
        assert result.success_count == 0
        assert result.failed_count == 0
        assert result.total_attempted == 0
        assert result.success_rate == 0.0
        assert len(result.errors) == 0
        assert len(result.exported_files) == 0
    
    def test_add_success(self):
        """Test adding successful exports."""
        result = ExportResult()
        result.add_success("/path/to/file1.pdf")
        result.add_success("/path/to/file2.pdf")
        
        assert result.success_count == 2
        assert result.failed_count == 0
        assert result.total_attempted == 2
        assert result.success_rate == 100.0
        assert len(result.exported_files) == 2
        assert "/path/to/file1.pdf" in result.exported_files
    
    def test_add_error(self):
        """Test adding failed exports."""
        result = ExportResult()
        result.add_error("Error message 1")
        result.add_error("Error message 2")
        
        assert result.success_count == 0
        assert result.failed_count == 2
        assert result.total_attempted == 2
        assert result.success_rate == 0.0
        assert len(result.errors) == 2
        assert "Error message 1" in result.errors
    
    def test_mixed_results(self):
        """Test mixed success and failure results."""
        result = ExportResult()
        result.add_success("/path/to/file1.pdf")
        result.add_error("Error message")
        result.add_success("/path/to/file2.pdf")
        
        assert result.success_count == 2
        assert result.failed_count == 1
        assert result.total_attempted == 3
        assert result.success_rate == pytest.approx(66.67, abs=0.01)


class TestExportConfig:
    """Test the ExportConfig data model."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ExportConfig()
        assert config.output_directory == str(Path("./output").resolve())
        assert config.overwrite_existing is False
        assert config.create_subdirectories is True
        assert config.filename_collision_strategy == 'rename'
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = ExportConfig(
            output_directory="/custom/path",
            overwrite_existing=True,
            create_subdirectories=False,
            filename_collision_strategy='overwrite'
        )
        assert config.output_directory == str(Path("/custom/path").resolve())
        assert config.overwrite_existing is True
        assert config.create_subdirectories is False
        assert config.filename_collision_strategy == 'overwrite'
    
    def test_invalid_collision_strategy(self):
        """Test invalid collision strategy validation."""
        with pytest.raises(ValueError, match="Invalid collision strategy"):
            ExportConfig(filename_collision_strategy='invalid')
    
    def test_output_path_property(self):
        """Test output_path property."""
        config = ExportConfig(output_directory="/test/path")
        assert isinstance(config.output_path, Path)
        assert str(config.output_path) == str(Path("/test/path").resolve())


class TestPDFExporter:
    """Test the PDFExporter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = ExportConfig(output_directory=self.temp_dir)
        self.exporter = PDFExporter(self.config)
        
        # Create sample document sections
        self.doc1 = DocumentSection(
            start_page=1,
            end_page=2,
            document_type="email",
            filename="test_email",
            classification_confidence=0.9
        )
        
        self.doc2 = DocumentSection(
            start_page=3,
            end_page=4,
            document_type="payment_application",
            filename="test_payment",
            classification_confidence=0.8
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test exporter initialization."""
        assert self.exporter.config == self.config
        assert Path(self.temp_dir).exists()
    
    def test_get_unique_filename_no_collision(self):
        """Test unique filename generation with no collision."""
        test_file = Path(self.temp_dir) / "test.pdf"
        result = self.exporter._get_unique_filename(str(test_file))
        assert result == str(test_file)
    
    def test_get_unique_filename_with_collision(self):
        """Test unique filename generation with collision."""
        test_file = Path(self.temp_dir) / "test.pdf"
        test_file.touch()  # Create the file to simulate collision
        
        result = self.exporter._get_unique_filename(str(test_file))
        expected = str(Path(self.temp_dir) / "test_001.pdf")
        assert result == expected
    
    def test_get_unique_filename_multiple_collisions(self):
        """Test unique filename generation with multiple collisions."""
        base_file = Path(self.temp_dir) / "test.pdf"
        base_file.touch()
        (Path(self.temp_dir) / "test_001.pdf").touch()
        (Path(self.temp_dir) / "test_002.pdf").touch()
        
        result = self.exporter._get_unique_filename(str(base_file))
        expected = str(Path(self.temp_dir) / "test_003.pdf")
        assert result == expected
    
    def test_handle_filename_collision_rename(self):
        """Test filename collision handling with rename strategy."""
        self.config.filename_collision_strategy = 'rename'
        test_file = Path(self.temp_dir) / "test.pdf"
        test_file.touch()
        
        result = self.exporter._handle_filename_collision(str(test_file))
        expected = str(Path(self.temp_dir) / "test_001.pdf")
        assert result == expected
    
    def test_handle_filename_collision_skip(self):
        """Test filename collision handling with skip strategy."""
        self.config.filename_collision_strategy = 'skip'
        test_file = Path(self.temp_dir) / "test.pdf"
        test_file.touch()
        
        result = self.exporter._handle_filename_collision(str(test_file))
        assert result is None
    
    def test_handle_filename_collision_overwrite(self):
        """Test filename collision handling with overwrite strategy."""
        self.config.filename_collision_strategy = 'overwrite'
        test_file = Path(self.temp_dir) / "test.pdf"
        test_file.touch()
        
        result = self.exporter._handle_filename_collision(str(test_file))
        assert result == str(test_file)
    
    def test_handle_filename_collision_invalid_strategy(self):
        """Test filename collision handling with invalid strategy."""
        self.config.filename_collision_strategy = 'invalid'
        test_file = Path(self.temp_dir) / "test.pdf"
        test_file.touch()  # File must exist to trigger collision handling
        
        with pytest.raises(ValueError, match="Unknown collision strategy"):
            self.exporter._handle_filename_collision(str(test_file))
    
    @patch('smart_splitter.export.exporter.fitz')
    def test_export_document_success(self, mock_fitz):
        """Test successful single document export."""
        # Mock PyMuPDF objects
        mock_source_doc = Mock()
        mock_output_doc = Mock()
        mock_fitz.open.side_effect = [mock_source_doc, mock_output_doc]
        
        # Configure mock
        mock_source_doc.__len__ = Mock(return_value=10)
        
        # Test export
        result = self.exporter.export_document("source.pdf", self.doc1)
        
        assert result is True
        mock_output_doc.insert_pdf.assert_called()
        mock_output_doc.save.assert_called()
        mock_output_doc.close.assert_called()
        mock_source_doc.close.assert_called()
    
    @patch('smart_splitter.export.exporter.fitz')
    def test_export_document_file_exists_skip(self, mock_fitz):
        """Test document export when file exists and strategy is skip."""
        self.config.filename_collision_strategy = 'skip'
        
        # Create existing file
        existing_file = Path(self.temp_dir) / f"{self.doc1.filename}.pdf"
        existing_file.touch()
        
        result = self.exporter.export_document("source.pdf", self.doc1)
        
        assert result is False
        mock_fitz.open.assert_not_called()
    
    @patch('smart_splitter.export.exporter.fitz')
    def test_export_document_error(self, mock_fitz):
        """Test document export with error."""
        mock_fitz.open.side_effect = Exception("PDF error")
        
        result = self.exporter.export_document("source.pdf", self.doc1)
        
        assert result is False
    
    @patch('smart_splitter.export.exporter.fitz')
    def test_export_all_documents_success(self, mock_fitz):
        """Test successful export of all documents."""
        # Mock PyMuPDF objects
        mock_source_doc = Mock()
        mock_output_doc = Mock()
        mock_fitz.open.side_effect = [mock_source_doc, mock_output_doc] * 2
        
        # Configure mock
        mock_source_doc.__len__ = Mock(return_value=10)
        
        documents = [self.doc1, self.doc2]
        result = self.exporter.export_all_documents("source.pdf", documents)
        
        assert isinstance(result, ExportResult)
        assert result.success_count == 2
        assert result.failed_count == 0
        assert len(result.exported_files) == 2
    
    def test_export_all_documents_empty_list(self):
        """Test export with empty document list."""
        result = self.exporter.export_all_documents("source.pdf", [])
        
        assert isinstance(result, ExportResult)
        assert result.success_count == 0
        assert result.failed_count == 0
    
    @patch('smart_splitter.export.exporter.fitz')
    def test_export_all_documents_partial_failure(self, mock_fitz):
        """Test export with some failures."""
        # Mock PyMuPDF to succeed for first doc, fail for second
        mock_source_doc = Mock()
        mock_output_doc = Mock()
        mock_fitz.open.side_effect = [
            mock_source_doc, mock_output_doc,  # First doc succeeds
            Exception("Error")  # Second doc fails
        ]
        
        # Configure mock
        mock_source_doc.__len__ = Mock(return_value=10)
        
        documents = [self.doc1, self.doc2]
        result = self.exporter.export_all_documents("source.pdf", documents)
        
        assert result.success_count == 1
        assert result.failed_count == 1
        assert len(result.errors) == 1
        assert len(result.exported_files) == 1