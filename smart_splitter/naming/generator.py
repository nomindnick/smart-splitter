"""
File naming generator with intelligent metadata extraction
"""
import re
import os
import logging
from datetime import datetime
from typing import Dict, Tuple, Optional, Set
from pathlib import Path

from .data_models import NamingConfig


class FileNameGenerator:
    """Generate intelligent filenames for split documents"""
    
    def __init__(self, config: NamingConfig):
        """
        Initialize filename generator
        
        Args:
            config: Naming configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._used_filenames: Set[str] = set()
    
    def generate_filename(self, doc_text: str, doc_type: str, 
                         page_range: Tuple[int, int], 
                         output_dir: Optional[str] = None) -> str:
        """
        Generate filename for a document
        
        Args:
            doc_text: Document text content
            doc_type: Classified document type
            page_range: Tuple of (start_page, end_page)
            output_dir: Output directory to check for duplicates
            
        Returns:
            Generated filename (without extension)
        """
        # Extract key information from document text
        extracted_info = self.extract_key_info(doc_text, doc_type)
        
        # Get appropriate template
        template = self._get_template(doc_type)
        
        # Build filename components
        components = self._build_components(extracted_info, doc_type, page_range)
        
        # Apply template
        filename = self._apply_template(template, components)
        
        # Sanitize filename
        filename = self.sanitize_filename(filename)
        
        # Handle duplicates if output directory specified
        if output_dir:
            filename = self._handle_duplicates(filename, output_dir)
        
        self._used_filenames.add(filename)
        self.logger.debug(f"Generated filename: {filename}")
        
        return filename
    
    def extract_key_info(self, text: str, doc_type: str) -> Dict[str, str]:
        """
        Extract key information from document text based on document type
        
        Args:
            text: Document text content
            doc_type: Document type
            
        Returns:
            Dictionary of extracted information
        """
        info = {}
        
        # Get extraction patterns for this document type
        patterns = self._get_extraction_patterns().get(doc_type, {})
        
        # Apply patterns to extract information
        for key, pattern in patterns.items():
            try:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    # Take the first capturing group or the whole match
                    value = match.group(1) if match.groups() else match.group(0)
                    info[key] = self._clean_extracted_value(value)
            except re.error as e:
                self.logger.warning(f"Invalid regex pattern for {key}: {e}")
                continue
        
        # Add current date as fallback
        if 'date' not in info:
            info['date'] = datetime.now().strftime(self.config.date_format)
        
        self.logger.debug(f"Extracted info for {doc_type}: {info}")
        return info
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to be valid for filesystem
        
        Args:
            filename: Raw filename to sanitize
            
        Returns:
            Sanitized filename
        """
        if not filename:
            return "document"
        
        # Remove invalid characters
        if self.config.remove_invalid_chars:
            # Remove/replace invalid characters for Linux/Windows compatibility
            invalid_chars = r'[<>:"|?*\\/]'
            filename = re.sub(invalid_chars, '', filename)
        
        # Replace spaces with underscores if configured
        if self.config.use_underscores:
            filename = re.sub(r'\s+', '_', filename)
        
        # Remove multiple consecutive underscores/hyphens
        filename = re.sub(r'[_-]+', '_', filename)
        
        # Remove leading/trailing underscores
        filename = filename.strip('_-')
        
        # Ensure filename is not empty
        if not filename:
            filename = "document"
        
        # Truncate if too long
        if len(filename) > self.config.max_filename_length:
            filename = filename[:self.config.max_filename_length]
            # Try to break at word boundary
            if '_' in filename:
                parts = filename.split('_')
                filename = '_'.join(parts[:-1])  # Remove last partial part
        
        return filename
    
    def _get_template(self, doc_type: str) -> str:
        """Get filename template for document type"""
        return self.config.custom_templates.get(
            doc_type, 
            self.config.custom_templates.get('default', '{type}_{date}_{pages}')
        )
    
    def _build_components(self, extracted_info: Dict[str, str], 
                         doc_type: str, page_range: Tuple[int, int]) -> Dict[str, str]:
        """Build filename components for template substitution"""
        components = extracted_info.copy()
        
        # Add standard components
        components['type'] = doc_type.replace('_', '')
        
        # Add page range
        if self.config.include_page_numbers:
            start, end = page_range
            if start == end:
                components['pages'] = f"p{start}"
            else:
                components['pages'] = f"p{start}-{end}"
        else:
            components['pages'] = ""
        
        # Clean all component values
        for key, value in components.items():
            if isinstance(value, str):
                components[key] = self._clean_component_value(value)
        
        return components
    
    def _apply_template(self, template: str, components: Dict[str, str]) -> str:
        """Apply template with component substitution"""
        try:
            # Create a safe formatter that handles missing keys
            class SafeDict(dict):
                def __missing__(self, key):
                    return ''  # Return empty string for missing keys
            
            safe_components = SafeDict(components)
            
            # Replace template variables
            filename = template.format_map(safe_components)
            
            # Clean up any empty substitutions
            filename = re.sub(r'_{2,}', '_', filename)  # Multiple underscores
            filename = re.sub(r'_+$', '', filename)     # Trailing underscores
            filename = re.sub(r'^_+', '', filename)     # Leading underscores
            
            return filename
            
        except KeyError as e:
            self.logger.warning(f"Template variable not found: {e}")
            # Fallback to simple template
            return f"{components.get('type', 'document')}_{components.get('date', '')}_{components.get('pages', '')}"
    
    def _handle_duplicates(self, filename: str, output_dir: str) -> str:
        """Handle duplicate filenames by adding sequence numbers"""
        if not self.config.add_sequence_on_duplicate:
            return filename
        
        output_path = Path(output_dir)
        base_name = filename
        counter = 1
        
        # Check for existing files with .pdf extension
        while (output_path / f"{filename}.pdf").exists() or filename in self._used_filenames:
            filename = f"{base_name}_{counter:02d}"
            counter += 1
            
            # Prevent infinite loop
            if counter > 999:
                break
        
        return filename
    
    def _clean_extracted_value(self, value: str) -> str:
        """Clean extracted value for use in filename"""
        if not value:
            return ""
        
        # Basic cleaning
        value = value.strip()
        
        # Remove extra whitespace
        value = re.sub(r'\s+', ' ', value)
        
        # Truncate long values
        if len(value) > 50:
            value = value[:47] + "..."
        
        return value
    
    def _clean_component_value(self, value: str) -> str:
        """Clean component value for filename use"""
        if not value:
            return ""
        
        # More aggressive cleaning for filename components
        value = value.strip()
        
        # Remove problematic characters
        value = re.sub(r'[^\w\s\-.]', '', value)
        
        # Limit length for components
        if len(value) > 30:
            value = value[:30]
        
        return value
    
    def _get_extraction_patterns(self) -> Dict[str, Dict[str, str]]:
        """Get regex patterns for extracting information by document type"""
        return {
            'payment_application': {
                'number': r"(?:APPLICATION|PAY.*APP).*?(?:NO|#)\.?\s*(\d+)",
                'date': r"(?:DATE|THROUGH|FOR\s+PERIOD).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                'amount': r"\$\s*([\d,]+\.?\d*)",
                'period': r"PERIOD.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
            },
            'change_order': {
                'number': r"CHANGE\s*ORDER.*?(?:NO|#)\.?\s*(\d+)",
                'date': r"(?:DATE|DATED).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                'description': r"(?:DESCRIPTION|REASON)[:\s]*([^\n]{10,50})",
                'amount': r"\$\s*([\d,]+\.?\d*)"
            },
            'email': {
                'from': r"From:\s*([^<\n@]+)(?:@|\s)",
                'subject': r"Subject:\s*([^\n]{5,40})",
                'date': r"(?:Sent|Date).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                'to': r"To:\s*([^<\n@]+)(?:@|\s)"
            },
            'rfi': {
                'number': r"RFI.*?(?:NO|#)\.?\s*(\d+)",
                'date': r"(?:DATE|DATED).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                'subject': r"(?:SUBJECT|RE|REGARDING):\s*([^\n]{10,40})",
                'from': r"(?:FROM|PREPARED BY):\s*([^\n]{5,30})"
            },
            'rfi_response': {
                'number': r"RFI.*?(?:NO|#)\.?\s*(\d+)",
                'date': r"(?:DATE|DATED|RESPONSE\s+DATE).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                'subject': r"(?:SUBJECT|RE|REGARDING):\s*([^\n]{10,40})"
            },
            'contract_document': {
                'date': r"(?:DATE|DATED|EXECUTED).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                'description': r"(?:CONTRACT|AGREEMENT)\s+(?:FOR|BETWEEN)?\s*([^\n]{10,40})",
                'parties': r"BETWEEN\s+(.+?)\s+AND"
            },
            'inspection_report': {
                'date': r"(?:INSPECTION\s+DATE|DATE\s+OF\s+VISIT).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                'description': r"(?:INSPECTION\s+OF|LOCATION):\s*([^\n]{10,40})",
                'inspector': r"(?:INSPECTOR|PREPARED\s+BY):\s*([^\n]{5,30})"
            },
            'evidence_of_payment': {
                'date': r"(?:DATE|DATED|CHECK\s+DATE).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                'amount': r"\$\s*([\d,]+\.?\d*)",
                'type': r"(CHECK|WIRE|ACH|PAYMENT)",
                'number': r"(?:CHECK|WIRE|REF).*?(?:NO|#)\.?\s*(\w+)"
            },
            'change_order_response': {
                'number': r"(?:CHANGE\s*ORDER|CO).*?(?:NO|#)\.?\s*(\d+)",
                'date': r"(?:DATE|DATED|RESPONSE\s+DATE).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                'status': r"(ACCEPT|REJECT|APPROVE|DENY)"
            },
            'plans_specifications': {
                'title': r"(?:DRAWING|PLAN|SPEC).*?TITLE[:\s]*([^\n]{10,40})",
                'number': r"(?:DRAWING|SHEET).*?(?:NO|#)\.?\s*([A-Z0-9\-]+)",
                'date': r"(?:DATE|REVISION\s+DATE).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                'revision': r"REVISION[:\s]*([A-Z0-9]+)"
            },
            'letter': {
                'date': r"(?:DATE|DATED).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                'subject': r"(?:RE|SUBJECT|REGARDING):\s*([^\n]{10,40})",
                'from': r"(?:FROM|SINCERELY|SIGNED).*?([A-Z][a-z]+\s+[A-Z][a-z]+)"
            }
        }
    
    def reset_used_filenames(self):
        """Reset the set of used filenames"""
        self._used_filenames.clear()
    
    def get_used_filenames(self) -> Set[str]:
        """Get set of filenames that have been used"""
        return self._used_filenames.copy()