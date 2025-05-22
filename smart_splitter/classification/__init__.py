"""
Document Classification System
"""

from .data_models import ClassificationResult, ClassificationConfig, DocumentType, ClassificationMethod
from .classifier import DocumentClassifier
from .feedback import FeedbackLearningSystem, CorrectionEntry, CorrectionStats

__all__ = [
    'ClassificationResult', 
    'ClassificationConfig', 
    'DocumentType', 
    'ClassificationMethod', 
    'DocumentClassifier',
    'FeedbackLearningSystem',
    'CorrectionEntry',
    'CorrectionStats'
]