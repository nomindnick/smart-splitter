#!/usr/bin/env python3
"""
Phase 4 Demo Runner for Smart-Splitter

This script demonstrates the Phase 4 polish and optimization features:
- Performance monitoring and optimization
- Enhanced error handling and recovery
- Advanced configuration management
- Comprehensive benchmarking and testing
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from smart_splitter.main_phase4 import main
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you're in the smart-splitter directory and have installed dependencies:")
    print("   pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error running Phase 4 demo: {e}")
    sys.exit(1)