"""Advanced configuration management for power users and optimization."""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict

from .manager import ConfigManager
from ..error_handling.validators import InputValidator
from ..error_handling.exceptions import ConfigurationError


@dataclass
class PerformanceConfig:
    """Performance optimization configuration."""
    max_memory_mb: int = 500
    max_workers: int = 3
    cache_enabled: bool = True
    cache_size_limit: int = 3
    batch_size: int = 10
    chunk_size_large_docs: int = 50
    enable_memory_monitoring: bool = True
    gc_frequency: int = 10  # Pages processed before garbage collection


@dataclass
class APIConfig:
    """API configuration for external services."""
    openai_api_key: str = ""
    model: str = "gpt-4o-mini"
    temperature: float = 0.0
    max_tokens: int = 10
    timeout: int = 10
    max_retries: int = 3
    retry_delay: float = 1.0
    confidence_threshold: float = 0.7
    fallback_enabled: bool = True


@dataclass
class ExportConfig:
    """Export configuration and preferences."""
    default_directory: str = "~/Documents/split_pdfs"
    create_subdirectories: bool = True
    include_metadata: bool = True
    compress_pdfs: bool = False
    quality_level: int = 75  # For compression
    filename_collision_strategy: str = "rename"  # rename, skip, overwrite
    filename_max_length: int = 200  # Match existing config name
    preserve_bookmarks: bool = False
    include_page_numbers: bool = True  # Match existing config name


@dataclass
class UIConfig:
    """User interface configuration."""
    window_width: int = 1200
    window_height: int = 800
    preview_size: int = 300
    theme: str = "default"  # default, dark, light
    auto_save_interval: int = 300  # seconds
    show_tooltips: bool = True
    remember_window_position: bool = True
    default_sort_column: str = "start_page"
    show_confidence_colors: bool = True


@dataclass
class ProcessingConfig:
    """Document processing configuration."""
    min_document_length: int = 100
    confidence_threshold: float = 0.7
    max_input_chars: int = 2000
    enable_ocr: bool = False
    ocr_language: str = "eng"
    text_extraction_method: str = "fast"  # fast, detailed, ocr
    boundary_detection_sensitivity: float = 0.8
    classification_timeout: int = 30


