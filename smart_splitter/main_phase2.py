"""
Phase 2 Demo Application - Document Classification and File Naming
"""
import sys
import os
import logging
from pathlib import Path
from typing import List, Tuple

from smart_splitter.pdf_processing import PDFProcessor
from smart_splitter.boundary_detection import BoundaryDetector
from smart_splitter.config import ConfigManager
from smart_splitter.classification import DocumentClassifier, ClassificationConfig
from smart_splitter.naming import FileNameGenerator, NamingConfig


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def extract_document_sections(pages_data, boundaries) -> List[Tuple[str, Tuple[int, int]]]:
    """
    Extract document sections based on boundaries
    
    Args:
        pages_data: List of PageData objects
        boundaries: List of boundary page numbers
        
    Returns:
        List of (document_text, page_range) tuples
    """
    sections = []
    
    # Add boundary at the end if not present
    if boundaries and boundaries[-1] != len(pages_data):
        boundaries.append(len(pages_data))
    
    # Extract sections between boundaries
    start_page = 0
    for boundary in boundaries:
        if boundary > start_page:
            # Extract text from this section
            section_text = ""
            for i in range(start_page, boundary):
                if i < len(pages_data):
                    section_text += pages_data[i].text + "\n"
            
            # Create page range (1-indexed for display)
            page_range = (start_page + 1, boundary)
            sections.append((section_text.strip(), page_range))
            
            start_page = boundary
    
    return sections


def main():
    """Main Phase 2 demonstration"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    if len(sys.argv) != 2:
        print("Usage: python -m smart_splitter.main_phase2 <pdf_file>")
        print("Example: python -m smart_splitter.main_phase2 test_construction_docs.pdf")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    
    if not Path(pdf_file).exists():
        print(f"Error: File '{pdf_file}' not found")
        sys.exit(1)
    
    print("=" * 70)
    print("SMART-SPLITTER PHASE 2 DEMO")
    print("Document Classification and File Naming System")
    print("=" * 70)
    print()
    
    try:
        # Initialize components
        print("📄 Initializing PDF processor...")
        pdf_processor = PDFProcessor()
        
        print("🔧 Loading configuration...")
        config_manager = ConfigManager()
        
        print("🔍 Initializing boundary detector...")
        boundary_detector = BoundaryDetector(config_manager)
        
        print("🏷️  Initializing document classifier...")
        classification_config = ClassificationConfig(
            rule_patterns=config_manager.get_setting("classification_rules", {})
        )
        # Note: API key would come from environment or config in production
        api_key = config_manager.get_setting("api.key")
        classifier = DocumentClassifier(classification_config, api_key)
        
        print("📁 Initializing file name generator...")
        naming_config = NamingConfig(
            custom_templates=config_manager.get_setting("naming.templates", {})
        )
        file_generator = FileNameGenerator(naming_config)
        
        print()
        print(f"📖 Processing PDF: {pdf_file}")
        print()
        
        # Load and process PDF
        success = pdf_processor.load_pdf(pdf_file)
        if not success:
            print("❌ Failed to load PDF file")
            return
        
        pages_data = pdf_processor.extract_page_data()
        print(f"✅ Extracted data from {len(pages_data)} pages")
        
        # Detect document boundaries
        boundaries = boundary_detector.detect_boundaries(pages_data)
        print(f"✅ Detected {len(boundaries)} document boundaries: {boundaries}")
        
        # Extract document sections
        sections = extract_document_sections(pages_data, boundaries)
        print(f"✅ Extracted {len(sections)} document sections")
        print()
        
        # Process each document section
        print("🔍 CLASSIFYING AND NAMING DOCUMENTS")
        print("=" * 50)
        
        for i, (doc_text, page_range) in enumerate(sections, 1):
            print(f"\n📄 Document {i}:")
            print(f"   📍 Pages: {page_range[0]}-{page_range[1]}")
            print(f"   📏 Text length: {len(doc_text)} characters")
            
            # Show document preview
            preview_text = doc_text[:200].replace('\n', ' ').strip()
            if len(doc_text) > 200:
                preview_text += "..."
            print(f"   👀 Preview: {preview_text}")
            
            # Classify document
            classification_result = classifier.classify_document(doc_text, page_range)
            
            print(f"   🏷️  Classification: {classification_result.document_type}")
            print(f"   📊 Confidence: {classification_result.confidence:.2f}")
            print(f"   🔧 Method: {classification_result.method_used}")
            
            if classification_result.extracted_info:
                print(f"   📋 Extracted info:")
                for key, value in classification_result.extracted_info.items():
                    if key not in ['matched_patterns']:  # Skip pattern details for clean output
                        print(f"      • {key}: {value}")
            
            # Generate filename
            filename = file_generator.generate_filename(
                doc_text, 
                classification_result.document_type, 
                page_range
            )
            
            print(f"   📁 Generated filename: {filename}.pdf")
            print()
        
        # Show classification statistics
        print("📊 CLASSIFICATION STATISTICS")
        print("=" * 30)
        stats = classifier.get_classification_stats()
        for doc_type, pattern_count in stats.items():
            print(f"   {doc_type}: {pattern_count} patterns")
        
        print()
        print("✅ Phase 2 demo completed successfully!")
        print()
        print("🎯 PHASE 2 CAPABILITIES DEMONSTRATED:")
        print("   ✅ Rule-based document classification")
        print("   ✅ Intelligent metadata extraction") 
        print("   ✅ Template-based filename generation")
        print("   ✅ Document type-specific processing")
        print("   ✅ Confidence scoring and fallback handling")
        print("   ✅ Comprehensive pattern matching")
        print()
        print("🚀 Ready for Phase 3: GUI Application and Export System")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()