"""
Preview pane component for the Smart-Splitter GUI.

This module provides a preview of document pages with editing controls
for document type and filename modification.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
from PIL import Image, ImageTk
import fitz  # PyMuPDF
import io

from .data_models import DocumentSection


class PreviewPane(ttk.Frame):
    """Preview pane for displaying document pages and editing controls."""
    
    DOCUMENT_TYPES = [
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
    
    def __init__(self, parent, update_callback: Optional[Callable[[DocumentSection], None]] = None):
        """
        Initialize the preview pane.
        
        Args:
            parent: Parent tkinter widget
            update_callback: Function to call when document is updated
        """
        super().__init__(parent)
        self.update_callback = update_callback
        self.current_document: Optional[DocumentSection] = None
        self.current_pdf_path: Optional[str] = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the user interface components."""
        # Preview area
        self._setup_preview_area()
        
        # Control area
        self._setup_controls()
    
    def _setup_preview_area(self) -> None:
        """Set up the document preview area."""
        preview_frame = ttk.LabelFrame(self, text="Page Preview", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create canvas for image display
        self.canvas = tk.Canvas(preview_frame, bg='white', relief=tk.SUNKEN, bd=2)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars for canvas
        h_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        v_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        # No preview message
        self.no_preview_label = tk.Label(self.canvas, text="No document selected", 
                                        bg='white', fg='gray')
        self.canvas.create_window(150, 100, window=self.no_preview_label)
    
    def _setup_controls(self) -> None:
        """Set up the editing controls."""
        controls_frame = ttk.LabelFrame(self, text="Document Details", padding=10)
        controls_frame.pack(fill=tk.X)
        
        # Document type selection
        ttk.Label(controls_frame, text="Document Type:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(controls_frame, textvariable=self.type_var, 
                                      values=[t.replace('_', ' ').title() for t in self.DOCUMENT_TYPES],
                                      state='readonly', width=25)
        self.type_combo.grid(row=0, column=1, sticky=tk.W+tk.E, padx=(10, 0), pady=2)
        self.type_combo.bind('<<ComboboxSelected>>', self._on_type_changed)
        
        # Filename entry
        ttk.Label(controls_frame, text="Filename:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.filename_var = tk.StringVar()
        self.filename_entry = ttk.Entry(controls_frame, textvariable=self.filename_var, width=30)
        self.filename_entry.grid(row=1, column=1, sticky=tk.W+tk.E, padx=(10, 0), pady=2)
        self.filename_entry.bind('<KeyRelease>', self._on_filename_changed)
        
        # Page range display
        ttk.Label(controls_frame, text="Pages:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.pages_label = ttk.Label(controls_frame, text="N/A")
        self.pages_label.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Confidence display
        ttk.Label(controls_frame, text="Confidence:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.confidence_label = ttk.Label(controls_frame, text="N/A")
        self.confidence_label.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Control buttons
        button_frame = ttk.Frame(controls_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(button_frame, text="Update", 
                  command=self._apply_changes).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Reset", 
                  command=self._reset_changes).pack(side=tk.LEFT)
        
        # Configure grid weights
        controls_frame.columnconfigure(1, weight=1)
    
    def show_preview(self, document: DocumentSection, pdf_path: str) -> None:
        """
        Show preview for the given document section.
        
        Args:
            document: Document section to preview
            pdf_path: Path to the source PDF file
        """
        self.current_document = document
        self.current_pdf_path = pdf_path
        
        # Update controls
        self._update_controls()
        
        # Update preview image
        self._update_preview_image()
    
    def _update_controls(self) -> None:
        """Update the control widgets with current document data."""
        if not self.current_document:
            return
        
        doc = self.current_document
        
        # Set document type
        display_type = doc.document_type.replace('_', ' ').title()
        self.type_var.set(display_type)
        
        # Set filename
        self.filename_var.set(doc.filename)
        
        # Set page range
        self.pages_label.config(text=doc.page_range_str)
        
        # Set confidence
        self.confidence_label.config(text=doc.confidence_str)
    
    def _update_preview_image(self) -> None:
        """Update the preview image."""
        if not self.current_document or not self.current_pdf_path:
            self._show_no_preview()
            return
        
        try:
            # Open PDF and get first page of document
            pdf_doc = fitz.open(self.current_pdf_path)
            page_num = self.current_document.start_page - 1  # Convert to 0-based
            
            if page_num < len(pdf_doc):
                page = pdf_doc[page_num]
                
                # Render page as image
                mat = fitz.Matrix(1.5, 1.5)  # Scale factor for better quality
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("ppm")
                
                # Convert to PIL Image
                pil_image = Image.open(io.BytesIO(img_data))
                
                # Scale image to fit preview area
                preview_width = 300
                preview_height = int(pil_image.height * preview_width / pil_image.width)
                pil_image = pil_image.resize((preview_width, preview_height), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                self.preview_image = ImageTk.PhotoImage(pil_image)
                
                # Clear canvas and display image
                self.canvas.delete("all")
                self.canvas.create_image(10, 10, anchor=tk.NW, image=self.preview_image)
                
                # Update scroll region
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))
                
            pdf_doc.close()
            
        except Exception as e:
            print(f"Error loading preview: {e}")
            self._show_no_preview()
    
    def _show_no_preview(self) -> None:
        """Show the no preview message."""
        self.canvas.delete("all")
        self.canvas.create_window(150, 100, window=self.no_preview_label)
    
    def _on_type_changed(self, event=None) -> None:
        """Handle document type selection change."""
        # Note: Changes are not applied until Update button is clicked
        pass
    
    def _on_filename_changed(self, event=None) -> None:
        """Handle filename entry change."""
        # Note: Changes are not applied until Update button is clicked
        pass
    
    def _apply_changes(self) -> None:
        """Apply the current control values to the document."""
        if not self.current_document:
            return
        
        # Get values from controls
        display_type = self.type_var.get()
        new_type = display_type.lower().replace(' ', '_')
        new_filename = self.filename_var.get().strip()
        
        # Validate filename
        if not new_filename:
            messagebox.showerror("Error", "Filename cannot be empty")
            return
        
        # Update document
        self.current_document.document_type = new_type
        self.current_document.filename = new_filename
        
        # Notify callback
        if self.update_callback:
            self.update_callback(self.current_document)
    
    def _reset_changes(self) -> None:
        """Reset controls to original document values."""
        if self.current_document:
            self._update_controls()
    
    def clear_preview(self) -> None:
        """Clear the preview and reset controls."""
        self.current_document = None
        self.current_pdf_path = None
        
        # Clear controls
        self.type_var.set("")
        self.filename_var.set("")
        self.pages_label.config(text="N/A")
        self.confidence_label.config(text="N/A")
        
        # Clear preview
        self._show_no_preview()