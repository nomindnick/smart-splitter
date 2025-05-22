"""Phase 4 demonstration: Polish and Optimization features."""

import sys
import argparse
from pathlib import Path
import time

from .performance.benchmarks import BenchmarkRunner
from .performance.monitor import global_monitor
from .performance.optimizer import ProcessingOptimizer
from .config.advanced import AdvancedConfigManager, ConfigProfileManager
from .error_handling.handlers import global_error_handler, global_recovery_manager
from .error_handling.validators import InputValidator


def run_performance_demo():
    """Demonstrate performance monitoring and optimization."""
    print("🚀 Phase 4: Performance Optimization Demo")
    print("=" * 50)
    
    # Create sample PDF for testing (if available)
    test_pdf = None
    possible_test_files = [
        "test_construction_docs.pdf",
        "sample.pdf",
        "test.pdf"
    ]
    
    for filename in possible_test_files:
        if Path(filename).exists():
            test_pdf = filename
            break
    
    if not test_pdf:
        print("❌ No test PDF found. Creating mock benchmark...")
        print("   Place a test PDF file to see full performance analysis.")
        print()
        demonstrate_memory_management()
        return
    
    print(f"📄 Using test PDF: {test_pdf}")
    print()
    
    # Initialize performance tools
    benchmark_runner = BenchmarkRunner()
    
    print("1. Running comprehensive benchmark suite...")
    try:
        results = benchmark_runner.run_comprehensive_benchmark_suite(test_pdf)
        
        print("✅ Benchmark completed!")
        print()
        
        # Display results
        print("📊 Benchmark Results:")
        print("-" * 30)
        
        for test_name, result in results.items():
            status = "✅" if result.success else "❌"
            print(f"{status} {test_name.replace('_', ' ').title()}")
            print(f"   Duration: {result.duration:.2f}s")
            print(f"   Peak Memory: {result.memory_peak:.1f}MB")
            
            if result.additional_metrics:
                for key, value in result.additional_metrics.items():
                    if isinstance(value, float):
                        print(f"   {key.replace('_', ' ').title()}: {value:.2f}")
                    else:
                        print(f"   {key.replace('_', ' ').title()}: {value}")
            print()
        
        # Generate and save report
        report = benchmark_runner.generate_report()
        report_file = "benchmark_report.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"📁 Full benchmark report saved to: {report_file}")
        
    except Exception as e:
        error_info = global_error_handler.handle_error(e, context={"operation": "benchmarking"})
        print(f"❌ Benchmark failed: {error_info['message']}")
        print(f"   Suggested action: {error_info['suggested_action']}")
    
    print()
    demonstrate_memory_management()


def demonstrate_memory_management():
    """Demonstrate memory management features."""
    print("🧠 Memory Management Demo")
    print("-" * 30)
    
    from .performance.optimizer import MemoryManager
    
    memory_manager = MemoryManager(max_memory_mb=200)
    
    # Check current memory usage
    memory_info = memory_manager.check_memory_usage()
    print(f"📊 Current Memory Usage:")
    print(f"   RSS: {memory_info['rss_mb']:.1f}MB")
    print(f"   Available: {memory_info['available_mb']:.1f}MB")
    print(f"   Process %: {memory_info['percent']:.1f}%")
    print()
    
    # Demonstrate memory cleanup
    print("🧹 Testing memory cleanup...")
    cleanup_result = memory_manager.cleanup_memory(force=True)
    
    if cleanup_result:
        print("✅ Memory cleanup performed")
        
        # Check memory after cleanup
        new_memory_info = memory_manager.check_memory_usage()
        memory_freed = memory_info['rss_mb'] - new_memory_info['rss_mb']
        
        if memory_freed > 0:
            print(f"   Freed: {memory_freed:.1f}MB")
        else:
            print("   No significant memory freed (normal for small applications)")
    else:
        print("ℹ️  Memory cleanup not needed (usage below threshold)")
    
    print()


def run_error_handling_demo():
    """Demonstrate enhanced error handling and validation."""
    print("🛡️  Error Handling & Validation Demo")
    print("=" * 40)
    
    validator = InputValidator()
    
    # Test various validation scenarios
    validation_tests = [
        ("Valid filename", lambda: validator.validate_filename("document_001.pdf")),
        ("Invalid filename (special chars)", lambda: validator.validate_filename("doc<>ument.pdf")),
        ("Valid page range", lambda: validator.validate_page_range(1, 5, 10)),
        ("Invalid page range", lambda: validator.validate_page_range(8, 5, 10)),
        ("Valid API key format", lambda: validator.validate_api_key("sk-1234567890123456789012345678901234567890")),
        ("Invalid API key format", lambda: validator.validate_api_key("invalid-key")),
    ]
    
    for test_name, test_func in validation_tests:
        print(f"🧪 Testing: {test_name}")
        try:
            result = test_func()
            print(f"   ✅ Valid: {result.get('valid', True)}")
        except Exception as e:
            error_info = global_error_handler.handle_error(e, context={"test": test_name})
            print(f"   ❌ {error_info['message']}")
            print(f"   💡 Suggestion: {error_info['suggested_action']}")
        print()
    
    # Show error statistics
    error_stats = global_error_handler.get_error_stats()
    if error_stats["total_errors"] > 0:
        print("📈 Error Statistics:")
        print(f"   Total errors handled: {error_stats['total_errors']}")
        for error_type, count in error_stats["error_counts"].items():
            print(f"   {error_type}: {count}")
        print()