class AdvancedConfigManager:
    """Advanced configuration management with validation and user preferences."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager or ConfigManager()
        self.validator = InputValidator()
        self._load_advanced_configs()
    
    def _load_advanced_configs(self):
        """Load advanced configuration objects."""
        self.performance = self._load_config_section("performance", PerformanceConfig)
        self.api = self._load_config_section("api", APIConfig)
        self.export = self._load_config_section("export", ExportConfig)
        self.ui = self._load_config_section("ui", UIConfig)
        self.processing = self._load_config_section("processing", ProcessingConfig)
    
    def _load_config_section(self, section: str, config_class) -> Any:
        """Load a configuration section into a dataclass."""
        config_data = self.config_manager.get_setting(section, {})
        
        # Get default values from dataclass
        default_instance = config_class()
        default_dict = asdict(default_instance)
        
        # Merge with loaded config
        merged_config = {**default_dict, **config_data}
        
        try:
            return config_class(**merged_config)
        except TypeError as e:
            raise ConfigurationError(f"Invalid configuration for {section}: {str(e)}",
                                   config_key=section, config_value=config_data)
    
    def save_advanced_configs(self):
        """Save all advanced configurations."""
        self.config_manager.update_setting("performance", asdict(self.performance))
        self.config_manager.update_setting("api", asdict(self.api))
        self.config_manager.update_setting("export", asdict(self.export))
        self.config_manager.update_setting("ui", asdict(self.ui))
        self.config_manager.update_setting("processing", asdict(self.processing))
    
    def validate_performance_config(self) -> Dict[str, Any]:
        """Validate performance configuration."""
        issues = []
        
        # Validate memory limit
        try:
            self.validator.validate_config_value(
                "max_memory_mb", self.performance.max_memory_mb, int, 
                min_value=100, max_value=2048
            )
        except Exception as e:
            issues.append(str(e))
        
        # Validate worker count
        try:
            self.validator.validate_config_value(
                "max_workers", self.performance.max_workers, int,
                min_value=1, max_value=8
            )
        except Exception as e:
            issues.append(str(e))
        
        # Validate batch size
        try:
            self.validator.validate_config_value(
                "batch_size", self.performance.batch_size, int,
                min_value=1, max_value=100
            )
        except Exception as e:
            issues.append(str(e))
        
        return {"valid": len(issues) == 0, "issues": issues}
    
    def validate_api_config(self) -> Dict[str, Any]:
        """Validate API configuration."""
        issues = []
        
        # Validate API key if provided
        if self.api.openai_api_key:
            try:
                self.validator.validate_api_key(self.api.openai_api_key, "OpenAI")
            except Exception as e:
                issues.append(str(e))
        
        # Validate timeout
        try:
            self.validator.validate_config_value(
                "timeout", self.api.timeout, int,
                min_value=5, max_value=120
            )
        except Exception as e:
            issues.append(str(e))
        
        # Validate confidence threshold
        try:
            self.validator.validate_config_value(
                "confidence_threshold", self.api.confidence_threshold, float,
                min_value=0.0, max_value=1.0
            )
        except Exception as e:
            issues.append(str(e))
        
        return {"valid": len(issues) == 0, "issues": issues}
    
    def validate_export_config(self) -> Dict[str, Any]:
        """Validate export configuration."""
        issues = []
        
        # Validate default directory
        try:
            directory_path = Path(self.export.default_directory).expanduser()
            self.validator.validate_output_directory(str(directory_path), create_if_missing=False)
        except Exception as e:
            issues.append(f"Default directory: {str(e)}")
        
        # Validate filename length
        try:
            self.validator.validate_config_value(
                "filename_max_length", self.export.filename_max_length, int,
                min_value=50, max_value=255
            )
        except Exception as e:
            issues.append(str(e))
        
        # Validate collision strategy
        valid_strategies = ["rename", "skip", "overwrite"]
        if self.export.filename_collision_strategy not in valid_strategies:
            issues.append(f"Invalid collision strategy: {self.export.filename_collision_strategy}")
        
        return {"valid": len(issues) == 0, "issues": issues}
    
    def validate_all_configs(self) -> Dict[str, Any]:
        """Validate all configuration sections."""
        results = {
            "performance": self.validate_performance_config(),
            "api": self.validate_api_config(),
            "export": self.validate_export_config()
        }
        
        all_valid = all(result["valid"] for result in results.values())
        all_issues = []
        for section, result in results.items():
            for issue in result["issues"]:
                all_issues.append(f"{section}: {issue}")
        
        return {
            "valid": all_valid,
            "section_results": results,
            "all_issues": all_issues
        }
    
    def reset_to_defaults(self, section: Optional[str] = None):
        """Reset configuration to defaults."""
        if section:
            if section == "performance":
                self.performance = PerformanceConfig()
            elif section == "api":
                self.api = APIConfig()
            elif section == "export":
                self.export = ExportConfig()
            elif section == "ui":
                self.ui = UIConfig()
            elif section == "processing":
                self.processing = ProcessingConfig()
            else:
                raise ConfigurationError(f"Unknown configuration section: {section}")
        else:
            # Reset all sections
            self._load_advanced_configs()
        
        self.save_advanced_configs()
    
    def export_config(self, output_path: str):
        """Export configuration to file."""
        config_data = {
            "performance": asdict(self.performance),
            "api": asdict(self.api),
            "export": asdict(self.export),
            "ui": asdict(self.ui),
            "processing": asdict(self.processing)
        }
        
        with open(output_path, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def import_config(self, input_path: str, validate: bool = True):
        """Import configuration from file."""
        with open(input_path, 'r') as f:
            config_data = json.load(f)
        
        # Update configuration objects
        if "performance" in config_data:
            self.performance = PerformanceConfig(**config_data["performance"])
        if "api" in config_data:
            self.api = APIConfig(**config_data["api"])
        if "export" in config_data:
            self.export = ExportConfig(**config_data["export"])
        if "ui" in config_data:
            self.ui = UIConfig(**config_data["ui"])
        if "processing" in config_data:
            self.processing = ProcessingConfig(**config_data["processing"])
        
        # Validate if requested
        if validate:
            validation_result = self.validate_all_configs()
            if not validation_result["valid"]:
                raise ConfigurationError(
                    f"Imported configuration is invalid: {validation_result['all_issues']}"
                )
        
        self.save_advanced_configs()
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get recommendations for configuration optimization."""
        recommendations = []
        
        # Memory recommendations
        if self.performance.max_memory_mb > 300:
            recommendations.append(
                "Consider reducing max_memory_mb for better stability on lower-end systems"
            )
        
        # Worker recommendations
        import psutil
        cpu_count = psutil.cpu_count()
        if self.performance.max_workers > cpu_count:
            recommendations.append(
                f"Consider reducing max_workers to {cpu_count} (CPU count) for optimal performance"
            )
        
        # API recommendations
        if self.api.timeout < 10:
            recommendations.append(
                "Consider increasing API timeout for better reliability with large documents"
            )
        
        # Export recommendations
        if not self.export.create_subdirectories:
            recommendations.append(
                "Enable create_subdirectories to organize exported files better"
            )
        
        if self.export.filename_max_length > 150:
            recommendations.append(
                "Consider reducing filename_max_length for better compatibility"
            )
        
        return recommendations
    
    def auto_optimize_for_system(self):
        """Automatically optimize configuration for current system."""
        import psutil
        
        # Get system information
        memory_gb = psutil.virtual_memory().total / 1024 / 1024 / 1024
        cpu_count = psutil.cpu_count()
        
        # Optimize performance settings
        if memory_gb < 4:  # Low memory system
            self.performance.max_memory_mb = 200
            self.performance.max_workers = min(2, cpu_count)
            self.performance.batch_size = 5
        elif memory_gb < 8:  # Medium memory system
            self.performance.max_memory_mb = 350
            self.performance.max_workers = min(3, cpu_count)
            self.performance.batch_size = 8
        else:  # High memory system
            self.performance.max_memory_mb = 500
            self.performance.max_workers = min(4, cpu_count)
            self.performance.batch_size = 10
        
        # Optimize processing settings
        if cpu_count <= 2:
            self.processing.text_extraction_method = "fast"
            self.api.timeout = 20
        else:
            self.processing.text_extraction_method = "detailed"
            self.api.timeout = 15
        
        self.save_advanced_configs()


