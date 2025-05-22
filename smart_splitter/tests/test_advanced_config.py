"""Tests for advanced configuration management."""

import unittest
from unittest.mock import Mock, patch, mock_open
import tempfile
import json
import os
from pathlib import Path

from smart_splitter.config.advanced import (
    PerformanceConfig, APIConfig, ExportConfig, UIConfig, ProcessingConfig,
    AdvancedConfigManager, ConfigProfileManager
)
from smart_splitter.config.manager import ConfigManager
from smart_splitter.error_handling.exceptions import ConfigurationError


class TestConfigDataClasses(unittest.TestCase):
    """Test configuration dataclass definitions."""
    
    def test_performance_config_defaults(self):
        """Test PerformanceConfig default values."""
        config = PerformanceConfig()
        
        self.assertEqual(config.max_memory_mb, 500)
        self.assertEqual(config.max_workers, 3)
        self.assertTrue(config.cache_enabled)
        self.assertEqual(config.batch_size, 10)
        self.assertTrue(config.enable_memory_monitoring)
    
    def test_api_config_defaults(self):
        """Test APIConfig default values."""
        config = APIConfig()
        
        self.assertEqual(config.openai_api_key, "")
        self.assertEqual(config.model, "gpt-4o-mini")
        self.assertEqual(config.temperature, 0.0)
        self.assertEqual(config.max_tokens, 10)
        self.assertEqual(config.timeout, 10)
        self.assertTrue(config.fallback_enabled)
    
    def test_export_config_defaults(self):
        """Test ExportConfig default values."""
        config = ExportConfig()
        
        self.assertEqual(config.default_directory, "~/Documents/split_pdfs")
        self.assertTrue(config.create_subdirectories)
        self.assertTrue(config.include_metadata)
        self.assertFalse(config.compress_pdfs)
        self.assertEqual(config.filename_collision_strategy, "rename")
        self.assertEqual(config.max_filename_length, 200)
    
    def test_ui_config_defaults(self):
        """Test UIConfig default values."""
        config = UIConfig()
        
        self.assertEqual(config.window_width, 1200)
        self.assertEqual(config.window_height, 800)
        self.assertEqual(config.preview_size, 300)
        self.assertEqual(config.theme, "default")
        self.assertTrue(config.show_tooltips)
        self.assertTrue(config.remember_window_position)
    
    def test_processing_config_defaults(self):
        """Test ProcessingConfig default values."""
        config = ProcessingConfig()
        
        self.assertEqual(config.min_document_length, 100)
        self.assertEqual(config.confidence_threshold, 0.7)
        self.assertEqual(config.max_input_chars, 2000)
        self.assertFalse(config.enable_ocr)
        self.assertEqual(config.text_extraction_method, "fast")