def run_configuration_demo():
    """Demonstrate advanced configuration management."""
    print("⚙️  Advanced Configuration Demo")
    print("=" * 35)
    
    # Initialize advanced configuration
    advanced_config = AdvancedConfigManager()
    profile_manager = ConfigProfileManager(advanced_config)
    
    print("📋 Current Configuration:")
    print(f"   Max Memory: {advanced_config.performance.max_memory_mb}MB")
    print(f"   Max Workers: {advanced_config.performance.max_workers}")
    print(f"   API Timeout: {advanced_config.api.timeout}s")
    print(f"   Export Directory: {advanced_config.export.default_directory}")
    print()
    
    # Validate current configuration
    print("🔍 Validating configuration...")
    validation_result = advanced_config.validate_all_configs()
    
    if validation_result["valid"]:
        print("   ✅ Configuration is valid")
    else:
        print("   ❌ Configuration issues found:")
        for issue in validation_result["all_issues"]:
            print(f"      • {issue}")
    print()
    
    # Show optimization recommendations
    print("💡 Optimization Recommendations:")
    recommendations = advanced_config.get_optimization_recommendations()
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    else:
        print("   ✅ Configuration is already optimized!")
    print()
    
    # Demonstrate auto-optimization
    print("🎯 Auto-optimizing for current system...")
    advanced_config.auto_optimize_for_system()
    
    print("   New settings:")
    print(f"   Max Memory: {advanced_config.performance.max_memory_mb}MB")
    print(f"   Max Workers: {advanced_config.performance.max_workers}")
    print(f"   Batch Size: {advanced_config.performance.batch_size}")
    print()
    
    # Demonstrate profile management
    print("👤 Configuration Profiles:")
    
    # Create default profiles if they don't exist
    existing_profiles = profile_manager.list_profiles()
    if not existing_profiles:
        print("   Creating default profiles...")
        profile_manager.create_default_profiles()
        existing_profiles = profile_manager.list_profiles()
    
    for profile in existing_profiles:
        print(f"   • {profile['name']}: {profile['description']}")
    print()


def demonstrate_integration():
    """Demonstrate integrated Phase 4 features."""
    print("🔗 Integration Demo: Processing with Optimization")
    print("=" * 50)
    
    # Initialize optimized processor
    optimizer = ProcessingOptimizer()
    
    # Monitor the integration demonstration
    with global_monitor.monitor_operation("phase4_integration_demo") as metrics:
        print("🚀 Running optimized processing simulation...")
        
        # Simulate some processing work
        time.sleep(0.1)
        
        # Add some metrics
        metrics.additional_data["simulated_pages"] = 25
        metrics.additional_data["documents_processed"] = 5
        
        print("✅ Processing complete!")
    
    # Show performance metrics
    stats = global_monitor.get_operation_stats("phase4_integration_demo")
    if stats and stats["count"] > 0:
        print(f"📊 Performance Metrics:")
        print(f"   Duration: {stats['avg_duration']:.3f}s")
        print(f"   Memory Delta: {stats['avg_memory_delta']:.1f}MB")
        print(f"   Success Rate: {stats['success_rate']:.1%}")
    
    print()
    
    # Show memory optimization statistics
    memory_stats = optimizer.memory_manager.get_memory_stats()
    if memory_stats and memory_stats.get("count", 0) > 0:
        print("🧠 Memory Management:")
        print(f"   Checks performed: {memory_stats['count']}")
        print(f"   Average duration: {memory_stats['avg_duration']:.3f}s")
    
    print()


def main():
    """Main Phase 4 demonstration."""
    parser = argparse.ArgumentParser(description="Smart-Splitter Phase 4: Polish and Optimization Demo")
    parser.add_argument("--demo", choices=["performance", "error", "config", "integration", "all"],
                       default="all", help="Which demo to run")
    parser.add_argument("--save-config", type=str, help="Save current configuration to file")
    parser.add_argument("--benchmark-only", action="store_true", 
                       help="Run only performance benchmarks")
    
    args = parser.parse_args()
    
    print("🎯 Smart-Splitter Phase 4: Polish and Optimization")
    print("=" * 55)
    print()
    print("Phase 4 introduces:")
    print("• 🚀 Performance monitoring and optimization")
    print("• 🛡️  Enhanced error handling and recovery")
    print("• ⚙️  Advanced configuration management")
    print("• 📊 Comprehensive benchmarking and testing")
    print("• 🔗 Integrated optimization workflow")
    print()
    
    try:
        if args.benchmark_only:
            run_performance_demo()
        elif args.demo == "performance" or args.demo == "all":
            run_performance_demo()
            if args.demo == "all":
                print()
        
        if args.demo == "error" or args.demo == "all":
            run_error_handling_demo()
            if args.demo == "all":
                print()
        
        if args.demo == "config" or args.demo == "all":
            run_configuration_demo()
            if args.demo == "all":
                print()
        
        if args.demo == "integration" or args.demo == "all":
            demonstrate_integration()
        
        # Save configuration if requested
        if args.save_config:
            advanced_config = AdvancedConfigManager()
            advanced_config.export_config(args.save_config)
            print(f"💾 Configuration saved to: {args.save_config}")
        
        print("🎉 Phase 4 demonstration complete!")
        print()
        print("Next steps:")
        print("• Review benchmark results for performance insights")
        print("• Customize configuration profiles for your use case")
        print("• Use enhanced error handling for robust operation")
        print("• Monitor performance in production usage")
        
    except Exception as e:
        error_info = global_error_handler.handle_error(e, context={"operation": "phase4_demo"})
        print(f"❌ Demo failed: {error_info['message']}")
        print(f"💡 Suggested action: {error_info['suggested_action']}")
        
        if error_info["recoverable"]:
            print("🔄 This error might be recoverable - please try again")
        
        sys.exit(1)


if __name__ == "__main__":
    main()