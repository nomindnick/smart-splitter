"""
GUI module for Smart-Splitter application.

This module provides the tkinter-based graphical user interface for document
review, editing, and export functionality.
"""

from .main_window import SmartSplitterGUI
from .document_list import DocumentListView
from .preview_pane import PreviewPane
from .data_models import DocumentSection

__all__ = [
    'SmartSplitterGUI',
    'DocumentListView', 
    'PreviewPane',
    'DocumentSection'
]

__version__ = "0.3.0"