class TestAdvancedConfigManager(unittest.TestCase):
    """Test advanced configuration manager functionality."""
    
    def setUp(self):
        self.mock_config_manager = Mock(spec=ConfigManager)
        self.advanced_config = AdvancedConfigManager(self.mock_config_manager)
    
    def test_load_config_section(self):
        """Test loading configuration section into dataclass."""
        # Mock config data
        self.mock_config_manager.get_setting.return_value = {
            "max_memory_mb": 300,
            "max_workers": 2
        }
        
        config = self.advanced_config._load_config_section("performance", PerformanceConfig)
        
        self.assertEqual(config.max_memory_mb, 300)
        self.assertEqual(config.max_workers, 2)
        self.assertEqual(config.batch_size, 10)  # Should use default for missing values
    
    def test_load_config_section_invalid_data(self):
        """Test loading configuration section with invalid data."""
        # Mock invalid config data
        self.mock_config_manager.get_setting.return_value = {
            "max_memory_mb": "invalid",  # Should be int
            "unknown_field": "value"
        }
        
        with self.assertRaises(ConfigurationError):
            self.advanced_config._load_config_section("performance", PerformanceConfig)
    
    def test_save_advanced_configs(self):
        """Test saving advanced configurations."""
        # Update some configs
        self.advanced_config.performance.max_memory_mb = 400
        self.advanced_config.api.timeout = 20
        
        self.advanced_config.save_advanced_configs()
        
        # Check that update_setting was called for each section
        calls = self.mock_config_manager.update_setting.call_args_list
        self.assertEqual(len(calls), 5)  # 5 config sections
        
        # Check specific calls
        call_keys = [call[0][0] for call in calls]
        self.assertIn("performance", call_keys)
        self.assertIn("api", call_keys)
        self.assertIn("export", call_keys)
        self.assertIn("ui", call_keys)
        self.assertIn("processing", call_keys)
    
    @patch('smart_splitter.config.advanced.InputValidator')
    def test_validate_performance_config_valid(self, mock_validator_class):
        """Test validating valid performance configuration."""
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator
        mock_validator.validate_config_value.return_value = {"valid": True}
        
        self.advanced_config.validator = mock_validator
        
        result = self.advanced_config.validate_performance_config()
        
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["issues"]), 0)
    
    @patch('smart_splitter.config.advanced.InputValidator')
    def test_validate_performance_config_invalid(self, mock_validator_class):
        """Test validating invalid performance configuration."""
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator
        
        # Mock validation failure
        from smart_splitter.error_handling.exceptions import ValidationError
        mock_validator.validate_config_value.side_effect = [
            ValidationError("Invalid memory limit"),
            {"valid": True},  # Valid for other validations
            {"valid": True}
        ]
        
        self.advanced_config.validator = mock_validator
        
        result = self.advanced_config.validate_performance_config()
        
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["issues"]), 1)
        self.assertIn("Invalid memory limit", result["issues"][0])
    
    @patch('smart_splitter.config.advanced.InputValidator')
    def test_validate_api_config(self, mock_validator_class):
        """Test validating API configuration."""
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator
        mock_validator.validate_api_key.return_value = {"valid": True}
        mock_validator.validate_config_value.return_value = {"valid": True}
        
        self.advanced_config.validator = mock_validator
        self.advanced_config.api.openai_api_key = "sk-test123456789012345678901234567890"
        
        result = self.advanced_config.validate_api_config()
        
        self.assertTrue(result["valid"])
        mock_validator.validate_api_key.assert_called_once()
    
    def test_validate_all_configs(self):
        """Test validating all configuration sections."""
        # Mock individual validation methods
        with patch.object(self.advanced_config, 'validate_performance_config') as mock_perf, \
             patch.object(self.advanced_config, 'validate_api_config') as mock_api, \
             patch.object(self.advanced_config, 'validate_export_config') as mock_export:
            
            mock_perf.return_value = {"valid": True, "issues": []}
            mock_api.return_value = {"valid": False, "issues": ["API error"]}
            mock_export.return_value = {"valid": True, "issues": []}
            
            result = self.advanced_config.validate_all_configs()
            
            self.assertFalse(result["valid"])  # One section failed
            self.assertIn("api: API error", result["all_issues"])
    
    def test_reset_to_defaults_single_section(self):
        """Test resetting single configuration section to defaults."""
        # Modify performance config
        self.advanced_config.performance.max_memory_mb = 999
        
        self.advanced_config.reset_to_defaults("performance")
        
        # Should be back to default
        self.assertEqual(self.advanced_config.performance.max_memory_mb, 500)
    
    def test_reset_to_defaults_unknown_section(self):
        """Test resetting unknown configuration section."""
        with self.assertRaises(ConfigurationError):
            self.advanced_config.reset_to_defaults("unknown_section")
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_export_config(self, mock_json_dump, mock_file):
        """Test exporting configuration to file."""
        self.advanced_config.export_config("config.json")
        
        mock_file.assert_called_once_with("config.json", 'w')
        mock_json_dump.assert_called_once()
        
        # Check the data structure passed to json.dump
        call_args = mock_json_dump.call_args[0][0]
        self.assertIn("performance", call_args)
        self.assertIn("api", call_args)
        self.assertIn("export", call_args)
        self.assertIn("ui", call_args)
        self.assertIn("processing", call_args)
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"performance": {"max_memory_mb": 600}}')
    @patch('json.load')
    def test_import_config(self, mock_json_load, mock_file):
        """Test importing configuration from file."""
        mock_json_load.return_value = {
            "performance": {"max_memory_mb": 600, "max_workers": 4}
        }
        
        with patch.object(self.advanced_config, 'validate_all_configs') as mock_validate:
            mock_validate.return_value = {"valid": True}
            
            self.advanced_config.import_config("config.json", validate=True)
            
            self.assertEqual(self.advanced_config.performance.max_memory_mb, 600)
            self.assertEqual(self.advanced_config.performance.max_workers, 4)
    
    @patch('psutil.cpu_count')
    @patch('psutil.virtual_memory')
    def test_auto_optimize_for_system(self, mock_vm, mock_cpu_count):
        """Test automatic system optimization."""
        # Mock system with 2GB RAM and 2 CPUs
        mock_vm.return_value.total = 2 * 1024 * 1024 * 1024  # 2GB
        mock_cpu_count.return_value = 2
        
        self.advanced_config.auto_optimize_for_system()
        
        # Should optimize for low-memory system
        self.assertEqual(self.advanced_config.performance.max_memory_mb, 200)
        self.assertEqual(self.advanced_config.performance.max_workers, 2)
        self.assertEqual(self.advanced_config.performance.batch_size, 5)
    
    @patch('psutil.cpu_count')
    def test_get_optimization_recommendations(self, mock_cpu_count):
        """Test getting optimization recommendations."""
        mock_cpu_count.return_value = 2
        
        # Set config that should trigger recommendations
        self.advanced_config.performance.max_workers = 8  # More than CPU count
        self.advanced_config.api.timeout = 5  # Low timeout
        
        recommendations = self.advanced_config.get_optimization_recommendations()
        
        self.assertGreater(len(recommendations), 0)
        # Should recommend reducing workers to CPU count
        self.assertTrue(any("max_workers" in rec for rec in recommendations))
        # Should recommend increasing timeout
        self.assertTrue(any("timeout" in rec for rec in recommendations))


