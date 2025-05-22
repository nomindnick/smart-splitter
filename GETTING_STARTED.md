# Getting Started with Smart-Splitter

This guide will walk you through setting up and using Smart-Splitter for the first time. Smart-Splitter is designed to automatically process multi-document PDFs commonly found in construction legal disputes.

## 📋 Prerequisites

Before installing Smart-Splitter, ensure your system meets these requirements:

### System Requirements
- **Operating System**: Ubuntu Linux 20.04+ (recommended), other Linux distributions may work
- **Python**: Version 3.8 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended for large documents
- **Disk Space**: 500MB free space (more for document processing)
- **Display**: GUI requires X11 display server

### Check Your System
```bash
# Check Python version
python3 --version  # Should be 3.8+

# Check available memory
free -h  # Should show at least 4GB

# Check disk space
df -h  # Should have 500MB+ free space
```

## 🚀 Installation

### Step 1: Download Smart-Splitter

```bash
# Clone the repository (replace with actual repository URL)
git clone <repository-url>
cd smart-splitter

# Or download and extract the ZIP file
# wget <download-url>
# unzip smart-splitter.zip
# cd smart-splitter
```

### Step 2: Set Up Python Environment

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Your prompt should change to show (venv)
```

### Step 3: Install Dependencies

```bash
# Install required Python packages
pip install -r requirements.txt

# This will install:
# - PyMuPDF (PDF processing)
# - Pillow (image handling)
# - OpenAI (API integration)
# - psutil (performance monitoring)
# - python-dotenv (configuration)
```

### Step 4: Verify Installation

```bash
# Run the test suite to verify everything works
python -m pytest

# You should see output like:
# ===== 83 passed, 5 warnings in 0.30s =====
```

If tests fail, see the [Troubleshooting](#troubleshooting) section below.

## 🖥️ First Run

### Option 1: GUI Application (Recommended)

Start with the graphical user interface for the easiest experience:

```bash
# Make sure you're in the smart-splitter directory with venv activated
source venv/bin/activate

# Launch the GUI application
python -m smart_splitter.main_phase3
```

The GUI window will open with:
- **File menu**: Load PDF files
- **Document list**: View detected documents
- **Preview pane**: See document pages and edit details
- **Export controls**: Save individual PDFs

### Option 2: Command Line Demos

Explore different features through command-line demos:

```bash
# Phase 1: Basic PDF processing and boundary detection
python -m smart_splitter.main test_document.pdf

# Phase 2: Classification and filename generation
python -m smart_splitter.main_phase2 test_document.pdf

# Phase 4: Performance and optimization features
python -m smart_splitter.main_phase4
```

## 📖 Using Smart-Splitter

### Basic Workflow

1. **Prepare Your PDF**
   - Ensure your PDF contains multiple documents (emails, letters, forms, etc.)
   - File should be readable (not password protected)
   - Recommended: Under 500 pages for optimal performance

2. **Load and Process**
   ```bash
   # Start the GUI
   python -m smart_splitter.main_phase3
   ```
   - Click "Load PDF" and select your file
   - Click "Process PDF" to analyze the document
   - Wait for processing to complete (progress bar will show status)

3. **Review Results**
   - View detected documents in the left panel
   - Click documents to preview in the right panel
   - Check document types and filenames
   - Make adjustments as needed

4. **Export Documents**
   - Select documents to export (checkboxes in list)
   - Choose output directory
   - Click "Export Selected"
   - Individual PDF files will be created

### Example: Processing Legal Discovery Documents

Let's walk through a typical use case:

**Scenario**: You have a 50-page PDF containing discovery documents with emails, payment applications, and change orders.

1. **Load the PDF**:
   - File → Load PDF → select your discovery document
   - Status shows "PDF loaded: 50 pages"

2. **Process**:
   - Click "Process PDF"
   - Smart-Splitter analyzes and detects 8 separate documents
   - Each document is classified and given a filename

3. **Review**:
   - Document 1: Email from Smith to Jones (pages 1-3)
   - Document 2: Payment Application #5 (pages 4-12)
   - Document 3: Change Order #003 (pages 13-18)
   - ... and so on

4. **Edit if needed**:
   - Change document type if misclassified
   - Edit filename for better organization
   - Adjust page ranges if boundaries are incorrect

5. **Export**:
   - Select all documents or specific ones
   - Choose output folder: `/home/user/legal_docs/discovery/`
   - Export creates files like:
     - `Email_Project_Update_Smith_20240115_p1-3.pdf`
     - `PayApp_05_January_2024_p4-12.pdf`
     - `CO_003_Kitchen_Modification_p13-18.pdf`

## ⚙️ Configuration

### Basic Configuration

Smart-Splitter works well with default settings, but you can customize:

```bash
# Explore configuration options
python -m smart_splitter.main_phase4 --demo config
```

### Adding OpenAI API Key (Optional)

For enhanced document classification:

1. **Get API Key**: Sign up at [OpenAI](https://platform.openai.com/)
2. **Configure**: 
   ```bash
   # Create configuration directory
   mkdir -p ~/.config/smart-splitter
   
   # Edit configuration
   nano ~/.config/smart-splitter/config.json
   ```
3. **Add API Key**:
   ```json
   {
     "api": {
       "openai_api_key": "sk-your-api-key-here"
     }
   }
   ```

### Performance Profiles

Choose a profile based on your needs:

```bash
# Performance profile: Fast processing, lower memory
python -m smart_splitter.main_phase4 --demo config
# Select "performance" profile

