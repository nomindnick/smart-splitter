"""
Export module for Smart-Splitter application.

This module provides PDF export functionality for splitting and saving
individual documents from processed multi-document PDFs.
"""

from .exporter import PDFExporter
from .data_models import ExportResult, ExportConfig

__all__ = [
    'PDFExporter',
    'ExportResult',
    'ExportConfig'
]

__version__ = "0.3.0"