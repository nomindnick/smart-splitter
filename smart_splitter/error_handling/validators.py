"""Input validation utilities for Smart-Splitter."""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import fitz

from .exceptions import ValidationError, FileSystemError


class InputValidator:
    """Validates user inputs and system requirements."""
    
    @staticmethod
    def validate_pdf_file(file_path: str) -> Dict[str, Any]:
        """Validate PDF file and return file information."""
        if not file_path:
            raise ValidationError("PDF file path cannot be empty", field_name="file_path")
        
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            raise FileSystemError(f"PDF file not found: {file_path}", 
                                 file_path=file_path, operation="read")
        
        # Check if it's a file (not directory)
        if not path.is_file():
            raise ValidationError(f"Path is not a file: {file_path}", 
                                field_name="file_path", field_value=file_path)
        
        # Check file extension
        if path.suffix.lower() != '.pdf':
            raise ValidationError(f"File must be a PDF: {file_path}", 
                                field_name="file_path", field_value=file_path,
                                validation_rule="must_be_pdf")
        
        # Check file size (max 500MB)
        file_size = path.stat().st_size
        max_size = 500 * 1024 * 1024  # 500MB
        
        if file_size > max_size:
            raise ValidationError(f"PDF file too large: {file_size / 1024 / 1024:.1f}MB (max 500MB)",
                                field_name="file_size", field_value=file_size,
                                validation_rule="max_500mb")
        
        # Try to open with PyMuPDF to validate PDF structure
        try:
            doc = fitz.open(file_path)
            page_count = doc.page_count
            doc.close()
            
            if page_count == 0:
                raise ValidationError(f"PDF has no pages: {file_path}",
                                    field_name="page_count", field_value=0,
                                    validation_rule="min_1_page")
        
        except Exception as e:
            raise ValidationError(f"Invalid or corrupted PDF: {str(e)}",
                                field_name="pdf_structure", field_value=file_path,
                                validation_rule="valid_pdf_structure")
        
        return {
            "path": str(path.absolute()),
            "size_bytes": file_size,
            "size_mb": file_size / 1024 / 1024,
            "page_count": page_count,
            "valid": True
        }
    
    @staticmethod
    def validate_output_directory(directory_path: str, create_if_missing: bool = True) -> Dict[str, Any]:
        """Validate output directory for exports."""
        if not directory_path:
            raise ValidationError("Output directory path cannot be empty", 
                                field_name="output_directory")
        
        path = Path(directory_path).expanduser().resolve()
        
        # Check if parent directory exists
        if not path.parent.exists():
            raise FileSystemError(f"Parent directory does not exist: {path.parent}",
                                 file_path=str(path.parent), operation="access")
        
        # Create directory if it doesn't exist
        if not path.exists():
            if create_if_missing:
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    raise FileSystemError(f"Permission denied creating directory: {path}",
                                        file_path=str(path), operation="create")
                except Exception as e:
                    raise FileSystemError(f"Failed to create directory: {str(e)}",
                                        file_path=str(path), operation="create")
            else:
                raise FileSystemError(f"Output directory does not exist: {path}",
                                    file_path=str(path), operation="access")
        
        # Check if it's a directory
        if not path.is_dir():
            raise ValidationError(f"Path is not a directory: {path}",
                                field_name="output_directory", field_value=str(path),
                                validation_rule="must_be_directory")
        
        # Check write permissions
        if not os.access(path, os.W_OK):
            raise FileSystemError(f"No write permission for directory: {path}",
                                file_path=str(path), operation="write")
        
        # Check available disk space (at least 100MB)
        try:
            statvfs = os.statvfs(path)
            available_bytes = statvfs.f_frsize * statvfs.f_bavail
            available_mb = available_bytes / 1024 / 1024
            
            if available_mb < 100:
                raise FileSystemError(f"Insufficient disk space: {available_mb:.1f}MB available (min 100MB)",
                                    file_path=str(path), operation="write")
        except:
            # Skip disk space check if not supported
            available_mb = None
        
        return {
            "path": str(path),
            "exists": True,
            "writable": True,
            "available_space_mb": available_mb,
            "valid": True
        }
    
    @staticmethod
    def validate_filename(filename: str, max_length: int = 200) -> Dict[str, Any]:
        """Validate filename for export."""
        if not filename:
            raise ValidationError("Filename cannot be empty", field_name="filename")
        
        # Remove or replace invalid characters
        invalid_chars = r'[<>:"/\\|?*]'
        if re.search(invalid_chars, filename):
            raise ValidationError(f"Filename contains invalid characters: {filename}",
                                field_name="filename", field_value=filename,
                                validation_rule="no_invalid_chars")
        
        # Check length
        if len(filename) > max_length:
            raise ValidationError(f"Filename too long: {len(filename)} chars (max {max_length})",
                                field_name="filename", field_value=filename,
                                validation_rule=f"max_{max_length}_chars")
        
        # Check for reserved names (Windows)
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5',
            'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4',
            'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        
        base_name = Path(filename).stem.upper()
        if base_name in reserved_names:
            raise ValidationError(f"Filename uses reserved name: {filename}",
                                field_name="filename", field_value=filename,
                                validation_rule="no_reserved_names")
        
        return {
            "filename": filename,
            "length": len(filename),
            "valid": True
        }
    
    @staticmethod
    def validate_page_range(start_page: int, end_page: int, total_pages: int) -> Dict[str, Any]:
        """Validate page range for document sections."""
        # Check types
        if not isinstance(start_page, int) or not isinstance(end_page, int):
            raise ValidationError("Page numbers must be integers",
                                field_name="page_range", 
                                validation_rule="must_be_integers")
        
        # Check minimum values
        if start_page < 1:
            raise ValidationError(f"Start page must be >= 1: {start_page}",
                                field_name="start_page", field_value=start_page,
                                validation_rule="min_page_1")
        
        if end_page < 1:
            raise ValidationError(f"End page must be >= 1: {end_page}",
                                field_name="end_page", field_value=end_page,
                                validation_rule="min_page_1")
        
        # Check logical relationship
        if start_page > end_page:
            raise ValidationError(f"Start page ({start_page}) cannot be greater than end page ({end_page})",
                                field_name="page_range", 
                                field_value=f"{start_page}-{end_page}",
                                validation_rule="start_before_end")
        
        # Check against total pages
        if start_page > total_pages:
            raise ValidationError(f"Start page ({start_page}) exceeds total pages ({total_pages})",
                                field_name="start_page", field_value=start_page,
                                validation_rule=f"max_page_{total_pages}")
        
        if end_page > total_pages:
            raise ValidationError(f"End page ({end_page}) exceeds total pages ({total_pages})",
                                field_name="end_page", field_value=end_page,
                                validation_rule=f"max_page_{total_pages}")
        
        return {
            "start_page": start_page,
            "end_page": end_page,
            "page_count": end_page - start_page + 1,
            "valid": True
        }
    
    @staticmethod
    def validate_api_key(api_key: str, api_name: str = "OpenAI") -> Dict[str, Any]:
        """Validate API key format."""
        if not api_key:
            raise ValidationError(f"{api_name} API key cannot be empty",
                                field_name="api_key", validation_rule="not_empty")
        
        # Basic format validation for OpenAI keys
        if api_name.lower() == "openai":
            if not api_key.startswith("sk-"):
                raise ValidationError("OpenAI API key must start with 'sk-'",
                                    field_name="api_key", field_value="sk-...",
                                    validation_rule="openai_format")
            
            if len(api_key) < 20:
                raise ValidationError("OpenAI API key too short",
                                    field_name="api_key", 
                                    validation_rule="min_length_20")
        
        return {
            "api_key": api_key[:10] + "..." if len(api_key) > 10 else api_key,
            "api_name": api_name,
            "length": len(api_key),
            "valid": True
        }
    
    @staticmethod
    def validate_document_type(document_type: str, allowed_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Validate document type."""
        if not document_type:
            raise ValidationError("Document type cannot be empty",
                                field_name="document_type")
        
        # Default allowed types
        if allowed_types is None:
            allowed_types = [
                "email", "letter", "payment_application", "evidence_of_payment",
                "change_order", "change_order_response", "rfi", "rfi_response",
                "inspection_report", "contract_document", "plans_specifications", "other"
            ]
        
        if document_type not in allowed_types:
            raise ValidationError(f"Invalid document type: {document_type}",
                                field_name="document_type", field_value=document_type,
                                validation_rule=f"must_be_one_of_{allowed_types}")
        
        return {
            "document_type": document_type,
            "valid": True
        }
    
    @staticmethod
    def validate_config_value(key: str, value: Any, expected_type: type, 
                            min_value: Optional[Union[int, float]] = None,
                            max_value: Optional[Union[int, float]] = None) -> Dict[str, Any]:
        """Validate configuration value."""
        # Type validation
        if not isinstance(value, expected_type):
            raise ValidationError(f"Config {key} must be {expected_type.__name__}: {type(value).__name__}",
                                field_name=key, field_value=str(value),
                                validation_rule=f"type_{expected_type.__name__}")
        
        # Range validation for numeric types
        if isinstance(value, (int, float)):
            if min_value is not None and value < min_value:
                raise ValidationError(f"Config {key} must be >= {min_value}: {value}",
                                    field_name=key, field_value=value,
                                    validation_rule=f"min_{min_value}")
            
            if max_value is not None and value > max_value:
                raise ValidationError(f"Config {key} must be <= {max_value}: {value}",
                                    field_name=key, field_value=value,
                                    validation_rule=f"max_{max_value}")
        
        return {
            "key": key,
            "value": value,
            "type": expected_type.__name__,
            "valid": True
        }