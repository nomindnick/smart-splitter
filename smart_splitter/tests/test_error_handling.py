"""Tests for error handling and validation components."""

import unittest
from unittest.mock import Mock, patch, mock_open
import tempfile
import os
from pathlib import Path

from smart_splitter.error_handling.exceptions import (
    SmartSplitterError, PDFProcessingError, ClassificationError, 
    ExportError, ConfigurationError, ValidationError
)
from smart_splitter.error_handling.handlers import ErrorHandler, RecoveryManager, handle_errors
from smart_splitter.error_handling.validators import InputValidator


class TestSmartSplitterExceptions(unittest.TestCase):
    """Test custom exception classes."""
    
    def test_base_exception(self):
        """Test base SmartSplitterError exception."""
        error = SmartSplitterError(
            "Test error",
            error_code="TEST001",
            details={"key": "value"}
        )
        
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.error_code, "TEST001")
        self.assertEqual(error.details["key"], "value")
        
        error_dict = error.to_dict()
        self.assertEqual(error_dict["type"], "SmartSplitterError")
        self.assertEqual(error_dict["message"], "Test error")
        self.assertEqual(error_dict["error_code"], "TEST001")
        self.assertEqual(error_dict["details"]["key"], "value")
    
    def test_pdf_processing_error(self):
        """Test PDFProcessingError with PDF-specific details."""
        error = PDFProcessingError(
            "PDF processing failed",
            pdf_path="/path/to/file.pdf",
            page_number=5
        )
        
        self.assertEqual(error.pdf_path, "/path/to/file.pdf")
        self.assertEqual(error.page_number, 5)
        self.assertEqual(error.details["pdf_path"], "/path/to/file.pdf")
        self.assertEqual(error.details["page_number"], 5)
    
    def test_classification_error(self):
        """Test ClassificationError with classification details."""
        error = ClassificationError(
            "Classification failed",
            document_text="Sample document text...",
            classification_attempt="email"
        )
        
        self.assertEqual(error.document_text, "Sample document text...")
        self.assertEqual(error.classification_attempt, "email")
        self.assertEqual(error.details["text_sample"], "Sample document text...")
        self.assertEqual(error.details["attempted_classification"], "email")
    
    def test_export_error(self):
        """Test ExportError with export details."""
        error = ExportError(
            "Export failed",
            output_path="/output/file.pdf",
            page_range=(1, 5)
        )
        
        self.assertEqual(error.output_path, "/output/file.pdf")
        self.assertEqual(error.page_range, (1, 5))
        self.assertEqual(error.details["output_path"], "/output/file.pdf")
        self.assertEqual(error.details["page_range"], (1, 5))
    
    def test_validation_error(self):
        """Test ValidationError with validation details."""
        error = ValidationError(
            "Validation failed",
            field_name="filename",
            field_value="invalid<>name",
            validation_rule="no_invalid_chars"
        )
        
        self.assertEqual(error.field_name, "filename")
        self.assertEqual(error.field_value, "invalid<>name")
        self.assertEqual(error.validation_rule, "no_invalid_chars")


class TestErrorHandler(unittest.TestCase):
    """Test error handling functionality."""
    
    def setUp(self):
        self.error_handler = ErrorHandler()
    
    def test_handle_error_basic(self):
        """Test basic error handling."""
        error = ValueError("Test error")
        
        result = self.error_handler.handle_error(error)
        
        self.assertIn("error_id", result)
        self.assertIn("message", result)
        self.assertIn("recoverable", result)
        self.assertIn("suggested_action", result)
        self.assertFalse(result["recoverable"])  # ValueError not recoverable
    
    def test_handle_smart_splitter_error(self):
        """Test handling SmartSplitter-specific errors."""
        error = PDFProcessingError("PDF error", pdf_path="test.pdf")
        
        result = self.error_handler.handle_error(error)
        
        self.assertEqual(result["message"], "PDF error")
        self.assertTrue(result["recoverable"])  # PDFProcessingError is recoverable
        self.assertIn("PDF file", result["suggested_action"])
    
    def test_error_counting(self):
        """Test error counting functionality."""
        # Handle multiple errors
        self.error_handler.handle_error(ValueError("Error 1"))
        self.error_handler.handle_error(ValueError("Error 2"))
        self.error_handler.handle_error(PDFProcessingError("PDF Error"))
        
        stats = self.error_handler.get_error_stats()
        
        self.assertEqual(stats["total_errors"], 3)
        self.assertEqual(stats["error_counts"]["ValueError"], 2)
        self.assertEqual(stats["error_counts"]["PDFProcessingError"], 1)
        self.assertEqual(stats["most_common"][0], "ValueError")
    
    def test_error_callbacks(self):
        """Test error callback registration and execution."""
        callback_called = False
        callback_error_info = None
        
        def test_callback(error_info):
            nonlocal callback_called, callback_error_info
            callback_called = True
            callback_error_info = error_info
        
        # Register callback
        self.error_handler.register_callback("ValueError", test_callback)
        
        # Handle error
        error = ValueError("Test error")
        self.error_handler.handle_error(error)
        
        self.assertTrue(callback_called)
        self.assertEqual(callback_error_info["type"], "ValueError")
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_error_log(self, mock_json_dump, mock_file):
        """Test saving error log to file."""
        # Handle some errors
        self.error_handler.handle_error(ValueError("Test error"))
        
        # Save error log
        self.error_handler.save_error_log("error_log.json")
        
        mock_file.assert_called_once_with("error_log.json", 'w')
        mock_json_dump.assert_called_once()


