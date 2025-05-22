"""Performance monitoring and profiling utilities."""

import time
import psutil
import functools
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations."""
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    memory_start: float = 0.0
    memory_end: Optional[float] = None
    memory_delta: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)
    
    def complete(self, success: bool = True, error_message: Optional[str] = None):
        """Mark operation as complete and calculate metrics."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.memory_end = self._get_memory_usage()
        self.memory_delta = self.memory_end - self.memory_start
        self.success = success
        self.error_message = error_message
    
    @staticmethod
    def _get_memory_usage() -> float:
        """Get current memory usage in MB."""
        return psutil.Process().memory_info().rss / 1024 / 1024


class PerformanceMonitor:
    """Monitor and track performance metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, list] = {}
        self.current_operations: Dict[str, PerformanceMetrics] = {}
    
    @contextmanager
    def monitor_operation(self, operation_name: str, **additional_data):
        """Context manager for monitoring operations."""
        metrics = self.start_operation(operation_name, **additional_data)
        try:
            yield metrics
            metrics.complete(success=True)
        except Exception as e:
            metrics.complete(success=False, error_message=str(e))
            raise
        finally:
            self.end_operation(operation_name)
    
    def start_operation(self, operation_name: str, **additional_data) -> PerformanceMetrics:
        """Start monitoring an operation."""
        metrics = PerformanceMetrics(
            operation_name=operation_name,
            start_time=time.time(),
            memory_start=PerformanceMetrics._get_memory_usage(),
            additional_data=additional_data
        )
        self.current_operations[operation_name] = metrics
        return metrics
    
    def end_operation(self, operation_name: str, success: bool = True, 
                     error_message: Optional[str] = None):
        """End monitoring an operation."""
        if operation_name in self.current_operations:
            metrics = self.current_operations[operation_name]
            metrics.complete(success, error_message)
            
            # Store in history
            if operation_name not in self.metrics:
                self.metrics[operation_name] = []
            self.metrics[operation_name].append(metrics)
            
            # Remove from current operations
            del self.current_operations[operation_name]
    
    def get_operation_stats(self, operation_name: str) -> Dict[str, Any]:
        """Get statistics for an operation type."""
        if operation_name not in self.metrics:
            return {}
        
        operations = self.metrics[operation_name]
        successful_ops = [op for op in operations if op.success]
        
        if not successful_ops:
            return {"operation_name": operation_name, "count": 0}
        
        durations = [op.duration for op in successful_ops if op.duration]
        memory_deltas = [op.memory_delta for op in successful_ops if op.memory_delta]
        
        return {
            "operation_name": operation_name,
            "count": len(operations),
            "success_count": len(successful_ops),
            "success_rate": len(successful_ops) / len(operations),
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "avg_memory_delta": sum(memory_deltas) / len(memory_deltas) if memory_deltas else 0,
            "max_memory_delta": max(memory_deltas) if memory_deltas else 0
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all monitored operations."""
        return {name: self.get_operation_stats(name) for name in self.metrics.keys()}
    
    def clear_metrics(self):
        """Clear all stored metrics."""
        self.metrics.clear()
        self.current_operations.clear()


def monitor_performance(operation_name: str):
    """Decorator for monitoring function performance."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Try to get monitor from first arg if it's a class instance
            monitor = None
            if args and hasattr(args[0], 'performance_monitor'):
                monitor = args[0].performance_monitor
            elif args and hasattr(args[0], '_performance_monitor'):
                monitor = args[0]._performance_monitor
            else:
                # Create a global monitor
                if not hasattr(monitor_performance, '_global_monitor'):
                    monitor_performance._global_monitor = PerformanceMonitor()
                monitor = monitor_performance._global_monitor
            
            with monitor.monitor_operation(operation_name) as metrics:
                result = func(*args, **kwargs)
                return result
        
        return wrapper
    return decorator


# Global performance monitor instance
global_monitor = PerformanceMonitor()