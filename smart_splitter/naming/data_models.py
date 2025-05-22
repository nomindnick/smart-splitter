"""
Data models for file naming system
"""
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class NamingConfig:
    """Configuration for file naming generation"""
    max_filename_length: int = 200
    date_format: str = "%Y%m%d"
    include_page_numbers: bool = True
    custom_templates: Dict[str, str] = field(default_factory=dict)
    remove_invalid_chars: bool = True
    use_underscores: bool = True
    add_sequence_on_duplicate: bool = True
    
    def __post_init__(self):
        """Set default templates if not provided"""
        if not self.custom_templates:
            self.custom_templates = self._get_default_templates()
    
    def _get_default_templates(self) -> Dict[str, str]:
        """Get default filename templates for each document type"""
        return {
            'payment_application': "PayApp_{number}_{date}_{pages}",
            'change_order': "CO_{number}_{date}_{description}_{pages}",
            'email': "Email_{subject}_{from}_{date}_{pages}",
            'rfi': "RFI_{number}_{subject}_{date}_{pages}",
            'rfi_response': "RFI_Response_{number}_{date}_{pages}",
            'contract_document': "Contract_{description}_{date}_{pages}",
            'inspection_report': "Inspection_{date}_{description}_{pages}",
            'evidence_of_payment': "Payment_{type}_{date}_{amount}_{pages}",
            'change_order_response': "CO_Response_{number}_{date}_{pages}",
            'plans_specifications': "Plans_{title}_{date}_{pages}",
            'letter': "Letter_{date}_{subject}_{pages}",
            'other': "Document_{date}_{pages}",
            'default': "{type}_{date}_{pages}"
        }