class TestConfigProfileManager(unittest.TestCase):
    """Test configuration profile management."""
    
    def setUp(self):
        self.mock_advanced_config = Mock(spec=AdvancedConfigManager)
        
        # Create temporary profiles directory
        self.temp_dir = tempfile.mkdtemp()
        self.profiles_dir = Path(self.temp_dir) / "profiles"
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
        self.profile_manager = ConfigProfileManager(self.mock_advanced_config)
        self.profile_manager.profiles_dir = self.profiles_dir
    
    def tearDown(self):
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('time.time')
    def test_save_profile(self, mock_time):
        """Test saving configuration profile."""
        mock_time.return_value = 1234567890
        
        # Mock advanced config data
        self.mock_advanced_config.performance = PerformanceConfig(max_memory_mb=400)
        self.mock_advanced_config.api = APIConfig(timeout=15)
        self.mock_advanced_config.export = ExportConfig()
        self.mock_advanced_config.ui = UIConfig()
        self.mock_advanced_config.processing = ProcessingConfig()
        
        self.profile_manager.save_profile("test_profile", "Test description")
        
        # Check that profile file was created
        profile_file = self.profiles_dir / "test_profile.json"
        self.assertTrue(profile_file.exists())
        
        # Check profile content
        with open(profile_file, 'r') as f:
            profile_data = json.load(f)
        
        self.assertEqual(profile_data["name"], "test_profile")
        self.assertEqual(profile_data["description"], "Test description")
        self.assertEqual(profile_data["created"], 1234567890)
        self.assertIn("config", profile_data)
        self.assertEqual(profile_data["config"]["performance"]["max_memory_mb"], 400)
    
    def test_load_profile(self):
        """Test loading configuration profile."""
        # Create test profile
        profile_data = {
            "name": "test_profile",
            "description": "Test",
            "created": 1234567890,
            "config": {
                "performance": {"max_memory_mb": 300, "max_workers": 2, "cache_enabled": True, 
                              "cache_size_limit": 3, "batch_size": 10, "chunk_size_large_docs": 50,
                              "enable_memory_monitoring": True, "gc_frequency": 10},
                "api": {"openai_api_key": "", "model": "gpt-4o-mini", "temperature": 0.0,
                       "max_tokens": 10, "timeout": 20, "max_retries": 3, "retry_delay": 1.0,
                       "confidence_threshold": 0.7, "fallback_enabled": True},
                "export": {"default_directory": "~/Documents/split_pdfs", "create_subdirectories": True,
                          "include_metadata": True, "compress_pdfs": False, "quality_level": 75,
                          "filename_collision_strategy": "rename", "max_filename_length": 200,
                          "preserve_bookmarks": False, "add_page_numbers": True},
                "ui": {"window_width": 1200, "window_height": 800, "preview_size": 300,
                      "theme": "default", "auto_save_interval": 300, "show_tooltips": True,
                      "remember_window_position": True, "default_sort_column": "start_page",
                      "show_confidence_colors": True},
                "processing": {"min_document_length": 100, "confidence_threshold": 0.7,
                              "max_input_chars": 2000, "enable_ocr": False, "ocr_language": "eng",
                              "text_extraction_method": "fast", "boundary_detection_sensitivity": 0.8,
                              "classification_timeout": 30}
            }
        }
        
        profile_file = self.profiles_dir / "test_profile.json"
        with open(profile_file, 'w') as f:
            json.dump(profile_data, f)
        
        self.profile_manager.load_profile("test_profile")
        
        # Check that advanced config was updated
        self.mock_advanced_config.save_advanced_configs.assert_called_once()
    
    def test_load_profile_not_found(self):
        """Test loading non-existent profile."""
        with self.assertRaises(ConfigurationError):
            self.profile_manager.load_profile("nonexistent_profile")
    
    def test_list_profiles(self):
        """Test listing available profiles."""
        # Create test profiles
        for i in range(3):
            profile_data = {
                "name": f"profile_{i}",
                "description": f"Description {i}",
                "created": 1234567890 + i
            }
            
            profile_file = self.profiles_dir / f"profile_{i}.json"
            with open(profile_file, 'w') as f:
                json.dump(profile_data, f)
        
        profiles = self.profile_manager.list_profiles()
        
        self.assertEqual(len(profiles), 3)
        # Should be sorted by creation time (newest first)
        self.assertEqual(profiles[0]["name"], "profile_2")
        self.assertEqual(profiles[1]["name"], "profile_1")
        self.assertEqual(profiles[2]["name"], "profile_0")
    
    def test_delete_profile(self):
        """Test deleting configuration profile."""
        # Create test profile
        profile_data = {"name": "test_profile"}
        profile_file = self.profiles_dir / "test_profile.json"
        with open(profile_file, 'w') as f:
            json.dump(profile_data, f)
        
        self.assertTrue(profile_file.exists())
        
        self.profile_manager.delete_profile("test_profile")
        
        self.assertFalse(profile_file.exists())
    
    def test_delete_profile_not_found(self):
        """Test deleting non-existent profile."""
        with self.assertRaises(ConfigurationError):
            self.profile_manager.delete_profile("nonexistent_profile")
    
    def test_create_default_profiles(self):
        """Test creating default configuration profiles."""
        self.profile_manager.create_default_profiles()
        
        # Check that default profiles were created
        profiles = self.profile_manager.list_profiles()
        profile_names = [p["name"] for p in profiles]
        
        self.assertIn("performance", profile_names)
        self.assertIn("quality", profile_names)
        self.assertIn("large_docs", profile_names)


if __name__ == '__main__':
    unittest.main()