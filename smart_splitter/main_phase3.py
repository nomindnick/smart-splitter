#!/usr/bin/env python3
"""
Phase 3 main application for Smart-Splitter.

This module provides the main entry point for the GUI application
demonstrating the complete Phase 3 functionality including the
GUI interface and export system.
"""

import sys
import os
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from smart_splitter.gui.main_window import SmartSplitterGUI


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('smart_splitter.log')
        ]
    )


def main():
    """Main entry point for the Phase 3 application."""
    print("=" * 60)
    print("Smart-Splitter Phase 3 - GUI Application & Export System")
    print("=" * 60)
    print()
    
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize and run the GUI application
        logger.info("Starting Smart-Splitter GUI application")
        app = SmartSplitterGUI()
        
        print("📱 Launching Smart-Splitter GUI...")
        print()
        print("Features available in Phase 3:")
        print("• Load and process PDF documents")
        print("• Interactive document list with selection")
        print("• Document preview with page thumbnails")
        print("• Edit document types and filenames")
        print("• Export individual or all documents")
        print("• Progress tracking and status updates")
        print()
        print("Instructions:")
        print("1. Click 'Load PDF' to select a source document")
        print("2. Click 'Process' to analyze and split the document")
        print("3. Review and edit document classifications")
        print("4. Select documents for export")
        print("5. Click 'Export All' or 'Export Selected'")
        print()
        print("The GUI window will open shortly...")
        print("Close the window or press Ctrl+Q to exit.")
        print()
        
        # Run the application
        app.run()
        
        logger.info("Smart-Splitter GUI application closed")
        print("\n✅ Smart-Splitter GUI session completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Application interrupted by user")
        logger.info("Application interrupted by user")
        
    except Exception as e:
        print(f"\n❌ Application error: {str(e)}")
        logger.error(f"Application error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()