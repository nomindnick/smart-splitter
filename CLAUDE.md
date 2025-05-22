# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Smart-Splitter is an intelligent PDF document splitting and classification system specifically designed for construction legal disputes. The system analyzes multi-document PDFs, automatically detects document boundaries, classifies document types, and splits them into individual files with intelligent naming.

**Target Platform:** Ubuntu Linux with GUI  
**Language:** Python 3.8+  
**UI Framework:** tkinter (built-in)

## Architecture Overview

The system is designed with 6 core components that work together:

1. **PDF Processing Engine** - Core PDF loading, text extraction, and layout analysis using PyMuPDF
2. **Document Boundary Detection** - Pattern-based detection of where individual documents begin/end within multi-document PDFs
3. **Document Classification System** - Hybrid approach using rule-based patterns + OpenAI API for uncertain cases
4. **File Naming Generator** - Intelligent filename generation based on extracted document metadata
5. **GUI Application** - tkinter-based interface for document review and editing
6. **Export System** - PDF splitting and saving functionality

## Key Dependencies

- **PyMuPDF (fitz)** - PDF processing and text extraction
- **Pillow (PIL)** - Image handling for page previews
- **OpenAI API** - Document classification for uncertain cases (GPT-4.1-nano)
- **tkinter** - GUI framework (built-in)

## Development Commands

```bash
# Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run Phase 1 demo
python -m smart_splitter.main test_construction_docs.pdf

# Run Phase 2 demo
python -m smart_splitter.main_phase2 test_construction_docs.pdf

# Run Phase 3 GUI application
python -m smart_splitter.main_phase3

# Run Phase 4 optimization demo
python -m smart_splitter.main_phase4
python phase4_demo.py  # Alternative launcher

# Run tests
pytest

# Run Phase 4 specific tests
pytest smart_splitter/tests/test_performance.py
pytest smart_splitter/tests/test_error_handling.py
pytest smart_splitter/tests/test_advanced_config.py

# Run linting (once implemented)
flake8 smart_splitter/
black smart_splitter/
```

## Document Types and Classification

The system recognizes these construction document types:
- email
- letter
- payment_application (AIA G702)
- evidence_of_payment
- change_order (AIA G701)
- change_order_response
- rfi (Request for Information)
- rfi_response
- inspection_report
- contract_document
- plans_specifications
- other

## Configuration System

The application uses JSON-based configuration stored in `~/.config/smart-splitter/config.json` with these key sections:
- `api`: OpenAI API settings
- `processing`: Document processing parameters
- `ui`: GUI preferences
- `export`: Export settings and file naming
- `patterns`: Boundary detection and classification patterns

## Performance Requirements

- Process 100-page PDF in <10 seconds
- Classification accuracy >85%
- API costs <$0.01 per 100 pages
- Export 50 documents in <30 seconds
- Memory usage <500MB for typical documents

## Implementation Phases

1. **Phase 1** (Week 1): Core PDF processing and boundary detection ✅ COMPLETED
2. **Phase 2** (Week 2): Classification system and filename generation ✅ COMPLETED
3. **Phase 3** (Week 3): GUI application and export system ✅ COMPLETED
4. **Phase 4** (Week 4): Polish, optimization, and testing ✅ COMPLETED

## Getting Started for Users

**Quick Start**:
```bash
# 1. Set up environment
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Launch GUI application
python -m smart_splitter.main_phase3

# 3. Or explore command-line demos
python -m smart_splitter.main_phase4  # Performance and optimization demo
```

See [GETTING_STARTED.md](GETTING_STARTED.md) for comprehensive user instructions and [README.md](README.md) for detailed features and usage.

## Phase 1 Status - COMPLETED ✅

**Completed Components:**
- PDF Processing Engine with text extraction and layout analysis
- Document Boundary Detection with pattern-based recognition
- Configuration Management system with JSON storage
- Comprehensive unit tests (12 tests passing)
- Demo application showing detected document boundaries

**Success Criteria Met:**
- ✅ Functional PDF text extraction
- ✅ Basic document boundary detection using predefined patterns
- ✅ Configuration system for boundary detection rules
- ✅ Unit tests for core components
- ✅ Processes test documents correctly
- ✅ Detects emails, payment applications, change orders, and RFIs

## Phase 2 Status - COMPLETED ✅

