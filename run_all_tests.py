#!/usr/bin/env python3
"""
Unified Test Runner for Palette System
Runs all test suites in sequence and provides comprehensive report:
- Python Backend Generation Pipeline Tests
- Quality Validation Workflow Tests  
- VS Code Integration Tests
- Performance Benchmarks
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Import test suites
from test_generation_pipeline import PaletteTestSuite
from test_quality_workflow import QualityWorkflowTester
from test_vscode_integration import VSCodeIntegrationTester

class UnifiedTestRunner:
    def __init__(self):
        self.start_time = time.time()
        self.test_results = {}
        self.overall_summary = {}
        
    async def run_all_test_suites(self):
        """Run all test suites and generate comprehensive report"""
        print("🧪 Palette Unified Test Suite")
        print("=" * 50)
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        # Test Suite 1: Python Backend Generation Pipeline
        print("\n🐍 PHASE 1: Python Backend Generation Pipeline Tests")
        print("-" * 50)
        try:
            generation_tester = PaletteTestSuite()
            generation_results = await generation_tester.run_all_tests()
            self.test_results["generation_pipeline"] = generation_results
            print("✅ Generation pipeline tests completed")
        except Exception as e:
            print(f"❌ Generation pipeline tests failed: {e}")
            self.test_results["generation_pipeline"] = {
                "all_tests_passed": False,
                "error": str(e),
                "total_tests": 0,
                "passed": 0,
                "failed": 1
            }
        
        # Test Suite 2: Quality Validation Workflow
        print("\n🔍 PHASE 2: Quality Validation Workflow Tests")  
        print("-" * 50)
        try:
            quality_tester = QualityWorkflowTester()
            quality_results = quality_tester.run_all_quality_tests()
            self.test_results["quality_workflow"] = quality_results
            print("✅ Quality validation tests completed")
        except Exception as e:
            print(f"❌ Quality validation tests failed: {e}")
            self.test_results["quality_workflow"] = {
                "quality_system_working": False,
                "error": str(e),
                "total_tests": 0,
                "passed": 0,
                "failed": 1
            }
        
        # Test Suite 3: VS Code Integration
        print("\n🔗 PHASE 3: VS Code Integration Tests")
        print("-" * 50)
        try:
            integration_tester = VSCodeIntegrationTester()
            integration_results = await integration_tester.run_integration_tests()
            self.test_results["vscode_integration"] = integration_results
            print("✅ VS Code integration tests completed")
        except Exception as e:
            print(f"❌ VS Code integration tests failed: {e}")
            self.test_results["vscode_integration"] = {
                "integration_working": False,
                "error": str(e),
                "total_tests": 0,
                "passed": 0,
                "failed": 1
            }
        
        # Generate comprehensive report
        await self.generate_comprehensive_report()
        
        return self.overall_summary
    
    async def generate_comprehensive_report(self):
        """Generate comprehensive test report"""
        total_duration = time.time() - self.start_time
        
        print("\n" + "=" * 70)
        print("🏁 COMPREHENSIVE TEST REPORT")
        print("=" * 70)
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Total Duration: {total_duration:.2f} seconds")
        print("=" * 70)
        
        # Collect overall statistics
        total_tests = 0
        total_passed = 0
        total_failed = 0
        test_suites_passed = 0
        test_suites_failed = 0
        
        suite_summaries = []
        
        for suite_name, results in self.test_results.items():
            suite_tests = results.get("total_tests", 0)
            suite_passed = results.get("passed", 0)
            suite_failed = results.get("failed", 0)
            
            total_tests += suite_tests
            total_passed += suite_passed
            total_failed += suite_failed
            
            # Determine suite status
            if suite_name == "generation_pipeline":
                suite_success = results.get("all_tests_passed", False)
            elif suite_name == "quality_workflow":
                suite_success = results.get("quality_system_working", False)
            elif suite_name == "vscode_integration":
                suite_success = results.get("integration_working", False)
            else:
                suite_success = False
            
            if suite_success:
                test_suites_passed += 1
                status_icon = "✅"
            else:
                test_suites_failed += 1
                status_icon = "❌"
            
            suite_summaries.append({
                "name": suite_name,
                "status": status_icon,
                "success": suite_success,
                "tests": suite_tests,
                "passed": suite_passed,
                "failed": suite_failed,
                "success_rate": (suite_passed / suite_tests * 100) if suite_tests > 0 else 0
            })
        
        # Print suite summaries
        print("\n📋 Test Suite Summary:")
        for suite in suite_summaries:
            print(f"   {suite['status']} {suite['name']:<25} - {suite['passed']}/{suite['tests']} tests ({suite['success_rate']:.1f}%)")
            if 'error' in self.test_results[suite['name']]:
                print(f"      Error: {self.test_results[suite['name']]['error']}")
        
        # Overall statistics
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 Overall Statistics:")
        print(f"   Total Test Suites: {test_suites_passed + test_suites_failed}")
        print(f"   ✅ Suites Passed:  {test_suites_passed}")
        print(f"   ❌ Suites Failed:  {test_suites_failed}")
        print(f"   📈 Suite Success:   {(test_suites_passed / (test_suites_passed + test_suites_failed) * 100):.1f}%")
        print()
        print(f"   Total Individual Tests: {total_tests}")
        print(f"   ✅ Individual Passed:   {total_passed}")
        print(f"   ❌ Individual Failed:   {total_failed}")
        print(f"   📈 Test Success Rate:   {overall_success_rate:.1f}%")
        
        # System status assessment
        print(f"\n🎯 System Status Assessment:")
        
        critical_systems = [
            ("Python Backend", self.test_results.get("generation_pipeline", {}).get("all_tests_passed", False)),
            ("Quality Validation", self.test_results.get("quality_workflow", {}).get("quality_system_working", False)),
            ("VS Code Integration", self.test_results.get("vscode_integration", {}).get("integration_working", False))
        ]
        
        all_critical_working = True
        for system_name, system_working in critical_systems:
            status_icon = "✅" if system_working else "❌"
            print(f"   {status_icon} {system_name}: {'Working' if system_working else 'Issues Detected'}")
            if not system_working:
                all_critical_working = False
        
        print("\n" + "=" * 70)
        
        if all_critical_working:
            print("🎉 SYSTEM STATUS: ALL SYSTEMS OPERATIONAL")
            print("   Palette is ready for production use!")
            system_status = "OPERATIONAL"
        elif test_suites_passed >= 2:
            print("⚠️  SYSTEM STATUS: MOSTLY OPERATIONAL") 
            print("   Palette is functional but some components need attention.")
            system_status = "MOSTLY_OPERATIONAL"
        else:
            print("🚨 SYSTEM STATUS: CRITICAL ISSUES")
            print("   Palette requires immediate attention before use.")
            system_status = "CRITICAL_ISSUES"
        
        print("=" * 70)
        
        # Recommendations based on results
        print("\n💡 Recommendations:")
        recommendations = []
        
        if not self.test_results.get("generation_pipeline", {}).get("all_tests_passed", False):
            recommendations.append("🔧 Fix Python backend issues - check server startup and API endpoints")
        
        if not self.test_results.get("quality_workflow", {}).get("quality_system_working", False):
            recommendations.append("🔍 Address quality validation system - ensure ComponentValidator is working")
        
        if not self.test_results.get("vscode_integration", {}).get("integration_working", False):
            recommendations.append("🔗 Fix VS Code integration - check extension compilation and communication")
        
        if overall_success_rate < 80:
            recommendations.append("📈 Improve test coverage and fix failing tests")
        
        if not recommendations:
            recommendations.append("✨ System is working well - consider performance optimization and new features")
        
        for rec in recommendations:
            print(f"   {rec}")
        
        print("\n" + "=" * 70)
        
        # Store overall summary
        self.overall_summary = {
            "timestamp": datetime.now().isoformat(),
            "duration": total_duration,
            "system_status": system_status,
            "suite_results": {
                "total_suites": test_suites_passed + test_suites_failed,
                "suites_passed": test_suites_passed,
                "suites_failed": test_suites_failed,
                "suite_success_rate": (test_suites_passed / (test_suites_passed + test_suites_failed) * 100) if (test_suites_passed + test_suites_failed) > 0 else 0
            },
            "test_results": {
                "total_tests": total_tests,
                "passed": total_passed,
                "failed": total_failed,
                "success_rate": overall_success_rate
            },
            "critical_systems": dict(critical_systems),
            "all_systems_operational": all_critical_working,
            "recommendations": recommendations,
            "detailed_results": self.test_results
        }
        
        # Save detailed report to file
        await self.save_test_report()
    
    async def save_test_report(self):
        """Save detailed test report to JSON file"""
        try:
            report_file = Path(__file__).parent / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(report_file, 'w') as f:
                json.dump(self.overall_summary, f, indent=2, default=str)
            
            print(f"📄 Detailed report saved: {report_file}")
            
        except Exception as e:
            print(f"⚠️  Failed to save report: {e}")
    
    def get_exit_code(self) -> int:
        """Get appropriate exit code based on test results"""
        if self.overall_summary.get("all_systems_operational", False):
            return 0  # All systems working
        elif self.overall_summary.get("system_status") == "MOSTLY_OPERATIONAL":
            return 1  # Some issues but mostly working
        else:
            return 2  # Critical issues

async def main():
    """Main test runner entry point"""
    try:
        runner = UnifiedTestRunner()
        summary = await runner.run_all_test_suites()
        
        # Print final status
        print(f"\n🏁 Testing completed with status: {summary.get('system_status', 'UNKNOWN')}")
        
        exit_code = runner.get_exit_code()
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Check if we're being run directly or imported
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("""
🧪 Palette Unified Test Suite

This script runs comprehensive tests for the Palette system:

📋 Test Suites:
   1. Python Backend Generation Pipeline
   2. Quality Validation Workflow  
   3. VS Code Integration

🚀 Usage:
   python3 run_all_tests.py

📊 Exit Codes:
   0 - All systems operational
   1 - Mostly operational (some issues)
   2 - Critical issues detected
   130 - Interrupted by user

📄 Report:
   Detailed JSON report saved to test_report_YYYYMMDD_HHMMSS.json

💡 Prerequisites:
   - Python environment setup (src/palette modules)
   - VS Code extension compiled (npm run compile)
   - API keys set (OPENAI_API_KEY or ANTHROPIC_API_KEY)
   - Required Python dependencies installed
        """)
        sys.exit(0)
    
    asyncio.run(main())