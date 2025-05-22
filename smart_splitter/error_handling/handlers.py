"""Error handling and recovery mechanisms."""

import logging
import traceback
from typing import Dict, Any, Optional, Callable, List
from functools import wraps
from pathlib import Path
import json
import time

from .exceptions import SmartSplitterError, PDFProcessingError, ExportError, MemoryError


class ErrorHandler:
    """Centralized error handling and logging."""
    
    def __init__(self, log_file: Optional[str] = None):
        self.logger = self._setup_logger(log_file)
        self.error_counts: Dict[str, int] = {}
        self.error_callbacks: Dict[str, List[Callable]] = {}
    
    def _setup_logger(self, log_file: Optional[str] = None) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger("smart_splitter")
        logger.setLevel(logging.INFO)
        
        # Avoid adding multiple handlers
        if logger.handlers:
            return logger
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_format = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_format)
            logger.addHandler(file_handler)
        
        return logger
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None,
                    notify_user: bool = True) -> Dict[str, Any]:
        """Handle an error with logging and optional user notification."""
        error_info = self._extract_error_info(error, context)
        
        # Log the error
        self._log_error(error_info)
        
        # Track error counts
        error_type = error_info["type"]
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Execute callbacks
        self._execute_callbacks(error_type, error_info)
        
        # Return error information for caller
        return {
            "error_id": error_info["error_id"],
            "message": error_info["user_message"],
            "recoverable": error_info["recoverable"],
            "suggested_action": error_info["suggested_action"]
        }
    
    def _extract_error_info(self, error: Exception, 
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract comprehensive error information."""
        error_id = f"ERR_{int(time.time() * 1000) % 1000000:06d}"
        
        if isinstance(error, SmartSplitterError):
            error_info = error.to_dict()
            user_message = error.message
            recoverable = self._is_recoverable_error(error)
            suggested_action = self._get_suggested_action(error)
        else:
            error_info = {
                "type": type(error).__name__,
                "message": str(error),
                "details": {}
            }
            user_message = f"An unexpected error occurred: {str(error)}"
            recoverable = False
            suggested_action = "Please try again or contact support"
        
        return {
            "error_id": error_id,
            "timestamp": time.time(),
            "type": error_info["type"],
            "message": error_info["message"],
            "user_message": user_message,
            "details": error_info.get("details", {}),
            "context": context or {},
            "traceback": traceback.format_exc(),
            "recoverable": recoverable,
            "suggested_action": suggested_action
        }
    
    def _is_recoverable_error(self, error: SmartSplitterError) -> bool:
        """Determine if an error is potentially recoverable."""
        recoverable_types = {
            PDFProcessingError: True,
            ExportError: True,
            MemoryError: True,
        }
        
        return recoverable_types.get(type(error), False)
    
    def _get_suggested_action(self, error: SmartSplitterError) -> str:
        """Get suggested action for specific error types."""
        suggestions = {
            PDFProcessingError: "Check if the PDF file is valid and not corrupted",
            ExportError: "Verify output directory permissions and available disk space",
            MemoryError: "Close other applications to free memory or process smaller documents",
        }
        
        return suggestions.get(type(error), "Please try again or contact support")
    
    def _log_error(self, error_info: Dict[str, Any]):
        """Log error information."""
        log_message = (
            f"[{error_info['error_id']}] {error_info['type']}: {error_info['message']}"
        )
        
        if error_info["details"]:
            log_message += f" | Details: {error_info['details']}"
        
        if error_info["context"]:
            log_message += f" | Context: {error_info['context']}"
        
        self.logger.error(log_message)
        
        # Log traceback at debug level
        if error_info["traceback"]:
            self.logger.debug(f"Traceback for {error_info['error_id']}:\n{error_info['traceback']}")
    
    def register_callback(self, error_type: str, callback: Callable):
        """Register a callback for specific error types."""
        if error_type not in self.error_callbacks:
            self.error_callbacks[error_type] = []
        self.error_callbacks[error_type].append(callback)
    
    def _execute_callbacks(self, error_type: str, error_info: Dict[str, Any]):
        """Execute registered callbacks for error type."""
        callbacks = self.error_callbacks.get(error_type, [])
        for callback in callbacks:
            try:
                callback(error_info)
            except Exception as e:
                self.logger.warning(f"Error callback failed: {e}")
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        total_errors = sum(self.error_counts.values())
        return {
            "total_errors": total_errors,
            "error_counts": self.error_counts.copy(),
            "most_common": max(self.error_counts.items(), key=lambda x: x[1]) if self.error_counts else None
        }
    
    def save_error_log(self, output_path: str):
        """Save error statistics to file."""
        stats = self.get_error_stats()
        stats["timestamp"] = time.time()
        
        with open(output_path, 'w') as f:
            json.dump(stats, f, indent=2)


class RecoveryManager:
    """Manages error recovery and retry mechanisms."""
    
    def __init__(self, error_handler: ErrorHandler):
        self.error_handler = error_handler
        self.recovery_strategies: Dict[str, Callable] = {}
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """Register default recovery strategies."""
        self.recovery_strategies.update({
            "PDFProcessingError": self._recover_pdf_processing,
            "MemoryError": self._recover_memory_error,
            "ExportError": self._recover_export_error,
        })
    
    def attempt_recovery(self, error: Exception, operation: Callable, 
                        *args, max_retries: int = 3, **kwargs) -> Any:
        """Attempt to recover from an error and retry operation."""
        error_type = type(error).__name__
        
        if error_type not in self.recovery_strategies:
            raise error  # No recovery strategy available
        
        recovery_func = self.recovery_strategies[error_type]
        
        for attempt in range(max_retries):
            try:
                # Attempt recovery
                recovery_successful = recovery_func(error, attempt + 1)
                
                if recovery_successful:
                    # Retry the operation
                    return operation(*args, **kwargs)
                else:
                    break  # Recovery failed, don't retry
            
            except Exception as retry_error:
                if attempt == max_retries - 1:  # Last attempt
                    raise retry_error
                
                # Log retry attempt
                self.error_handler.logger.warning(
                    f"Recovery attempt {attempt + 1} failed: {retry_error}"
                )
        
        # All recovery attempts failed
        raise error
    
    def _recover_pdf_processing(self, error: PDFProcessingError, attempt: int) -> bool:
        """Attempt to recover from PDF processing errors."""
        # Clean up any corrupted PDF objects
        import gc
        gc.collect()
        
        # If it's a memory-related issue, try clearing cache
        try:
            from ..performance.optimizer import PDFOptimizer
            optimizer = PDFOptimizer()
            optimizer.clear_cache()
            return True
        except:
            return False
    
    def _recover_memory_error(self, error: MemoryError, attempt: int) -> bool:
        """Attempt to recover from memory errors."""
        try:
            from ..performance.optimizer import MemoryManager
            memory_manager = MemoryManager()
            
            # Force memory cleanup
            cleanup_successful = memory_manager.cleanup_memory(force=True)
            
            # Check if memory was freed
            current_memory = memory_manager.check_memory_usage()["rss_mb"]
            
            return cleanup_successful and current_memory < 400  # Under 400MB
        except:
            return False
    
    def _recover_export_error(self, error: ExportError, attempt: int) -> bool:
        """Attempt to recover from export errors."""
        if error.output_path:
            # Check if directory exists and create if needed
            output_dir = Path(error.output_path).parent
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
                return True
            except:
                return False
        
        return False
    
    def register_recovery_strategy(self, error_type: str, strategy: Callable) -> None:
        """Register a custom recovery strategy."""
        self.recovery_strategies[error_type] = strategy


def handle_errors(error_handler: Optional[ErrorHandler] = None, 
                 recovery_manager: Optional[RecoveryManager] = None,
                 max_retries: int = 0):
    """Decorator for automatic error handling and optional recovery."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = error_handler or ErrorHandler()
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Handle the error
                error_info = handler.handle_error(e, context={
                    "function": func.__name__,
                    "args": str(args)[:200],  # Limit arg string length
                    "kwargs": str(kwargs)[:200]
                })
                
                # Attempt recovery if configured
                if recovery_manager and max_retries > 0 and error_info["recoverable"]:
                    try:
                        return recovery_manager.attempt_recovery(
                            e, func, *args, max_retries=max_retries, **kwargs
                        )
                    except Exception as recovery_error:
                        # Log recovery failure
                        handler.handle_error(recovery_error, context={
                            "recovery_attempt": True,
                            "original_error": str(e)
                        })
                        raise recovery_error
                
                # Re-raise if no recovery or recovery failed
                raise e
        
        return wrapper
    return decorator


# Global error handler instance
global_error_handler = ErrorHandler()
global_recovery_manager = RecoveryManager(global_error_handler)