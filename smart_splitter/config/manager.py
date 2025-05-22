"""Configuration management for Smart-Splitter."""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Manages application configuration."""
    
    DEFAULT_CONFIG = {
        "api": {
            "openai_api_key": "",
            "model": "gpt-4.1-nano",
            "max_tokens": 10,
            "timeout": 30
        },
        "processing": {
            "min_document_length": 1,
            "confidence_threshold": 0.7,
            "max_input_chars": 1000
        },
        "ui": {
            "window_width": 1200,
            "window_height": 800,
            "preview_size": 300
        },
        "export": {
            "default_directory": "~/Documents/split_pdfs",
            "filename_max_length": 200,
            "include_page_numbers": True
        },
        "patterns": {
            "boundary_patterns": {
                "payment_application": [
                    r"PAYMENT APPLICATION\s*(?:NO|#)\.?\s*\d+",
                    r"APPLICATION FOR PAYMENT",
                    r"(?:AIA|FORM)\s*(?:DOCUMENT\s*)?G702"
                ],
                "change_order": [
                    r"CHANGE ORDER\s*(?:NO|#)\.?\s*\d+",
                    r"(?:AIA|FORM)\s*(?:DOCUMENT\s*)?G701"
                ],
                "email": [
                    r"From:\s*.+@.+",
                    r"Subject:\s*.+",
                    r"Sent:\s*\w+,\s*\w+\s*\d+"
                ],
                "letter": [
                    r"Dear\s+(?:Mr\.|Ms\.|Mrs\.|Dr\.|\w+)",
                    r"Re:\s*.+",
                    r"^\s*\w+,\s*\w+\s*\d{1,2},\s*\d{4}"
                ],
                "rfi": [
                    r"REQUEST FOR INFORMATION",
                    r"RFI\s*(?:NO|#)\.?\s*\d+"
                ],
                "contract": [
                    r"CONTRACT\s*(?:AGREEMENT|FOR)",
                    r"SUBCONTRACT\s*AGREEMENT",
                    r"AGREEMENT\s*BETWEEN"
                ],
                "inspection": [
                    r"INSPECTION\s*REPORT",
                    r"DAILY\s*(?:FIELD\s*)?REPORT",
                    r"SITE\s*VISIT\s*REPORT"
                ]
            },
            "classification_rules": {
                "email": [
                    r"From:\s*.+@.+",
                    r"To:\s*.+@.+",
                    r"Subject:\s*.+"
                ],
                "payment_application": [
                    r"APPLICATION FOR PAYMENT",
                    r"SCHEDULE OF VALUES",
                    r"(?:AIA|FORM)\s*G702"
                ],
                "change_order": [
                    r"CHANGE ORDER",
                    r"MODIFICATION TO CONTRACT",
                    r"(?:AIA|FORM)\s*G701"
                ],
                "rfi": [
                    r"REQUEST FOR INFORMATION",
                    r"RFI\s*(?:NO|#)\.?\s*\d+"
                ],
                "contract_document": [
                    r"CONTRACT AGREEMENT",
                    r"SUBCONTRACT",
                    r"GENERAL CONDITIONS"
                ]
            },
            "api": {
                "model": "gpt-4o-mini",
                "temperature": 0.0,
                "max_tokens": 10,
                "timeout": 10,
                "confidence_threshold": 0.7
            },
            "naming": {
                "max_filename_length": 200,
                "date_format": "%Y%m%d",
                "include_page_numbers": True,
                "remove_invalid_chars": True,
                "use_underscores": True,
                "add_sequence_on_duplicate": True,
                "templates": {
                    "payment_application": "PayApp_{number}_{date}_{pages}",
                    "change_order": "CO_{number}_{date}_{description}_{pages}",
                    "email": "Email_{subject}_{from}_{date}_{pages}",
                    "rfi": "RFI_{number}_{subject}_{date}_{pages}",
                    "contract_document": "Contract_{description}_{date}_{pages}",
                    "default": "{type}_{date}_{pages}"
                }
            },
            "export": {
                "output_directory": "./output",
                "overwrite_existing": False,
                "create_subdirectories": True,
                "filename_collision_strategy": "rename"
            }
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path:
            self.config_path = Path(config_path)
        else:
            config_dir = Path.home() / ".config" / "smart-splitter"
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_path = config_dir / "config.json"
        
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create with defaults."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                return self._merge_with_defaults(config)
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
        
        self.save_config(self.DEFAULT_CONFIG)
        return self.DEFAULT_CONFIG.copy()
    
    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge loaded config with defaults to ensure all keys exist."""
        def merge_dict(default: Dict, loaded: Dict) -> Dict:
            result = default.copy()
            for key, value in loaded.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dict(result[key], value)
                else:
                    result[key] = value
            return result
        
        return merge_dict(self.DEFAULT_CONFIG, config)
    
    def save_config(self, config: Optional[Dict[str, Any]] = None):
        """Save configuration to file."""
        if config is None:
            config = self.config
        
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get_setting(self, key_path: str, default=None):
        """Get a setting using dot notation (e.g., 'api.openai_api_key')."""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def update_setting(self, key_path: str, value: Any):
        """Update a setting using dot notation."""
        keys = key_path.split('.')
        current = self.config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
        self.save_config()


class PatternManager:
    """Manages boundary detection and classification patterns."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
    
    def get_boundary_patterns(self) -> Dict[str, list]:
        """Get boundary detection patterns."""
        return self.config_manager.get_setting("patterns.boundary_patterns", {})
    
    def get_classification_rules(self) -> Dict[str, list]:
        """Get classification rule patterns."""
        return self.config_manager.get_setting("patterns.classification_rules", {})
    
    def add_custom_pattern(self, category: str, pattern: str, pattern_type: str = "boundary"):
        """Add a custom pattern to the configuration."""
        if pattern_type == "boundary":
            key_path = f"patterns.boundary_patterns.{category}"
        else:
            key_path = f"patterns.classification_rules.{category}"
        
        current_patterns = self.config_manager.get_setting(key_path, [])
        if pattern not in current_patterns:
            current_patterns.append(pattern)
            self.config_manager.update_setting(key_path, current_patterns)