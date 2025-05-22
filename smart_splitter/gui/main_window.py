"""
Main GUI window for the Smart-Splitter application.

This module provides the main application window that coordinates
all GUI components and handles the overall workflow.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path
from typing import List, Optional
import logging

from .document_list import DocumentListView
from .preview_pane import PreviewPane
from .data_models import DocumentSection
from ..pdf_processing.processor import PDFProcessor
from ..boundary_detection.detector import BoundaryDetector
from ..classification.classifier import DocumentClassifier
from ..naming.generator import FileNameGenerator
from ..export.exporter import PDFExporter
from ..export.data_models import ExportConfig
from ..config.manager import ConfigManager
from ..performance.monitor import global_monitor, monitor_performance
from ..performance.optimizer import ProcessingOptimizer
from ..error_handling.handlers import global_error_handler
from ..error_handling.exceptions import GUIError, PDFProcessingError


logger = logging.getLogger(__name__)


class SmartSplitterGUI:
    """Main GUI application window."""
    
    def __init__(self):
        """Initialize the Smart-Splitter GUI."""
        self.root = tk.Tk()
        self.root.title("Smart-Splitter - Construction Document PDF Splitter")
        self.root.geometry("1200x800")
        
        # Application state
        self.current_pdf_path: Optional[str] = None
        self.documents: List[DocumentSection] = []
        self.processing = False
        
        # Initialize components
        self._initialize_components()
        
        # Set up UI
        self._setup_ui()
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
    
    def _initialize_components(self) -> None:
        """Initialize the processing components."""
        try:
            # Load configuration
            self.config_manager = ConfigManager()
            self.config = self.config_manager.config
            
            # Initialize processing components
            self.pdf_processor = PDFProcessor()
            # Pass the ConfigManager instance instead of dictionary
            self.boundary_detector = BoundaryDetector(self.config_manager)
            
            # Create ClassificationConfig from configuration
            from ..classification.data_models import ClassificationConfig
            # Get API settings and processing settings for classification
            api_config = self.config.get('patterns', {}).get('api', {})
            processing_config = self.config.get('processing', {})
            classification_rules = self.config.get('patterns', {}).get('classification_rules', {})
            
            classification_config = ClassificationConfig(
                api_model=api_config.get('model', 'gpt-4o-mini'),
                max_input_chars=processing_config.get('max_input_chars', 1000),
                confidence_threshold=processing_config.get('confidence_threshold', 0.7),
                rule_patterns=classification_rules,
                api_temperature=api_config.get('temperature', 0.0),
                max_output_tokens=api_config.get('max_tokens', 10),
                api_timeout=api_config.get('timeout', 10)
            )
            self.classifier = DocumentClassifier(
                classification_config,
                api_key=self.config.get('api', {}).get('openai_api_key', '')
            )
            
            from ..naming.data_models import NamingConfig
            naming_config_dict = self.config.get('patterns', {}).get('naming', {})
            # Map 'templates' to 'custom_templates' if present
            if 'templates' in naming_config_dict:
                naming_config_dict['custom_templates'] = naming_config_dict.pop('templates')
            naming_config = NamingConfig(**naming_config_dict) if naming_config_dict else NamingConfig()
            self.file_generator = FileNameGenerator(naming_config)
            
            # Initialize export configuration
            export_config_dict = self.config.get('patterns', {}).get('export', {})
            export_config = ExportConfig(
                output_directory=export_config_dict.get('output_directory', './output'),
                overwrite_existing=export_config_dict.get('overwrite_existing', False),
                create_subdirectories=export_config_dict.get('create_subdirectories', True),
                filename_collision_strategy=export_config_dict.get('filename_collision_strategy', 'rename')
            )
            self.exporter = PDFExporter(export_config)
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            messagebox.showerror("Initialization Error", 
                               f"Failed to initialize application components:\n{str(e)}")
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Create main menu
        self._create_menu()
        
        # Create toolbar
        self._create_toolbar()
        
        # Create main content area
        self._create_main_content()
        
        # Create status bar
        self._create_status_bar()
    
    def _create_menu(self) -> None:
        """Create the main menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load PDF", command=self.load_pdf, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Export All", command=self.export_all, accelerator="Ctrl+E")
        file_menu.add_command(label="Export Selected", command=self.export_selected)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Ctrl+Q")
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Select All", command=self._select_all_documents)
        edit_menu.add_command(label="Select None", command=self._select_no_documents)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self.load_pdf())
        self.root.bind('<Control-e>', lambda e: self.export_all())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
    
    def _create_toolbar(self) -> None:
        """Create the main toolbar."""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Main action buttons
        ttk.Button(toolbar, text="Load PDF", 
                  command=self.load_pdf).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Process", 
                  command=self.process_pdf).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Settings", 
                  command=self._show_settings).pack(side=tk.LEFT, padx=(0, 20))
        
        # Export button (right side)
        ttk.Button(toolbar, text="Export All", 
                  command=self.export_all).pack(side=tk.RIGHT)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(toolbar, variable=self.progress_var, 
                                          length=200, mode='determinate')
        self.progress_bar.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Progress label
        self.progress_label = ttk.Label(toolbar, text="Ready")
        self.progress_label.pack(side=tk.RIGHT, padx=(0, 5))
    
    def _create_main_content(self) -> None:
        """Create the main content area."""
        # Create paned window for resizable layout
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Document list
        left_frame = ttk.LabelFrame(main_paned, text="Detected Documents", padding=10)
        self.document_list = DocumentListView(left_frame, self._on_document_selected)
        self.document_list.pack(fill=tk.BOTH, expand=True)
        main_paned.add(left_frame, weight=1)
        
        # Right panel - Preview and editing
        right_frame = ttk.LabelFrame(main_paned, text="Preview & Edit", padding=10)
        self.preview_pane = PreviewPane(right_frame, self._on_document_updated)
        self.preview_pane.pack(fill=tk.BOTH, expand=True)
        main_paned.add(right_frame, weight=1)
    
    def _create_status_bar(self) -> None:
        """Create the status bar."""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=5, pady=2)
        
        # Document count label
        self.doc_count_label = ttk.Label(self.status_bar, text="No documents loaded")
        self.doc_count_label.pack(side=tk.RIGHT, padx=5, pady=2)
    
    def _update_status(self, message: str) -> None:
        """Update the status bar message."""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def _update_progress(self, value: float, message: str = "") -> None:
        """Update the progress bar and label."""
        self.progress_var.set(value)
        if message:
            self.progress_label.config(text=message)
        self.root.update_idletasks()
    
    def load_pdf(self) -> None:
        """Load a PDF file for processing."""
        if self.processing:
            messagebox.showwarning("Processing", "Please wait for current processing to complete.")
            return
        
        file_path = filedialog.askopenfilename(
            title="Select PDF file",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if file_path:
            self.current_pdf_path = file_path
            self.documents = []
            self.document_list.populate_documents([])
            self.preview_pane.clear_preview()
            
            filename = Path(file_path).name
            self._update_status(f"Loaded: {filename}")
            self.doc_count_label.config(text="Ready to process")
    
    def process_pdf(self) -> None:
        """Process the loaded PDF to detect and classify documents."""
        if not self.current_pdf_path:
            messagebox.showwarning("No PDF", "Please load a PDF file first.")
            return
        
        if self.processing:
            messagebox.showwarning("Processing", "Processing is already in progress.")
            return
        
        # Start processing in a separate thread
        self.processing = True
        thread = threading.Thread(target=self._process_pdf_worker)
        thread.daemon = True
        thread.start()
    
    def _process_pdf_worker(self) -> None:
        """Worker thread for PDF processing."""
        try:
            self._update_status("Processing PDF...")
            self._update_progress(0, "Loading PDF...")
            
            # Load PDF
            pdf_result = self.pdf_processor.process_pdf(self.current_pdf_path)
            self._update_progress(20, "Detecting boundaries...")
            
            # Detect document boundaries
            boundaries = self.boundary_detector.detect_boundaries(pdf_result.pages)
            self._update_progress(40, "Classifying documents...")
            
            # Process each document section
            documents = []
            total_sections = len(boundaries)
            
            for i, boundary in enumerate(boundaries):
                try:
                    # Get text sample for classification
                    start_page = boundary.start_page
                    end_page = boundary.end_page
                    
                    # Extract text from first few pages of the section
                    text_sample = ""
                    for page_num in range(start_page, min(start_page + 3, end_page + 1)):
                        if page_num <= len(pdf_result.pages):
                            page_data = pdf_result.pages[page_num - 1]
                            text_sample += page_data.text + "\n"
                    
                    # Classify document
                    classification = self.classifier.classify_document(
                        text_sample, (start_page, end_page)
                    )
                    
                    # Generate filename
                    filename = self.file_generator.generate_filename(
                        text_sample, classification.document_type, (start_page, end_page)
                    )
                    
                    # Create document section
                    doc_section = DocumentSection(
                        start_page=start_page,
                        end_page=end_page,
                        document_type=classification.document_type,
                        filename=filename,
                        classification_confidence=classification.confidence,
                        text_sample=text_sample[:500],  # Store sample for preview
                        selected=True  # Default to selected
                    )
                    
                    documents.append(doc_section)
                    
                    # Update progress
                    progress = 40 + (50 * (i + 1) / total_sections)
                    self._update_progress(progress, f"Processing document {i + 1}/{total_sections}")
                    
                except Exception as e:
                    logger.error(f"Error processing document section {i + 1}: {e}")
            
            # Update UI in main thread
            self.root.after(0, self._processing_complete, documents)
            
        except Exception as e:
            logger.error(f"Error during PDF processing: {e}")
            self.root.after(0, self._processing_error, str(e))
    
    def _processing_complete(self, documents: List[DocumentSection]) -> None:
        """Handle completion of PDF processing."""
        self.processing = False
        self.documents = documents
        
        # Update UI
        self.document_list.populate_documents(documents)
        self._update_progress(100, "Complete")
        self._update_status(f"Processing complete - {len(documents)} documents detected")
        self.doc_count_label.config(text=f"{len(documents)} documents")
        
        # Reset progress after a delay
        self.root.after(2000, lambda: self._update_progress(0, "Ready"))
    
    def _processing_error(self, error_message: str) -> None:
        """Handle processing errors."""
        self.processing = False
        self._update_progress(0, "Error")
        self._update_status("Processing failed")
        messagebox.showerror("Processing Error", f"Failed to process PDF:\n{error_message}")
    
    def _on_document_selected(self, index: int) -> None:
        """Handle document selection in the list."""
        if 0 <= index < len(self.documents):
            document = self.documents[index]
            if self.current_pdf_path:
                self.preview_pane.show_preview(document, self.current_pdf_path)
    
    def _on_document_updated(self, updated_document: DocumentSection) -> None:
        """Handle document updates from the preview pane."""
        # Find and update the document in the list
        for i, doc in enumerate(self.documents):
            if (doc.start_page == updated_document.start_page and 
                doc.end_page == updated_document.end_page):
                self.document_list.update_document(i, updated_document)
                break
    
    def export_all(self) -> None:
        """Export all documents."""
        if not self.documents:
            messagebox.showwarning("No Documents", "No documents to export.")
            return
        
        self._export_documents(self.documents)
    
    def export_selected(self) -> None:
        """Export only selected documents."""
        selected_docs = self.document_list.get_selected_documents()
        if not selected_docs:
            messagebox.showwarning("No Selection", "No documents selected for export.")
            return
        
        self._export_documents(selected_docs)
    
    def _export_documents(self, documents: List[DocumentSection]) -> None:
        """Export the specified documents."""
        if not self.current_pdf_path:
            messagebox.showerror("No PDF", "No source PDF loaded.")
            return
        
        # Ask for output directory
        output_dir = filedialog.askdirectory(title="Select output directory")
        if not output_dir:
            return
        
        try:
            self._update_status("Exporting documents...")
            
            # Perform export
            result = self.exporter.export_all_documents(
                self.current_pdf_path, documents, output_dir
            )
            
            # Show results
            message = f"Export completed:\n"
            message += f"• {result.success_count} documents exported successfully\n"
            if result.failed_count > 0:
                message += f"• {result.failed_count} documents failed\n"
                message += f"\nErrors:\n" + "\n".join(result.errors[:5])
                if len(result.errors) > 5:
                    message += f"\n... and {len(result.errors) - 5} more errors"
            
            if result.success_count > 0:
                messagebox.showinfo("Export Complete", message)
            else:
                messagebox.showerror("Export Failed", message)
            
            self._update_status(f"Export complete - {result.success_count} files saved")
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            messagebox.showerror("Export Error", f"Failed to export documents:\n{str(e)}")
    
    def _select_all_documents(self) -> None:
        """Select all documents."""
        self.document_list._select_all()
    
    def _select_no_documents(self) -> None:
        """Deselect all documents."""
        self.document_list._select_none()
    
    def _show_settings(self) -> None:
        """Show the settings dialog."""
        messagebox.showinfo("Settings", "Settings dialog not yet implemented.")
    
    def _show_about(self) -> None:
        """Show the about dialog."""
        about_text = """Smart-Splitter v0.3.0

An intelligent PDF document splitting and classification system
specifically designed for construction legal disputes.

The system analyzes multi-document PDFs, automatically detects
document boundaries, classifies document types, and splits them
into individual files with intelligent naming.

© 2025 Smart-Splitter Development Team"""
        
        messagebox.showinfo("About Smart-Splitter", about_text)
    
    def run(self) -> None:
        """Start the GUI application."""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.root.quit()


def main():
    """Main entry point for the GUI application."""
    app = SmartSplitterGUI()
    app.run()


if __name__ == "__main__":
    main()