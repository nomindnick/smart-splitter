"""
PDF export functionality for Smart-Splitter.

This module handles the splitting and saving of individual documents
from processed multi-document PDFs.
"""

import logging
from pathlib import Path
from typing import List
import fitz  # PyMuPDF

from .data_models import ExportResult, ExportConfig


logger = logging.getLogger(__name__)


class PDFExporter:
    """Handles exporting individual documents from a source PDF."""
    
    def __init__(self, config: ExportConfig):
        """
        Initialize the PDF exporter.
        
        Args:
            config: Export configuration settings
        """
        self.config = config
        self._ensure_output_directory()
    
    def _ensure_output_directory(self) -> None:
        """Ensure the output directory exists."""
        output_path = self.config.output_path
        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created output directory: {output_path}")
    
    def _get_unique_filename(self, filepath: str) -> str:
        """
        Generate a unique filename by appending a number if the file exists.
        
        Args:
            filepath: The desired file path
            
        Returns:
            A unique file path
        """
        path = Path(filepath)
        if not path.exists():
            return str(path)
        
        base_name = path.stem
        suffix = path.suffix
        parent = path.parent
        counter = 1
        
        while True:
            new_name = f"{base_name}_{counter:03d}{suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return str(new_path)
            counter += 1
    
    def _handle_filename_collision(self, filepath: str) -> str:
        """
        Handle filename collisions based on the configured strategy.
        
        Args:
            filepath: The file path that may have a collision
            
        Returns:
            The final file path to use, or None if the file should be skipped
        """
        if not Path(filepath).exists():
            return filepath
        
        strategy = self.config.filename_collision_strategy
        
        if strategy == 'rename':
            return self._get_unique_filename(filepath)
        elif strategy == 'skip':
            return None
        elif strategy == 'overwrite':
            return filepath
        else:
            raise ValueError(f"Unknown collision strategy: {strategy}")
    
    def export_document(self, source_pdf_path: str, doc_section, 
                       output_dir: str = None) -> bool:
        """
        Export a single document section to a separate PDF file.
        
        Args:
            source_pdf_path: Path to the source PDF file
            doc_section: Document section to export
            output_dir: Optional output directory (uses config default if None)
            
        Returns:
            True if export was successful, False otherwise
        """
        try:
            # Determine output directory
            if output_dir is None:
                output_dir = self.config.output_directory
            
            # Construct output file path
            output_path = Path(output_dir) / f"{doc_section.filename}.pdf"
            
            # Handle filename collisions
            final_path = self._handle_filename_collision(str(output_path))
            if final_path is None:
                logger.info(f"Skipping export of {doc_section.filename} (file exists)")
                return False
            
            # Open source PDF
            source_doc = fitz.open(source_pdf_path)
            
            # Create new PDF with selected pages
            output_doc = fitz.open()
            
            # Copy pages (convert to 0-based indexing)
            start_idx = doc_section.start_page - 1
            end_idx = doc_section.end_page - 1
            
            for page_num in range(start_idx, end_idx + 1):
                if page_num < len(source_doc):
                    output_doc.insert_pdf(source_doc, from_page=page_num, to_page=page_num)
                else:
                    logger.warning(f"Page {page_num + 1} not found in source PDF")
            
            # Save the new PDF
            output_doc.save(final_path)
            output_doc.close()
            source_doc.close()
            
            logger.info(f"Exported {doc_section.filename} to {final_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export {doc_section.filename}: {str(e)}")
            return False
    
    def export_all_documents(self, source_pdf_path: str, 
                           documents: List, 
                           output_dir: str = None) -> ExportResult:
        """
        Export all document sections to separate PDF files.
        
        Args:
            source_pdf_path: Path to the source PDF file
            documents: List of document sections to export
            output_dir: Optional output directory (uses config default if None)
            
        Returns:
            ExportResult with summary of the export operation
        """
        result = ExportResult()
        
        if not documents:
            logger.warning("No documents to export")
            return result
        
        # Determine output directory
        if output_dir is None:
            output_dir = self.config.output_directory
        
        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Starting export of {len(documents)} documents to {output_dir}")
        
        # Export each document
        for doc_section in documents:
            try:
                success = self.export_document(source_pdf_path, doc_section, output_dir)
                if success:
                    output_file = output_path / f"{doc_section.filename}.pdf"
                    result.add_success(str(output_file))
                else:
                    result.add_error(f"Failed to export {doc_section.filename}")
            except Exception as e:
                error_msg = f"Error exporting {doc_section.filename}: {str(e)}"
                result.add_error(error_msg)
                logger.error(error_msg)
        
        logger.info(f"Export completed: {result.success_count} successful, {result.failed_count} failed")
        return result