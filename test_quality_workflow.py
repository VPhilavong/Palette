#!/usr/bin/env python3
"""
Quality Validation Workflow Test Suite
Tests the comprehensive quality validation system including:
- ComponentValidator functionality
- Auto-fix engine capabilities
- Quality scoring accuracy
- Error detection and classification
- Performance benchmarks
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

@dataclass
class QualityTestCase:
    name: str
    code: str
    expected_issues: int
    expected_score_range: Tuple[int, int]  # (min, max)
    expected_issue_types: List[str]
    description: str

class QualityWorkflowTester:
    def __init__(self):
        self.test_results = []
        self.temp_dir = None
        
    def run_all_quality_tests(self):
        """Run comprehensive quality validation tests"""
        print("🔍 Quality Validation Workflow Test Suite")
        print("=" * 50)
        
        try:
            self.setup_test_environment()
            
            # Test cases covering different quality scenarios
            test_cases = self.get_test_cases()
            
            for test_case in test_cases:
                self.run_quality_test_case(test_case)
            
            # Additional specialized tests
            self.test_project_quality_analysis()
            self.test_auto_fix_engine()
            self.test_quality_performance()
            self.test_edge_cases()
            
        finally:
            self.cleanup_test_environment()
            
        self.print_quality_report()
        return self.get_summary()
    
    def setup_test_environment(self):
        """Setup temporary test environment"""
        self.temp_dir = tempfile.mkdtemp(prefix="palette_quality_test_")
        print(f"📂 Test environment: {self.temp_dir}")
    
    def get_test_cases(self) -> List[QualityTestCase]:
        """Define comprehensive test cases for quality validation"""
        return [
            QualityTestCase(
                name="perfect_component",
                code='''import React from 'react';

interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
  className?: string;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
  disabled = false,
  className = ''
}) => {
  const baseClasses = 'px-4 py-2 rounded-md font-medium transition-colors focus:outline-none focus:ring-2';
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500'
  };

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      aria-pressed={false}
    >
      {children}
    </button>
  );
};

export default Button;''',
                expected_issues=0,
                expected_score_range=(85, 100),
                expected_issue_types=[],
                description="High-quality component with proper TypeScript, accessibility, and styling"
            ),
            
            QualityTestCase(
                name="problematic_component",
                code='''import React from "react";
import React from "react";  // Duplicate import

const BadComponent = () => {
    console.log("debug message");  // Console.log
    console.log("another debug");
    
    // Invalid Tailwind classes and missing accessibility
    return <div className="bg-gray text-black invalid-class">
        <img src="test.jpg" />  {/* Missing alt */}
        <img />  {/* Missing src and alt */}
        <button onClick={() => console.log("click")}>  {/* Console in handler */}
            Click me
        </button>
        <input type="text" />  {/* Missing label */}
    </div>;
};

export default BadComponent;''',
                expected_issues=6,
                expected_score_range=(20, 50),
                expected_issue_types=["typescript", "eslint", "accessibility", "structure"],
                description="Component with multiple quality issues"
            ),
            
            QualityTestCase(
                name="typescript_errors",
                code='''import React from 'react';

// Missing interface definition
const ComponentWithoutTypes = ({ data, onClick }) => {
    // Using any type
    const processData = (input: any): any => {
        return input.map(item => item.value);
    };
    
    // Unused variables
    const unusedVar = "test";
    const anotherUnused = 123;
    
    return (
        <div>
            <button onClick={onClick}>
                {processData(data)}
            </button>
        </div>
    );
};

export default ComponentWithoutTypes;''',
                expected_issues=3,
                expected_score_range=(40, 70),
                expected_issue_types=["typescript"],
                description="TypeScript-related quality issues"
            ),
            
            QualityTestCase(
                name="accessibility_issues",
                code='''import React from 'react';

const InaccessibleForm = () => {
    return (
        <form>
            <input type="text" placeholder="Name" />  {/* No label */}
            <input type="email" />  {/* No label or placeholder */}
            
            <img src="avatar.jpg" />  {/* Missing alt */}
            <img src="logo.png" alt="" />  {/* Empty alt should be decorative */}
            
            <button>  {/* Missing type */}
                Submit
            </button>
            
            <div onClick={() => {}}>  {/* Non-interactive div with click */}
                Clickable div
            </div>
        </form>
    );
};

export default InaccessibleForm;''',
                expected_issues=4,
                expected_score_range=(30, 60),
                expected_issue_types=["accessibility"],
                description="Accessibility violations"
            ),
            
            QualityTestCase(
                name="performance_issues",
                code='''import React from 'react';

const PerformanceProblems = ({ items, onSelect }) => {
    // Inline object creation (should use useMemo)
    const expensiveCalculation = items.map(item => ({
        ...item,
        calculated: item.value * Math.random()  // Expensive calculation in render
    }));
    
    // Inline function creation (should use useCallback)
    return (
        <div>
            {expensiveCalculation.map(item => 
                <div key={item.id} onClick={() => onSelect(item)}>  {/* Inline function */}
                    {item.name}
                    {/* Date creation in render */}
                    <span>{new Date().toISOString()}</span>
                </div>
            )}
        </div>
    );
};

export default PerformanceProblems;''',
                expected_issues=2,
                expected_score_range=(50, 75),
                expected_issue_types=["performance"],
                description="Performance anti-patterns"
            ),
            
            QualityTestCase(
                name="modern_best_practices",
                code='''import React, { useState, useCallback, useMemo } from 'react';

interface Item {
  id: string;
  name: string;
  value: number;
}

interface Props {
  items: Item[];
  onSelect: (item: Item) => void;
  className?: string;
}

const ModernComponent: React.FC<Props> = ({ 
  items, 
  onSelect, 
  className = '' 
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  
  // Proper memoization
  const filteredItems = useMemo(() => 
    items.filter(item => 
      item.name.toLowerCase().includes(searchTerm.toLowerCase())
    ), [items, searchTerm]
  );
  
  // Proper callback memoization
  const handleItemClick = useCallback((item: Item) => {
    onSelect(item);
  }, [onSelect]);
  
  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  }, []);
  
  return (
    <div className={`space-y-4 ${className}`}>
      <div>
        <label htmlFor="search-input" className="block text-sm font-medium mb-1">
          Search Items
        </label>
        <input
          id="search-input"
          type="text"
          value={searchTerm}
          onChange={handleSearchChange}
          placeholder="Enter search term..."
          className="w-full px-3 py-2 border rounded-md"
        />
      </div>
      
      <div className="space-y-2">
        {filteredItems.map(item => (
          <button
            key={item.id}
            type="button"
            onClick={() => handleItemClick(item)}
            className="block w-full text-left p-3 border rounded hover:bg-gray-50"
          >
            <div className="font-medium">{item.name}</div>
            <div className="text-sm text-gray-500">Value: {item.value}</div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default ModernComponent;''',
                expected_issues=0,
                expected_score_range=(90, 100),
                expected_issue_types=[],
                description="Modern React component with best practices"
            )
        ]
    
    def run_quality_test_case(self, test_case: QualityTestCase):
        """Run a single quality test case"""
        start_time = time.time()
        
        try:
            from palette.quality.validator import ComponentValidator
            
            # Write test component to file
            test_file = Path(self.temp_dir) / f"{test_case.name}.tsx"
            test_file.write_text(test_case.code)
            
            # Initialize validator
            validator = ComponentValidator(self.temp_dir)
            
            # Test file validation
            file_result = validator.validate_files([str(test_file)], validation_type="comprehensive")
            
            # Test inline code validation
            inline_result = validator.validate_code_content(test_case.code, file_type="comprehensive")
            
            # Analyze results
            file_issues = file_result["issues"]
            file_score = file_result["score"]
            inline_score = inline_result["score"]
            
            # Validate expectations
            issues_in_range = abs(len(file_issues) - test_case.expected_issues) <= 2  # Allow ±2 variance
            score_in_range = (test_case.expected_score_range[0] <= file_score <= test_case.expected_score_range[1])
            
            # Check issue types
            detected_types = set(issue["type"] for issue in file_issues)
            expected_types = set(test_case.expected_issue_types)
            types_match = len(expected_types - detected_types) <= 1  # Allow 1 missing type
            
            # Determine test result
            if issues_in_range and score_in_range and types_match:
                status = "PASS"
                message = f"Quality validation accurate (score: {file_score:.1f}, issues: {len(file_issues)})"
            else:
                status = "FAIL"
                issues_str = f"issues: {len(file_issues)} (expected ~{test_case.expected_issues})"
                score_str = f"score: {file_score:.1f} (expected {test_case.expected_score_range[0]}-{test_case.expected_score_range[1]})"
                types_str = f"types: {detected_types} (expected {expected_types})"
                message = f"Validation inaccurate - {issues_str}, {score_str}, {types_str}"
            
            self.test_results.append({
                "test_name": f"quality_{test_case.name}",
                "status": status,
                "duration": time.time() - start_time,
                "message": message,
                "details": {
                    "description": test_case.description,
                    "file_score": file_score,
                    "inline_score": inline_score,
                    "issues_found": len(file_issues),
                    "expected_issues": test_case.expected_issues,
                    "issue_types": list(detected_types),
                    "expected_types": test_case.expected_issue_types,
                    "sample_issues": file_issues[:3] if file_issues else []
                }
            })
            
        except Exception as e:
            self.test_results.append({
                "test_name": f"quality_{test_case.name}",
                "status": "FAIL",
                "duration": time.time() - start_time,
                "message": f"Test case failed: {str(e)}",
                "details": {"error": str(e), "test_case": test_case.name}
            })
    
    def test_project_quality_analysis(self):
        """Test project-wide quality analysis"""
        start_time = time.time()
        
        try:
            from palette.quality.validator import ComponentValidator
            
            # Create multiple files with varying quality
            test_files = {
                "GoodComponent.tsx": '''
import React from 'react';

interface Props {
  title: string;
  onClick: () => void;
}

export const GoodComponent: React.FC<Props> = ({ title, onClick }) => (
  <button type="button" onClick={onClick} className="btn-primary">
    {title}
  </button>
);
''',
                "BadComponent.tsx": '''
import React from "react";
import React from "react";

const Bad = () => {
    console.log("test");
    return <div className="invalid-class"><img /></div>;
};
''',
                "MediumComponent.tsx": '''
import React from 'react';

const Medium = ({ data }) => {
    return (
        <div>
            {data.map(item => <div key={item.id}>{item.name}</div>)}
        </div>
    );
};
'''
            }
            
            # Write test files
            for filename, content in test_files.items():
                (Path(self.temp_dir) / filename).write_text(content)
            
            # Run project quality analysis
            validator = ComponentValidator(self.temp_dir)
            project_result = validator.validate_project_quality()
            
            # Validate results
            has_score = "score" in project_result and 0 <= project_result["score"] <= 100
            has_issues = "issues" in project_result
            has_suggestions = "suggestions" in project_result
            has_metrics = "metrics" in project_result
            
            if has_score and has_issues and has_suggestions and has_metrics:
                status = "PASS"
                message = f"Project analysis complete (score: {project_result['score']:.1f})"
            else:
                status = "FAIL"
                message = f"Project analysis incomplete - score: {has_score}, issues: {has_issues}, suggestions: {has_suggestions}, metrics: {has_metrics}"
            
            self.test_results.append({
                "test_name": "project_quality_analysis",
                "status": status,
                "duration": time.time() - start_time,
                "message": message,
                "details": {
                    "project_score": project_result.get("score", 0),
                    "total_issues": len(project_result.get("issues", [])),
                    "total_suggestions": len(project_result.get("suggestions", [])),
                    "metrics_available": bool(project_result.get("metrics")),
                    "files_analyzed": 3
                }
            })
            
        except Exception as e:
            self.test_results.append({
                "test_name": "project_quality_analysis",
                "status": "FAIL",
                "duration": time.time() - start_time,
                "message": f"Project analysis failed: {str(e)}"
            })
    
    def test_auto_fix_engine(self):
        """Test auto-fix engine capabilities"""
        start_time = time.time()
        
        try:
            from palette.quality.validator import ComponentValidator
            
            # Component with fixable issues
            fixable_code = '''import React from "react";
import React from "react";  // Duplicate import

const TestComponent = () => {
    console.log("debug message");  // Console.log to remove
    
    return <div className="bg-gray text-black">  // Invalid Tailwind classes
        <img />  // Missing alt
        Test component
    </div>;
};

export default TestComponent;'''
            
            test_file = Path(self.temp_dir) / "FixableComponent.tsx"
            test_file.write_text(fixable_code)
            
            # Validate and get report
            validator = ComponentValidator(self.temp_dir)
            report = validator.validate_component(fixable_code, str(test_file))
            
            # Check if auto-fixes are available
            auto_fixable_issues = [issue for issue in report.issues if issue.auto_fixable]
            
            # Test auto-fix engine
            try:
                fixed_code, fixes_applied = validator.auto_fix_component(fixable_code, report)
                
                # Validate that fixes were applied
                fixes_were_applied = len(fixes_applied) > 0
                code_was_changed = fixed_code != fixable_code
                
                if fixes_were_applied and code_was_changed:
                    # Validate fixed code
                    fixed_report = validator.validate_component(fixed_code, str(test_file))
                    quality_improved = fixed_report.score > report.score
                    
                    status = "PASS" if quality_improved else "PARTIAL"
                    message = f"Auto-fix applied {len(fixes_applied)} fixes, quality {'improved' if quality_improved else 'unchanged'}"
                else:
                    status = "PARTIAL"
                    message = f"Auto-fix available but limited fixes applied ({len(fixes_applied)})"
                    
            except Exception as fix_error:
                status = "FAIL"
                message = f"Auto-fix engine failed: {str(fix_error)}"
                fixes_applied = []
                quality_improved = False
            
            self.test_results.append({
                "test_name": "auto_fix_engine",
                "status": status,
                "duration": time.time() - start_time,
                "message": message,
                "details": {
                    "initial_score": report.score,
                    "auto_fixable_issues": len(auto_fixable_issues),
                    "fixes_applied": len(fixes_applied) if 'fixes_applied' in locals() else 0,
                    "sample_fixes": fixes_applied[:3] if 'fixes_applied' in locals() else []
                }
            })
            
        except Exception as e:
            self.test_results.append({
                "test_name": "auto_fix_engine",
                "status": "FAIL",
                "duration": time.time() - start_time,
                "message": f"Auto-fix test failed: {str(e)}"
            })
    
    def test_quality_performance(self):
        """Test quality validation performance"""
        start_time = time.time()
        
        try:
            from palette.quality.validator import ComponentValidator
            
            # Create large component to test performance
            large_component = '''import React from 'react';

interface Props {
  items: Array<{id: string; name: string; value: number}>;
  onSelect: (id: string) => void;
}

const LargeComponent: React.FC<Props> = ({ items, onSelect }) => {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Items List</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map(item => (
          <div key={item.id} className="bg-white rounded-lg shadow-md p-4">
            <h3 className="text-lg font-semibold">{item.name}</h3>
            <p className="text-gray-600">Value: {item.value}</p>
            <button 
              type="button"
              onClick={() => onSelect(item.id)}
              className="mt-2 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              Select
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LargeComponent;''' * 5  # Repeat to make it larger
            
            validator = ComponentValidator(self.temp_dir)
            
            # Time the validation
            validation_start = time.time()
            result = validator.validate_code_content(large_component, "comprehensive")
            validation_duration = time.time() - validation_start
            
            # Performance criteria
            performance_acceptable = validation_duration < 5.0  # Should complete in < 5 seconds
            memory_efficient = True  # Assuming no memory issues if it completes
            
            if performance_acceptable and memory_efficient:
                status = "PASS"
                message = f"Performance acceptable ({validation_duration:.2f}s)"
            else:
                status = "FAIL"
                message = f"Performance issues - duration: {validation_duration:.2f}s"
            
            self.test_results.append({
                "test_name": "quality_performance",
                "status": status,
                "duration": time.time() - start_time,
                "message": message,
                "details": {
                    "validation_duration": validation_duration,
                    "component_size": len(large_component),
                    "performance_acceptable": performance_acceptable,
                    "score": result["score"]
                }
            })
            
        except Exception as e:
            self.test_results.append({
                "test_name": "quality_performance",
                "status": "FAIL",
                "duration": time.time() - start_time,
                "message": f"Performance test failed: {str(e)}"
            })
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        start_time = time.time()
        
        try:
            from palette.quality.validator import ComponentValidator
            
            validator = ComponentValidator(self.temp_dir)
            edge_cases_passed = 0
            total_edge_cases = 0
            
            # Edge case 1: Empty code
            total_edge_cases += 1
            try:
                result = validator.validate_code_content("", "syntax")
                if result["score"] >= 0:  # Should handle gracefully
                    edge_cases_passed += 1
            except Exception:
                pass
            
            # Edge case 2: Invalid syntax
            total_edge_cases += 1
            try:
                result = validator.validate_code_content("invalid javascript code {{{", "syntax")
                if "issues" in result:  # Should detect syntax issues
                    edge_cases_passed += 1
            except Exception:
                pass
            
            # Edge case 3: Very small valid component
            total_edge_cases += 1
            try:
                result = validator.validate_code_content("export const Test = () => null;", "comprehensive")
                if result["score"] > 0:  # Should provide some score
                    edge_cases_passed += 1
            except Exception:
                pass
            
            # Edge case 4: Non-existent file validation
            total_edge_cases += 1
            try:
                result = validator.validate_files(["/nonexistent/file.tsx"])
                if "issues" in result:  # Should handle missing file gracefully
                    edge_cases_passed += 1
            except Exception:
                pass
            
            success_rate = edge_cases_passed / total_edge_cases
            
            if success_rate >= 0.75:  # At least 75% of edge cases handled
                status = "PASS"
                message = f"Edge cases handled well ({edge_cases_passed}/{total_edge_cases})"
            else:
                status = "FAIL" 
                message = f"Poor edge case handling ({edge_cases_passed}/{total_edge_cases})"
            
            self.test_results.append({
                "test_name": "edge_cases",
                "status": status,
                "duration": time.time() - start_time,
                "message": message,
                "details": {
                    "edge_cases_passed": edge_cases_passed,
                    "total_edge_cases": total_edge_cases,
                    "success_rate": success_rate
                }
            })
            
        except Exception as e:
            self.test_results.append({
                "test_name": "edge_cases",
                "status": "FAIL",
                "duration": time.time() - start_time,
                "message": f"Edge cases test failed: {str(e)}"
            })
    
    def cleanup_test_environment(self):
        """Clean up test environment"""
        if self.temp_dir:
            import shutil
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception as e:
                print(f"⚠️  Cleanup warning: {e}")
    
    def print_quality_report(self):
        """Print formatted quality test report"""
        print("\n" + "=" * 60)
        print("🔍 QUALITY VALIDATION TEST REPORT")
        print("=" * 60)
        
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
        
        print(f"\n📝 Detailed Results:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"   {status_icon} {result['test_name']:<30} ({result['duration']:.2f}s) - {result['message']}")
            
            if result.get("details") and result["status"] != "PASS":
                key_details = {k: v for k, v in result["details"].items() 
                             if k in ["score", "issues_found", "fixes_applied", "error"]}
                if key_details:
                    print(f"      Details: {key_details}")
        
        print("\n" + "=" * 60)
        
        if failed == 0:
            print("🎉 Quality validation system is working correctly!")
        else:
            print(f"⚠️  {failed} test(s) failed. Quality system needs attention.")
        
        print("=" * 60)
    
    def get_summary(self) -> Dict:
        """Get test summary"""
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
            "quality_system_working": failed == 0,
            "test_results": self.test_results
        }

def main():
    """Main test runner for quality workflow"""
    tester = QualityWorkflowTester()
    summary = tester.run_all_quality_tests()
    
    # Exit with error code if tests failed
    sys.exit(0 if summary["quality_system_working"] else 1)

if __name__ == "__main__":
    main()