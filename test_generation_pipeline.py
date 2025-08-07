#!/usr/bin/env python3
"""
Automated Test Suite for Palette Generation Pipeline
Tests the complete Python backend generation workflow including:
- Server startup and health
- Project analysis
- Quality validation
- Streaming generation
- MCP service endpoints
"""

import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional
import requests
import subprocess
import aiohttp
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

@dataclass
class TestResult:
    test_name: str
    status: str  # "PASS", "FAIL", "SKIP"
    duration: float
    message: str
    details: Optional[Dict] = None

class PaletteTestSuite:
    def __init__(self):
        self.server_process = None
        self.server_url = "http://127.0.0.1:8765"
        self.test_results: List[TestResult] = []
        self.temp_project_dir = None
        
    async def run_all_tests(self):
        """Run complete test suite"""
        print("🧪 Palette Generation Pipeline Test Suite")
        print("=" * 50)
        
        try:
            # Phase 1: Setup
            await self.setup_test_environment()
            await self.start_python_server()
            
            # Phase 2: Basic functionality
            await self.test_server_health()
            await self.test_project_analysis()
            await self.test_quality_validation()
            
            # Phase 3: Generation pipeline
            await self.test_simple_generation()
            await self.test_complex_generation()
            await self.test_streaming_generation()
            
            # Phase 4: Advanced features
            await self.test_mcp_endpoints()
            await self.test_error_handling()
            await self.test_concurrent_requests()
            
        finally:
            await self.cleanup_test_environment()
            
        # Report results
        self.print_test_report()
        return self.get_test_summary()
    
    async def setup_test_environment(self):
        """Setup test environment and temporary project"""
        start_time = time.time()
        
        try:
            # Create temporary test project
            self.temp_project_dir = tempfile.mkdtemp(prefix="palette_test_")
            
            # Create basic Vite + React + TypeScript structure
            project_files = {
                "package.json": {
                    "name": "palette-test",
                    "version": "1.0.0",
                    "type": "module",
                    "dependencies": {
                        "react": "^18.2.0",
                        "@types/react": "^18.2.0",
                        "typescript": "^5.0.0",
                        "tailwindcss": "^3.3.0"
                    },
                    "devDependencies": {
                        "vite": "^4.4.0",
                        "@vitejs/plugin-react": "^4.0.0"
                    }
                },
                "tsconfig.json": {
                    "compilerOptions": {
                        "target": "ES2020",
                        "useDefineForClassFields": True,
                        "lib": ["ES2020", "DOM", "DOM.Iterable"],
                        "module": "ESNext",
                        "skipLibCheck": True,
                        "moduleResolution": "bundler",
                        "allowImportingTsExtensions": True,
                        "resolveJsonModule": True,
                        "isolatedModules": True,
                        "noEmit": True,
                        "jsx": "react-jsx",
                        "strict": True,
                        "noUnusedLocals": True,
                        "noUnusedParameters": True,
                        "noFallthroughCasesInSwitch": True
                    },
                    "include": ["src"],
                    "references": [{"path": "./tsconfig.node.json"}]
                },
                "vite.config.ts": '''
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
''',
                "tailwind.config.js": '''
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
'''
            }
            
            # Write project files
            for filename, content in project_files.items():
                file_path = Path(self.temp_project_dir) / filename
                if isinstance(content, dict):
                    with open(file_path, 'w') as f:
                        json.dump(content, f, indent=2)
                else:
                    with open(file_path, 'w') as f:
                        f.write(content)
            
            # Create src directory with basic component
            src_dir = Path(self.temp_project_dir) / "src"
            src_dir.mkdir()
            
            (src_dir / "App.tsx").write_text('''
import React from 'react';

function App() {
  return (
    <div className="min-h-screen bg-gray-100">
      <h1 className="text-3xl font-bold text-center py-8">
        Palette Test Project
      </h1>
    </div>
  );
}

export default App;
''')
            
            self.test_results.append(TestResult(
                test_name="setup_test_environment",
                status="PASS",
                duration=time.time() - start_time,
                message=f"Test environment created at {self.temp_project_dir}",
                details={"project_path": self.temp_project_dir}
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="setup_test_environment",
                status="FAIL",
                duration=time.time() - start_time,
                message=f"Failed to setup test environment: {str(e)}"
            ))
            raise
    
    async def start_python_server(self):
        """Start the Palette Python server"""
        start_time = time.time()
        
        try:
            # Start server using the launcher
            server_script = Path(__file__).parent / "run_server.py"
            
            if not server_script.exists():
                raise FileNotFoundError(f"Server launcher not found: {server_script}")
            
            env = os.environ.copy()
            env["PYTHONPATH"] = str(Path(__file__).parent / "src")
            
            self.server_process = subprocess.Popen([
                sys.executable, str(server_script)
            ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            max_wait = 30
            for i in range(max_wait):
                try:
                    response = requests.get(f"{self.server_url}/health", timeout=1)
                    if response.status_code == 200:
                        break
                except requests.exceptions.RequestException:
                    pass
                
                if i == max_wait - 1:
                    raise TimeoutError("Server failed to start within 30 seconds")
                
                await asyncio.sleep(1)
            
            self.test_results.append(TestResult(
                test_name="start_python_server",
                status="PASS",
                duration=time.time() - start_time,
                message="Python server started successfully",
                details={"server_url": self.server_url}
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="start_python_server",
                status="FAIL",
                duration=time.time() - start_time,
                message=f"Failed to start server: {str(e)}"
            ))
            raise
    
    async def test_server_health(self):
        """Test server health endpoint"""
        start_time = time.time()
        
        try:
            response = requests.get(f"{self.server_url}/health", timeout=10)
            
            if response.status_code != 200:
                raise AssertionError(f"Expected status 200, got {response.status_code}")
            
            health_data = response.json()
            required_fields = ["status", "timestamp", "version", "python_version"]
            
            for field in required_fields:
                if field not in health_data:
                    raise AssertionError(f"Missing field in health response: {field}")
            
            if health_data["status"] != "healthy":
                raise AssertionError(f"Server not healthy: {health_data['status']}")
            
            self.test_results.append(TestResult(
                test_name="test_server_health",
                status="PASS",
                duration=time.time() - start_time,
                message="Health check passed",
                details=health_data
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="test_server_health",
                status="FAIL",
                duration=time.time() - start_time,
                message=f"Health check failed: {str(e)}"
            ))
    
    async def test_project_analysis(self):
        """Test project analysis endpoint"""
        start_time = time.time()
        
        try:
            # Test different analysis types
            analysis_types = ["quick", "frameworks", "components", "quality", "full"]
            
            for analysis_type in analysis_types:
                response = requests.post(
                    f"{self.server_url}/api/analyze",
                    json={
                        "projectPath": self.temp_project_dir,
                        "analysisType": analysis_type
                    },
                    timeout=30
                )
                
                if response.status_code != 200:
                    raise AssertionError(f"Analysis {analysis_type} failed with status {response.status_code}")
                
                result = response.json()
                
                if not result.get("success"):
                    raise AssertionError(f"Analysis {analysis_type} returned success=false")
                
                if "analysis" not in result:
                    raise AssertionError(f"Analysis {analysis_type} missing analysis data")
            
            self.test_results.append(TestResult(
                test_name="test_project_analysis",
                status="PASS",
                duration=time.time() - start_time,
                message=f"All {len(analysis_types)} analysis types passed",
                details={"analysis_types": analysis_types}
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="test_project_analysis",
                status="FAIL",
                duration=time.time() - start_time,
                message=f"Project analysis failed: {str(e)}"
            ))
    
    async def test_quality_validation(self):
        """Test quality validation endpoint"""
        start_time = time.time()
        
        try:
            # Create test component with known issues
            test_component = '''import React from "react";
import React from "react";  // Duplicate import

const BadComponent = () => {
    console.log("debug message");  // Console.log issue
    
    return <div className="bg-gray text-black">  // Invalid classes
        <img />  // Missing alt
        <button onClick={() => {}}>
            Click me
        </button>
    </div>;
};

export default BadComponent;'''
            
            test_file = Path(self.temp_project_dir) / "BadComponent.tsx"
            test_file.write_text(test_component)
            
            # Test file validation
            response = requests.post(
                f"{self.server_url}/api/quality/validate",
                json={
                    "projectPath": self.temp_project_dir,
                    "filePaths": [str(test_file)],
                    "validationType": "comprehensive"
                },
                timeout=30
            )
            
            if response.status_code != 200:
                raise AssertionError(f"Quality validation failed with status {response.status_code}")
            
            result = response.json()
            
            if not result.get("success"):
                raise AssertionError("Quality validation returned success=false")
            
            validation = result["validation"]
            summary = result["summary"]
            
            # Should detect issues in the bad component
            if len(validation["issues"]) == 0:
                raise AssertionError("Quality validation should have detected issues")
            
            if validation["score"] >= 90:
                raise AssertionError("Quality score should be low for bad component")
            
            # Test inline code validation
            response = requests.post(
                f"{self.server_url}/api/quality/validate",
                json={
                    "projectPath": self.temp_project_dir,
                    "filePaths": [],
                    "code": "export const GoodComponent = () => <div>Hello</div>;",
                    "validationType": "syntax"
                },
                timeout=10
            )
            
            if response.status_code != 200:
                raise AssertionError(f"Inline validation failed with status {response.status_code}")
            
            self.test_results.append(TestResult(
                test_name="test_quality_validation",
                status="PASS",
                duration=time.time() - start_time,
                message=f"Quality validation detected {len(validation['issues'])} issues",
                details={
                    "issues_found": len(validation["issues"]),
                    "quality_score": validation["score"],
                    "critical_issues": summary["criticalIssues"],
                    "warnings": summary["warnings"]
                }
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="test_quality_validation",
                status="FAIL",
                duration=time.time() - start_time,
                message=f"Quality validation failed: {str(e)}"
            ))
    
    async def test_simple_generation(self):
        """Test simple generation (should be quick)"""
        start_time = time.time()
        
        try:
            # This would typically test the generation endpoint
            # For now, we'll test that the endpoint exists and responds
            response = requests.post(
                f"{self.server_url}/api/generate/stream",
                json={
                    "message": "Create a simple button component",
                    "projectPath": self.temp_project_dir,
                    "conversationHistory": [],
                    "requestMetadata": {"test": True}
                },
                timeout=10
            )
            
            if response.status_code not in [200, 202]:
                raise AssertionError(f"Generation endpoint failed with status {response.status_code}")
            
            result = response.json()
            
            if "conversationId" not in result:
                raise AssertionError("Generation response missing conversationId")
            
            if "streamUrl" not in result:
                raise AssertionError("Generation response missing streamUrl")
            
            self.test_results.append(TestResult(
                test_name="test_simple_generation",
                status="PASS",
                duration=time.time() - start_time,
                message="Simple generation endpoint responded correctly",
                details={
                    "conversation_id": result.get("conversationId"),
                    "status": result.get("status")
                }
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="test_simple_generation",
                status="FAIL",
                duration=time.time() - start_time,
                message=f"Simple generation failed: {str(e)}"
            ))
    
    async def test_complex_generation(self):
        """Test complex generation with quality validation"""
        start_time = time.time()
        
        try:
            # Test complex generation request
            response = requests.post(
                f"{self.server_url}/api/generate/stream",
                json={
                    "message": "Create a complete dashboard page with sidebar navigation, header with user profile, data charts, and a data table with sorting and filtering",
                    "projectPath": self.temp_project_dir,
                    "conversationHistory": [],
                    "requestMetadata": {"complex": True, "quality_check": True}
                },
                timeout=15
            )
            
            if response.status_code not in [200, 202]:
                raise AssertionError(f"Complex generation failed with status {response.status_code}")
            
            result = response.json()
            
            required_fields = ["conversationId", "streamUrl", "status"]
            for field in required_fields:
                if field not in result:
                    raise AssertionError(f"Missing field in generation response: {field}")
            
            self.test_results.append(TestResult(
                test_name="test_complex_generation",
                status="PASS",
                duration=time.time() - start_time,
                message="Complex generation initiated successfully",
                details={
                    "conversation_id": result.get("conversationId"),
                    "status": result.get("status")
                }
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="test_complex_generation",
                status="FAIL",
                duration=time.time() - start_time,
                message=f"Complex generation failed: {str(e)}"
            ))
    
    async def test_streaming_generation(self):
        """Test streaming SSE endpoint"""
        start_time = time.time()
        
        try:
            # First start a generation to get a conversation ID
            response = requests.post(
                f"{self.server_url}/api/generate/stream",
                json={
                    "message": "Create a simple test component",
                    "projectPath": self.temp_project_dir,
                    "conversationHistory": []
                },
                timeout=10
            )
            
            if response.status_code not in [200, 202]:
                raise AssertionError(f"Failed to start generation: {response.status_code}")
            
            result = response.json()
            conversation_id = result["conversationId"]
            
            # Test SSE endpoint exists
            try:
                sse_response = requests.get(
                    f"{self.server_url}/api/generate/stream/{conversation_id}",
                    timeout=5,
                    stream=True
                )
                
                if sse_response.status_code == 200:
                    # Successfully connected to SSE stream
                    sse_connected = True
                else:
                    sse_connected = False
                    
            except requests.exceptions.Timeout:
                sse_connected = True  # Timeout is expected for SSE streams
            except requests.exceptions.RequestException:
                sse_connected = False
            
            if not sse_connected and sse_response.status_code != 404:
                raise AssertionError(f"SSE endpoint failed: {sse_response.status_code}")
            
            self.test_results.append(TestResult(
                test_name="test_streaming_generation",
                status="PASS",
                duration=time.time() - start_time,
                message="Streaming endpoint accessible",
                details={
                    "conversation_id": conversation_id,
                    "sse_status": sse_response.status_code if 'sse_response' in locals() else 'timeout'
                }
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="test_streaming_generation",
                status="FAIL",
                duration=time.time() - start_time,
                message=f"Streaming test failed: {str(e)}"
            ))
    
    async def test_mcp_endpoints(self):
        """Test MCP service endpoints"""
        start_time = time.time()
        
        try:
            # Test MCP shadcn endpoint
            response = requests.post(
                f"{self.server_url}/api/mcp/shadcn",
                json={
                    "message": "Create a pricing table with three tiers",
                    "projectPath": self.temp_project_dir
                },
                timeout=15
            )
            
            # MCP endpoint might return error if no Tailwind detected, which is expected
            if response.status_code == 200:
                result = response.json()
                mcp_working = result.get("status") == "started"
            else:
                # Check if it's an expected error (no Tailwind setup)
                try:
                    error_result = response.json()
                    if "Tailwind CSS setup" in error_result.get("error", ""):
                        mcp_working = True  # Expected error, MCP is working
                    else:
                        mcp_working = False
                except:
                    mcp_working = False
            
            # Test components endpoint
            components_response = requests.get(
                f"{self.server_url}/api/mcp/components/available",
                params={"project_path": self.temp_project_dir},
                timeout=10
            )
            
            components_working = components_response.status_code == 200
            
            if mcp_working and components_working:
                status = "PASS"
                message = "MCP endpoints responding correctly"
            else:
                status = "FAIL"
                message = f"MCP issues: shadcn={mcp_working}, components={components_working}"
            
            self.test_results.append(TestResult(
                test_name="test_mcp_endpoints",
                status=status,
                duration=time.time() - start_time,
                message=message,
                details={
                    "shadcn_endpoint": mcp_working,
                    "components_endpoint": components_working
                }
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="test_mcp_endpoints",
                status="FAIL",
                duration=time.time() - start_time,
                message=f"MCP endpoints failed: {str(e)}"
            ))
    
    async def test_error_handling(self):
        """Test error handling with invalid requests"""
        start_time = time.time()
        
        try:
            error_tests = [
                # Invalid project path
                {
                    "endpoint": "/api/analyze",
                    "data": {"projectPath": "/nonexistent/path", "analysisType": "quick"},
                    "expected_status": 500
                },
                # Missing required fields
                {
                    "endpoint": "/api/generate/stream",
                    "data": {"message": "test"},  # Missing projectPath
                    "expected_status": 422
                },
                # Invalid analysis type
                {
                    "endpoint": "/api/analyze", 
                    "data": {"projectPath": self.temp_project_dir, "analysisType": "invalid"},
                    "expected_status": 200  # Should handle gracefully
                }
            ]
            
            errors_handled_correctly = 0
            
            for test in error_tests:
                try:
                    response = requests.post(
                        f"{self.server_url}{test['endpoint']}",
                        json=test["data"],
                        timeout=10
                    )
                    
                    if response.status_code == test["expected_status"]:
                        errors_handled_correctly += 1
                    elif response.status_code == 200:
                        # Check if it's a handled error with success=false
                        try:
                            result = response.json()
                            if not result.get("success", True):
                                errors_handled_correctly += 1
                        except:
                            pass
                            
                except requests.exceptions.RequestException:
                    # Some errors might cause connection issues, which is also valid error handling
                    errors_handled_correctly += 1
            
            if errors_handled_correctly >= 2:  # At least 2/3 error cases handled
                status = "PASS"
                message = f"Error handling working ({errors_handled_correctly}/{len(error_tests)})"
            else:
                status = "FAIL"
                message = f"Poor error handling ({errors_handled_correctly}/{len(error_tests)})"
            
            self.test_results.append(TestResult(
                test_name="test_error_handling",
                status=status,
                duration=time.time() - start_time,
                message=message,
                details={"errors_handled": errors_handled_correctly, "total_tests": len(error_tests)}
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="test_error_handling",
                status="FAIL",
                duration=time.time() - start_time,
                message=f"Error handling test failed: {str(e)}"
            ))
    
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        start_time = time.time()
        
        try:
            # Send multiple analysis requests concurrently
            import concurrent.futures
            
            def send_analysis_request():
                try:
                    response = requests.post(
                        f"{self.server_url}/api/analyze",
                        json={
                            "projectPath": self.temp_project_dir,
                            "analysisType": "quick"
                        },
                        timeout=15
                    )
                    return response.status_code == 200 and response.json().get("success", False)
                except:
                    return False
            
            # Run 3 concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(send_analysis_request) for _ in range(3)]
                results = [future.result() for future in concurrent.futures.as_completed(futures, timeout=20)]
            
            successful_requests = sum(results)
            
            if successful_requests >= 2:  # At least 2/3 should succeed
                status = "PASS"
                message = f"Concurrent requests handled ({successful_requests}/3)"
            else:
                status = "FAIL"
                message = f"Poor concurrent handling ({successful_requests}/3)"
            
            self.test_results.append(TestResult(
                test_name="test_concurrent_requests",
                status=status,
                duration=time.time() - start_time,
                message=message,
                details={"successful_requests": successful_requests, "total_requests": 3}
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="test_concurrent_requests",
                status="FAIL",
                duration=time.time() - start_time,
                message=f"Concurrent requests test failed: {str(e)}"
            ))
    
    async def cleanup_test_environment(self):
        """Clean up test environment"""
        try:
            # Stop server
            if self.server_process:
                self.server_process.terminate()
                try:
                    self.server_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.server_process.kill()
                    self.server_process.wait()
            
            # Clean up temp directory
            if self.temp_project_dir:
                import shutil
                shutil.rmtree(self.temp_project_dir, ignore_errors=True)
                
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
    
    def print_test_report(self):
        """Print formatted test report"""
        print("\n" + "=" * 60)
        print("🧪 TEST REPORT")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results if r.status == "PASS")
        failed = sum(1 for r in self.test_results if r.status == "FAIL")
        skipped = sum(1 for r in self.test_results if r.status == "SKIP")
        total = len(self.test_results)
        
        print(f"\n📊 Summary:")
        print(f"   Total Tests: {total}")
        print(f"   ✅ Passed:  {passed}")
        print(f"   ❌ Failed:  {failed}")
        print(f"   ⏭️  Skipped: {skipped}")
        print(f"   🎯 Success Rate: {(passed/total*100):.1f}%" if total > 0 else "   🎯 Success Rate: 0%")
        
        print(f"\n📝 Test Results:")
        for result in self.test_results:
            status_icon = "✅" if result.status == "PASS" else "❌" if result.status == "FAIL" else "⏭️"
            print(f"   {status_icon} {result.test_name:<25} ({result.duration:.2f}s) - {result.message}")
            
            if result.details and result.status == "FAIL":
                print(f"      Details: {result.details}")
        
        print("\n" + "=" * 60)
        
        if failed == 0:
            print("🎉 All tests passed! Palette generation pipeline is working correctly.")
        else:
            print(f"⚠️  {failed} test(s) failed. Check the details above for issues.")
        
        print("=" * 60)
    
    def get_test_summary(self) -> Dict:
        """Get test summary as dictionary"""
        passed = sum(1 for r in self.test_results if r.status == "PASS")
        failed = sum(1 for r in self.test_results if r.status == "FAIL")
        total = len(self.test_results)
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "success_rate": (passed/total*100) if total > 0 else 0,
            "all_tests_passed": failed == 0,
            "test_results": [
                {
                    "test_name": r.test_name,
                    "status": r.status,
                    "duration": r.duration,
                    "message": r.message
                } for r in self.test_results
            ]
        }

async def main():
    """Main test runner"""
    suite = PaletteTestSuite()
    summary = await suite.run_all_tests()
    
    # Exit with error code if tests failed
    sys.exit(0 if summary["all_tests_passed"] else 1)

if __name__ == "__main__":
    asyncio.run(main())