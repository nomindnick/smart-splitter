"""
Smart-Splitter: Intelligent PDF Document Splitting System

A comprehensive system for analyzing multi-document PDFs, detecting boundaries,
classifying document types, and splitting them into individual files with
intelligent naming - specifically designed for construction legal disputes.
"""

__version__ = "0.3.0"
__author__ = "Smart-Splitter Development Team"

# Core functionality available for import
try:
    from .processing import PDFProcessor, BoundaryDetector
    from .classification import DocumentClassifier
    from .naming import FileNameGenerator
    from .config import ConfigurationManager
    from .export import PDFExporter
    from .gui import SmartSplitterGUI
    
    __all__ = [
        'PDFProcessor',
        'BoundaryDetector', 
        'DocumentClassifier',
        'FileNameGenerator',
        'ConfigurationManager',
        'PDFExporter',
        'SmartSplitterGUI'
    ]
except ImportError:
    # Allow partial imports for testing
    __all__ = []