"""Custom exceptions for Smart-Splitter application."""

from typing import Optional, Dict, Any


class SmartSplitterError(Exception):
    """Base exception for Smart-Splitter application."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/reporting."""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


class PDFProcessingError(SmartSplitterError):
    """Raised when PDF processing operations fail."""
    
    def __init__(self, message: str, pdf_path: Optional[str] = None, 
                 page_number: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.pdf_path = pdf_path
        self.page_number = page_number
        if pdf_path:
            self.details["pdf_path"] = pdf_path
        if page_number is not None:
            self.details["page_number"] = page_number


class ClassificationError(SmartSplitterError):
    """Raised when document classification fails."""
    
    def __init__(self, message: str, document_text: Optional[str] = None,
                 classification_attempt: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.document_text = document_text
        self.classification_attempt = classification_attempt
        if document_text:
            self.details["text_sample"] = document_text[:200]  # First 200 chars
        if classification_attempt:
            self.details["attempted_classification"] = classification_attempt


class ExportError(SmartSplitterError):
    """Raised when document export operations fail."""
    
    def __init__(self, message: str, output_path: Optional[str] = None,
                 page_range: Optional[tuple] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.output_path = output_path
        self.page_range = page_range
        if output_path:
            self.details["output_path"] = output_path
        if page_range:
            self.details["page_range"] = page_range


class ConfigurationError(SmartSplitterError):
    """Raised when configuration-related errors occur."""
    
    def __init__(self, message: str, config_key: Optional[str] = None,
                 config_value: Optional[Any] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.config_key = config_key
        self.config_value = config_value
        if config_key:
            self.details["config_key"] = config_key
        if config_value is not None:
            self.details["config_value"] = str(config_value)


class MemoryError(SmartSplitterError):
    """Raised when memory-related errors occur."""
    
    def __init__(self, message: str, current_memory: Optional[float] = None,
                 max_memory: Optional[float] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.current_memory = current_memory
        self.max_memory = max_memory
        if current_memory is not None:
            self.details["current_memory_mb"] = current_memory
        if max_memory is not None:
            self.details["max_memory_mb"] = max_memory


class ValidationError(SmartSplitterError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field_name: Optional[str] = None,
                 field_value: Optional[Any] = None, validation_rule: Optional[str] = None,
                 **kwargs):
        super().__init__(message, **kwargs)
        self.field_name = field_name
        self.field_value = field_value
        self.validation_rule = validation_rule
        
        if field_name:
            self.details["field_name"] = field_name
        if field_value is not None:
            self.details["field_value"] = str(field_value)
        if validation_rule:
            self.details["validation_rule"] = validation_rule


class APIError(SmartSplitterError):
    """Raised when external API calls fail."""
    
    def __init__(self, message: str, api_name: Optional[str] = None,
                 status_code: Optional[int] = None, response_data: Optional[str] = None,
                 **kwargs):
        super().__init__(message, **kwargs)
        self.api_name = api_name
        self.status_code = status_code
        self.response_data = response_data
        
        if api_name:
            self.details["api_name"] = api_name
        if status_code is not None:
            self.details["status_code"] = status_code
        if response_data:
            self.details["response_data"] = response_data[:500]  # Limit response data


class FileSystemError(SmartSplitterError):
    """Raised when file system operations fail."""
    
    def __init__(self, message: str, file_path: Optional[str] = None,
                 operation: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.file_path = file_path
        self.operation = operation
        
        if file_path:
            self.details["file_path"] = file_path
        if operation:
            self.details["operation"] = operation


class GUIError(SmartSplitterError):
    """Raised when GUI-related errors occur."""
    
    def __init__(self, message: str, component: Optional[str] = None,
                 action: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.component = component
        self.action = action
        
        if component:
            self.details["component"] = component
        if action:
            self.details["action"] = action