class ConfigProfileManager:
    """Manages configuration profiles for different use cases."""
    
    def __init__(self, advanced_config: AdvancedConfigManager):
        self.advanced_config = advanced_config
        self.profiles_dir = Path.home() / ".config" / "smart-splitter" / "profiles"
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
    
    def save_profile(self, profile_name: str, description: str = ""):
        """Save current configuration as a profile."""
        profile_data = {
            "name": profile_name,
            "description": description,
            "created": time.time(),
            "config": {
                "performance": asdict(self.advanced_config.performance),
                "api": asdict(self.advanced_config.api),
                "export": asdict(self.advanced_config.export),
                "ui": asdict(self.advanced_config.ui),
                "processing": asdict(self.advanced_config.processing)
            }
        }
        
        profile_file = self.profiles_dir / f"{profile_name}.json"
        with open(profile_file, 'w') as f:
            json.dump(profile_data, f, indent=2)
    
    def load_profile(self, profile_name: str):
        """Load a configuration profile."""
        profile_file = self.profiles_dir / f"{profile_name}.json"
        
        if not profile_file.exists():
            raise ConfigurationError(f"Profile not found: {profile_name}")
        
        with open(profile_file, 'r') as f:
            profile_data = json.load(f)
        
        config = profile_data["config"]
        
        # Update advanced config
        self.advanced_config.performance = PerformanceConfig(**config["performance"])
        self.advanced_config.api = APIConfig(**config["api"])
        self.advanced_config.export = ExportConfig(**config["export"])
        self.advanced_config.ui = UIConfig(**config["ui"])
        self.advanced_config.processing = ProcessingConfig(**config["processing"])
        
        self.advanced_config.save_advanced_configs()
    
    def list_profiles(self) -> List[Dict[str, Any]]:
        """List available configuration profiles."""
        profiles = []
        
        for profile_file in self.profiles_dir.glob("*.json"):
            try:
                with open(profile_file, 'r') as f:
                    profile_data = json.load(f)
                
                profiles.append({
                    "name": profile_data["name"],
                    "description": profile_data.get("description", ""),
                    "created": profile_data.get("created", 0),
                    "file": str(profile_file)
                })
            except:
                continue
        
        return sorted(profiles, key=lambda x: x["created"], reverse=True)
    
    def delete_profile(self, profile_name: str):
        """Delete a configuration profile."""
        profile_file = self.profiles_dir / f"{profile_name}.json"
        
        if not profile_file.exists():
            raise ConfigurationError(f"Profile not found: {profile_name}")
        
        profile_file.unlink()
    
    def create_default_profiles(self):
        """Create default configuration profiles."""
        # Performance profile
        self.advanced_config.performance = PerformanceConfig(
            max_memory_mb=300, max_workers=2, batch_size=5
        )
        self.save_profile("performance", "Optimized for speed and low memory usage")
        
        # Quality profile
        self.advanced_config.performance = PerformanceConfig(
            max_memory_mb=500, max_workers=4, batch_size=10
        )
        self.advanced_config.processing = ProcessingConfig(
            text_extraction_method="detailed", confidence_threshold=0.8
        )
        self.save_profile("quality", "Optimized for accuracy and detailed processing")
        
        # Large documents profile
        self.advanced_config.performance = PerformanceConfig(
            max_memory_mb=600, max_workers=3, batch_size=20, chunk_size_large_docs=100
        )
        self.save_profile("large_docs", "Optimized for processing large documents (500+ pages)")
        
        # Reset to defaults
        self.advanced_config.reset_to_defaults()