class TestRecoveryManager(unittest.TestCase):
    """Test error recovery functionality."""
    
    def setUp(self):
        self.error_handler = ErrorHandler()
        self.recovery_manager = RecoveryManager(self.error_handler)
    
    def test_register_recovery_strategy(self):
        """Test registering custom recovery strategies."""
        def custom_recovery(error, attempt):
            return True
        
        self.recovery_manager.register_recovery_strategy("CustomError", custom_recovery)
        
        self.assertIn("CustomError", self.recovery_manager.recovery_strategies)
        self.assertEqual(
            self.recovery_manager.recovery_strategies["CustomError"],
            custom_recovery
        )
    
    @patch.object(RecoveryManager, '_recover_memory_error')
    def test_attempt_recovery_success(self, mock_recover):
        """Test successful error recovery."""
        mock_recover.return_value = True
        
        # Mock operation that succeeds after recovery
        operation_calls = 0
        def test_operation():
            nonlocal operation_calls
            operation_calls += 1
            if operation_calls == 1:
                raise MemoryError("Memory error")
            return "success"
        
        from smart_splitter.error_handling.exceptions import MemoryError as SmartMemoryError
        error = SmartMemoryError("Memory error")
        
        result = self.recovery_manager.attempt_recovery(error, test_operation, max_retries=2)
        
        self.assertEqual(result, "success")
        mock_recover.assert_called_once()
    
    def test_attempt_recovery_no_strategy(self):
        """Test recovery attempt with no available strategy."""
        error = ValueError("Unknown error")
        
        def test_operation():
            return "should not be called"
        
        with self.assertRaises(ValueError):
            self.recovery_manager.attempt_recovery(error, test_operation)


class TestHandleErrorsDecorator(unittest.TestCase):
    """Test handle_errors decorator."""
    
    def test_decorator_no_error(self):
        """Test decorator with successful function execution."""
        @handle_errors()
        def test_function(x, y):
            return x + y
        
        result = test_function(2, 3)
        self.assertEqual(result, 5)
    
    def test_decorator_with_error(self):
        """Test decorator with function that raises error."""
        error_handler = ErrorHandler()
        
        @handle_errors(error_handler=error_handler)
        def test_function():
            raise ValueError("Test error")
        
        with self.assertRaises(ValueError):
            test_function()
        
        # Check that error was handled
        stats = error_handler.get_error_stats()
        self.assertEqual(stats["error_counts"]["ValueError"], 1)


