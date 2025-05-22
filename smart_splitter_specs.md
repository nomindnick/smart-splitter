# Smart-Splitter Project Specifications

## Project Overview

**Project Name:** smart-splitter  
**Purpose:** Intelligent PDF document splitting and classification system for construction legal disputes  
**Target Platform:** Ubuntu Linux with GUI  
**Development Language:** Python 3.8+

---

## 1. Overall Implementation Plan

### Phase 1: Core Infrastructure (Week 1)
**Objective:** Establish basic PDF processing and project structure

**Components to Implement:**
- [PDF Processing Engine](#pdf-processing-engine) (Core functionality)
- [Document Boundary Detection](#document-boundary-detection) (Basic rule-based detection)
- [Configuration Management](#configuration-management) (Settings and patterns)

**Deliverables:**
- Functional PDF text extraction
- Basic document boundary detection using predefined patterns
- Configuration system for boundary detection rules
- Unit tests for core components

**Success Criteria:**
- Can load and extract text from multi-page PDFs
- Identifies potential document boundaries with >70% accuracy on test documents
- All core functions have unit test coverage

### Phase 2: Classification System (Week 2)
**Objective:** Implement intelligent document classification

**Components to Implement:**
- [Document Classification System](#document-classification-system) (Rule-based + API)
- [File Naming Generator](#file-naming-generator) (Smart naming logic)

**Deliverables:**
- Rule-based classification for common document types
- API-based classification for uncertain cases
- Filename generation with extracted metadata
- Classification accuracy testing framework

**Success Criteria:**
- Classification accuracy >85% on test document set
- API costs remain under $0.01 per 100 pages processed
- Generated filenames are meaningful and unique

### Phase 3: User Interface (Week 3)
**Objective:** Create intuitive GUI for document review and correction

**Components to Implement:**
- [GUI Application](#gui-application) (Main interface)
- [Export System](#export-system) (PDF splitting and saving)

**Deliverables:**
- Complete GUI with document list, preview, and editing capabilities
- Export functionality for individual PDFs
- User manual and help documentation

**Success Criteria:**
- Users can complete typical workflow in <5 minutes
- All major use cases covered by GUI
- Export produces correctly split and named PDFs

### Phase 4: Polish and Optimization (Week 4)
**Objective:** Refine system based on testing and feedback

**Components to Refine:**
- All components (performance optimization and bug fixes)
- Error handling and user feedback
- Configuration options and customization

**Deliverables:**
- Performance-optimized system
- Comprehensive error handling
- User configuration options
- Final testing and validation

**Success Criteria:**
- System processes 100+ page documents in <30 seconds
- Robust error handling for edge cases
- User satisfaction with accuracy and usability

---

## 2. Component Specifications

### PDF Processing Engine

**Purpose:** Core component for PDF loading, text extraction, and basic analysis

**Dependencies:**
- PyMuPDF (fitz)
- Pillow (PIL)

**Key Classes:**
```python
class PDFProcessor:
    def load_pdf(self, file_path: str) -> bool
    def extract_page_data(self) -> List[PageData]
    def get_page_count(self) -> int
    def get_page_preview(self, page_num: int) -> Image
    def extract_page_text(self, page_num: int) -> str
    def get_page_layout_info(self, page_num: int) -> LayoutInfo

class PageData:
    page_num: int
    text: str
    has_large_text: bool
    first_lines: List[str]
    layout_info: LayoutInfo
    
class LayoutInfo:
    has_header: bool
    has_footer: bool
    font_sizes: List[float]
    text_blocks: List[TextBlock]
```

**Input Requirements:**
- PDF file path (string)
- Page range specification (optional)

**Output Specifications:**
- PageData objects containing text and layout information
- Page preview images (PIL Image objects)
- Error status and messages

**Performance Requirements:**
- Process 100-page PDF in <10 seconds
- Memory usage <500MB for typical documents

**Error Handling:**
- Corrupted PDF files
- Password-protected PDFs
- OCR requirements for scanned documents

---

### Document Boundary Detection

**Purpose:** Identify where individual documents begin and end within the PDF

**Dependencies:**
- PDF Processing Engine
- Configuration Management
- re (regex)

**Key Classes:**
```python
class BoundaryDetector:
    def __init__(self, config: BoundaryConfig)
    def detect_boundaries(self, pages_data: List[PageData]) -> List[int]
    def validate_boundaries(self, boundaries: List[int]) -> List[int]
    def add_custom_pattern(self, pattern: str, document_type: str)

class BoundaryConfig:
    patterns: Dict[str, List[str]]
    min_document_length: int
    confidence_threshold: float
```

**Detection Patterns:**
```python
BOUNDARY_PATTERNS = {
    'payment_application': [
        r"PAYMENT APPLICATION\s*(?:NO|#)\.?\s*\d+",
        r"APPLICATION FOR PAYMENT",
        r"(?:AIA|FORM)\s*(?:DOCUMENT\s*)?G702"
    ],
    'change_order': [
        r"CHANGE ORDER\s*(?:NO|#)\.?\s*\d+",
        r"(?:AIA|FORM)\s*(?:DOCUMENT\s*)?G701"
    ],
    'email': [
        r"From:\s*.+@.+",
        r"Subject:\s*.+",
        r"Sent:\s*\w+,\s*\w+\s*\d+"
    ],
    'letter': [
        r"Dear\s+(?:Mr\.|Ms\.|Mrs\.|Dr\.|\w+)",
        r"Re:\s*.+",
        r"^\s*\w+,\s*\w+\s*\d{1,2},\s*\d{4}"  # Date line
    ],
    'rfi': [
        r"REQUEST FOR INFORMATION",
        r"RFI\s*(?:NO|#)\.?\s*\d+"
    ],
    'contract': [
        r"CONTRACT\s*(?:AGREEMENT|FOR)",
        r"SUBCONTRACT\s*AGREEMENT",
        r"AGREEMENT\s*BETWEEN"
    ],
    'inspection': [
        r"INSPECTION\s*REPORT",
        r"DAILY\s*(?:FIELD\s*)?REPORT",
        r"SITE\s*VISIT\s*REPORT"
    ]
}
```

**Algorithm:**
1. Scan each page for boundary patterns
2. Check for visual layout changes (font size, formatting)
3. Look for page numbering resets
4. Validate boundaries using minimum document length
5. Return sorted list of boundary page numbers

**Performance Requirements:**
- Process boundary detection in <5 seconds for 100-page document
- Accuracy >80% for common document types

---

### Document Classification System

**Purpose:** Classify detected document sections into predefined categories

**Dependencies:**
- OpenAI API (GPT-4.1-nano)
- Configuration Management
- re (regex)

**Document Types:**
```python
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
```

**Key Classes:**
```python
class DocumentClassifier:
    def __init__(self, api_key: str, config: ClassificationConfig)
    def classify_document(self, text_sample: str) -> ClassificationResult
    def classify_batch(self, documents: List[str]) -> List[ClassificationResult]
    def add_rule_pattern(self, document_type: str, pattern: str)

class ClassificationResult:
    document_type: str
    confidence: float
    method_used: str  # 'rule_based' or 'api'
    extracted_info: Dict[str, str]

class ClassificationConfig:
    api_model: str
    max_input_chars: int
    confidence_threshold: float
    rule_patterns: Dict[str, List[str]]
```

**Classification Strategy:**
1. **Rule-Based First Pass:** Check document text against predefined patterns
2. **API Classification:** Use GPT-4.1-nano for uncertain cases
3. **Confidence Scoring:** Rate classification certainty
4. **Fallback:** Default to "other" category if confidence is too low

**Rule-Based Patterns:**
```python
CLASSIFICATION_RULES = {
    'email': [
        r"From:\s*.+@.+",
        r"To:\s*.+@.+", 
        r"Subject:\s*.+"
    ],
    'payment_application': [
        r"APPLICATION FOR PAYMENT",
        r"SCHEDULE OF VALUES",
        r"(?:AIA|FORM)\s*G702"
    ],
    'change_order': [
        r"CHANGE ORDER",
        r"MODIFICATION TO CONTRACT",
        r"(?:AIA|FORM)\s*G701"
    ],
    'rfi': [
        r"REQUEST FOR INFORMATION",
        r"RFI\s*(?:NO|#)\.?\s*\d+"
    ],
    'contract_document': [
        r"CONTRACT AGREEMENT",
        r"SUBCONTRACT",
        r"GENERAL CONDITIONS"
    ]
}
```

**API Integration:**
- Model: GPT-4.1-nano
- Max input: 1000 characters per document
- Temperature: 0 (deterministic)
- Max output tokens: 10
- Estimated cost: <$0.000012 per classification

**Performance Requirements:**
- Rule-based classification: <1 second per document
- API classification: <3 seconds per document
- Overall accuracy: >85%
- Cost: <$0.01 per 100 pages

---

### File Naming Generator

**Purpose:** Generate intelligent, descriptive filenames for split documents

**Dependencies:**
- Document Classification System
- re (regex)
- datetime

**Key Classes:**
```python
class FileNameGenerator:
    def __init__(self, config: NamingConfig)
    def generate_filename(self, doc_text: str, doc_type: str, 
                         page_range: Tuple[int, int]) -> str
    def extract_key_info(self, text: str, doc_type: str) -> Dict[str, str]
    def sanitize_filename(self, filename: str) -> str

class NamingConfig:
    max_filename_length: int
    date_format: str
    include_page_numbers: bool
    custom_templates: Dict[str, str]
```

**Extraction Patterns by Document Type:**
```python
EXTRACTION_PATTERNS = {
    'payment_application': {
        'number': r"(?:APPLICATION|PAY.*APP).*?(?:NO|#)\.?\s*(\d+)",
        'date': r"(?:DATE|THROUGH).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        'amount': r"\$\s*([\d,]+\.?\d*)"
    },
    'change_order': {
        'number': r"CHANGE\s*ORDER.*?(?:NO|#)\.?\s*(\d+)",
        'date': r"(?:DATE|DATED).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        'description': r"DESCRIPTION[:\s]*([^\n]{10,50})"
    },
    'email': {
        'from': r"From:\s*([^<\n]+)",
        'subject': r"Subject:\s*([^\n]{5,30})",
        'date': r"(?:Sent|Date).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
    },
    'rfi': {
        'number': r"RFI.*?(?:NO|#)\.?\s*(\d+)",
        'date': r"(?:DATE|DATED).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        'subject': r"(?:SUBJECT|RE):\s*([^\n]{10,40})"
    }
}
```

**Filename Templates:**
```python
FILENAME_TEMPLATES = {
    'payment_application': "{type}_No{number}_{date}_{pages}",
    'change_order': "CO_{number}_{date}_{description}_{pages}",
    'email': "Email_{subject}_{from}_{date}_{pages}",
    'rfi': "RFI_{number}_{subject}_{date}_{pages}",
    'contract_document': "Contract_{description}_{date}_{pages}",
    'default': "{type}_{date}_{pages}"
}
```

**Filename Sanitization:**
- Remove invalid characters: `< > : " | ? * \ /`
- Replace spaces with underscores
- Limit total length to 200 characters
- Ensure uniqueness by adding sequence numbers if needed

**Performance Requirements:**
- Generate filename in <1 second per document
- Filenames must be valid for Linux filesystem
- Unique filenames within export directory

---

### GUI Application

**Purpose:** Provide user interface for document review, editing, and export

**Dependencies:**
- tkinter (built-in)
- PIL (Pillow)
- All other component modules

**Key Classes:**
```python
class SmartSplitterGUI:
    def __init__(self)
    def setup_ui(self)
    def load_pdf(self)
    def process_pdf(self)
    def export_all(self)

class DocumentListView:
    def __init__(self, parent)
    def populate_documents(self, documents: List[DocumentSection])
    def update_selection(self, index: int)
    
class PreviewPane:
    def __init__(self, parent)
    def show_preview(self, page_image: Image)
    def update_controls(self, doc_section: DocumentSection)

class DocumentSection:
    start_page: int
    end_page: int
    document_type: str
    filename: str
    classification_confidence: float
    preview_image: Image
```

**UI Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ Smart-Splitter - Construction Document PDF Splitter        │
├─────────────────────────────────────────────────────────────┤
│ [Load PDF] [Process] [Settings]           [Export All]     │
│ ████████████████████████████████████████████ 85%           │
├─────────────────────────────────────────────────────────────┤
│ Detected Documents          │ Preview & Edit                │
│ ┌─────────────────────────┐ │ ┌───────────────────────────┐ │
│ │☐ PayApp_005_2023-10-15 │ │ │                           │ │
│ │☐ Email_Re_Schedule_... │ │ │     [Page Preview]        │ │
│ │☐ CO_023_ProjectX_...   │ │ │                           │ │
│ │☐ RFI_012_Foundation... │ │ │                           │ │
│ │☐ Contract_Main_...     │ │ └───────────────────────────┘ │
│ │                       │ │ Document Type: [Dropdown ▼]   │
│ │                       │ │ Filename: [Text Entry     ]   │
│ │                       │ │ Pages: 15-18                  │
│ │                       │ │ Confidence: High              │
│ │                       │ │ [Update] [Split] [Merge]      │
│ └─────────────────────────┘ └───────────────────────────────┘
├─────────────────────────────────────────────────────────────┤
│ Status: Ready to export 12 documents                       │
└─────────────────────────────────────────────────────────────┘
```

**Key Features:**
- **Document List:** Checkbox list of all detected documents
- **Preview Pane:** Shows first page preview of selected document  
- **Editing Controls:** Dropdown for document type, editable filename
- **Batch Operations:** Select multiple documents for bulk changes
- **Progress Indication:** Progress bar during processing
- **Status Updates:** Real-time feedback to user

**User Workflow:**
1. Click "Load PDF" to select source document
2. Click "Process" to analyze and split document
3. Review proposed document splits in list view
4. Select individual documents to preview and edit
5. Modify document types and filenames as needed
6. Click "Export All" to save individual PDFs

**Error Handling:**
- File access errors (permissions, file not found)
- Processing errors (corrupted PDF, API failures)
- Export errors (disk space, write permissions)
- User input validation

---

### Configuration Management

**Purpose:** Manage application settings, patterns, and user preferences

**Dependencies:**
- json (built-in)
- pathlib (built-in)

**Key Classes:**
```python
class ConfigManager:
    def __init__(self, config_path: str)
    def load_config(self) -> Dict
    def save_config(self, config: Dict)
    def get_setting(self, key: str, default=None)
    def update_setting(self, key: str, value)

class PatternManager:
    def __init__(self, config_manager: ConfigManager)
    def get_boundary_patterns(self) -> Dict[str, List[str]]
    def get_classification_rules(self) -> Dict[str, List[str]]
    def add_custom_pattern(self, category: str, pattern: str)
```

**Configuration File Structure:**
```json
{
    "api": {
        "openai_api_key": "",
        "model": "gpt-4.1-nano",
        "max_tokens": 10,
        "timeout": 30
    },
    "processing": {
        "min_document_length": 1,
        "confidence_threshold": 0.7,
        "max_input_chars": 1000
    },
    "ui": {
        "window_width": 1200,
        "window_height": 800,
        "preview_size": 300
    },
    "export": {
        "default_directory": "~/Documents/split_pdfs",
        "filename_max_length": 200,
        "include_page_numbers": true
    },
    "patterns": {
        "boundary_patterns": { /* ... */ },
        "classification_rules": { /* ... */ },
        "extraction_patterns": { /* ... */ }
    }
}
```

**Settings Management:**
- Auto-save on changes
- Validation of settings values
- Default fallbacks for missing settings
- User-specific configuration directory

---

### Export System

**Purpose:** Split original PDF into individual documents and save with generated filenames

**Dependencies:**
- PyMuPDF (fitz)
- pathlib
- Configuration Management

**Key Classes:**
```python
class PDFExporter:
    def __init__(self, config: ExportConfig)
    def export_document(self, source_pdf: str, doc_section: DocumentSection, 
                       output_dir: str) -> bool
    def export_all_documents(self, source_pdf: str, 
                           documents: List[DocumentSection], 
                           output_dir: str) -> ExportResult

class ExportResult:
    success_count: int
    failed_count: int
    errors: List[str]
    exported_files: List[str]

class ExportConfig:
    output_directory: str
    overwrite_existing: bool
    create_subdirectories: bool
    filename_collision_strategy: str  # 'rename', 'skip', 'overwrite'
```

**Export Process:**
1. **Validate Inputs:** Check source PDF exists, output directory is writable
2. **Create Output Directory:** Ensure export directory exists
3. **Process Each Document:**
   - Extract pages from source PDF
   - Create new PDF with extracted pages
   - Save with generated filename
   - Handle filename collisions
4. **Generate Report:** Summary of export results

**Filename Collision Handling:**
```python
def handle_filename_collision(self, filepath: str, strategy: str) -> str:
    if strategy == 'rename':
        return self.get_unique_filename(filepath)
    elif strategy == 'skip':
        return None  # Skip this file
    elif strategy == 'overwrite':
        return filepath
```

**Error Recovery:**
- Continue processing remaining documents if one fails
- Log all errors with specific details
- Provide user with detailed error report
- Allow retry of failed exports

**Performance Requirements:**
- Export 50 documents in <30 seconds
- Handle large documents (500+ pages) efficiently
- Minimal memory usage during export

---

## 3. Testing Strategy

### Unit Testing
- **PDF Processing Engine:** Test with various PDF formats and sizes
- **Boundary Detection:** Test with known good/bad boundary examples
- **Classification System:** Test accuracy with sample documents
- **File Naming:** Test edge cases and special characters

### Integration Testing  
- **End-to-End Workflow:** Load PDF → Process → Export
- **API Integration:** Test API failures and recovery
- **GUI Functionality:** Test all user interactions

### Performance Testing
- **Large Documents:** Test with 500+ page PDFs
- **Memory Usage:** Monitor memory consumption during processing
- **Processing Speed:** Benchmark processing times

### User Acceptance Testing
- **Workflow Validation:** Test with real construction documents
- **Accuracy Assessment:** Measure classification and naming accuracy
- **Usability Testing:** Observe user interactions and pain points

---

## 4. Deployment Requirements

### System Requirements
- **Operating System:** Ubuntu 18.04 or later
- **Python:** 3.8 or later
- **Memory:** 4GB RAM minimum, 8GB recommended
- **Storage:** 1GB free space for application and temporary files

### Dependencies
```bash
pip install PyMuPDF Pillow openai python-dotenv
```

### Installation Process
1. Clone repository
2. Install Python dependencies  
3. Configure API credentials
4. Run initial setup script
5. Launch GUI application

### Configuration
- API key setup for OpenAI
- Default directory configuration
- Custom pattern configuration (optional)

---

## 5. Future Enhancements

### Phase 2 Features
- **OCR Integration:** Handle scanned documents
- **Batch Processing:** Process multiple PDFs simultaneously  
- **Cloud Storage:** Integration with Google Drive, Dropbox
- **Advanced Classification:** Custom model training capability

### Phase 3 Features
- **Web Interface:** Browser-based version
- **Mobile App:** Android/iOS companion app
- **Collaboration:** Multi-user document review
- **Analytics:** Processing statistics and accuracy metrics

---

## Success Metrics

### Technical Metrics
- **Classification Accuracy:** >85% correct classification
- **Processing Speed:** <30 seconds for 100-page document
- **API Costs:** <$0.01 per 100 pages processed
- **Error Rate:** <5% processing failures

### User Experience Metrics
- **Task Completion Time:** <5 minutes for typical workflow
- **User Satisfaction:** >4/5 rating in usability testing
- **Adoption Rate:** Regular use by target users
- **Feature Utilization:** >80% of features used regularly