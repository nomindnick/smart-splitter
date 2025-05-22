"""
Document list view component for the Smart-Splitter GUI.

This module provides a scrollable list of detected documents with
checkboxes for selection and basic document information display.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Optional

from .data_models import DocumentSection


class DocumentListView(ttk.Frame):
    """Scrollable list view for displaying detected documents."""
    
    def __init__(self, parent, selection_callback: Optional[Callable[[int], None]] = None):
        """
        Initialize the document list view.
        
        Args:
            parent: Parent tkinter widget
            selection_callback: Function to call when a document is selected
        """
        super().__init__(parent)
        self.selection_callback = selection_callback
        self.documents: List[DocumentSection] = []
        self.current_selection = -1
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the user interface components."""
        # Create main frame with scrollbar
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview for document list
        columns = ('select', 'filename', 'type', 'pages', 'confidence')
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show='headings', height=12)
        
        # Configure column headings
        self.tree.heading('select', text='✓')
        self.tree.heading('filename', text='Filename')
        self.tree.heading('type', text='Type')
        self.tree.heading('pages', text='Pages')
        self.tree.heading('confidence', text='Confidence')
        
        # Configure column widths
        self.tree.column('select', width=30, minwidth=30, anchor='center')
        self.tree.column('filename', width=200, minwidth=150)
        self.tree.column('type', width=120, minwidth=100)
        self.tree.column('pages', width=80, minwidth=60, anchor='center')
        self.tree.column('confidence', width=80, minwidth=60, anchor='center')
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self._on_selection_changed)
        self.tree.bind('<Button-1>', self._on_click)
        
        # Add control buttons
        self._setup_control_buttons()
    
    def _setup_control_buttons(self) -> None:
        """Set up control buttons for bulk operations."""
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(button_frame, text="Select All", 
                  command=self._select_all).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Select None", 
                  command=self._select_none).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Invert Selection", 
                  command=self._invert_selection).pack(side=tk.LEFT)
    
    def _on_click(self, event) -> None:
        """Handle click events on the treeview."""
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x, event.y)
            if column == '#1':  # Select column
                item = self.tree.identify_row(event.y)
                if item:
                    self._toggle_selection(item)
    
    def _toggle_selection(self, item_id: str) -> None:
        """Toggle the selection state of a document."""
        try:
            index = int(item_id) - 1  # Convert to 0-based index
            if 0 <= index < len(self.documents):
                self.documents[index].selected = not self.documents[index].selected
                self._update_item_display(item_id, index)
        except (ValueError, IndexError):
            pass
    
    def _update_item_display(self, item_id: str, index: int) -> None:
        """Update the display of a single item."""
        doc = self.documents[index]
        values = (
            '✓' if doc.selected else '',
            doc.filename,
            doc.document_type.replace('_', ' ').title(),
            doc.page_range_str,
            doc.confidence_str
        )
        self.tree.item(item_id, values=values)
    
    def _on_selection_changed(self, event) -> None:
        """Handle treeview selection changes."""
        selection = self.tree.selection()
        if selection and self.selection_callback:
            try:
                index = int(selection[0]) - 1  # Convert to 0-based index
                if 0 <= index < len(self.documents):
                    self.current_selection = index
                    self.selection_callback(index)
            except (ValueError, IndexError):
                pass
    
    def _select_all(self) -> None:
        """Select all documents."""
        for doc in self.documents:
            doc.selected = True
        self._refresh_display()
    
    def _select_none(self) -> None:
        """Deselect all documents."""
        for doc in self.documents:
            doc.selected = False
        self._refresh_display()
    
    def _invert_selection(self) -> None:
        """Invert the selection state of all documents."""
        for doc in self.documents:
            doc.selected = not doc.selected
        self._refresh_display()
    
    def populate_documents(self, documents: List[DocumentSection]) -> None:
        """
        Populate the list with document sections.
        
        Args:
            documents: List of document sections to display
        """
        self.documents = documents
        self._refresh_display()
    
    def _refresh_display(self) -> None:
        """Refresh the entire display."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add documents
        for i, doc in enumerate(self.documents):
            values = (
                '✓' if doc.selected else '',
                doc.filename,
                doc.document_type.replace('_', ' ').title(),
                doc.page_range_str,
                doc.confidence_str
            )
            self.tree.insert('', 'end', iid=str(i + 1), values=values)
    
    def get_selected_documents(self) -> List[DocumentSection]:
        """
        Get all currently selected documents.
        
        Returns:
            List of selected document sections
        """
        return [doc for doc in self.documents if doc.selected]
    
    def get_current_document(self) -> Optional[DocumentSection]:
        """
        Get the currently highlighted document.
        
        Returns:
            The currently selected document or None
        """
        if 0 <= self.current_selection < len(self.documents):
            return self.documents[self.current_selection]
        return None
    
    def update_document(self, index: int, updated_doc: DocumentSection) -> None:
        """
        Update a specific document in the list.
        
        Args:
            index: Index of the document to update
            updated_doc: Updated document section
        """
        if 0 <= index < len(self.documents):
            self.documents[index] = updated_doc
            item_id = str(index + 1)
            self._update_item_display(item_id, index)