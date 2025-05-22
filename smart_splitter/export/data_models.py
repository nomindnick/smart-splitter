"""
Data models for export functionality.

This module defines the data structures used for PDF export operations
and configuration.
"""

from dataclasses import dataclass, field
from typing import List, Literal
from pathlib import Path


@dataclass
class ExportResult:
    """Result of a PDF export operation."""
    
    success_count: int = 0
    failed_count: int = 0
    errors: List[str] = field(default_factory=list)
    exported_files: List[str] = field(default_factory=list)
    
    @property
    def total_attempted(self) -> int:
        """Get the total number of documents attempted for export."""
        return self.success_count + self.failed_count
    
    @property
    def success_rate(self) -> float:
        """Get the success rate as a percentage."""
        if self.total_attempted == 0:
            return 0.0
        return (self.success_count / self.total_attempted) * 100
    
    def add_success(self, filepath: str) -> None:
        """Record a successful export."""
        self.success_count += 1
        self.exported_files.append(filepath)
    
    def add_error(self, error_msg: str) -> None:
        """Record a failed export."""
        self.failed_count += 1
        self.errors.append(error_msg)


@dataclass
class ExportConfig:
    """Configuration for PDF export operations."""
    
    output_directory: str = "./output"
    overwrite_existing: bool = False
    create_subdirectories: bool = True
    filename_collision_strategy: Literal['rename', 'skip', 'overwrite'] = 'rename'
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        # Ensure output directory path is absolute
        self.output_directory = str(Path(self.output_directory).resolve())
        
        # Validate collision strategy
        valid_strategies = ['rename', 'skip', 'overwrite']
        if self.filename_collision_strategy not in valid_strategies:
            raise ValueError(f"Invalid collision strategy. Must be one of: {valid_strategies}")
    
    @property
    def output_path(self) -> Path:
        """Get the output directory as a Path object."""
        return Path(self.output_directory)