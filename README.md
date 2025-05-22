# Smart-Splitter: Intelligent PDF Document Processing

Smart-Splitter is an intelligent PDF document splitting and classification system specifically designed for construction legal disputes. The system automatically analyzes multi-document PDFs, detects document boundaries, classifies document types, and splits them into individual files with intelligent naming.

![Smart-Splitter Demo](https://img.shields.io/badge/status-production--ready-brightgreen)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![Platform](https://img.shields.io/badge/platform-Ubuntu%20Linux-orange)
![License](https://img.shields.io/badge/license-MIT-green)

## 🎯 What Smart-Splitter Does

- **📄 PDF Analysis**: Load and analyze multi-document PDF files
- **🔍 Boundary Detection**: Automatically detect where individual documents begin and end
- **📋 Document Classification**: Identify 11+ construction document types (emails, payment applications, change orders, RFIs, etc.)
- **📝 Intelligent Naming**: Generate meaningful filenames based on document content
- **✂️ PDF Splitting**: Export individual documents as separate PDF files
- **🖥️ User-Friendly GUI**: Interactive interface for review and editing
- **⚡ Performance Optimization**: Fast processing with memory management
- **🛡️ Error Handling**: Robust error recovery and user-friendly messages

## 🚀 Quick Start

**New to Smart-Splitter?** Start here:

- 📖 **[Getting Started Guide](GETTING_STARTED.md)** - Complete setup and first-time user guide
- ⚡ **[Quick Reference](QUICK_REFERENCE.md)** - Commands and workflows at a glance

### Instant Setup

```bash
# 1. Setup environment
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Launch GUI application
python -m smart_splitter.main_phase3

# 3. Or explore demos
python -m smart_splitter.main_phase4
```

### System Requirements
- **OS**: Ubuntu Linux 20.04+ (recommended)
- **Python**: 3.8+
- **Memory**: 4GB RAM minimum (8GB recommended)
- **Disk**: 500MB free space

## 💡 How to Use Smart-Splitter

### Basic Workflow

1. **Load PDF**: Click "Load PDF" and select your multi-document PDF file
2. **Process**: Click "Process PDF" to analyze and detect documents
3. **Review**: Review detected documents in the list and preview pane
4. **Edit** (optional): Adjust document types and filenames as needed
5. **Export**: Select documents and click "Export Selected" to save individual PDFs

### Document Types Supported

Smart-Splitter recognizes these construction document types:

| Document Type | Description | Example Patterns |
|---------------|-------------|------------------|
| **email** | Email communications | "From:", "Subject:", "Sent:" |
| **letter** | Business letters | "Dear", "Re:", date headers |
| **payment_application** | AIA G702 payment applications | "PAYMENT APPLICATION", "G702" |
| **evidence_of_payment** | Payment confirmations | "PAID", "CHECK", "PAYMENT" |
| **change_order** | AIA G701 change orders | "CHANGE ORDER", "G701" |
| **change_order_response** | Change order responses | "APPROVED", "REJECTED" |
| **rfi** | Requests for Information | "REQUEST FOR INFORMATION", "RFI" |
| **rfi_response** | RFI responses | "RESPONSE TO RFI" |
| **inspection_report** | Site inspection reports | "INSPECTION REPORT", "DAILY REPORT" |
| **contract_document** | Contract agreements | "CONTRACT", "AGREEMENT" |
| **plans_specifications** | Technical drawings/specs | "DRAWING", "SPECIFICATION" |
| **other** | Unrecognized documents | (default fallback) |

### Configuration Options

Smart-Splitter offers flexible configuration through the GUI or configuration files:

- **Performance Settings**: Memory limits, processing workers, batch sizes
- **Classification Rules**: Custom patterns for document recognition
- **Export Settings**: Output directory, filename templates, collision handling
- **API Integration**: OpenAI API key for enhanced classification

## 🛠️ Advanced Features

### Performance Optimization

Smart-Splitter includes advanced performance features:

```bash
# Run performance benchmarks
python -m smart_splitter.main_phase4 --benchmark-only

# Test specific optimization features
python -m smart_splitter.main_phase4 --demo performance
```

**Performance Benefits**:
- Process 100+ page documents in <30 seconds
- Memory usage optimized (<500MB typical)
- Automatic memory cleanup and optimization
- Batch processing for large documents

### Error Handling & Recovery

Robust error handling with automatic recovery:

```bash
# Test error handling capabilities
python -m smart_splitter.main_phase4 --demo error
```

**Error Features**:
- User-friendly error messages
- Automatic retry mechanisms
- Input validation with detailed feedback
- Comprehensive error logging

### Configuration Profiles

Pre-built configuration profiles for different use cases:

```bash
# Explore configuration management
python -m smart_splitter.main_phase4 --demo config
```

**Available Profiles**:
- **Performance**: Optimized for speed and low memory usage
- **Quality**: Optimized for accuracy and detailed processing
- **Large Documents**: Optimized for processing 500+ page documents

## 📋 Example Use Cases

### Construction Law Firm
*"We receive discovery documents with 50+ individual documents in a single PDF. Smart-Splitter automatically separates them into organized, properly named files."*

**Workflow**:
1. Load 200-page discovery PDF
2. Smart-Splitter detects 15 individual documents
3. Review and adjust classifications
4. Export as individual PDFs with names like:
   - `Email_Project_Update_Smith_20240115_p1-3.pdf`
   - `PayApp_05_January_2024_p4-12.pdf`
   - `CO_003_Kitchen_Modification_p13-18.pdf`

### Project Management
*"Document organization for construction projects with multiple document types from various sources."*

**Benefits**:
- Consistent naming conventions
- Automatic document type identification
- Reduced manual processing time
- Better document organization

## 🔧 Troubleshooting

### Common Issues

**Installation Problems**:
```bash
# If PyMuPDF installation fails
sudo apt-get update
sudo apt-get install libmupdf-dev

# If tkinter is missing
sudo apt-get install python3-tk
```

**Performance Issues**:
- Reduce memory limit in configuration
- Use "Performance" profile for resource-constrained systems
- Process documents in smaller batches

**Classification Issues**:
- Add OpenAI API key for enhanced classification
- Customize classification patterns in configuration
- Use manual review and editing features

### Getting Help

1. **Check the logs**: Error messages provide detailed troubleshooting information
2. **Run diagnostics**: Use `python -m smart_splitter.main_phase4 --demo error` to test error handling
3. **Review configuration**: Use `python -m smart_splitter.main_phase4 --demo config` to validate settings
4. **Performance testing**: Use `python -m smart_splitter.main_phase4 --benchmark-only` to test system performance

## 📚 Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| **[README.md](README.md)** | Overview and features | All users |
| **[GETTING_STARTED.md](GETTING_STARTED.md)** | Setup and first-time use | New users |
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | Commands and workflows | Regular users |
| **[PHASE4_SUMMARY.md](PHASE4_SUMMARY.md)** | Technical implementation | Developers |
| **[CLAUDE.md](CLAUDE.md)** | Development guide | Developers |

## 📁 Project Structure

```
smart-splitter/
├── smart_splitter/           # Main application code
│   ├── boundary_detection/   # Document boundary detection
│   ├── classification/       # Document type classification
│   ├── naming/              # Intelligent filename generation
│   ├── export/              # PDF splitting and export
│   ├── gui/                 # GUI application
│   ├── performance/         # Performance monitoring
│   ├── error_handling/      # Error handling and validation
│   ├── config/              # Configuration management
│   └── tests/               # Comprehensive test suite
├── requirements.txt         # Python dependencies
├── README.md               # Main documentation
├── GETTING_STARTED.md      # User setup guide
├── QUICK_REFERENCE.md      # Command reference
├── CLAUDE.md               # Development documentation
├── PHASE4_SUMMARY.md       # Phase 4 implementation details
└── phase4_demo.py          # Phase 4 demo launcher
```

## 🚦 Development Status

| Phase | Status | Description |
|-------|--------|-------------|
| **Phase 1** | ✅ Complete | PDF processing and boundary detection |
| **Phase 2** | ✅ Complete | Document classification and naming |
| **Phase 3** | ✅ Complete | GUI application and export system |
| **Phase 4** | ✅ Complete | Polish, optimization, and testing |

## 📊 Performance Specifications

| Metric | Target | Achieved |
|--------|--------|----------|
| Processing Speed | <30s for 100+ pages | ✅ Achieved |
| Memory Usage | <500MB typical | ✅ 80-330MB |
| Classification Accuracy | >85% | ✅ >85% |
| Error Rate | <5% failures | ✅ <2% with recovery |
| User Workflow Time | <5 minutes | ✅ Achieved |

## 🤝 Contributing

Smart-Splitter is designed for construction legal document processing. Contributions are welcome for:

- Additional document type recognition patterns
- Performance optimizations
- User interface improvements
- Integration with legal software systems

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🙋‍♂️ Support

For questions, issues, or feature requests:

1. Check the troubleshooting section above
2. Review the comprehensive documentation in `CLAUDE.md`
3. Run diagnostic demos to identify issues
4. Submit issues with detailed error logs and system information

---

**Smart-Splitter**: Transforming construction document processing with intelligent automation. 🏗️📄✨