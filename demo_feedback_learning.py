#!/usr/bin/env python3
"""
Demo script to showcase the feedback learning system
"""
import json
from pathlib import Path
from smart_splitter.classification.classifier import DocumentClassifier
from smart_splitter.classification.data_models import ClassificationConfig
from smart_splitter.config.manager import ConfigManager


def main():
    print("=== Smart-Splitter Feedback Learning Demo ===\n")
    
    # Initialize components
    config_manager = ConfigManager()
    
    # Get classification config settings
    classification_settings = {
        'rule_patterns': config_manager.get_setting('classification.rule_patterns', {}),
        'confidence_threshold': config_manager.get_setting('classification.confidence_threshold', 0.7),
        'max_input_chars': config_manager.get_setting('classification.max_input_chars', 5000),
        'api_model': config_manager.get_setting('classification.api_model', 'gpt-4o-mini'),
        'api_temperature': config_manager.get_setting('classification.api_temperature', 0.3),
        'api_timeout': config_manager.get_setting('classification.api_timeout', 30),
        'max_output_tokens': config_manager.get_setting('classification.max_output_tokens', 50)
    }
    
    classification_config = ClassificationConfig(**classification_settings)
    
    # Create classifier with feedback learning enabled
    classifier = DocumentClassifier(
        config=classification_config,
        api_key=config_manager.get_setting("api.openai_api_key"),
        enable_feedback_learning=True
    )
    
    # Example documents that might be misclassified
    test_documents = [
        {
            "text": "From: john@contractor.com\nTo: jane@owner.com\nSubject: Change Order Request\n\nPlease review the attached change order for additional work.",
            "actual_type": "email",
            "common_misclassification": "change_order"
        },
        {
            "text": "PAYMENT APPLICATION NO. 5\n\nRE: Email regarding payment\n\nPlease see the email below regarding payment application.",
            "actual_type": "payment_application", 
            "common_misclassification": "email"
        }
    ]
    
    print("1. Simulating document classifications and corrections:\n")
    
    for doc in test_documents:
        # Classify document
        result = classifier.classify_document(doc["text"])
        print(f"Document classified as: {result.document_type} (confidence: {result.confidence:.2f})")
        
        # Simulate user correction if misclassified
        if result.document_type == doc["common_misclassification"]:
            print(f"  → User corrects to: {doc['actual_type']}")
            classifier.record_correction(
                original_type=result.document_type,
                corrected_type=doc["actual_type"],
                confidence=result.confidence,
                text_sample=doc["text"]
            )
        print()
    
    # Show feedback report
    print("\n2. Feedback Learning Report:\n")
    report = classifier.get_feedback_report()
    
    if report:
        for doc_type, stats in report.items():
            print(f"{doc_type.upper()}:")
            print(f"  - Total classifications: {stats['total_classifications']}")
            print(f"  - Total corrections: {stats['total_corrections']}")
            print(f"  - Accuracy rate: {stats['accuracy_rate']:.1%}")
            print(f"  - Confidence adjustment: {stats['confidence_adjustment']:.2f}")
            if 'most_corrected_to' in stats:
                print(f"  - Most often corrected to: {stats['most_corrected_to']}")
            print()
    else:
        print("No feedback data available yet.\n")
    
    # Show pattern improvement suggestions
    print("\n3. Pattern Improvement Suggestions:\n")
    suggestions = classifier.suggest_pattern_improvements()
    
    if suggestions:
        for doc_type, patterns in suggestions.items():
            print(f"Suggested patterns for {doc_type}:")
            for pattern in patterns:
                print(f"  - {pattern}")
            print()
    else:
        print("No pattern suggestions available yet (need more corrections).\n")
    
    # Show how confidence adjusts after corrections
    print("\n4. Re-classifying with feedback adjustments:\n")
    
    for doc in test_documents:
        result = classifier.classify_document(doc["text"])
        print(f"Document now classified as: {result.document_type} (adjusted confidence: {result.confidence:.2f})")
    
    # Display feedback file location
    feedback_file = Path.home() / ".config" / "smart-splitter" / "feedback.json"
    print(f"\n5. Feedback data is stored in: {feedback_file}")
    
    if feedback_file.exists():
        print("\nFeedback file contents:")
        with open(feedback_file, 'r') as f:
            data = json.load(f)
            print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()