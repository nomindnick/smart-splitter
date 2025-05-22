# Smart-Splitter Quick Reference

## 🚀 Quick Start Commands

```bash
# Setup (one time)
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Launch GUI (most common)
python -m smart_splitter.main_phase3

# Test installation
python -m pytest
```

## 📱 GUI Workflow

1. **Load PDF** → Click "Load PDF" button
2. **Process** → Click "Process PDF" button  
3. **Review** → Check document list and preview
4. **Edit** → Adjust types/names if needed
5. **Export** → Select documents and click "Export Selected"

## 💻 Command Line Demos

| Command | Purpose |
|---------|---------|
| `python -m smart_splitter.main test.pdf` | Basic processing demo |
| `python -m smart_splitter.main_phase2 test.pdf` | Classification demo |
| `python -m smart_splitter.main_phase4` | Full optimization demo |
| `python -m smart_splitter.main_phase4 --demo error` | Error handling test |
| `python -m smart_splitter.main_phase4 --demo config` | Configuration management |
| `python -m smart_splitter.main_phase4 --benchmark-only` | Performance testing |

## 📋 Document Types Recognized

| Type | Examples |
|------|----------|
| **email** | "From:", "Subject:", "Sent:" |
| **payment_application** | "PAYMENT APPLICATION", "G702" |
| **change_order** | "CHANGE ORDER", "G701" |
| **rfi** | "REQUEST FOR INFORMATION" |
| **letter** | "Dear", "Re:", business letters |
| **contract_document** | "CONTRACT", "AGREEMENT" |
| **inspection_report** | "INSPECTION REPORT", "DAILY REPORT" |
| **other** | Unrecognized documents |

## ⚙️ Configuration Profiles

```bash
# Access configuration management
python -m smart_splitter.main_phase4 --demo config
```

**Available Profiles:**
- `performance` - Fast, low memory (2GB RAM systems)
- `quality` - Accurate, detailed processing
- `large_docs` - 500+ page documents

## 🔧 Common Settings

**Configuration file**: `~/.config/smart-splitter/config.json`

```json
{
  "performance": {
    "max_memory_mb": 500,
    "max_workers": 3
  },
  "api": {
    "openai_api_key": "sk-your-key-here"
  },
  "export": {
    "default_directory": "~/Documents/split_pdfs",
    "filename_collision_strategy": "rename"
  }
}
```

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| **PyMuPDF install fails** | `sudo apt-get install libmupdf-dev` |
| **GUI won't start** | `sudo apt-get install python3-tk` |
| **Memory errors** | Use performance profile, close other apps |
| **Poor classification** | Add OpenAI API key, review manually |
| **Slow processing** | Use performance profile, smaller batches |

## 📊 Performance Expectations

| Document Size | Processing Time | Memory Usage |
|---------------|-----------------|--------------|
| 10-50 pages | <10 seconds | 80-150 MB |
| 50-100 pages | 10-20 seconds | 150-250 MB |
| 100-500 pages | 20-60 seconds | 250-400 MB |
| 500+ pages | 1-3 minutes | 400-500 MB |

## 🆘 Getting Help

1. **Error messages** - Read detailed error information
2. **Run diagnostics** - `python -m smart_splitter.main_phase4 --demo error`
3. **Check performance** - `python -m smart_splitter.main_phase4 --benchmark-only`
4. **Review docs** - See [README.md](README.md) and [GETTING_STARTED.md](GETTING_STARTED.md)

## 📁 Key Files

| File | Purpose |
|------|---------|
| `README.md` | Comprehensive documentation |
| `GETTING_STARTED.md` | Step-by-step setup guide |
| `QUICK_REFERENCE.md` | This reference (you are here) |
| `PHASE4_SUMMARY.md` | Technical implementation details |
| `requirements.txt` | Python dependencies |

## ⌨️ Example Workflow

```bash
# 1. Start application
source venv/bin/activate
python -m smart_splitter.main_phase3

# 2. In GUI:
#    - Load PDF: discovery_docs.pdf (150 pages)
#    - Process: Detects 12 documents
#    - Review: Check email from Smith, PayApp #5, CO #003
#    - Export: Select all → ~/legal_docs/case_123/

# 3. Result:
#    Email_Project_Update_Smith_20240115_p1-3.pdf
#    PayApp_05_January_2024_p4-12.pdf
#    CO_003_Kitchen_Modification_p13-18.pdf
#    (+ 9 more organized documents)
```

---

**Need more help?** See [GETTING_STARTED.md](GETTING_STARTED.md) for detailed instructions.