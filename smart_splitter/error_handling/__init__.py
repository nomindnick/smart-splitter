"""Enhanced error handling and recovery system for Smart-Splitter."""

from .exceptions import (
    SmartSplitterError,
    PDFProcessingError,
    ClassificationError,
    ExportError,
    ConfigurationError,
    MemoryError as SmartSplitterMemoryError,
    ValidationError
)
from .handlers import ErrorHandler, RecoveryManager
from .validators import InputValidator

__all__ = [
    'SmartSplitterError',
    'PDFProcessingError', 
    'ClassificationError',
    'ExportError',
    'ConfigurationError',
    'SmartSplitterMemoryError',
    'ValidationError',
    'ErrorHandler',
    'RecoveryManager',
    'InputValidator'
]