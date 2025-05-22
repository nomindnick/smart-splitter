"""Tests for configuration management."""

import unittest
import tempfile
import json
from pathlib import Path

from smart_splitter.config.manager import ConfigManager, PatternManager


class TestConfigManager(unittest.TestCase):
    """Test configuration manager functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"
        self.config_manager = ConfigManager(str(self.config_path))
    
    def test_default_config_creation(self):
        """Test that default config is created."""
        self.assertTrue(self.config_path.exists())
        self.assertIsInstance(self.config_manager.config, dict)
        self.assertIn("api", self.config_manager.config)
        self.assertIn("processing", self.config_manager.config)
    
    def test_get_setting(self):
        """Test getting configuration settings."""
        api_key = self.config_manager.get_setting("api.openai_api_key")
        self.assertEqual(api_key, "")
        
        timeout = self.config_manager.get_setting("api.timeout")
        self.assertEqual(timeout, 30)
        
        nonexistent = self.config_manager.get_setting("nonexistent.key", "default")
        self.assertEqual(nonexistent, "default")
    
    def test_update_setting(self):
        """Test updating configuration settings."""
        self.config_manager.update_setting("api.openai_api_key", "test_key")
        
        updated_key = self.config_manager.get_setting("api.openai_api_key")
        self.assertEqual(updated_key, "test_key")
    
    def test_pattern_manager(self):
        """Test pattern manager functionality."""
        pattern_manager = PatternManager(self.config_manager)
        
        boundary_patterns = pattern_manager.get_boundary_patterns()
        self.assertIsInstance(boundary_patterns, dict)
        self.assertIn("email", boundary_patterns)
        
        classification_rules = pattern_manager.get_classification_rules()
        self.assertIsInstance(classification_rules, dict)
        self.assertIn("email", classification_rules)


if __name__ == "__main__":
    unittest.main()