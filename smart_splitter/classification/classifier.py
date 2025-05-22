"""
Document classification system with rule-based and API-based classification
"""
import re
import json
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import asdict

from .data_models import ClassificationResult, ClassificationConfig, DocumentType, ClassificationMethod
from .feedback import FeedbackLearningSystem

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class DocumentClassifier:
    """Document classifier using rule-based patterns and OpenAI API fallback"""
    
    def __init__(self, config: ClassificationConfig, api_key: Optional[str] = None, 
                 enable_feedback_learning: bool = True):
        """
        Initialize document classifier
        
        Args:
            config: Classification configuration
            api_key: OpenAI API key (required for API classification)
            enable_feedback_learning: Enable feedback learning system
        """
        self.config = config
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        
        # Initialize feedback learning system
        self.feedback_system = None
        if enable_feedback_learning:
            try:
                self.feedback_system = FeedbackLearningSystem()
                self.logger.info("Feedback learning system initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize feedback system: {e}")
                self.feedback_system = None
        
        # Initialize OpenAI client if available and API key provided
        self.openai_client = None
        if OPENAI_AVAILABLE and api_key:
            try:
                self.openai_client = OpenAI(api_key=api_key)
                self.logger.info("OpenAI client initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.openai_client = None
        elif api_key and not OPENAI_AVAILABLE:
            self.logger.warning("OpenAI package not available. Install with: pip install openai")
    
    def classify_document(self, text_sample: str, page_range: Optional[Tuple[int, int]] = None) -> ClassificationResult:
        """
        Classify a single document using rule-based patterns first, then API if needed
        
        Args:
            text_sample: Text content of the document
            page_range: Optional page range tuple (start, end)
            
        Returns:
            ClassificationResult with classification details
        """
        if not text_sample or not text_sample.strip():
            return ClassificationResult(
                document_type=DocumentType.OTHER.value,
                confidence=0.0,
                method_used=ClassificationMethod.FALLBACK.value,
                extracted_info={"error": "Empty text sample"}
            )
        
        # Truncate text if too long
        if len(text_sample) > self.config.max_input_chars:
            text_sample = text_sample[:self.config.max_input_chars]
        
        # Try rule-based classification first
        rule_result = self._classify_by_rules(text_sample)
        
        # If rule-based classification is confident enough, return it
        if rule_result.confidence >= self.config.confidence_threshold:
            self.logger.debug(f"Rule-based classification successful: {rule_result.document_type}")
            # Record classification for feedback learning
            if self.feedback_system:
                self.feedback_system.record_classification(rule_result.document_type)
            return rule_result
        
        # Try API classification if available and rule-based wasn't confident
        if self.openai_client:
            try:
                api_result = self._classify_by_api(text_sample)
                # Combine confidence scores (weighted average)
                combined_confidence = (rule_result.confidence * 0.3 + api_result.confidence * 0.7)
                
                # Use API result if it's more confident
                if api_result.confidence > rule_result.confidence:
                    api_result.confidence = combined_confidence
                    self.logger.debug(f"API classification used: {api_result.document_type}")
                    return api_result
                else:
                    rule_result.confidence = combined_confidence
                    self.logger.debug(f"Rule-based result preferred: {rule_result.document_type}")
                    return rule_result
                    
            except Exception as e:
                self.logger.warning(f"API classification failed: {e}")
        
        # Return rule-based result or fallback
        if rule_result.confidence > 0.3:
            self.logger.debug(f"Using rule-based result with low confidence: {rule_result.document_type}")
            return rule_result
        else:
            self.logger.debug("Falling back to 'other' classification")
            return ClassificationResult(
                document_type=DocumentType.OTHER.value,
                confidence=0.1,
                method_used=ClassificationMethod.FALLBACK.value,
                extracted_info={"reason": "No patterns matched"}
            )
    
    def classify_batch(self, documents: List[str]) -> List[ClassificationResult]:
        """
        Classify multiple documents
        
        Args:
            documents: List of document text samples
            
        Returns:
            List of ClassificationResult objects
        """
        results = []
        for i, doc_text in enumerate(documents):
            try:
                result = self.classify_document(doc_text)
                results.append(result)
                self.logger.debug(f"Classified document {i+1}/{len(documents)}: {result.document_type}")
            except Exception as e:
                self.logger.error(f"Failed to classify document {i+1}: {e}")
                results.append(ClassificationResult(
                    document_type=DocumentType.OTHER.value,
                    confidence=0.0,
                    method_used=ClassificationMethod.FALLBACK.value,
                    extracted_info={"error": str(e)}
                ))
        
        return results
    
    def add_rule_pattern(self, document_type: str, pattern: str):
        """
        Add a new rule pattern for document classification
        
        Args:
            document_type: Document type to add pattern for
            pattern: Regex pattern to add
        """
        if document_type not in self.config.rule_patterns:
            self.config.rule_patterns[document_type] = []
        
        if pattern not in self.config.rule_patterns[document_type]:
            self.config.rule_patterns[document_type].append(pattern)
            self.logger.info(f"Added pattern for {document_type}: {pattern}")
    
    def _classify_by_rules(self, text: str) -> ClassificationResult:
        """
        Classify document using rule-based patterns
        
        Args:
            text: Document text to classify
            
        Returns:
            ClassificationResult from rule-based classification
        """
        best_match = None
        best_confidence = 0.0
        best_type = DocumentType.OTHER.value
        
        # Normalize text for pattern matching
        text_upper = text.upper()
        
        for doc_type, patterns in self.config.rule_patterns.items():
            confidence = 0.0
            matches = []
            
            for pattern in patterns:
                try:
                    if re.search(pattern, text_upper, re.IGNORECASE | re.MULTILINE):
                        matches.append(pattern)
                except re.error as e:
                    self.logger.warning(f"Invalid regex pattern '{pattern}': {e}")
                    continue
            
            # Calculate confidence based on pattern matches
            if matches:
                # Base confidence of 0.6 for 1 match, +0.2 for each additional match
                confidence = min(0.6 + (len(matches) - 1) * 0.2, 1.0)
                
                # Apply feedback learning adjustment if available
                if self.feedback_system:
                    adjustment = self.feedback_system.get_confidence_adjustment(doc_type)
                    confidence *= adjustment
                    self.logger.debug(f"Applied feedback adjustment for {doc_type}: {adjustment}")
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_type = doc_type
                best_match = matches
        
        extracted_info = {}
        if best_match:
            extracted_info["matched_patterns"] = best_match
            extracted_info["pattern_count"] = len(best_match)
        
        return ClassificationResult(
            document_type=best_type,
            confidence=best_confidence,
            method_used=ClassificationMethod.RULE_BASED.value,
            extracted_info=extracted_info
        )
    
    def _classify_by_api(self, text: str) -> ClassificationResult:
        """
        Classify document using OpenAI API
        
        Args:
            text: Document text to classify
            
        Returns:
            ClassificationResult from API classification
        """
        if not self.openai_client:
            raise ValueError("OpenAI client not available")
        
        # Prepare document types list for prompt
        valid_types = [dt.value for dt in DocumentType]
        types_str = ", ".join(valid_types)
        
        prompt = f"""Classify this construction legal document into one of these categories:
{types_str}

Document text (first 1000 chars):
{text[:1000]}

Return only the category name, nothing else."""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.config.api_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.api_temperature,
                max_tokens=self.config.max_output_tokens,
                timeout=self.config.api_timeout
            )
            
            result_text = response.choices[0].message.content.strip().lower()
            
            # Validate response
            if result_text in valid_types:
                confidence = 0.8  # API results get high confidence
                return ClassificationResult(
                    document_type=result_text,
                    confidence=confidence,
                    method_used=ClassificationMethod.API.value,
                    extracted_info={"api_model": self.config.api_model},
                    raw_response=result_text
                )
            else:
                self.logger.warning(f"API returned invalid type: {result_text}")
                return ClassificationResult(
                    document_type=DocumentType.OTHER.value,
                    confidence=0.2,
                    method_used=ClassificationMethod.API.value,
                    extracted_info={"error": "Invalid API response", "raw_response": result_text}
                )
                
        except Exception as e:
            self.logger.error(f"API classification error: {e}")
            raise
    
    def get_classification_stats(self) -> Dict[str, int]:
        """
        Get statistics about available classification patterns
        
        Returns:
            Dictionary with pattern counts by document type
        """
        stats = {}
        for doc_type, patterns in self.config.rule_patterns.items():
            stats[doc_type] = len(patterns)
        
        return stats
    
    def record_correction(self, original_type: str, corrected_type: str, 
                         confidence: float, text_sample: str):
        """
        Record a user correction for feedback learning
        
        Args:
            original_type: Original classification
            corrected_type: User's corrected classification
            confidence: Original confidence score
            text_sample: Sample of document text
        """
        if self.feedback_system:
            self.feedback_system.record_correction(
                original_type, corrected_type, confidence, text_sample
            )
    
    def get_feedback_report(self) -> Dict[str, Dict[str, float]]:
        """
        Get feedback learning accuracy report
        
        Returns:
            Dictionary with accuracy metrics by document type
        """
        if self.feedback_system:
            return self.feedback_system.get_accuracy_report()
        return {}
    
    def suggest_pattern_improvements(self) -> Dict[str, List[str]]:
        """
        Get suggested pattern improvements based on user corrections
        
        Returns:
            Dictionary of document types to suggested patterns
        """
        if self.feedback_system:
            return self.feedback_system.suggest_pattern_improvements()
        return {}