"""Benchmarking and performance testing utilities."""

import time
import json
import psutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from .monitor import PerformanceMonitor
from .optimizer import ProcessingOptimizer


@dataclass
class BenchmarkResult:
    """Results from a benchmark test."""
    test_name: str
    duration: float
    memory_peak: float
    memory_start: float
    memory_end: float
    success: bool
    error_message: Optional[str] = None
    additional_metrics: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


class BenchmarkRunner:
    """Runs performance benchmarks and tests."""
    
    def __init__(self):
        self.performance_monitor = PerformanceMonitor()
        self.results: List[BenchmarkResult] = []
    
    def run_pdf_processing_benchmark(self, pdf_path: str, 
                                   iterations: int = 3) -> BenchmarkResult:
        """Benchmark PDF processing performance."""
        test_name = f"pdf_processing_{Path(pdf_path).name}"
        
        durations = []
        memory_peaks = []
        success_count = 0
        last_error = None
        
        for i in range(iterations):
            try:
                start_time = time.time()
                start_memory = self._get_memory_usage()
                peak_memory = start_memory
                
                # Create optimizer and process document
                optimizer = ProcessingOptimizer()
                
                # Mock boundary detector, classifier, naming generator for benchmark
                from ..boundary_detection.detector import BoundaryDetector
                from ..classification.classifier import DocumentClassifier
                from ..naming.generator import FileNameGenerator
                from ..config.manager import ConfigManager
                
                config_manager = ConfigManager()
                boundary_detector = BoundaryDetector(config_manager)
                classifier = DocumentClassifier(config_manager)
                naming_generator = FileNameGenerator(config_manager)
                
                # Monitor memory during processing
                def memory_callback():
                    nonlocal peak_memory
                    current_memory = self._get_memory_usage()
                    peak_memory = max(peak_memory, current_memory)
                
                # Process document
                results = optimizer.process_document_optimized(
                    pdf_path, boundary_detector, classifier, naming_generator
                )
                
                end_time = time.time()
                end_memory = self._get_memory_usage()
                
                duration = end_time - start_time
                durations.append(duration)
                memory_peaks.append(peak_memory)
                success_count += 1
                
                # Clean up
                optimizer.pdf_optimizer.clear_cache()
                
            except Exception as e:
                last_error = str(e)
                print(f"Benchmark iteration {i+1} failed: {e}")
        
        # Calculate averages
        avg_duration = sum(durations) / len(durations) if durations else 0
        avg_peak_memory = sum(memory_peaks) / len(memory_peaks) if memory_peaks else 0
        
        result = BenchmarkResult(
            test_name=test_name,
            duration=avg_duration,
            memory_peak=avg_peak_memory,
            memory_start=start_memory if 'start_memory' in locals() else 0,
            memory_end=end_memory if 'end_memory' in locals() else 0,
            success=success_count == iterations,
            error_message=last_error if success_count < iterations else None,
            additional_metrics={
                "iterations": iterations,
                "success_count": success_count,
                "success_rate": success_count / iterations,
                "min_duration": min(durations) if durations else 0,
                "max_duration": max(durations) if durations else 0,
                "std_duration": self._calculate_std(durations) if len(durations) > 1 else 0
            }
        )
        
        self.results.append(result)
        return result
    
    def run_memory_stress_test(self, target_memory_mb: int = 400, 
                              duration_seconds: int = 60) -> BenchmarkResult:
        """Run memory stress test to validate memory management."""
        test_name = f"memory_stress_{target_memory_mb}mb_{duration_seconds}s"
        
        start_time = time.time()
        start_memory = self._get_memory_usage()
        peak_memory = start_memory
        success = True
        error_message = None
        
        try:
            from .optimizer import MemoryManager
            memory_manager = MemoryManager(max_memory_mb=target_memory_mb)
            
            # Allocate memory in chunks and monitor
            allocated_data = []
            chunk_size = 10 * 1024 * 1024  # 10MB chunks
            
            while time.time() - start_time < duration_seconds:
                current_memory = self._get_memory_usage()
                peak_memory = max(peak_memory, current_memory)
                
                if current_memory < target_memory_mb * 0.8:  # 80% of target
                    # Allocate more memory
                    data = bytearray(chunk_size)
                    allocated_data.append(data)
                else:
                    # Test memory cleanup
                    if memory_manager.cleanup_memory():
                        # Clear some allocated data
                        if allocated_data:
                            allocated_data.pop()
                
                time.sleep(0.1)  # Small delay
            
            # Final cleanup
            allocated_data.clear()
            memory_manager.cleanup_memory(force=True)
            
        except Exception as e:
            success = False
            error_message = str(e)
        
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        result = BenchmarkResult(
            test_name=test_name,
            duration=end_time - start_time,
            memory_peak=peak_memory,
            memory_start=start_memory,
            memory_end=end_memory,
            success=success,
            error_message=error_message,
            additional_metrics={
                "target_memory_mb": target_memory_mb,
                "peak_exceeded_target": peak_memory > target_memory_mb,
                "memory_efficiency": min(target_memory_mb / peak_memory, 1.0) if peak_memory > 0 else 0
            }
        )
        
        self.results.append(result)
        return result
    
    def run_export_performance_test(self, source_pdf: str, 
                                   document_count: int = 50) -> BenchmarkResult:
        """Test export performance with multiple documents."""
        test_name = f"export_performance_{document_count}_docs"
        
        start_time = time.time()
        start_memory = self._get_memory_usage()
        peak_memory = start_memory
        success = True
        error_message = None
        
        try:
            from .optimizer import PDFOptimizer
            import fitz
            import tempfile
            import os
            
            pdf_optimizer = PDFOptimizer()
            pdf_doc = pdf_optimizer.load_pdf_optimized(source_pdf)
            
            # Create export tasks
            pages_per_doc = max(1, pdf_doc.page_count // document_count)
            export_tasks = []
            
            with tempfile.TemporaryDirectory() as temp_dir:
                for i in range(document_count):
                    start_page = i * pages_per_doc
                    end_page = min(start_page + pages_per_doc - 1, pdf_doc.page_count - 1)
                    
                    if start_page >= pdf_doc.page_count:
                        break
                    
                    output_path = os.path.join(temp_dir, f"export_{i:03d}.pdf")
                    export_tasks.append({
                        "start_page": start_page,
                        "end_page": end_page,
                        "output_path": output_path
                    })
                
                # Monitor memory during export
                def memory_callback():
                    nonlocal peak_memory
                    current_memory = self._get_memory_usage()
                    peak_memory = max(peak_memory, current_memory)
                
                # Run batch export
                results = pdf_optimizer.export_pdfs_batch(pdf_doc, export_tasks)
                
                # Verify results
                successful_exports = sum(1 for r in results if r["success"])
                success = successful_exports == len(export_tasks)
                
                if not success:
                    failed_tasks = [r for r in results if not r["success"]]
                    error_message = f"Failed exports: {len(failed_tasks)}"
            
            pdf_optimizer.clear_cache()
            
        except Exception as e:
            success = False
            error_message = str(e)
        
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        result = BenchmarkResult(
            test_name=test_name,
            duration=end_time - start_time,
            memory_peak=peak_memory,
            memory_start=start_memory,
            memory_end=end_memory,
            success=success,
            error_message=error_message,
            additional_metrics={
                "target_document_count": document_count,
                "actual_exports": len(export_tasks) if 'export_tasks' in locals() else 0,
                "successful_exports": successful_exports if 'successful_exports' in locals() else 0,
                "export_rate": len(export_tasks) / (end_time - start_time) if 'export_tasks' in locals() and (end_time - start_time) > 0 else 0
            }
        )
        
        self.results.append(result)
        return result
    
    def run_comprehensive_benchmark_suite(self, test_pdf_path: str) -> Dict[str, BenchmarkResult]:
        """Run comprehensive benchmark suite."""
        results = {}
        
        print("Running comprehensive benchmark suite...")
        
        # Test 1: PDF Processing Performance
        print("1. PDF Processing Performance...")
        results["pdf_processing"] = self.run_pdf_processing_benchmark(test_pdf_path)
        
        # Test 2: Memory Management
        print("2. Memory Stress Test...")
        results["memory_stress"] = self.run_memory_stress_test()
        
        # Test 3: Export Performance
        print("3. Export Performance...")
        results["export_performance"] = self.run_export_performance_test(test_pdf_path, 25)
        
        return results
    
    def save_results(self, output_path: str):
        """Save benchmark results to file."""
        results_data = {
            "timestamp": time.time(),
            "system_info": self._get_system_info(),
            "results": [result.to_dict() for result in self.results]
        }
        
        with open(output_path, 'w') as f:
            json.dump(results_data, f, indent=2)
    
    def generate_report(self) -> str:
        """Generate a human-readable benchmark report."""
        if not self.results:
            return "No benchmark results available."
        
        report = ["Performance Benchmark Report", "=" * 40, ""]
        
        for result in self.results:
            report.append(f"Test: {result.test_name}")
            report.append(f"  Duration: {result.duration:.2f}s")
            report.append(f"  Memory Peak: {result.memory_peak:.2f}MB")
            report.append(f"  Memory Delta: {result.memory_end - result.memory_start:.2f}MB")
            report.append(f"  Success: {'✓' if result.success else '✗'}")
            
            if result.error_message:
                report.append(f"  Error: {result.error_message}")
            
            if result.additional_metrics:
                report.append("  Additional Metrics:")
                for key, value in result.additional_metrics.items():
                    if isinstance(value, float):
                        report.append(f"    {key}: {value:.2f}")
                    else:
                        report.append(f"    {key}: {value}")
            
            report.append("")
        
        # Summary
        successful_tests = sum(1 for r in self.results if r.success)
        total_tests = len(self.results)
        
        report.extend([
            "Summary",
            "-" * 20,
            f"Total Tests: {total_tests}",
            f"Successful: {successful_tests}",
            f"Success Rate: {successful_tests/total_tests*100:.1f}%"
        ])
        
        return "\n".join(report)
    
    @staticmethod
    def _get_memory_usage() -> float:
        """Get current memory usage in MB."""
        return psutil.Process().memory_info().rss / 1024 / 1024
    
    @staticmethod
    def _get_system_info() -> Dict[str, Any]:
        """Get system information for benchmark context."""
        return {
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
            "python_version": psutil.version_info,
            "platform": psutil.LINUX if hasattr(psutil, 'LINUX') else "unknown"
        }
    
    @staticmethod
    def _calculate_std(values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5