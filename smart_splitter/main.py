"""Main module for Smart-Splitter - Phase 1 demonstration."""

import sys
from pathlib import Path

from .pdf_processing.processor import PDFProcessor
from .boundary_detection.detector import BoundaryDetector
from .config.manager import ConfigManager


def main():
    """Main function to demonstrate Phase 1 functionality."""
    if len(sys.argv) != 2:
        print("Usage: python -m smart_splitter.main <pdf_file>")
        return
    
    pdf_path = sys.argv[1]
    if not Path(pdf_path).exists():
        print(f"Error: File {pdf_path} does not exist")
        return
    
    print("Smart-Splitter Phase 1 Demo")
    print("=" * 40)
    
    # Initialize components
    print("Initializing configuration...")
    config_manager = ConfigManager()
    
    print("Loading PDF processor...")
    pdf_processor = PDFProcessor()
    
    print("Initializing boundary detector...")
    boundary_detector = BoundaryDetector(config_manager)
    
    # Load and process PDF
    print(f"\nLoading PDF: {pdf_path}")
    if not pdf_processor.load_pdf(pdf_path):
        print("Error: Failed to load PDF")
        return
    
    page_count = pdf_processor.get_page_count()
    print(f"PDF loaded successfully - {page_count} pages")
    
    # Extract page data
    print("\nExtracting page data...")
    pages_data = pdf_processor.extract_page_data()
    print(f"Extracted data from {len(pages_data)} pages")
    
    # Detect boundaries
    print("\nDetecting document boundaries...")
    boundaries = boundary_detector.detect_boundaries(pages_data)
    print(f"Detected {len(boundaries)} document boundaries: {boundaries}")
    
    # Get document sections
    sections = boundary_detector.get_document_sections(boundaries, page_count)
    print(f"\nDocument sections:")
    for i, (start, end) in enumerate(sections, 1):
        page_range = f"Page {start + 1}" if start == end else f"Pages {start + 1}-{end + 1}"
        print(f"  Document {i}: {page_range}")
        
        # Show first few lines of each document
        if start < len(pages_data):
            first_lines = pages_data[start].first_lines[:2]
            if first_lines:
                preview = " | ".join(first_lines)[:80]
                print(f"    Preview: {preview}...")
    
    # Clean up
    pdf_processor.close()
    print("\nPhase 1 processing complete!")


if __name__ == "__main__":
    main()