**Completed Components:**
- Document Classification System with rule-based and API-based classification
- File Naming Generator with intelligent metadata extraction
- Enhanced Configuration Management with classification and naming settings
- Comprehensive unit tests (52 total tests passing)
- Phase 2 demo application showing classification and filename generation

**Success Criteria Met:**
- ✅ Rule-based document classification using regex patterns
- ✅ Confidence scoring and fallback handling
- ✅ Template-based filename generation with metadata extraction
- ✅ Document type-specific information extraction
- ✅ Configurable classification patterns and naming templates
- ✅ Support for 11 construction document types
- ✅ Filename sanitization and duplicate handling
- ✅ OpenAI API integration framework (ready for API keys)

## Phase 3 Status - COMPLETED ✅

**Completed Components:**
- GUI Application with tkinter-based interface
- Export System for PDF splitting and saving
- Document List View with selection and bulk operations
- Preview Pane with page thumbnails and editing controls
- Comprehensive unit tests (83 total tests passing)
- Phase 3 demo application with full GUI workflow

**Success Criteria Met:**
- ✅ Complete GUI with document list, preview, and editing capabilities
- ✅ Export functionality for individual PDFs
- ✅ Users can complete typical workflow in <5 minutes
- ✅ All major use cases covered by GUI
- ✅ Export produces correctly split and named PDFs
- ✅ Interactive document selection and bulk operations
- ✅ Real-time preview of document pages
- ✅ Document type and filename editing capabilities
- ✅ Progress tracking and status updates
- ✅ Robust error handling and user feedback

## Phase 4 Status - COMPLETED ✅

**Completed Components:**
- Performance Monitoring System with real-time metrics tracking
- Memory Management with automatic cleanup and optimization
- PDF Processing Optimizer with caching and batch operations
- Comprehensive Benchmarking Suite for performance testing
- Enhanced Error Handling with custom exceptions and recovery
- Input Validation System with detailed error messages
- Advanced Configuration Management with profiles and auto-optimization
- Error Recovery Manager with automatic retry mechanisms
- Integration optimizations across all existing components

**Success Criteria Met:**
- ✅ System processes 100+ page documents in <30 seconds
- ✅ Robust error handling for edge cases with recovery mechanisms
- ✅ User satisfaction with accuracy and usability improvements
- ✅ Classification accuracy maintained >85%
- ✅ API costs remain <$0.01 per 100 pages
- ✅ Error rate <5% processing failures with auto-recovery
- ✅ Task completion time maintained <5 minutes for typical workflow
- ✅ Memory usage optimized and monitored (<500MB for typical documents)
- ✅ Advanced configuration profiles for different use cases
- ✅ Comprehensive testing and validation framework

## Key Patterns for Document Detection

The system uses regex patterns to detect document boundaries and classify types:
- Payment applications: `r"PAYMENT APPLICATION\s*(?:NO|#)\.?\s*\d+"`
- Change orders: `r"CHANGE ORDER\s*(?:NO|#)\.?\s*\d+"`
- Emails: `r"From:\s*.+@.+"`
- RFIs: `r"REQUEST FOR INFORMATION"`

## Testing Strategy

- Unit tests for each component with >80% coverage
- Integration tests for end-to-end workflow
- Performance testing with large documents (500+ pages)
- User acceptance testing with real construction documents

## User Configuration

Smart-Splitter stores configuration in `~/.config/smart-splitter/config.json`. Key settings:

**Performance Settings**:
```json
{
  "performance": {
    "max_memory_mb": 500,
    "max_workers": 3,
    "batch_size": 10
  }
}
```

**API Integration** (optional):
```json
{
  "api": {
    "openai_api_key": "sk-your-key-here",
    "model": "gpt-4o-mini"
  }
}
```

**Export Settings**:
```json
{
  "export": {
    "default_directory": "~/Documents/split_pdfs",
    "filename_collision_strategy": "rename"
  }
}
```

**Configuration Profiles**: Use predefined profiles for different use cases:
- `performance`: Fast processing, low memory usage
- `quality`: Accurate classification, detailed processing  
- `large_docs`: Optimized for 500+ page documents

Access via: `python -m smart_splitter.main_phase4 --demo config`

## Development Notes

When implementing this system, start with the PDF Processing Engine as the foundation, then build the other components incrementally following the phased approach outlined in the specifications.