# Quality profile: More accurate classification
# Select "quality" profile

# Large docs profile: Optimized for 500+ page documents
# Select "large_docs" profile
```

## 🔧 Troubleshooting

### Common Installation Issues

**PyMuPDF Installation Fails**:
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install libmupdf-dev

# Retry installation
pip install PyMuPDF
```

**Tkinter Missing (GUI won't start)**:
```bash
# Install tkinter
sudo apt-get install python3-tk

# Test
python3 -c "import tkinter; print('Tkinter works!')"
```

**Permission Errors**:
```bash
# Make sure you own the directory
sudo chown -R $USER:$USER smart-splitter/

# Use virtual environment
source venv/bin/activate
```

### Common Usage Issues

**PDF Won't Load**:
- Ensure PDF isn't password protected
- Check file permissions (readable)
- Try with a smaller test PDF first

**Poor Classification Results**:
- Add OpenAI API key for better accuracy
- Review and edit classifications manually
- Check if document contains clear text (not scanned images)

**Performance Issues**:
```bash
# Test system performance
python -m smart_splitter.main_phase4 --benchmark-only

# Use performance profile for slower systems
python -m smart_splitter.main_phase4 --demo config
```

**Memory Errors**:
```bash
# Check available memory
free -h

# Use performance profile with lower memory limits
# Process smaller documents
# Close other applications
```

### Getting Help

1. **Check Error Messages**: Smart-Splitter provides detailed error information
2. **Run Diagnostics**:
   ```bash
   # Test error handling
   python -m smart_splitter.main_phase4 --demo error
   
   # Test performance
   python -m smart_splitter.main_phase4 --demo performance
   ```
3. **Review Logs**: Check console output for detailed error information
4. **Test with Sample Data**: Start with small, simple PDFs to verify functionality

## 💡 Tips for Best Results

### Document Preparation
- **Clean PDFs work best**: Text-based PDFs give better results than scanned images
- **Organize source documents**: Well-formatted source documents improve boundary detection
- **Test with samples**: Start with small, known documents to understand the system

### Processing Tips
- **Review before export**: Always review detected boundaries and classifications
- **Use manual editing**: Fine-tune results for perfect organization
- **Batch processing**: Process similar document types together for consistency

### Performance Optimization
- **Use appropriate profiles**: Choose profile based on system capabilities
- **Process in chunks**: For very large documents, consider splitting manually first
- **Monitor memory**: Keep an eye on system resources during processing

## 🎯 Next Steps

After completing this guide, you should be able to:
- ✅ Install and run Smart-Splitter
- ✅ Process multi-document PDFs
- ✅ Review and edit results
- ✅ Export individual documents
- ✅ Configure the system for your needs

### Advanced Features to Explore

1. **Performance Monitoring**:
   ```bash
   python -m smart_splitter.main_phase4 --demo performance
   ```

2. **Custom Configuration Profiles**:
   ```bash
   python -m smart_splitter.main_phase4 --demo config
   ```

3. **Error Handling and Recovery**:
   ```bash
   python -m smart_splitter.main_phase4 --demo error
   ```

4. **Integration Testing**:
   ```bash
   python -m smart_splitter.main_phase4 --demo integration
   ```

### Recommended Workflow

1. **Start Simple**: Use GUI with small test documents
2. **Learn Patterns**: Understand how your documents are classified
3. **Customize**: Adjust settings and profiles for your specific needs
4. **Scale Up**: Process larger, more complex document sets
5. **Automate**: Consider batch processing for regular workflows

---

**Welcome to Smart-Splitter!** 🎉 

You're now ready to transform your document processing workflow with intelligent automation. For more detailed information, see the main [README.md](README.md) and [CLAUDE.md](CLAUDE.md) documentation.