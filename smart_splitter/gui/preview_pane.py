"""
Preview pane component for the Smart-Splitter GUI.

This module provides a preview of document pages with editing controls
for document type and filename modification.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
from PIL import Image
try:
    from PIL import ImageTk
    IMAGETK_AVAILABLE = True
except ImportError:
    IMAGETK_AVAILABLE = False
    print("Warning: ImageTk not available. Install with: sudo apt-get install python3-pil.imagetk")
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
        self.current_page_index = 0  # Track current page within document
        self.pdf_doc = None  # Keep PDF document open for navigation
        
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
        
        # Navigation controls for multi-page documents
        nav_frame = ttk.Frame(preview_frame)
        nav_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.prev_button = ttk.Button(nav_frame, text="◀ Previous", command=self._prev_page, state='disabled')
        self.prev_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.page_label = ttk.Label(nav_frame, text="Page 1 of 1")
        self.page_label.pack(side=tk.LEFT, padx=10)
        
        self.next_button = ttk.Button(nav_frame, text="Next ▶", command=self._next_page, state='disabled')
        self.next_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Page number entry for direct navigation
        ttk.Label(nav_frame, text="Go to page:").pack(side=tk.LEFT, padx=(20, 5))
        self.page_var = tk.StringVar(value="1")
        self.page_entry = ttk.Entry(nav_frame, textvariable=self.page_var, width=5)
        self.page_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.page_entry.bind('<Return>', self._on_page_entry)
        
        ttk.Button(nav_frame, text="Go", command=self._go_to_page).pack(side=tk.LEFT)
        
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
        
        # Bind resize event
        self.canvas.bind('<Configure>', self._on_canvas_resize)
    
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
        # Close previous PDF if open
        if self.pdf_doc:
            self.pdf_doc.close()
            self.pdf_doc = None
            
        self.current_document = document
        self.current_pdf_path = pdf_path
        self.current_page_index = 0  # Reset to first page of document
        
        # Open PDF for navigation
        try:
            self.pdf_doc = fitz.open(pdf_path)
        except Exception as e:
            print(f"Error opening PDF: {e}")
            self.pdf_doc = None
        
        # Update controls
        self._update_controls()
        self._update_navigation_controls()
        
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
        if not self.current_document or not self.pdf_doc:
            self._show_no_preview()
            return
        
        if not IMAGETK_AVAILABLE:
            self._show_no_preview()
            self.no_preview_label.config(text="Preview unavailable\n(ImageTk not installed)")
            return
        
        try:
            # Calculate actual page number in PDF
            page_num = (self.current_document.start_page - 1) + self.current_page_index
            
            if page_num < len(self.pdf_doc) and page_num <= self.current_document.end_page - 1:
                page = self.pdf_doc[page_num]
                
                # Get canvas dimensions
                self.canvas.update_idletasks()  # Ensure canvas has updated dimensions
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                
                # Ensure minimum dimensions
                if canvas_width < 100:
                    canvas_width = 600
                if canvas_height < 100:
                    canvas_height = 400
                
                # Calculate scale to fit canvas while maintaining aspect ratio
                page_rect = page.rect
                page_width = page_rect.width
                page_height = page_rect.height
                
                # Calculate scale factors
                scale_x = (canvas_width - 20) / page_width  # Leave 10px margin on each side
                scale_y = (canvas_height - 20) / page_height
                scale = min(scale_x, scale_y)  # Use smaller scale to fit both dimensions
                
                # Ensure reasonable scale
                scale = max(scale, 0.5)  # Minimum 50% scale
                scale = min(scale, 3.0)  # Maximum 300% scale
                
                # Render page as image with calculated scale
                mat = fitz.Matrix(scale, scale)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("ppm")
                
                # Convert to PIL Image
                pil_image = Image.open(io.BytesIO(img_data))
                
                # Convert to PhotoImage
                self.preview_image = ImageTk.PhotoImage(pil_image)
                
                # Clear canvas and display image centered
                self.canvas.delete("all")
                img_width = pil_image.width
                img_height = pil_image.height
                x = max(10, (canvas_width - img_width) // 2)
                y = max(10, (canvas_height - img_height) // 2)
                self.canvas.create_image(x, y, anchor=tk.NW, image=self.preview_image)
                
                # Update scroll region
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))
                
                # Update page label
                current_page = self.current_page_index + 1
                total_pages = self.current_document.page_count
                self.page_label.config(text=f"Page {current_page} of {total_pages}")
                self.page_var.set(str(current_page))
            
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
        # Close PDF if open
        if self.pdf_doc:
            self.pdf_doc.close()
            self.pdf_doc = None
            
        self.current_document = None
        self.current_pdf_path = None
        self.current_page_index = 0
        
        # Clear controls
        self.type_var.set("")
        self.filename_var.set("")
        self.pages_label.config(text="N/A")
        self.confidence_label.config(text="N/A")
        
        # Clear navigation
        self._update_navigation_controls()
        
        # Clear preview
        self._show_no_preview()
    
    def _on_canvas_resize(self, event=None) -> None:
        """Handle canvas resize events."""
        # Only update preview if we have a document and the canvas size has changed significantly
        if self.current_document and self.current_pdf_path:
            # Debounce resize events by scheduling update
            if hasattr(self, '_resize_after_id'):
                self.after_cancel(self._resize_after_id)
            self._resize_after_id = self.after(100, self._update_preview_image)
    
    def _update_navigation_controls(self) -> None:
        """Update the state of navigation controls."""
        if not self.current_document:
            self.prev_button.config(state='disabled')
            self.next_button.config(state='disabled')
            self.page_entry.config(state='disabled')
            self.page_label.config(text="Page 1 of 1")
            return
        
        total_pages = self.current_document.page_count
        current_page = self.current_page_index + 1
        
        # Update button states
        self.prev_button.config(state='normal' if current_page > 1 else 'disabled')
        self.next_button.config(state='normal' if current_page < total_pages else 'disabled')
        self.page_entry.config(state='normal' if total_pages > 1 else 'disabled')
        
        # Update page label
        self.page_label.config(text=f"Page {current_page} of {total_pages}")
        self.page_var.set(str(current_page))
    
    def _prev_page(self) -> None:
        """Navigate to the previous page."""
        if self.current_page_index > 0:
            self.current_page_index -= 1
            self._update_navigation_controls()
            self._update_preview_image()
    
    def _next_page(self) -> None:
        """Navigate to the next page."""
        if self.current_document and self.current_page_index < self.current_document.page_count - 1:
            self.current_page_index += 1
            self._update_navigation_controls()
            self._update_preview_image()
    
    def _go_to_page(self) -> None:
        """Go to a specific page number."""
        if not self.current_document:
            return
        
        try:
            page_num = int(self.page_var.get())
            if 1 <= page_num <= self.current_document.page_count:
                self.current_page_index = page_num - 1
                self._update_navigation_controls()
                self._update_preview_image()
            else:
                # Reset to current page if invalid
                self.page_var.set(str(self.current_page_index + 1))
        except ValueError:
            # Reset to current page if invalid
            self.page_var.set(str(self.current_page_index + 1))
    
    def _on_page_entry(self, event=None) -> None:
        """Handle Enter key in page entry."""
        self._go_to_page()