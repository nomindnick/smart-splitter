"""Performance optimization utilities for PDF processing and memory management."""

import gc
import fitz
import psutil
from typing import List, Optional, Dict, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from .monitor import PerformanceMonitor, monitor_performance


class MemoryManager:
    """Manages memory usage and garbage collection."""
    
    def __init__(self, max_memory_mb: int = 500):
        self.max_memory_mb = max_memory_mb
        self.performance_monitor = PerformanceMonitor()
    
    @monitor_performance("memory_check")
    def check_memory_usage(self) -> Dict[str, float]:
        """Check current memory usage."""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent": process.memory_percent(),
            "available_mb": psutil.virtual_memory().available / 1024 / 1024
        }
    
    @monitor_performance("memory_cleanup")
    def cleanup_memory(self, force: bool = False) -> bool:
        """Clean up memory if usage is high."""
        memory_info = self.check_memory_usage()
        
        if force or memory_info["rss_mb"] > self.max_memory_mb:
            # Force garbage collection
            gc.collect()
            
            # Additional cleanup for PyMuPDF
            if hasattr(fitz, 'TOOLS') and hasattr(fitz.TOOLS, 'store_shrink'):
                fitz.TOOLS.store_shrink(100)  # Free 100% of store
            
            return True
        
        return False
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        return self.performance_monitor.get_operation_stats("memory_check")


