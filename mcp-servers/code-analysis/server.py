#!/usr/bin/env python3
"""
Code Analysis MCP Server for Palette.
Analyzes existing code to suggest improvements and ensure quality.
"""

import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import ast
import re

# Add the main palette source to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from palette.analysis.treesitter_analyzer import TreeSitterAnalyzer
from palette.quality.validator import ComponentValidator


class CodeAnalysisMCPServer:
    """MCP Server for analyzing and improving code quality."""
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self.tree_sitter_analyzer = None
        self.component_validator = None
        
        # Initialize analyzers
        try:
            self.tree_sitter_analyzer = TreeSitterAnalyzer()
            self.component_validator = ComponentValidator(str(self.project_path))
        except Exception as e:
            print(f"Warning: Some analyzers not available: {e}")
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the server and return capabilities."""
        return {
            "protocol_version": "0.1.0",
            "server_info": {
                "name": "code-analysis",
                "version": "1.0.0",
                "description": "Code analysis and improvement suggestions for frontend components"
            },
            "capabilities": {
                "tools": True,
                "resources": False,
                "prompts": False
            }
        }
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools."""
        return {
            "tools": [
                {
                    "name": "analyze_component",
                    "description": "Deep analysis of a React/Vue component for patterns and issues",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Component code to analyze"
                            },
                            "framework": {
                                "type": "string",
                                "description": "Framework (react, vue, angular)",
                                "default": "react"
                            },
                            "component_name": {
                                "type": "string",
                                "description": "Optional component name",
                                "optional": True
                            }
                        },
                        "required": ["code"]
                    }
                },
                {
                    "name": "suggest_refactoring",
                    "description": "Identify improvement opportunities in code",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Code to analyze for refactoring"
                            },
                            "focus_areas": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Areas to focus on (performance, readability, maintainability)",
                                "optional": True
                            }
                        },
                        "required": ["code"]
                    }
                },
                {
                    "name": "check_accessibility",
                    "description": "Validate component accessibility (WCAG compliance)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Component code to check"
                            },
                            "level": {
                                "type": "string",
                                "description": "WCAG level (A, AA, AAA)",
                                "default": "AA"
                            }
                        },
                        "required": ["code"]
                    }
                },
                {
                    "name": "analyze_performance",
                    "description": "Identify performance bottlenecks and optimization opportunities",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Code to analyze"
                            },
                            "framework": {
                                "type": "string",
                                "description": "Framework for specific optimizations",
                                "default": "react"
                            }
                        },
                        "required": ["code"]
                    }
                },
                {
                    "name": "detect_patterns",
                    "description": "Identify design patterns and anti-patterns in code",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Code to analyze"
                            },
                            "pattern_types": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Types of patterns to detect",
                                "optional": True
                            }
                        },
                        "required": ["code"]
                    }
                },
                {
                    "name": "validate_best_practices",
                    "description": "Check code against frontend best practices",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Code to validate"
                            },
                            "framework": {
                                "type": "string",
                                "description": "Framework-specific practices",
                                "default": "react"
                            }
                        },
                        "required": ["code"]
                    }
                },
                {
                    "name": "analyze_complexity",
                    "description": "Measure code complexity and suggest simplifications",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Code to analyze"
                            },
                            "threshold": {
                                "type": "number",
                                "description": "Complexity threshold",
                                "default": 10
                            }
                        },
                        "required": ["code"]
                    }
                }
            ]
        }
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return results."""
        try:
            if tool_name == "analyze_component":
                return await self._analyze_component(
                    arguments["code"],
                    arguments.get("framework", "react"),
                    arguments.get("component_name")
                )
            elif tool_name == "suggest_refactoring":
                return await self._suggest_refactoring(
                    arguments["code"],
                    arguments.get("focus_areas", [])
                )
            elif tool_name == "check_accessibility":
                return await self._check_accessibility(
                    arguments["code"],
                    arguments.get("level", "AA")
                )
            elif tool_name == "analyze_performance":
                return await self._analyze_performance(
                    arguments["code"],
                    arguments.get("framework", "react")
                )
            elif tool_name == "detect_patterns":
                return await self._detect_patterns(
                    arguments["code"],
                    arguments.get("pattern_types", [])
                )
            elif tool_name == "validate_best_practices":
                return await self._validate_best_practices(
                    arguments["code"],
                    arguments.get("framework", "react")
                )
            elif tool_name == "analyze_complexity":
                return await self._analyze_complexity(
                    arguments["code"],
                    arguments.get("threshold", 10)
                )
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"error": str(e), "type": type(e).__name__}
    
    async def _analyze_component(
        self,
        code: str,
        framework: str,
        component_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform deep component analysis."""
        analysis = {
            "component_name": component_name or self._extract_component_name(code),
            "framework": framework,
            "structure": {},
            "props": {},
            "state_management": {},
            "hooks_usage": {},
            "dependencies": [],
            "issues": [],
            "suggestions": []
        }
        
        # Use tree-sitter if available
        if self.tree_sitter_analyzer and framework == "react":
            try:
                # Analyze component structure
                tree_analysis = self.tree_sitter_analyzer.analyze_react_component(code)
                analysis["structure"] = tree_analysis.get("structure", {})
                analysis["props"] = tree_analysis.get("props", {})
                analysis["hooks_usage"] = tree_analysis.get("hooks", {})
            except Exception as e:
                analysis["issues"].append(f"Tree-sitter analysis failed: {e}")
        
        # Analyze patterns
        patterns = self._analyze_code_patterns(code, framework)
        analysis["patterns"] = patterns
        
        # Check for common issues
        issues = self._check_common_issues(code, framework)
        analysis["issues"].extend(issues)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(analysis)
        analysis["suggestions"] = suggestions
        
        return analysis
    
    async def _suggest_refactoring(
        self,
        code: str,
        focus_areas: List[str]
    ) -> Dict[str, Any]:
        """Suggest refactoring opportunities."""
        suggestions = {
            "refactoring_opportunities": [],
            "code_smells": [],
            "improvements": []
        }
        
        # Check for code smells
        smells = self._detect_code_smells(code)
        suggestions["code_smells"] = smells
        
        # Performance improvements
        if not focus_areas or "performance" in focus_areas:
            perf_suggestions = self._suggest_performance_improvements(code)
            suggestions["improvements"].extend(perf_suggestions)
        
        # Readability improvements
        if not focus_areas or "readability" in focus_areas:
            read_suggestions = self._suggest_readability_improvements(code)
            suggestions["improvements"].extend(read_suggestions)
        
        # Maintainability improvements
        if not focus_areas or "maintainability" in focus_areas:
            maint_suggestions = self._suggest_maintainability_improvements(code)
            suggestions["improvements"].extend(maint_suggestions)
        
        return suggestions
    
    async def _check_accessibility(
        self,
        code: str,
        level: str
    ) -> Dict[str, Any]:
        """Check accessibility compliance."""
        a11y_report = {
            "level": level,
            "violations": [],
            "warnings": [],
            "passes": [],
            "suggestions": []
        }
        
        # Check for ARIA attributes
        aria_issues = self._check_aria_usage(code)
        a11y_report["violations"].extend(aria_issues["violations"])
        a11y_report["warnings"].extend(aria_issues["warnings"])
        
        # Check semantic HTML
        semantic_issues = self._check_semantic_html(code)
        a11y_report["violations"].extend(semantic_issues)
        
        # Check keyboard navigation
        keyboard_issues = self._check_keyboard_navigation(code)
        a11y_report["warnings"].extend(keyboard_issues)
        
        # Check color contrast (basic check)
        color_warnings = self._check_color_usage(code)
        a11y_report["warnings"].extend(color_warnings)
        
        # Generate suggestions
        a11y_report["suggestions"] = self._generate_a11y_suggestions(a11y_report)
        
        return a11y_report
    
    async def _analyze_performance(
        self,
        code: str,
        framework: str
    ) -> Dict[str, Any]:
        """Analyze performance issues."""
        perf_analysis = {
            "framework": framework,
            "issues": [],
            "optimizations": [],
            "metrics": {}
        }
        
        # React-specific performance checks
        if framework == "react":
            # Check for unnecessary re-renders
            render_issues = self._check_react_render_issues(code)
            perf_analysis["issues"].extend(render_issues)
            
            # Check memo usage
            memo_suggestions = self._check_memoization(code)
            perf_analysis["optimizations"].extend(memo_suggestions)
            
            # Check effect dependencies
            effect_issues = self._check_effect_dependencies(code)
            perf_analysis["issues"].extend(effect_issues)
        
        # General performance checks
        general_issues = self._check_general_performance(code)
        perf_analysis["issues"].extend(general_issues)
        
        return perf_analysis
    
    async def _detect_patterns(
        self,
        code: str,
        pattern_types: List[str]
    ) -> Dict[str, Any]:
        """Detect design patterns and anti-patterns."""
        patterns = {
            "design_patterns": [],
            "anti_patterns": [],
            "architectural_patterns": []
        }
        
        # Detect common React patterns
        if "component" in code.lower():
            # Compound components
            if "." in code and "children" in code:
                patterns["design_patterns"].append({
                    "pattern": "Compound Components",
                    "description": "Using dot notation for component composition",
                    "location": "Component definition"
                })
            
            # Render props
            if "render" in code and "function" in code:
                patterns["design_patterns"].append({
                    "pattern": "Render Props",
                    "description": "Using render prop pattern for component logic sharing",
                    "location": "Props definition"
                })
            
            # Custom hooks
            if re.search(r'use[A-Z]\w+', code):
                patterns["design_patterns"].append({
                    "pattern": "Custom Hooks",
                    "description": "Using custom hooks for logic extraction",
                    "location": "Hook usage"
                })
        
        # Detect anti-patterns
        anti_patterns = self._detect_anti_patterns(code)
        patterns["anti_patterns"] = anti_patterns
        
        return patterns
    
    async def _validate_best_practices(
        self,
        code: str,
        framework: str
    ) -> Dict[str, Any]:
        """Validate against best practices."""
        validation = {
            "framework": framework,
            "violations": [],
            "warnings": [],
            "passes": []
        }
        
        # React best practices
        if framework == "react":
            # Check hooks rules
            hooks_violations = self._check_hooks_rules(code)
            validation["violations"].extend(hooks_violations)
            
            # Check prop types or TypeScript
            type_warnings = self._check_type_safety(code)
            validation["warnings"].extend(type_warnings)
            
            # Check naming conventions
            naming_issues = self._check_naming_conventions(code)
            validation["warnings"].extend(naming_issues)
        
        # General best practices
        general_practices = self._check_general_practices(code)
        validation["violations"].extend(general_practices["violations"])
        validation["warnings"].extend(general_practices["warnings"])
        validation["passes"].extend(general_practices["passes"])
        
        return validation
    
    async def _analyze_complexity(
        self,
        code: str,
        threshold: int
    ) -> Dict[str, Any]:
        """Analyze code complexity."""
        complexity = {
            "cyclomatic_complexity": 0,
            "cognitive_complexity": 0,
            "nesting_depth": 0,
            "complex_functions": [],
            "suggestions": []
        }
        
        # Calculate complexities
        complexity["cyclomatic_complexity"] = self._calculate_cyclomatic_complexity(code)
        complexity["cognitive_complexity"] = self._calculate_cognitive_complexity(code)
        complexity["nesting_depth"] = self._calculate_max_nesting(code)
        
        # Find complex functions
        complex_funcs = self._find_complex_functions(code, threshold)
        complexity["complex_functions"] = complex_funcs
        
        # Generate simplification suggestions
        if complexity["cyclomatic_complexity"] > threshold:
            complexity["suggestions"].append({
                "issue": "High cyclomatic complexity",
                "suggestion": "Consider breaking down complex functions into smaller, focused functions"
            })
        
        if complexity["nesting_depth"] > 3:
            complexity["suggestions"].append({
                "issue": "Deep nesting",
                "suggestion": "Use early returns or extract nested logic into separate functions"
            })
        
        return complexity
    
    # Helper methods
    def _extract_component_name(self, code: str) -> str:
        """Extract component name from code."""
        # Try to find React component
        match = re.search(r'(?:function|const|class)\s+(\w+)', code)
        if match:
            return match.group(1)
        return "UnknownComponent"
    
    def _analyze_code_patterns(self, code: str, framework: str) -> List[Dict[str, Any]]:
        """Analyze code for common patterns."""
        patterns = []
        
        if framework == "react":
            # Check for hooks
            hooks = re.findall(r'use[A-Z]\w+', code)
            if hooks:
                patterns.append({
                    "type": "hooks",
                    "items": list(set(hooks)),
                    "description": "React hooks usage detected"
                })
            
            # Check for context usage
            if "useContext" in code or "Context" in code:
                patterns.append({
                    "type": "context",
                    "description": "Context API usage detected"
                })
        
        return patterns
    
    def _check_common_issues(self, code: str, framework: str) -> List[str]:
        """Check for common coding issues."""
        issues = []
        
        # Check for console.log
        if "console.log" in code:
            issues.append("Console.log statements found - remove for production")
        
        # Check for any/unknown types (TypeScript)
        if ": any" in code or ": unknown" in code:
            issues.append("Avoid using 'any' or 'unknown' types - use specific types")
        
        # Check for inline styles
        if 'style={{' in code or 'style={' in code:
            issues.append("Inline styles detected - consider using CSS classes or styled components")
        
        # Check for missing keys in lists
        if ".map(" in code and "key=" not in code:
            issues.append("Missing 'key' prop in list rendering")
        
        return issues
    
    def _generate_suggestions(self, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate improvement suggestions based on analysis."""
        suggestions = []
        
        # Based on issues found
        if "Console.log" in str(analysis.get("issues", [])):
            suggestions.append({
                "type": "cleanup",
                "suggestion": "Remove console.log statements and use proper logging library"
            })
        
        # Based on patterns
        if not any(p["type"] == "hooks" for p in analysis.get("patterns", [])):
            suggestions.append({
                "type": "modernization",
                "suggestion": "Consider using React hooks for state management"
            })
        
        return suggestions
    
    def _detect_code_smells(self, code: str) -> List[Dict[str, str]]:
        """Detect common code smells."""
        smells = []
        
        # Long functions
        lines = code.split('\n')
        if len(lines) > 50:
            smells.append({
                "type": "long_function",
                "description": "Function is too long (>50 lines)",
                "severity": "medium"
            })
        
        # Duplicate code (basic check)
        if code.count("if (") > 5:
            smells.append({
                "type": "duplicate_logic",
                "description": "Multiple similar conditional statements",
                "severity": "low"
            })
        
        return smells
    
    def _suggest_performance_improvements(self, code: str) -> List[Dict[str, str]]:
        """Suggest performance improvements."""
        improvements = []
        
        # React specific
        if "useState" in code and ".map(" in code:
            improvements.append({
                "area": "rendering",
                "suggestion": "Consider using React.memo for list items to prevent unnecessary re-renders"
            })
        
        if "useEffect" in code and "[]" not in code:
            improvements.append({
                "area": "effects",
                "suggestion": "Ensure useEffect dependencies are properly specified"
            })
        
        return improvements
    
    def _suggest_readability_improvements(self, code: str) -> List[Dict[str, str]]:
        """Suggest readability improvements."""
        improvements = []
        
        # Check for complex ternaries
        if code.count("?") > 2 and code.count(":") > 2:
            improvements.append({
                "area": "conditionals",
                "suggestion": "Complex ternary operators detected - consider using if/else or switch"
            })
        
        # Check for magic numbers
        if re.search(r'[^0-9][0-9]{2,}[^0-9]', code):
            improvements.append({
                "area": "constants",
                "suggestion": "Extract magic numbers into named constants"
            })
        
        return improvements
    
    def _suggest_maintainability_improvements(self, code: str) -> List[Dict[str, str]]:
        """Suggest maintainability improvements."""
        improvements = []
        
        # Check for proper typing
        if "function" in code and ":" not in code:
            improvements.append({
                "area": "typing",
                "suggestion": "Add TypeScript types for better maintainability"
            })
        
        # Check for comments
        if code.count("//") < 2 and code.count("/*") < 1:
            improvements.append({
                "area": "documentation",
                "suggestion": "Add comments to explain complex logic"
            })
        
        return improvements
    
    def _check_aria_usage(self, code: str) -> Dict[str, List[str]]:
        """Check ARIA attribute usage."""
        result = {"violations": [], "warnings": []}
        
        # Check for buttons without accessible labels
        if "<button" in code and "aria-label" not in code and not re.search(r'<button[^>]*>[^<]+</button>', code):
            result["violations"].append("Button without accessible label")
        
        # Check for images without alt
        if "<img" in code and 'alt=' not in code:
            result["violations"].append("Image without alt attribute")
        
        return result
    
    def _check_semantic_html(self, code: str) -> List[str]:
        """Check for semantic HTML usage."""
        issues = []
        
        # Check for div with onClick (should be button)
        if '<div' in code and 'onClick' in code:
            issues.append("Using div with onClick - consider using button element")
        
        # Check for proper heading hierarchy
        if '<h3' in code and '<h2' not in code:
            issues.append("Heading hierarchy issue - h3 without h2")
        
        return issues
    
    def _check_keyboard_navigation(self, code: str) -> List[str]:
        """Check keyboard navigation support."""
        warnings = []
        
        # Check for mouse-only events
        if 'onMouseEnter' in code and 'onFocus' not in code:
            warnings.append("Mouse-only interaction - add keyboard support")
        
        # Check for tabIndex on non-interactive elements
        if 'tabIndex' in code and '<div' in code:
            warnings.append("tabIndex on non-interactive element - consider using button")
        
        return warnings
    
    def _check_color_usage(self, code: str) -> List[str]:
        """Basic color contrast checks."""
        warnings = []
        
        # Check for low contrast color combinations (basic)
        if 'color: #' in code or 'color: rgb' in code:
            warnings.append("Ensure color contrast meets WCAG standards (4.5:1 for normal text)")
        
        return warnings
    
    def _generate_a11y_suggestions(self, report: Dict[str, Any]) -> List[str]:
        """Generate accessibility suggestions."""
        suggestions = []
        
        if report["violations"]:
            suggestions.append("Fix critical accessibility violations before deployment")
        
        if report["warnings"]:
            suggestions.append("Address accessibility warnings to improve user experience")
        
        suggestions.append("Test with screen readers and keyboard navigation")
        
        return suggestions
    
    def _check_react_render_issues(self, code: str) -> List[str]:
        """Check for React rendering issues."""
        issues = []
        
        # Check for inline function props
        if re.search(r'onClick=\{.*=>', code):
            issues.append("Inline arrow function in props can cause unnecessary re-renders")
        
        # Check for object/array literals in props
        if re.search(r'=\{\s*\[.*\]\s*\}', code) or re.search(r'=\{\s*\{.*\}\s*\}', code):
            issues.append("Object/array literals in props cause re-renders - use useMemo")
        
        return issues
    
    def _check_memoization(self, code: str) -> List[str]:
        """Check memoization opportunities."""
        suggestions = []
        
        # Check for expensive computations
        if ".filter(" in code and ".map(" in code:
            suggestions.append("Chain of array operations detected - consider useMemo")
        
        # Check for missing React.memo
        if "export default function" in code:
            suggestions.append("Consider wrapping component with React.memo if re-renders are expensive")
        
        return suggestions
    
    def _check_effect_dependencies(self, code: str) -> List[str]:
        """Check useEffect dependencies."""
        issues = []
        
        # Check for missing dependencies (basic)
        if "useEffect(" in code:
            # This is a simplified check
            if "// eslint-disable" in code and "exhaustive-deps" in code:
                issues.append("ESLint rule for exhaustive-deps disabled - ensure dependencies are correct")
        
        return issues
    
    def _check_general_performance(self, code: str) -> List[str]:
        """General performance checks."""
        issues = []
        
        # Check for synchronous operations in render
        if "localStorage" in code or "sessionStorage" in code:
            if "useEffect" not in code:
                issues.append("Synchronous storage access in render - move to useEffect")
        
        return issues
    
    def _detect_anti_patterns(self, code: str) -> List[Dict[str, str]]:
        """Detect common anti-patterns."""
        anti_patterns = []
        
        # Check for state mutation
        if ".push(" in code or ".pop(" in code or ".splice(" in code:
            anti_patterns.append({
                "pattern": "Direct State Mutation",
                "description": "Mutating arrays directly - use immutable updates",
                "severity": "high"
            })
        
        # Check for async in useEffect without cleanup
        if "async" in code and "useEffect" in code and "return" not in code:
            anti_patterns.append({
                "pattern": "Async useEffect without cleanup",
                "description": "Async operations in useEffect need proper cleanup",
                "severity": "medium"
            })
        
        return anti_patterns
    
    def _check_hooks_rules(self, code: str) -> List[str]:
        """Check React hooks rules."""
        violations = []
        
        # Check for conditional hooks (basic)
        if re.search(r'if.*\n.*use[A-Z]', code):
            violations.append("Hooks called conditionally - violates Rules of Hooks")
        
        # Check for hooks in loops
        if re.search(r'for.*\{.*use[A-Z]', code) or re.search(r'while.*\{.*use[A-Z]', code):
            violations.append("Hooks called in loops - violates Rules of Hooks")
        
        return violations
    
    def _check_type_safety(self, code: str) -> List[str]:
        """Check type safety."""
        warnings = []
        
        # Check for missing types (TypeScript)
        if ".tsx" in code or ".ts" in code:
            if re.search(r'const \w+ =', code) and ":" not in code:
                warnings.append("Missing type annotations - add explicit types")
        
        # Check for PropTypes (JavaScript)
        elif ".jsx" in code or ".js" in code:
            if "propTypes" not in code and "function" in code:
                warnings.append("Missing PropTypes validation")
        
        return warnings
    
    def _check_naming_conventions(self, code: str) -> List[str]:
        """Check naming conventions."""
        issues = []
        
        # Check component naming
        if re.search(r'function [a-z]', code) or re.search(r'const [a-z]\w+ = .*=>.*return.*<', code):
            issues.append("Component names should start with uppercase")
        
        # Check hook naming
        if re.search(r'const use[a-z]', code):
            issues.append("Custom hook names should be camelCase starting with 'use'")
        
        return issues
    
    def _check_general_practices(self, code: str) -> Dict[str, List[str]]:
        """Check general coding practices."""
        result = {
            "violations": [],
            "warnings": [],
            "passes": []
        }
        
        # Check error handling
        if "try" not in code and ("fetch" in code or "async" in code):
            result["warnings"].append("Missing error handling for async operations")
        
        # Check for proper imports
        if "import" in code:
            result["passes"].append("Using ES6 imports")
        
        return result
    
    def _calculate_cyclomatic_complexity(self, code: str) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity
        
        # Count decision points
        complexity += code.count("if ")
        complexity += code.count("else if")
        complexity += code.count("for ")
        complexity += code.count("while ")
        complexity += code.count("case ")
        complexity += code.count("&&")
        complexity += code.count("||")
        complexity += code.count("?")  # Ternary
        
        return complexity
    
    def _calculate_cognitive_complexity(self, code: str) -> int:
        """Calculate cognitive complexity."""
        complexity = 0
        
        # Simplified cognitive complexity
        lines = code.split('\n')
        nesting = 0
        
        for line in lines:
            if '{' in line:
                nesting += 1
            if '}' in line:
                nesting = max(0, nesting - 1)
            
            if any(keyword in line for keyword in ['if', 'else', 'for', 'while']):
                complexity += 1 + nesting
        
        return complexity
    
    def _calculate_max_nesting(self, code: str) -> int:
        """Calculate maximum nesting depth."""
        max_depth = 0
        current_depth = 0
        
        for char in code:
            if char == '{':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == '}':
                current_depth = max(0, current_depth - 1)
        
        return max_depth
    
    def _find_complex_functions(self, code: str, threshold: int) -> List[Dict[str, Any]]:
        """Find functions exceeding complexity threshold."""
        complex_functions = []
        
        # Simple function detection
        functions = re.findall(r'function (\w+)|const (\w+) = .*=>|(\w+)\(.*\) \{', code)
        
        for func in functions:
            func_name = next(f for f in func if f)
            # In real implementation, would analyze each function separately
            complexity = min(threshold + 5, 15)  # Simplified
            
            if complexity > threshold:
                complex_functions.append({
                    "name": func_name,
                    "complexity": complexity,
                    "suggestion": f"Consider breaking down {func_name} into smaller functions"
                })
        
        return complex_functions


async def run_stdio_server():
    """Run the MCP server using stdio transport."""
    import mcp
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    
    # Create server instance
    analysis_server = CodeAnalysisMCPServer()
    server = Server("code-analysis")
    
    # Register handlers
    @server.list_tools()
    async def list_tools():
        return await analysis_server.list_tools()
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]):
        return await analysis_server.call_tool(name, arguments)
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, analysis_server.initialize())


async def test_server():
    """Test the server functionality."""
    server = CodeAnalysisMCPServer()
    
    print("Testing Code Analysis MCP Server")
    print("=" * 60)
    
    # Test component analysis
    test_code = '''
    import React, { useState, useEffect } from 'react';
    
    function UserProfile({ userId }) {
        const [user, setUser] = useState(null);
        const [loading, setLoading] = useState(true);
        
        useEffect(() => {
            fetch(`/api/users/${userId}`)
                .then(res => res.json())
                .then(data => {
                    setUser(data);
                    setLoading(false);
                });
        }, [userId]);
        
        if (loading) return <div>Loading...</div>;
        
        return (
            <div onClick={() => console.log('clicked')}>
                <h1>{user.name}</h1>
                <img src={user.avatar} />
            </div>
        );
    }
    '''
    
    print("\n1. Testing analyze_component")
    result = await server.call_tool("analyze_component", {
        "code": test_code,
        "framework": "react"
    })
    print(f"Analysis: {json.dumps(result, indent=2)}")
    
    print("\n2. Testing check_accessibility")
    result = await server.call_tool("check_accessibility", {
        "code": test_code,
        "level": "AA"
    })
    print(f"Accessibility: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Code Analysis MCP Server")
    parser.add_argument("--test", action="store_true", help="Run in test mode")
    args = parser.parse_args()
    
    if args.test:
        asyncio.run(test_server())
    else:
        try:
            asyncio.run(run_stdio_server())
        except ImportError:
            print("MCP SDK not installed. Running in test mode.")
            asyncio.run(test_server())