class TestInputValidator(unittest.TestCase):
    """Test input validation functionality."""
    
    def setUp(self):
        self.validator = InputValidator()
    
    def test_validate_filename_valid(self):
        """Test validating valid filename."""
        result = self.validator.validate_filename("valid_filename.pdf")
        
        self.assertTrue(result["valid"])
        self.assertEqual(result["filename"], "valid_filename.pdf")
    
    def test_validate_filename_invalid_chars(self):
        """Test validating filename with invalid characters."""
        with self.assertRaises(ValidationError) as context:
            self.validator.validate_filename("invalid<>filename.pdf")
        
        error = context.exception
        self.assertEqual(error.field_name, "filename")
        self.assertEqual(error.validation_rule, "no_invalid_chars")
    
    def test_validate_filename_too_long(self):
        """Test validating filename that's too long."""
        long_filename = "a" * 250 + ".pdf"
        
        with self.assertRaises(ValidationError) as context:
            self.validator.validate_filename(long_filename, max_length=200)
        
        error = context.exception
        self.assertEqual(error.field_name, "filename")
        self.assertIn("max_200_chars", error.validation_rule)
    
    def test_validate_filename_reserved_name(self):
        """Test validating filename with reserved name."""
        with self.assertRaises(ValidationError) as context:
            self.validator.validate_filename("CON.pdf")
        
        error = context.exception
        self.assertEqual(error.validation_rule, "no_reserved_names")
    
    def test_validate_page_range_valid(self):
        """Test validating valid page range."""
        result = self.validator.validate_page_range(1, 5, 10)
        
        self.assertTrue(result["valid"])
        self.assertEqual(result["start_page"], 1)
        self.assertEqual(result["end_page"], 5)
        self.assertEqual(result["page_count"], 5)
    
    def test_validate_page_range_invalid_order(self):
        """Test validating page range with invalid order."""
        with self.assertRaises(ValidationError) as context:
            self.validator.validate_page_range(5, 3, 10)
        
        error = context.exception
        self.assertEqual(error.field_name, "page_range")
        self.assertEqual(error.validation_rule, "start_before_end")
    
    def test_validate_page_range_exceeds_total(self):
        """Test validating page range that exceeds total pages."""
        with self.assertRaises(ValidationError) as context:
            self.validator.validate_page_range(1, 15, 10)
        
        error = context.exception
        self.assertEqual(error.field_name, "end_page")
        self.assertIn("max_page_10", error.validation_rule)
    
    def test_validate_api_key_valid(self):
        """Test validating valid OpenAI API key."""
        result = self.validator.validate_api_key("sk-1234567890abcdef1234567890abcdef")
        
        self.assertTrue(result["valid"])
        self.assertEqual(result["api_name"], "OpenAI")
    
    def test_validate_api_key_invalid_format(self):
        """Test validating API key with invalid format."""
        with self.assertRaises(ValidationError) as context:
            self.validator.validate_api_key("invalid-key")
        
        error = context.exception
        self.assertEqual(error.validation_rule, "openai_format")
    
    def test_validate_api_key_too_short(self):
        """Test validating API key that's too short."""
        with self.assertRaises(ValidationError) as context:
            self.validator.validate_api_key("sk-short")
        
        error = context.exception
        self.assertEqual(error.validation_rule, "min_length_20")
    
    def test_validate_document_type_valid(self):
        """Test validating valid document type."""
        result = self.validator.validate_document_type("email")
        
        self.assertTrue(result["valid"])
        self.assertEqual(result["document_type"], "email")
    
    def test_validate_document_type_invalid(self):
        """Test validating invalid document type."""
        with self.assertRaises(ValidationError) as context:
            self.validator.validate_document_type("invalid_type")
        
        error = context.exception
        self.assertEqual(error.field_name, "document_type")
    
    def test_validate_config_value_valid(self):
        """Test validating valid configuration value."""
        result = self.validator.validate_config_value("timeout", 30, int, min_value=5, max_value=120)
        
        self.assertTrue(result["valid"])
        self.assertEqual(result["value"], 30)
        self.assertEqual(result["type"], "int")
    
    def test_validate_config_value_wrong_type(self):
        """Test validating config value with wrong type."""
        with self.assertRaises(ValidationError) as context:
            self.validator.validate_config_value("timeout", "30", int)
        
        error = context.exception
        self.assertEqual(error.validation_rule, "type_int")
    
    def test_validate_config_value_out_of_range(self):
        """Test validating config value out of range."""
        with self.assertRaises(ValidationError) as context:
            self.validator.validate_config_value("timeout", 200, int, min_value=5, max_value=120)
        
        error = context.exception
        self.assertEqual(error.validation_rule, "max_120")
    
    def test_validate_output_directory_with_temp(self):
        """Test validating output directory using temporary directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.validator.validate_output_directory(temp_dir)
            
            self.assertTrue(result["valid"])
            self.assertTrue(result["exists"])
            self.assertTrue(result["writable"])
    
    def test_validate_output_directory_create_missing(self):
        """Test validating output directory with creation of missing directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = os.path.join(temp_dir, "new_directory")
            
            result = self.validator.validate_output_directory(new_dir, create_if_missing=True)
            
            self.assertTrue(result["valid"])
            self.assertTrue(os.path.exists(new_dir))
    
    @patch('fitz.open')
    def test_validate_pdf_file_valid(self, mock_fitz_open):
        """Test validating valid PDF file."""
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Mock PyMuPDF document
            mock_doc = Mock()
            mock_doc.page_count = 5
            mock_fitz_open.return_value = mock_doc
            
            result = self.validator.validate_pdf_file(temp_path)
            
            self.assertTrue(result["valid"])
            self.assertEqual(result["page_count"], 5)
            self.assertTrue(result["size_bytes"] >= 0)
        finally:
            os.unlink(temp_path)
    
    def test_validate_pdf_file_not_found(self):
        """Test validating non-existent PDF file."""
        with self.assertRaises(Exception) as context:
            self.validator.validate_pdf_file("/nonexistent/file.pdf")
        
        # Should raise either FileSystemError or ValidationError
        self.assertIn("Error", str(type(context.exception)))
    
    def test_validate_pdf_file_wrong_extension(self):
        """Test validating file with wrong extension."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            with self.assertRaises(ValidationError) as context:
                self.validator.validate_pdf_file(temp_path)
            
            error = context.exception
            self.assertEqual(error.validation_rule, "must_be_pdf")
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()