class PDFOptimizer:
    """Optimizes PDF processing operations for better performance."""
    
    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        self.memory_manager = memory_manager or MemoryManager()
        self.performance_monitor = PerformanceMonitor()
        self._pdf_cache: Dict[str, fitz.Document] = {}
        self._cache_lock = threading.Lock()
    
    @monitor_performance("pdf_load_optimized")
    def load_pdf_optimized(self, pdf_path: str, use_cache: bool = True) -> fitz.Document:
        """Load PDF with optimization and caching."""
        if use_cache:
            with self._cache_lock:
                if pdf_path in self._pdf_cache:
                    return self._pdf_cache[pdf_path]
        
        # Check memory before loading
        self.memory_manager.cleanup_memory()
        
        try:
            # Open with optimizations
            doc = fitz.open(pdf_path)
            
            if use_cache and len(self._pdf_cache) < 3:  # Limit cache size
                with self._cache_lock:
                    self._pdf_cache[pdf_path] = doc
            
            return doc
        
        except Exception as e:
            raise RuntimeError(f"Failed to load PDF {pdf_path}: {str(e)}")
    
    @monitor_performance("batch_text_extraction")
    def extract_text_batch(self, pdf_doc: fitz.Document, 
                          page_ranges: List[tuple], 
                          max_workers: int = 3) -> Dict[tuple, str]:
        """Extract text from multiple page ranges concurrently."""
        results = {}
        
        def extract_range_text(page_range: tuple) -> tuple:
            start_page, end_page = page_range
            text_parts = []
            
            for page_num in range(start_page, min(end_page + 1, pdf_doc.page_count)):
                try:
                    page = pdf_doc[page_num]
                    text = page.get_text()
                    text_parts.append(text)
                    
                    # Periodic memory check
                    if page_num % 10 == 0:
                        self.memory_manager.cleanup_memory()
                
                except Exception as e:
                    print(f"Error extracting text from page {page_num}: {e}")
                    continue
            
            return page_range, " ".join(text_parts)
        
        # Use thread pool for concurrent extraction
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_range = {
                executor.submit(extract_range_text, page_range): page_range 
                for page_range in page_ranges
            }
            
            for future in as_completed(future_to_range):
                try:
                    page_range, text = future.result()
                    results[page_range] = text
                except Exception as e:
                    page_range = future_to_range[future]
                    print(f"Error processing range {page_range}: {e}")
                    results[page_range] = ""
        
        return results
    
    @monitor_performance("optimized_page_rendering")
    def render_page_optimized(self, pdf_doc: fitz.Document, page_num: int, 
                            scale: float = 1.5) -> Optional[bytes]:
        """Render page with memory optimization."""
        try:
            # Check memory before rendering
            self.memory_manager.cleanup_memory()
            
            page = pdf_doc[page_num]
            
            # Use optimized matrix and rendering settings
            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat, alpha=False)  # No alpha for performance
            
            # Convert to bytes immediately and free pixmap
            img_data = pix.tobytes("png")
            pix = None  # Free memory
            
            return img_data
        
        except Exception as e:
            print(f"Error rendering page {page_num}: {e}")
            return None
    
    @monitor_performance("batch_pdf_export")
    def export_pdfs_batch(self, source_doc: fitz.Document, 
                         export_tasks: List[Dict[str, Any]], 
                         max_workers: int = 2) -> List[Dict[str, Any]]:
        """Export multiple PDF sections concurrently."""
        results = []
        
        def export_single_pdf(task: Dict[str, Any]) -> Dict[str, Any]:
            try:
                start_page = task["start_page"]
                end_page = task["end_page"]
                output_path = task["output_path"]
                
                # Check memory before export
                self.memory_manager.cleanup_memory()
                
                # Create new document
                output_doc = fitz.open()
                
                # Insert pages
                for page_num in range(start_page, end_page + 1):
                    if page_num < source_doc.page_count:
                        output_doc.insert_pdf(source_doc, from_page=page_num, to_page=page_num)
                
                # Save document
                output_doc.save(output_path)
                output_doc.close()
                
                return {
                    "task": task,
                    "success": True,
                    "output_path": output_path,
                    "page_count": end_page - start_page + 1
                }
            
            except Exception as e:
                return {
                    "task": task,
                    "success": False,
                    "error": str(e)
                }
        
        # Use thread pool for concurrent exports (limited to prevent memory issues)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(export_single_pdf, task): task 
                for task in export_tasks
            }
            
            for future in as_completed(future_to_task):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    task = future_to_task[future]
                    results.append({
                        "task": task,
                        "success": False,
                        "error": str(e)
                    })
        
        return results
    
    def clear_cache(self):
        """Clear PDF cache and free memory."""
        with self._cache_lock:
            for doc in self._pdf_cache.values():
                try:
                    doc.close()
                except:
                    pass
            self._pdf_cache.clear()
        
        self.memory_manager.cleanup_memory(force=True)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for PDF operations."""
        return self.performance_monitor.get_all_stats()


class ProcessingOptimizer:
    """Optimizes overall document processing workflow."""
    
    def __init__(self):
        self.memory_manager = MemoryManager()
        self.pdf_optimizer = PDFOptimizer(self.memory_manager)
        self.performance_monitor = PerformanceMonitor()
    
    @monitor_performance("optimized_document_processing")
    def process_document_optimized(self, pdf_path: str, 
                                 boundary_detector, classifier, 
                                 naming_generator) -> List[Dict[str, Any]]:
        """Process document with optimizations applied."""
        # Load PDF with optimization
        pdf_doc = self.pdf_optimizer.load_pdf_optimized(pdf_path)
        
        try:
            # Extract text in batches for large documents
            page_count = pdf_doc.page_count
            
            if page_count > 100:
                # For large documents, process in chunks
                chunk_size = 50
                all_boundaries = []
                
                for i in range(0, page_count, chunk_size):
                    end_page = min(i + chunk_size - 1, page_count - 1)
                    chunk_boundaries = boundary_detector.detect_boundaries_range(
                        pdf_doc, i, end_page
                    )
                    # Adjust page numbers for global context
                    adjusted_boundaries = [
                        (start + i, end + i, doc_type) 
                        for start, end, doc_type in chunk_boundaries
                    ]
                    all_boundaries.extend(adjusted_boundaries)
                    
                    # Memory cleanup between chunks
                    self.memory_manager.cleanup_memory()
                
                boundaries = all_boundaries
            else:
                # Normal processing for smaller documents
                boundaries = boundary_detector.detect_boundaries(pdf_doc)
            
            # Process classifications and naming in batches
            results = []
            batch_size = 10
            
            for i in range(0, len(boundaries), batch_size):
                batch_boundaries = boundaries[i:i + batch_size]
                
                # Extract text for batch
                page_ranges = [(start, end) for start, end, _ in batch_boundaries]
                texts = self.pdf_optimizer.extract_text_batch(pdf_doc, page_ranges)
                
                # Process each boundary in batch
                for j, (start_page, end_page, doc_type) in enumerate(batch_boundaries):
                    page_range = (start_page, end_page)
                    text = texts.get(page_range, "")
                    
                    # Classify document
                    classification = classifier.classify_document(text[:1000])  # Limit text
                    
                    # Generate filename
                    filename = naming_generator.generate_filename(
                        classification.document_type,
                        text[:500],  # Limit text for naming
                        start_page + 1,
                        end_page + 1
                    )
                    
                    results.append({
                        "start_page": start_page,
                        "end_page": end_page,
                        "document_type": classification.document_type,
                        "filename": filename,
                        "confidence": classification.confidence,
                        "text_sample": text[:200]
                    })
                
                # Memory cleanup between batches
                self.memory_manager.cleanup_memory()
            
            return results
        
        finally:
            # Always clean up
            if pdf_path not in self.pdf_optimizer._pdf_cache:
                pdf_doc.close()
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get comprehensive optimization statistics."""
        return {
            "memory_stats": self.memory_manager.get_memory_stats(),
            "pdf_stats": self.pdf_optimizer.get_performance_stats(),
            "processing_stats": self.performance_monitor.get_all_stats()
        }