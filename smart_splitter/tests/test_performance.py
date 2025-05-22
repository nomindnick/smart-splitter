"""Tests for performance monitoring and optimization components."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
from pathlib import Path

from smart_splitter.performance.monitor import PerformanceMonitor, PerformanceMetrics, monitor_performance
from smart_splitter.performance.optimizer import MemoryManager, PDFOptimizer, ProcessingOptimizer
from smart_splitter.performance.benchmarks import BenchmarkRunner, BenchmarkResult


class TestPerformanceMonitor(unittest.TestCase):
    """Test performance monitoring functionality."""
    
    def setUp(self):
        self.monitor = PerformanceMonitor()
    
    def test_start_operation(self):
        """Test starting operation monitoring."""
        metrics = self.monitor.start_operation("test_operation", test_data="value")
        
        self.assertEqual(metrics.operation_name, "test_operation")
        self.assertTrue(metrics.start_time > 0)
        self.assertTrue(metrics.memory_start > 0)
        self.assertEqual(metrics.additional_data["test_data"], "value")
        self.assertIn("test_operation", self.monitor.current_operations)
    
    def test_end_operation(self):
        """Test ending operation monitoring."""
        # Start operation
        self.monitor.start_operation("test_operation")
        
        # Wait a bit
        time.sleep(0.01)
        
        # End operation
        self.monitor.end_operation("test_operation", success=True)
        
        # Check results
        self.assertNotIn("test_operation", self.monitor.current_operations)
        self.assertIn("test_operation", self.monitor.metrics)
        
        metrics = self.monitor.metrics["test_operation"][0]
        self.assertTrue(metrics.success)
        self.assertIsNotNone(metrics.duration)
        self.assertTrue(metrics.duration > 0)
    
    def test_context_manager(self):
        """Test monitor_operation context manager."""
        with self.monitor.monitor_operation("context_test") as metrics:
            self.assertEqual(metrics.operation_name, "context_test")
            time.sleep(0.01)
        
        # Should be automatically completed
        self.assertNotIn("context_test", self.monitor.current_operations)
        self.assertIn("context_test", self.monitor.metrics)
    
    def test_context_manager_with_exception(self):
        """Test context manager handles exceptions."""
        with self.assertRaises(ValueError):
            with self.monitor.monitor_operation("error_test"):
                raise ValueError("Test error")
        
        # Should record the failure
        self.assertIn("error_test", self.monitor.metrics)
        metrics = self.monitor.metrics["error_test"][0]
        self.assertFalse(metrics.success)
        self.assertEqual(metrics.error_message, "Test error")
    
    def test_get_operation_stats(self):
        """Test getting operation statistics."""
        # Record some operations
        for i in range(3):
            with self.monitor.monitor_operation("stat_test"):
                time.sleep(0.001)
        
        stats = self.monitor.get_operation_stats("stat_test")
        
        self.assertEqual(stats["count"], 3)
        self.assertEqual(stats["success_count"], 3)
        self.assertEqual(stats["success_rate"], 1.0)
        self.assertTrue(stats["avg_duration"] > 0)
    
    def test_monitor_performance_decorator(self):
        """Test monitor_performance decorator."""
        @monitor_performance("decorated_test")
        def test_function():
            time.sleep(0.001)
            return "result"
        
        result = test_function()
        
        self.assertEqual(result, "result")
        # Check if global monitor recorded the operation
        from smart_splitter.performance.monitor import global_monitor
        self.assertIn("decorated_test", global_monitor.metrics)


class TestMemoryManager(unittest.TestCase):
    """Test memory management functionality."""
    
    def setUp(self):
        self.memory_manager = MemoryManager(max_memory_mb=100)
    
    @patch('psutil.Process')
    def test_check_memory_usage(self, mock_process):
        """Test memory usage checking."""
        # Mock memory info
        mock_memory_info = Mock()
        mock_memory_info.rss = 100 * 1024 * 1024  # 100MB
        mock_memory_info.vms = 200 * 1024 * 1024  # 200MB
        
        mock_process_instance = Mock()
        mock_process_instance.memory_info.return_value = mock_memory_info
        mock_process_instance.memory_percent.return_value = 50.0
        mock_process.return_value = mock_process_instance
        
        # Mock virtual memory
        with patch('psutil.virtual_memory') as mock_vm:
            mock_vm.return_value.available = 1024 * 1024 * 1024  # 1GB
            
            memory_info = self.memory_manager.check_memory_usage()
            
            self.assertEqual(memory_info["rss_mb"], 100.0)
            self.assertEqual(memory_info["vms_mb"], 200.0)
            self.assertEqual(memory_info["percent"], 50.0)
            self.assertEqual(memory_info["available_mb"], 1024.0)
    
    @patch('gc.collect')
    def test_cleanup_memory(self, mock_gc):
        """Test memory cleanup."""
        # Mock high memory usage
        with patch.object(self.memory_manager, 'check_memory_usage') as mock_check:
            mock_check.return_value = {"rss_mb": 150}  # Above threshold
            
            result = self.memory_manager.cleanup_memory()
            
            self.assertTrue(result)
            mock_gc.assert_called_once()


class TestPDFOptimizer(unittest.TestCase):
    """Test PDF optimization functionality."""
    
    def setUp(self):
        self.pdf_optimizer = PDFOptimizer()
    
    @patch('fitz.open')
    def test_load_pdf_optimized(self, mock_fitz_open):
        """Test optimized PDF loading."""
        mock_doc = Mock()
        mock_fitz_open.return_value = mock_doc
        
        # Test loading without cache
        result = self.pdf_optimizer.load_pdf_optimized("test.pdf", use_cache=False)
        
        self.assertEqual(result, mock_doc)
        mock_fitz_open.assert_called_once_with("test.pdf")
    
    @patch('fitz.open')
    def test_load_pdf_with_cache(self, mock_fitz_open):
        """Test PDF loading with caching."""
        mock_doc = Mock()
        mock_fitz_open.return_value = mock_doc
        
        # First load
        result1 = self.pdf_optimizer.load_pdf_optimized("test.pdf", use_cache=True)
        
        # Second load should use cache
        result2 = self.pdf_optimizer.load_pdf_optimized("test.pdf", use_cache=True)
        
        self.assertEqual(result1, result2)
        mock_fitz_open.assert_called_once()  # Should only be called once
    
    def test_extract_text_batch(self):
        """Test batch text extraction."""
        # Mock PDF document
        mock_doc = Mock()
        mock_doc.page_count = 10
        
        # Mock pages
        mock_pages = []
        for i in range(10):
            mock_page = Mock()
            mock_page.get_text.return_value = f"Page {i} text"
            mock_pages.append(mock_page)
        
        mock_doc.__getitem__ = lambda self, idx: mock_pages[idx]
        
        # Test batch extraction
        page_ranges = [(0, 2), (3, 5), (6, 9)]
        results = self.pdf_optimizer.extract_text_batch(mock_doc, page_ranges, max_workers=2)
        
        self.assertEqual(len(results), 3)
        self.assertIn((0, 2), results)
        self.assertIn((3, 5), results)
        self.assertIn((6, 9), results)
    
    @patch('fitz.open')
    def test_render_page_optimized(self, mock_fitz_open):
        """Test optimized page rendering."""
        # Mock document and page
        mock_doc = Mock()
        mock_page = Mock()
        mock_pix = Mock()
        mock_pix.tobytes.return_value = b"image_data"
        
        mock_page.get_pixmap.return_value = mock_pix
        mock_doc.__getitem__ = lambda self, idx: mock_page
        
        result = self.pdf_optimizer.render_page_optimized(mock_doc, 0, scale=1.0)
        
        self.assertEqual(result, b"image_data")
        mock_page.get_pixmap.assert_called_once()
    
    def test_clear_cache(self):
        """Test cache clearing."""
        # Add mock document to cache
        mock_doc = Mock()
        self.pdf_optimizer._pdf_cache["test.pdf"] = mock_doc
        
        self.pdf_optimizer.clear_cache()
        
        self.assertEqual(len(self.pdf_optimizer._pdf_cache), 0)
        mock_doc.close.assert_called_once()


class TestBenchmarkRunner(unittest.TestCase):
    """Test benchmark runner functionality."""
    
    def setUp(self):
        self.benchmark_runner = BenchmarkRunner()
    
    @patch('psutil.Process')
    def test_memory_stress_test(self, mock_process):
        """Test memory stress testing."""
        # Mock memory usage
        mock_memory_info = Mock()
        mock_memory_info.rss = 100 * 1024 * 1024  # 100MB
        
        mock_process_instance = Mock()
        mock_process_instance.memory_info.return_value = mock_memory_info
        mock_process.return_value = mock_process_instance
        
        # Run short stress test
        result = self.benchmark_runner.run_memory_stress_test(
            target_memory_mb=200, duration_seconds=0.1
        )
        
        self.assertIsInstance(result, BenchmarkResult)
        self.assertTrue(result.duration >= 0.1)
        self.assertTrue(result.memory_start > 0)
    
    def test_benchmark_result_to_dict(self):
        """Test benchmark result serialization."""
        result = BenchmarkResult(
            test_name="test",
            duration=1.5,
            memory_peak=100.0,
            memory_start=80.0,
            memory_end=90.0,
            success=True,
            additional_metrics={"key": "value"}
        )
        
        result_dict = result.to_dict()
        
        self.assertEqual(result_dict["test_name"], "test")
        self.assertEqual(result_dict["duration"], 1.5)
        self.assertEqual(result_dict["success"], True)
        self.assertEqual(result_dict["additional_metrics"]["key"], "value")
    
    def test_generate_report(self):
        """Test benchmark report generation."""
        # Add a mock result
        result = BenchmarkResult(
            test_name="test_operation",
            duration=2.5,
            memory_peak=150.0,
            memory_start=100.0,
            memory_end=120.0,
            success=True
        )
        self.benchmark_runner.results.append(result)
        
        report = self.benchmark_runner.generate_report()
        
        self.assertIn("Performance Benchmark Report", report)
        self.assertIn("test_operation", report)
        self.assertIn("Duration: 2.50s", report)
        self.assertIn("Success: ✓", report)
    
    @patch('json.dump')
    def test_save_results(self, mock_json_dump):
        """Test saving benchmark results."""
        # Add a mock result
        result = BenchmarkResult(
            test_name="test",
            duration=1.0,
            memory_peak=100.0,
            memory_start=90.0,
            memory_end=95.0,
            success=True
        )
        self.benchmark_runner.results.append(result)
        
        # Mock file operations
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            self.benchmark_runner.save_results("output.json")
            
            mock_open.assert_called_once_with("output.json", 'w')
            mock_json_dump.assert_called_once()


if __name__ == '__main__':
    unittest.main()