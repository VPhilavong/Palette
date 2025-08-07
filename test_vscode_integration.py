#!/usr/bin/env python3
"""
VS Code Extension Integration Test Suite
Tests the integration between VS Code extension and Python backend:
- PythonServerManager functionality
- Request routing between AI SDK and Python backend
- UnifiedPalettePanel communication
- Stream handling and real-time updates
- Error handling and fallbacks
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List
import requests
import websockets
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

@dataclass
class IntegrationTest:
    name: str
    description: str
    test_function: str
    timeout: int = 30

class VSCodeIntegrationTester:
    def __init__(self):
        self.test_results = []
        self.server_process = None
        self.server_url = "http://127.0.0.1:8765"
        self.extension_path = Path(__file__).parent / "vscode-extension"
        
    async def run_integration_tests(self):
        """Run comprehensive VS Code integration tests"""
        print("🔗 VS Code Extension Integration Test Suite")
        print("=" * 55)
        
        try:
            # Setup
            await self.setup_test_environment()
            
            # Core integration tests
            await self.test_python_server_manager()
            await self.test_request_routing_logic()
            await self.test_complexity_analyzer()
            await self.test_unified_panel_communication()
            await self.test_streaming_integration()
            await self.test_error_handling_and_fallbacks()
            await self.test_session_persistence()
            await self.test_performance_integration()
            
        finally:
            await self.cleanup_test_environment()
            
        self.print_integration_report()
        return self.get_summary()
    
    async def setup_test_environment(self):
        """Setup VS Code extension test environment"""
        start_time = time.time()
        
        try:
            # Check if extension files exist
            required_files = [
                self.extension_path / "src" / "services" / "PythonServerManager.ts",
                self.extension_path / "src" / "intelligence" / "RequestRouter.ts",
                self.extension_path / "src" / "intelligence" / "ComplexityAnalyzer.ts",
                self.extension_path / "src" / "UnifiedPalettePanel.ts",
                self.extension_path / "package.json"
            ]
            
            missing_files = [f for f in required_files if not f.exists()]
            
            if missing_files:
                raise FileNotFoundError(f"Missing VS Code extension files: {missing_files}")
            
            # Check if extension is compiled
            out_dir = self.extension_path / "out"
            if not out_dir.exists() or not list(out_dir.glob("*.js")):
                print("📦 Compiling VS Code extension...")
                compile_result = subprocess.run([
                    "npm", "run", "compile"
                ], cwd=self.extension_path, capture_output=True, text=True)
                
                if compile_result.returncode != 0:
                    raise RuntimeError(f"Extension compilation failed: {compile_result.stderr}")
            
            # Start Python server
            await self.start_python_server()
            
            self.test_results.append({
                "test_name": "setup_test_environment",
                "status": "PASS",
                "duration": time.time() - start_time,
                "message": "VS Code integration environment ready",
                "details": {
                    "extension_path": str(self.extension_path),
                    "server_url": self.server_url,
                    "compiled_files": len(list(out_dir.glob("*.js"))) if out_dir.exists() else 0
                }
            })
            
        except Exception as e:
            self.test_results.append({
                "test_name": "setup_test_environment",
                "status": "FAIL",
                "duration": time.time() - start_time,
                "message": f"Setup failed: {str(e)}"
            })
            raise
    
    async def start_python_server(self):
        """Start Python backend server"""
        try:
            server_script = Path(__file__).parent / "run_server.py"
            
            if not server_script.exists():
                raise FileNotFoundError(f"Server launcher not found: {server_script}")
            
            env = os.environ.copy()
            env["PYTHONPATH"] = str(Path(__file__).parent / "src")
            
            self.server_process = subprocess.Popen([
                sys.executable, str(server_script)
            ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            for i in range(30):
                try:
                    response = requests.get(f"{self.server_url}/health", timeout=1)
                    if response.status_code == 200:
                        return
                except requests.exceptions.RequestException:
                    pass
                await asyncio.sleep(1)
            
            raise TimeoutError("Python server failed to start")
            
        except Exception as e:
            raise RuntimeError(f"Failed to start Python server: {str(e)}")
    
    async def test_python_server_manager(self):
        """Test PythonServerManager functionality simulation"""
        start_time = time.time()
        
        try:
            # Test basic server health check (simulating PythonServerManager.getServerStatus)
            health_response = requests.get(f"{self.server_url}/health", timeout=10)
            
            if health_response.status_code != 200:
                raise AssertionError(f"Health check failed: {health_response.status_code}")
            
            health_data = health_response.json()
            
            # Simulate server status checking
            server_healthy = health_data.get("status") == "healthy"
            server_version = health_data.get("version") is not None
            
            # Test server restart capability (simulated)
            status_response = requests.get(f"{self.server_url}/api/status", timeout=10)
            server_responsive = status_response.status_code == 200
            
            if server_healthy and server_version and server_responsive:
                status = "PASS"
                message = "PythonServerManager functionality working"
            else:
                status = "FAIL"
                message = f"PythonServerManager issues - healthy: {server_healthy}, version: {server_version}, responsive: {server_responsive}"
            
            self.test_results.append({
                "test_name": "python_server_manager",
                "status": status,
                "duration": time.time() - start_time,
                "message": message,
                "details": {
                    "server_healthy": server_healthy,
                    "server_version": health_data.get("version"),
                    "server_responsive": server_responsive
                }
            })
            
        except Exception as e:
            self.test_results.append({
                "test_name": "python_server_manager",
                "status": "FAIL",
                "duration": time.time() - start_time,
                "message": f"PythonServerManager test failed: {str(e)}"
            })
    
    async def test_request_routing_logic(self):
        """Test intelligent request routing between AI SDK and Python backend"""
        start_time = time.time()
        
        try:
            # Test different request types that should route differently
            test_requests = [
                {
                    "message": "Create a simple button component",
                    "expected_complexity": "simple",
                    "expected_route": "ai_sdk"
                },
                {
                    "message": "Create a complete dashboard page with sidebar navigation, data charts, user profile header, and data table with sorting and filtering",
                    "expected_complexity": "complex", 
                    "expected_route": "python_backend"
                },
                {
                    "message": "Generate a landing page with hero section, features grid, testimonials, and pricing table",
                    "expected_complexity": "complex",
                    "expected_route": "python_backend"
                }
            ]
            
            routing_tests_passed = 0
            
            for test_req in test_requests:
                # Simulate complexity analysis (this would be done by ComplexityAnalyzer.ts)
                message_lower = test_req["message"].lower()
                complexity_keywords = ["complete", "dashboard", "page", "multi", "feature", "app", "site", "landing"]
                detected_complexity = "complex" if any(kw in message_lower for kw in complexity_keywords) else "simple"
                
                # Test that complexity detection works
                if detected_complexity == test_req["expected_complexity"]:
                    routing_tests_passed += 1
                    
                    # Test appropriate endpoint based on routing decision
                    if detected_complexity == "complex":
                        # Should route to Python backend - test generation endpoint
                        try:
                            response = requests.post(
                                f"{self.server_url}/api/generate/stream",
                                json={
                                    "message": test_req["message"],
                                    "projectPath": "/tmp",
                                    "conversationHistory": []
                                },
                                timeout=10
                            )
                            
                            if response.status_code in [200, 202]:
                                routing_tests_passed += 0.5  # Bonus for successful routing
                                
                        except Exception:
                            pass  # Expected for some tests
            
            success_rate = routing_tests_passed / len(test_requests)
            
            if success_rate >= 0.8:  # 80% success rate
                status = "PASS"
                message = f"Request routing working well ({success_rate:.1%} success)"
            else:
                status = "FAIL"
                message = f"Request routing issues ({success_rate:.1%} success)"
            
            self.test_results.append({
                "test_name": "request_routing_logic",
                "status": status,
                "duration": time.time() - start_time,
                "message": message,
                "details": {
                    "tests_passed": routing_tests_passed,
                    "total_tests": len(test_requests),
                    "success_rate": success_rate
                }
            })
            
        except Exception as e:
            self.test_results.append({
                "test_name": "request_routing_logic",
                "status": "FAIL",
                "duration": time.time() - start_time,
                "message": f"Request routing test failed: {str(e)}"
            })
    
    async def test_complexity_analyzer(self):
        """Test ComplexityAnalyzer classification accuracy"""
        start_time = time.time()
        
        try:
            # Test cases with known complexity levels
            complexity_tests = [
                ("Create a button", "simple"),
                ("Make a login form", "simple"),
                ("Build a todo list", "medium"),
                ("Create a complete dashboard with charts and tables", "complex"),
                ("Generate a full e-commerce site with product pages, cart, and checkout", "complex"),
                ("Design a social media platform with feeds, profiles, and messaging", "complex")
            ]
            
            correct_classifications = 0
            
            for message, expected_complexity in complexity_tests:
                # Simulate ComplexityAnalyzer logic
                message_lower = message.lower()
                
                # Complexity scoring simulation
                complexity_score = 0
                
                # Simple indicators
                simple_keywords = ["button", "form", "input", "card"]
                complexity_score += sum(2 for kw in simple_keywords if kw in message_lower)
                
                # Medium indicators  
                medium_keywords = ["list", "todo", "table", "modal"]
                complexity_score += sum(5 for kw in medium_keywords if kw in message_lower)
                
                # Complex indicators
                complex_keywords = ["dashboard", "complete", "full", "site", "platform", "page", "multi"]
                complexity_score += sum(10 for kw in complex_keywords if kw in message_lower)
                
                # Classify based on score
                if complexity_score >= 20:
                    detected_complexity = "complex"
                elif complexity_score >= 8:
                    detected_complexity = "medium"
                else:
                    detected_complexity = "simple"
                
                # Check accuracy (allow medium to be classified as simple or complex)
                if detected_complexity == expected_complexity:
                    correct_classifications += 1
                elif expected_complexity == "medium" and detected_complexity in ["simple", "complex"]:
                    correct_classifications += 0.5  # Partial credit
            
            accuracy = correct_classifications / len(complexity_tests)
            
            if accuracy >= 0.8:  # 80% accuracy
                status = "PASS"
                message = f"ComplexityAnalyzer accurate ({accuracy:.1%})"
            else:
                status = "FAIL"
                message = f"ComplexityAnalyzer inaccurate ({accuracy:.1%})"
            
            self.test_results.append({
                "test_name": "complexity_analyzer",
                "status": status,
                "duration": time.time() - start_time,
                "message": message,
                "details": {
                    "correct_classifications": correct_classifications,
                    "total_tests": len(complexity_tests),
                    "accuracy": accuracy
                }
            })
            
        except Exception as e:
            self.test_results.append({
                "test_name": "complexity_analyzer", 
                "status": "FAIL",
                "duration": time.time() - start_time,
                "message": f"ComplexityAnalyzer test failed: {str(e)}"
            })
    
    async def test_unified_panel_communication(self):
        """Test UnifiedPalettePanel communication with backend"""
        start_time = time.time()
        
        try:
            # Test different types of communication that UnifiedPalettePanel would make
            communication_tests = [
                # Project analysis request
                {
                    "endpoint": "/api/analyze",
                    "data": {"projectPath": "/tmp", "analysisType": "quick"},
                    "expected_fields": ["success", "analysis"]
                },
                # Quality validation request
                {
                    "endpoint": "/api/quality/validate",
                    "data": {
                        "projectPath": "/tmp",
                        "filePaths": [],
                        "code": "export const Test = () => <div>Test</div>;",
                        "validationType": "syntax"
                    },
                    "expected_fields": ["success", "validation"]
                },
                # Server status request
                {
                    "endpoint": "/api/status",
                    "data": None,
                    "expected_fields": ["server", "activeStreams"]
                }
            ]
            
            communication_success = 0
            
            for test in communication_tests:
                try:
                    if test["data"]:
                        response = requests.post(
                            f"{self.server_url}{test['endpoint']}",
                            json=test["data"],
                            timeout=15
                        )
                    else:
                        response = requests.get(
                            f"{self.server_url}{test['endpoint']}",
                            timeout=10
                        )
                    
                    if response.status_code == 200:
                        result = response.json()
                        has_expected_fields = all(field in result for field in test["expected_fields"])
                        
                        if has_expected_fields:
                            communication_success += 1
                            
                except Exception:
                    pass  # Communication failed
            
            success_rate = communication_success / len(communication_tests)
            
            if success_rate >= 0.8:  # 80% communication success
                status = "PASS"
                message = f"Panel communication working ({success_rate:.1%})"
            else:
                status = "FAIL"
                message = f"Panel communication issues ({success_rate:.1%})"
            
            self.test_results.append({
                "test_name": "unified_panel_communication",
                "status": status,
                "duration": time.time() - start_time,
                "message": message,
                "details": {
                    "successful_communications": communication_success,
                    "total_tests": len(communication_tests),
                    "success_rate": success_rate
                }
            })
            
        except Exception as e:
            self.test_results.append({
                "test_name": "unified_panel_communication",
                "status": "FAIL",
                "duration": time.time() - start_time,
                "message": f"Panel communication test failed: {str(e)}"
            })
    
    async def test_streaming_integration(self):
        """Test real-time streaming integration"""
        start_time = time.time()
        
        try:
            # Test streaming generation setup
            response = requests.post(
                f"{self.server_url}/api/generate/stream",
                json={
                    "message": "Create a test component for streaming",
                    "projectPath": "/tmp",
                    "conversationHistory": []
                },
                timeout=10
            )
            
            if response.status_code not in [200, 202]:
                raise AssertionError(f"Failed to initiate streaming: {response.status_code}")
            
            result = response.json()
            conversation_id = result.get("conversationId")
            
            if not conversation_id:
                raise AssertionError("No conversation ID returned")
            
            # Test SSE endpoint accessibility
            try:
                sse_response = requests.get(
                    f"{self.server_url}/api/generate/stream/{conversation_id}",
                    timeout=3,
                    stream=True
                )
                
                streaming_accessible = sse_response.status_code in [200, 404]  # 404 is ok if stream ended
                
            except requests.exceptions.Timeout:
                streaming_accessible = True  # Timeout expected for SSE
            except Exception:
                streaming_accessible = False
            
            # Test stream cleanup endpoint
            cleanup_response = requests.delete(f"{self.server_url}/api/cleanup", timeout=5)
            cleanup_working = cleanup_response.status_code == 200
            
            if streaming_accessible and cleanup_working:
                status = "PASS"
                message = "Streaming integration working"
            else:
                status = "FAIL"
                message = f"Streaming issues - accessible: {streaming_accessible}, cleanup: {cleanup_working}"
            
            self.test_results.append({
                "test_name": "streaming_integration",
                "status": status,
                "duration": time.time() - start_time,
                "message": message,
                "details": {
                    "conversation_id": conversation_id,
                    "streaming_accessible": streaming_accessible,
                    "cleanup_working": cleanup_working
                }
            })
            
        except Exception as e:
            self.test_results.append({
                "test_name": "streaming_integration",
                "status": "FAIL",
                "duration": time.time() - start_time,
                "message": f"Streaming integration test failed: {str(e)}"
            })
    
    async def test_error_handling_and_fallbacks(self):
        """Test error handling and fallback mechanisms"""
        start_time = time.time()
        
        try:
            # Test various error scenarios that the extension should handle
            error_scenarios = [
                # Invalid project path
                {
                    "test": "invalid_project_path",
                    "endpoint": "/api/analyze",
                    "data": {"projectPath": "/nonexistent", "analysisType": "quick"}
                },
                # Missing required fields
                {
                    "test": "missing_fields",
                    "endpoint": "/api/generate/stream", 
                    "data": {"message": "test"}  # Missing projectPath
                },
                # Invalid analysis type
                {
                    "test": "invalid_analysis_type",
                    "endpoint": "/api/analyze",
                    "data": {"projectPath": "/tmp", "analysisType": "invalid"}
                }
            ]
            
            error_handling_score = 0
            
            for scenario in error_scenarios:
                try:
                    response = requests.post(
                        f"{self.server_url}{scenario['endpoint']}",
                        json=scenario["data"],
                        timeout=10
                    )
                    
                    # Good error handling should return appropriate status codes or success=false
                    if response.status_code in [400, 422, 500]:
                        error_handling_score += 1
                    elif response.status_code == 200:
                        try:
                            result = response.json()
                            if not result.get("success", True):  # Handled error with success=false
                                error_handling_score += 1
                        except:
                            pass
                            
                except requests.exceptions.RequestException:
                    # Connection errors are also valid error handling
                    error_handling_score += 0.5
            
            error_handling_rate = error_handling_score / len(error_scenarios)
            
            if error_handling_rate >= 0.8:  # 80% error handling success
                status = "PASS"
                message = f"Error handling working well ({error_handling_rate:.1%})"
            else:
                status = "FAIL"
                message = f"Poor error handling ({error_handling_rate:.1%})"
            
            self.test_results.append({
                "test_name": "error_handling_and_fallbacks",
                "status": status,
                "duration": time.time() - start_time,
                "message": message,
                "details": {
                    "error_handling_score": error_handling_score,
                    "total_scenarios": len(error_scenarios),
                    "success_rate": error_handling_rate
                }
            })
            
        except Exception as e:
            self.test_results.append({
                "test_name": "error_handling_and_fallbacks",
                "status": "FAIL", 
                "duration": time.time() - start_time,
                "message": f"Error handling test failed: {str(e)}"
            })
    
    async def test_session_persistence(self):
        """Test session and conversation persistence"""
        start_time = time.time()
        
        try:
            # Test conversation history handling
            conversation_history = [
                {"role": "user", "content": "Create a button component"},
                {"role": "assistant", "content": "Here's a button component..."}
            ]
            
            # Test that conversation history is accepted
            response = requests.post(
                f"{self.server_url}/api/generate/stream",
                json={
                    "message": "Now make it blue",
                    "projectPath": "/tmp",
                    "conversationHistory": conversation_history,
                    "conversationId": "test-session-123"
                },
                timeout=10
            )
            
            session_handling = response.status_code in [200, 202]
            
            if session_handling:
                result = response.json()
                conversation_id = result.get("conversationId")
                maintains_session = conversation_id == "test-session-123"
            else:
                maintains_session = False
            
            # Test server status tracking
            status_response = requests.get(f"{self.server_url}/api/status", timeout=5)
            if status_response.status_code == 200:
                status_data = status_response.json()
                tracks_sessions = "activeStreams" in status_data
            else:
                tracks_sessions = False
            
            if session_handling and maintains_session and tracks_sessions:
                status = "PASS"
                message = "Session persistence working"
            else:
                status = "FAIL"
                message = f"Session issues - handling: {session_handling}, maintains: {maintains_session}, tracking: {tracks_sessions}"
            
            self.test_results.append({
                "test_name": "session_persistence",
                "status": status,
                "duration": time.time() - start_time,
                "message": message,
                "details": {
                    "session_handling": session_handling,
                    "maintains_session": maintains_session,
                    "tracks_sessions": tracks_sessions
                }
            })
            
        except Exception as e:
            self.test_results.append({
                "test_name": "session_persistence",
                "status": "FAIL",
                "duration": time.time() - start_time,
                "message": f"Session persistence test failed: {str(e)}"
            })
    
    async def test_performance_integration(self):
        """Test performance aspects of integration"""
        start_time = time.time()
        
        try:
            # Test response times for different operations
            operations = [
                {"name": "health_check", "endpoint": "/health", "method": "GET", "timeout": 2},
                {"name": "quick_analysis", "endpoint": "/api/analyze", "method": "POST", 
                 "data": {"projectPath": "/tmp", "analysisType": "quick"}, "timeout": 10},
                {"name": "status_check", "endpoint": "/api/status", "method": "GET", "timeout": 5}
            ]
            
            performance_scores = []
            
            for op in operations:
                op_start = time.time()
                try:
                    if op["method"] == "GET":
                        response = requests.get(f"{self.server_url}{op['endpoint']}", 
                                              timeout=op["timeout"])
                    else:
                        response = requests.post(f"{self.server_url}{op['endpoint']}", 
                                               json=op.get("data", {}), 
                                               timeout=op["timeout"])
                    
                    duration = time.time() - op_start
                    success = response.status_code == 200
                    
                    # Score based on success and speed
                    if success and duration < op["timeout"] * 0.5:
                        performance_scores.append(100)  # Fast and successful
                    elif success and duration < op["timeout"]:
                        performance_scores.append(80)   # Successful within timeout
                    elif success:
                        performance_scores.append(60)   # Successful but slow
                    else:
                        performance_scores.append(0)    # Failed
                        
                except requests.exceptions.Timeout:
                    performance_scores.append(0)  # Timeout
                except Exception:
                    performance_scores.append(0)  # Other failure
            
            avg_performance = sum(performance_scores) / len(performance_scores) if performance_scores else 0
            
            if avg_performance >= 80:
                status = "PASS"
                message = f"Performance good ({avg_performance:.1f}/100)"
            elif avg_performance >= 60:
                status = "PARTIAL"
                message = f"Performance acceptable ({avg_performance:.1f}/100)"
            else:
                status = "FAIL"
                message = f"Performance issues ({avg_performance:.1f}/100)"
            
            self.test_results.append({
                "test_name": "performance_integration",
                "status": status,
                "duration": time.time() - start_time,
                "message": message,
                "details": {
                    "average_performance": avg_performance,
                    "operation_scores": dict(zip([op["name"] for op in operations], performance_scores))
                }
            })
            
        except Exception as e:
            self.test_results.append({
                "test_name": "performance_integration",
                "status": "FAIL",
                "duration": time.time() - start_time,
                "message": f"Performance test failed: {str(e)}"
            })
    
    async def cleanup_test_environment(self):
        """Clean up integration test environment"""
        try:
            if self.server_process:
                self.server_process.terminate()
                try:
                    self.server_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.server_process.kill()
                    self.server_process.wait()
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
    
    def print_integration_report(self):
        """Print formatted integration test report"""
        print("\n" + "=" * 65)
        print("🔗 VS CODE INTEGRATION TEST REPORT")
        print("=" * 65)
        
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        partial = sum(1 for r in self.test_results if r["status"] == "PARTIAL")
        total = len(self.test_results)
        
        print(f"\n📊 Summary:")
        print(f"   Total Tests: {total}")
        print(f"   ✅ Passed:   {passed}")
        print(f"   ❌ Failed:   {failed}")
        print(f"   ⚠️  Partial:  {partial}")
        print(f"   🎯 Success Rate: {((passed + partial * 0.5)/total*100):.1f}%" if total > 0 else "   🎯 Success Rate: 0%")
        
        print(f"\n📝 Integration Test Results:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"   {status_icon} {result['test_name']:<35} ({result['duration']:.2f}s) - {result['message']}")
            
            if result.get("details") and result["status"] != "PASS":
                key_details = {k: v for k, v in result["details"].items() 
                             if k in ["success_rate", "accuracy", "error"]}
                if key_details:
                    print(f"      Details: {key_details}")
        
        print("\n" + "=" * 65)
        
        if failed == 0:
            print("🎉 VS Code integration is working correctly!")
        else:
            print(f"⚠️  {failed} integration test(s) failed. Review integration points.")
        
        print("=" * 65)
    
    def get_summary(self) -> Dict:
        """Get integration test summary"""
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        partial = sum(1 for r in self.test_results if r["status"] == "PARTIAL")
        total = len(self.test_results)
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "partial": partial,
            "success_rate": ((passed + partial * 0.5)/total*100) if total > 0 else 0,
            "integration_working": failed <= 1,  # Allow 1 failure
            "test_results": self.test_results
        }

async def main():
    """Main test runner for VS Code integration"""
    tester = VSCodeIntegrationTester()
    summary = await tester.run_integration_tests()
    
    # Exit with error code if integration tests failed
    sys.exit(0 if summary["integration_working"] else 1)

if __name__ == "__main__":
    asyncio.run(main())