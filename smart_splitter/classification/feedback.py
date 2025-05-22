"""
Feedback learning system for document classification
"""
import json
import os
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, asdict

from .data_models import DocumentType


@dataclass
class CorrectionEntry:
    """Single correction entry for tracking user feedback"""
    timestamp: str
    original_type: str
    corrected_type: str
    confidence: float
    text_sample: str  # First 200 chars for pattern analysis
    
    
@dataclass
class CorrectionStats:
    """Statistics for a specific document type"""
    total_classifications: int = 0
    total_corrections: int = 0
    correction_targets: Dict[str, int] = None  # What types it was corrected TO
    
    def __post_init__(self):
        if self.correction_targets is None:
            self.correction_targets = {}
    
    @property
    def correction_rate(self) -> float:
        """Calculate correction rate (0.0 to 1.0)"""
        if self.total_classifications == 0:
            return 0.0
        return self.total_corrections / self.total_classifications
    
    @property
    def accuracy_rate(self) -> float:
        """Calculate accuracy rate (0.0 to 1.0)"""
        return 1.0 - self.correction_rate


class FeedbackLearningSystem:
    """Manages user correction feedback and improves classification accuracy"""
    
    def __init__(self, feedback_file: Optional[str] = None):
        """
        Initialize feedback learning system
        
        Args:
            feedback_file: Path to feedback JSON file (default: ~/.config/smart-splitter/feedback.json)
        """
        if feedback_file is None:
            config_dir = Path.home() / ".config" / "smart-splitter"
            config_dir.mkdir(parents=True, exist_ok=True)
            feedback_file = str(config_dir / "feedback.json")
            
        self.feedback_file = feedback_file
        self.logger = logging.getLogger(__name__)
        self.corrections: List[CorrectionEntry] = []
        self.stats: Dict[str, CorrectionStats] = defaultdict(CorrectionStats)
        
        # Load existing feedback
        self._load_feedback()
        
    def _load_feedback(self):
        """Load feedback data from file"""
        if os.path.exists(self.feedback_file):
            try:
                with open(self.feedback_file, 'r') as f:
                    data = json.load(f)
                    
                # Load corrections
                for entry_data in data.get('corrections', []):
                    self.corrections.append(CorrectionEntry(**entry_data))
                    
                # Load stats
                for doc_type, stats_data in data.get('stats', {}).items():
                    stats = CorrectionStats()
                    stats.total_classifications = stats_data.get('total_classifications', 0)
                    stats.total_corrections = stats_data.get('total_corrections', 0)
                    stats.correction_targets = stats_data.get('correction_targets', {})
                    self.stats[doc_type] = stats
                    
                self.logger.info(f"Loaded {len(self.corrections)} corrections from feedback file")
            except Exception as e:
                self.logger.warning(f"Failed to load feedback file: {e}")
    
    def _save_feedback(self):
        """Save feedback data to file"""
        try:
            data = {
                'corrections': [asdict(c) for c in self.corrections[-1000:]],  # Keep last 1000
                'stats': {
                    doc_type: {
                        'total_classifications': stats.total_classifications,
                        'total_corrections': stats.total_corrections,
                        'correction_targets': stats.correction_targets
                    }
                    for doc_type, stats in self.stats.items()
                },
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.feedback_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            self.logger.debug(f"Saved feedback to {self.feedback_file}")
        except Exception as e:
            self.logger.error(f"Failed to save feedback: {e}")
    
    def record_classification(self, document_type: str):
        """
        Record that a document was classified (increases total count)
        
        Args:
            document_type: The document type that was classified
        """
        self.stats[document_type].total_classifications += 1
        self._save_feedback()
    
    def record_correction(self, original_type: str, corrected_type: str, 
                         confidence: float, text_sample: str):
        """
        Record a user correction
        
        Args:
            original_type: Original classification
            corrected_type: User's corrected classification
            confidence: Original confidence score
            text_sample: Sample of document text
        """
        # Create correction entry
        entry = CorrectionEntry(
            timestamp=datetime.now().isoformat(),
            original_type=original_type,
            corrected_type=corrected_type,
            confidence=confidence,
            text_sample=text_sample[:200]  # Store first 200 chars
        )
        
        self.corrections.append(entry)
        
        # Update stats
        self.stats[original_type].total_corrections += 1
        if corrected_type not in self.stats[original_type].correction_targets:
            self.stats[original_type].correction_targets[corrected_type] = 0
        self.stats[original_type].correction_targets[corrected_type] += 1
        
        self._save_feedback()
        
        self.logger.info(f"Recorded correction: {original_type} -> {corrected_type}")
    
    def get_confidence_adjustment(self, document_type: str) -> float:
        """
        Get confidence adjustment factor based on historical accuracy
        
        Args:
            document_type: Document type to get adjustment for
            
        Returns:
            Adjustment factor (0.5 to 1.0)
        """
        stats = self.stats.get(document_type)
        if not stats or stats.total_classifications < 5:
            return 1.0  # No adjustment if insufficient data
        
        # Calculate adjustment based on accuracy
        # If 50% corrected, multiply confidence by 0.75
        # If 100% corrected, multiply confidence by 0.5
        correction_rate = stats.correction_rate
        adjustment = 1.0 - (correction_rate * 0.5)
        
        return max(0.5, adjustment)  # Never go below 0.5
    
    def get_alternative_types(self, document_type: str, threshold: float = 0.2) -> List[Tuple[str, float]]:
        """
        Get alternative document types based on correction history
        
        Args:
            document_type: Original document type
            threshold: Minimum correction rate to consider alternative
            
        Returns:
            List of (alternative_type, probability) tuples
        """
        stats = self.stats.get(document_type)
        if not stats or stats.total_corrections == 0:
            return []
        
        alternatives = []
        for alt_type, count in stats.correction_targets.items():
            probability = count / stats.total_corrections
            if probability >= threshold:
                alternatives.append((alt_type, probability))
                
        # Sort by probability (highest first)
        alternatives.sort(key=lambda x: x[1], reverse=True)
        return alternatives
    
    def suggest_pattern_improvements(self, min_corrections: int = 5) -> Dict[str, List[str]]:
        """
        Suggest pattern improvements based on correction history
        
        Args:
            min_corrections: Minimum corrections needed to suggest improvements
            
        Returns:
            Dictionary of document types to suggested patterns
        """
        suggestions = {}
        
        # Group corrections by original type -> corrected type
        correction_groups = defaultdict(list)
        for correction in self.corrections:
            key = (correction.original_type, correction.corrected_type)
            correction_groups[key].append(correction.text_sample)
        
        # Analyze patterns in misclassified text
        for (orig_type, correct_type), samples in correction_groups.items():
            if len(samples) >= min_corrections:
                # Find common patterns in the misclassified samples
                # This is a simplified version - could use more sophisticated NLP
                common_words = self._find_common_patterns(samples)
                
                if common_words:
                    if correct_type not in suggestions:
                        suggestions[correct_type] = []
                    
                    # Suggest patterns based on common words
                    for word in common_words[:3]:  # Top 3 patterns
                        pattern = rf"\b{re.escape(word)}\b"
                        suggestions[correct_type].append(pattern)
                        
        return suggestions
    
    def _find_common_patterns(self, text_samples: List[str]) -> List[str]:
        """
        Find common patterns in text samples
        
        Args:
            text_samples: List of text samples
            
        Returns:
            List of common words/patterns
        """
        import re
        from collections import Counter
        
        # Extract words from all samples
        all_words = []
        for sample in text_samples:
            # Extract words (alphanumeric sequences)
            words = re.findall(r'\b\w+\b', sample.upper())
            all_words.extend(words)
        
        # Count word frequencies
        word_counts = Counter(all_words)
        
        # Filter out common words and return significant ones
        common_words = []
        total_samples = len(text_samples)
        
        for word, count in word_counts.most_common(20):
            # Word should appear in at least 50% of samples
            if count >= total_samples * 0.5 and len(word) > 3:
                common_words.append(word)
                
        return common_words
    
    def get_accuracy_report(self) -> Dict[str, Dict[str, float]]:
        """
        Get accuracy report for all document types
        
        Returns:
            Dictionary with accuracy metrics by document type
        """
        report = {}
        
        for doc_type, stats in self.stats.items():
            if stats.total_classifications > 0:
                report[doc_type] = {
                    'total_classifications': stats.total_classifications,
                    'total_corrections': stats.total_corrections,
                    'accuracy_rate': stats.accuracy_rate,
                    'correction_rate': stats.correction_rate,
                    'confidence_adjustment': self.get_confidence_adjustment(doc_type)
                }
                
                # Add top correction target
                if stats.correction_targets:
                    top_target = max(stats.correction_targets.items(), 
                                   key=lambda x: x[1])
                    report[doc_type]['most_corrected_to'] = top_target[0]
                    report[doc_type]['most_corrected_to_rate'] = (
                        top_target[1] / stats.total_corrections
                    )
                    
        return report