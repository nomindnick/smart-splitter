"""
Data models for document classification system
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class DocumentType(Enum):
    """Supported document types for classification"""
    EMAIL = "email"
    LETTER = "letter"
    PAYMENT_APPLICATION = "payment_application"
    EVIDENCE_OF_PAYMENT = "evidence_of_payment"
    CHANGE_ORDER = "change_order"
    CHANGE_ORDER_RESPONSE = "change_order_response"
    RFI = "rfi"
    RFI_RESPONSE = "rfi_response"
    INSPECTION_REPORT = "inspection_report"
    CONTRACT_DOCUMENT = "contract_document"
    PLANS_SPECIFICATIONS = "plans_specifications"
    OTHER = "other"


class ClassificationMethod(Enum):
    """Methods used for document classification"""
    RULE_BASED = "rule_based"
    API = "api"
    FALLBACK = "fallback"


@dataclass
class ClassificationResult:
    """Result of document classification"""
    document_type: str
    confidence: float
    method_used: str
    extracted_info: Dict[str, str] = field(default_factory=dict)
    raw_response: Optional[str] = None
    
    def __post_init__(self):
        """Validate classification result"""
        if not 0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0 and 1")
        
        valid_types = [dt.value for dt in DocumentType]
        if self.document_type not in valid_types:
            raise ValueError(f"Invalid document type: {self.document_type}")
        
        valid_methods = [cm.value for cm in ClassificationMethod]
        if self.method_used not in valid_methods:
            raise ValueError(f"Invalid classification method: {self.method_used}")


@dataclass
class ClassificationConfig:
    """Configuration for document classification"""
    api_model: str = "gpt-4.1-nano"
    max_input_chars: int = 1000
    confidence_threshold: float = 0.7
    rule_patterns: Dict[str, List[str]] = field(default_factory=dict)
    api_temperature: float = 0.0
    max_output_tokens: int = 10
    api_timeout: int = 10
    
    def __post_init__(self):
        """Set default rule patterns if not provided"""
        if not self.rule_patterns:
            self.rule_patterns = self._get_default_patterns()
    
    def _get_default_patterns(self) -> Dict[str, List[str]]:
        """Get default classification patterns"""
        return {
            'email': [
                r"From:\s*.+@.+",
                r"To:\s*.+@.+", 
                r"Subject:\s*.+",
                r"Sent:\s*\w+.*\d{4}",
                r"Message-ID:"
            ],
            'payment_application': [
                r"APPLICATION FOR PAYMENT",
                r"SCHEDULE OF VALUES",
                r"(?:AIA|FORM)\s*G702",
                r"PAYMENT APPLICATION\s*(?:NO|#)\.?\s*\d+",
                r"APPLICATION AND CERTIFICATE FOR PAYMENT"
            ],
            'change_order': [
                r"CHANGE ORDER",
                r"MODIFICATION TO CONTRACT",
                r"(?:AIA|FORM)\s*G701",
                r"CHANGE ORDER\s*(?:NO|#)\.?\s*\d+",
                r"CONSTRUCTION CHANGE DIRECTIVE"
            ],
            'rfi': [
                r"REQUEST FOR INFORMATION",
                r"RFI\s*(?:NO|#)\.?\s*\d+",
                r"INFORMATION REQUEST",
                r"CLARIFICATION REQUEST"
            ],
            'rfi_response': [
                r"RFI.*RESPONSE",
                r"RESPONSE TO.*RFI",
                r"INFORMATION REQUEST.*RESPONSE"
            ],
            'contract_document': [
                r"CONTRACT AGREEMENT",
                r"SUBCONTRACT",
                r"GENERAL CONDITIONS",
                r"SPECIAL CONDITIONS",
                r"CONSTRUCTION CONTRACT"
            ],
            'inspection_report': [
                r"INSPECTION REPORT",
                r"SITE VISIT REPORT",
                r"FIELD REPORT",
                r"PROGRESS INSPECTION"
            ],
            'evidence_of_payment': [
                r"CHECK\s*(?:NO|#)\.?\s*\d+",
                r"PAYMENT RECEIPT",
                r"PROOF OF PAYMENT",
                r"BANK STATEMENT",
                r"WIRE TRANSFER"
            ],
            'change_order_response': [
                r"CHANGE ORDER.*RESPONSE",
                r"RESPONSE TO.*CHANGE ORDER",
                r"CO.*ACCEPTANCE",
                r"CO.*REJECTION"
            ],
            'plans_specifications': [
                r"DRAWING\s*(?:NO|#)",
                r"SPECIFICATION",
                r"ARCHITECTURAL PLANS",
                r"TECHNICAL SPECIFICATIONS",
                r"BLUEPRINT"
            ]
        }