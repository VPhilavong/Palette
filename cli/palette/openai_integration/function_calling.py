"""
Function calling system for real project interaction.
Enables AI to interact with actual codebases for validation and analysis.
"""

import os
import json
import subprocess
import tempfile
import ast
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
import re

from ..analysis.context import ProjectAnalyzer
from ..utils.file_manager import FileManager


class FunctionCallingSystem:
    """Manages function calling for OpenAI to interact with real projects."""
    
    def __init__(self, project_path: Optional[str] = None):
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.project_analyzer = ProjectAnalyzer()
        self.file_manager = FileManager()
        
        # Register available functions
        self.functions = {
            "analyze_existing_component": self.analyze_existing_component,
            "validate_typescript": self.validate_typescript,
            "check_import_availability": self.check_import_availability,
            "get_design_tokens": self.get_design_tokens,
            "run_component_tests": self.run_component_tests,
            "check_styling_compliance": self.check_styling_compliance,
            "find_similar_components": self.find_similar_components,
            "get_project_structure": self.get_project_structure,
            "verify_type_definitions": self.verify_type_definitions,
            "run_linter": self.run_linter,
            "check_accessibility": self.check_accessibility,
            "get_component_dependencies": self.get_component_dependencies,
        }
    
    def get_function_definitions(self) -> List[Dict]:
        """Get OpenAI-compatible function definitions."""
        return [
            {
                "name": "analyze_existing_component",
                "description": "Analyze an existing component to understand patterns and structure",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the component file relative to project root"
                        },
                        "analysis_type": {
                            "type": "string",
                            "enum": ["structure", "patterns", "dependencies", "styling", "all"],
                            "description": "Type of analysis to perform"
                        }
                    },
                    "required": ["file_path", "analysis_type"]
                }
            },
            {
                "name": "validate_typescript",
                "description": "Run TypeScript compiler to validate code",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "TypeScript code to validate"
                        },
                        "file_name": {
                            "type": "string",
                            "description": "Name for the temporary file (e.g., Component.tsx)"
                        },
                        "tsconfig_path": {
                            "type": "string",
                            "description": "Path to tsconfig.json (optional, uses project default)"
                        }
                    },
                    "required": ["code", "file_name"]
                }
            },
            {
                "name": "check_import_availability",
                "description": "Check if an import path is available in the project",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "import_path": {
                            "type": "string",
                            "description": "Import path to check (e.g., '@/components/ui/button')"
                        }
                    },
                    "required": ["import_path"]
                }
            },
            {
                "name": "get_design_tokens",
                "description": "Get design tokens from the project",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "token_type": {
                            "type": "string",
                            "enum": ["colors", "spacing", "typography", "shadows", "all"],
                            "description": "Type of design tokens to retrieve"
                        }
                    },
                    "required": ["token_type"]
                }
            },
            {
                "name": "run_component_tests",
                "description": "Run tests for a component",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "component_code": {
                            "type": "string",
                            "description": "Component code to test"
                        },
                        "test_code": {
                            "type": "string",
                            "description": "Test code to run"
                        },
                        "test_framework": {
                            "type": "string",
                            "enum": ["jest", "vitest", "cypress"],
                            "description": "Test framework to use"
                        }
                    },
                    "required": ["component_code", "test_code"]
                }
            },
            {
                "name": "find_similar_components",
                "description": "Find components similar to a description",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Description of the component to find"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 5
                        }
                    },
                    "required": ["description"]
                }
            },
            {
                "name": "run_linter",
                "description": "Run ESLint on code",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Code to lint"
                        },
                        "file_name": {
                            "type": "string",
                            "description": "File name for the code"
                        },
                        "fix": {
                            "type": "boolean",
                            "description": "Whether to auto-fix issues",
                            "default": True
                        }
                    },
                    "required": ["code", "file_name"]
                }
            }
        ]
    
    async def execute_function(self, function_name: str, arguments: Dict) -> Dict:
        """Execute a function call and return results."""
        if function_name not in self.functions:
            return {
                "error": f"Unknown function: {function_name}",
                "available_functions": list(self.functions.keys())
            }
        
        try:
            # Get the function
            func = self.functions[function_name]
            
            # Execute it
            result = await func(**arguments) if asyncio.iscoroutinefunction(func) else func(**arguments)
            
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "function": function_name,
                "arguments": arguments
            }
    
    def analyze_existing_component(
        self, 
        file_path: str, 
        analysis_type: str = "all"
    ) -> Dict[str, Any]:
        """Analyze an existing component file."""
        full_path = self.project_path / file_path
        
        if not full_path.exists():
            return {"error": f"File not found: {file_path}"}
        
        try:
            with open(full_path, 'r') as f:
                content = f.read()
            
            results = {}
            
            if analysis_type in ["structure", "all"]:
                results["structure"] = self._analyze_component_structure(content)
            
            if analysis_type in ["patterns", "all"]:
                results["patterns"] = self._analyze_code_patterns(content)
            
            if analysis_type in ["dependencies", "all"]:
                results["dependencies"] = self._analyze_dependencies(content)
            
            if analysis_type in ["styling", "all"]:
                results["styling"] = self._analyze_styling(content)
            
            return results
            
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    def validate_typescript(
        self, 
        code: str, 
        file_name: str = "Component.tsx",
        tsconfig_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate TypeScript code using the project's TypeScript compiler."""
        
        # Find tsconfig if not provided
        if not tsconfig_path:
            tsconfig_path = self._find_tsconfig()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=file_name,
            dir=str(self.project_path),
            delete=False
        ) as tmp_file:
            tmp_file.write(code)
            tmp_path = tmp_file.name
        
        try:
            # Run TypeScript compiler
            cmd = ['npx', 'tsc', '--noEmit', '--skipLibCheck']
            
            if tsconfig_path:
                cmd.extend(['--project', tsconfig_path])
            
            cmd.append(tmp_path)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_path),
                timeout=30
            )
            
            # Parse results
            errors = self._parse_tsc_output(result.stderr or result.stdout)
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "command": ' '.join(cmd),
                "raw_output": result.stderr or result.stdout
            }
            
        except subprocess.TimeoutExpired:
            return {
                "valid": False,
                "errors": [{"message": "TypeScript validation timed out"}]
            }
        except Exception as e:
            return {
                "valid": False,
                "errors": [{"message": f"Validation failed: {str(e)}"}]
            }
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def check_import_availability(self, import_path: str) -> Dict[str, Any]:
        """Check if an import path is available in the project."""
        
        # Handle different import types
        if import_path.startswith('@/'):
            # Alias import
            resolved_path = self._resolve_alias_import(import_path)
        elif import_path.startswith('.'):
            # Relative import
            resolved_path = import_path
        else:
            # Node module import
            return self._check_node_module(import_path)
        
        # Check if the resolved path exists
        if resolved_path:
            possible_extensions = ['.ts', '.tsx', '.js', '.jsx', '/index.ts', '/index.tsx', '/index.js', '/index.jsx']
            
            for ext in possible_extensions:
                full_path = self.project_path / (resolved_path + ext)
                if full_path.exists():
                    return {
                        "available": True,
                        "resolved_path": str(full_path.relative_to(self.project_path)),
                        "import_type": "local",
                        "original_path": import_path
                    }
        
        return {
            "available": False,
            "import_type": "unknown",
            "original_path": import_path,
            "suggestion": self._suggest_alternative_import(import_path)
        }
    
    def get_design_tokens(self, token_type: str = "all") -> Dict[str, Any]:
        """Get design tokens from the project."""
        
        # Use the project analyzer to get design tokens
        project_context = self.project_analyzer.analyze_project(str(self.project_path))
        design_tokens = project_context.get("design_tokens", {})
        
        if token_type == "all":
            return design_tokens
        elif token_type in design_tokens:
            return {token_type: design_tokens[token_type]}
        else:
            return {
                "error": f"Unknown token type: {token_type}",
                "available_types": list(design_tokens.keys())
            }
    
    def run_component_tests(
        self,
        component_code: str,
        test_code: str,
        test_framework: str = "jest"
    ) -> Dict[str, Any]:
        """Run tests for a component."""
        
        # Create temp directory for test
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write component file
            component_path = Path(tmpdir) / "Component.tsx"
            with open(component_path, 'w') as f:
                f.write(component_code)
            
            # Write test file
            test_path = Path(tmpdir) / "Component.test.tsx"
            with open(test_path, 'w') as f:
                f.write(test_code)
            
            # Determine test command
            if test_framework == "jest":
                cmd = ['npx', 'jest', str(test_path), '--no-coverage']
            elif test_framework == "vitest":
                cmd = ['npx', 'vitest', 'run', str(test_path)]
            else:
                return {"error": f"Unsupported test framework: {test_framework}"}
            
            try:
                # Run tests
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=str(self.project_path),
                    timeout=60
                )
                
                return {
                    "success": result.returncode == 0,
                    "output": result.stdout,
                    "errors": result.stderr,
                    "test_framework": test_framework
                }
                
            except subprocess.TimeoutExpired:
                return {"error": "Test execution timed out"}
            except Exception as e:
                return {"error": f"Test execution failed: {str(e)}"}
    
    def check_styling_compliance(self, code: str, styling_system: str = "tailwind") -> Dict[str, Any]:
        """Check if code follows the project's styling conventions."""
        
        if styling_system == "tailwind":
            return self._check_tailwind_compliance(code)
        elif styling_system == "styled-components":
            return self._check_styled_components_compliance(code)
        elif styling_system == "css-modules":
            return self._check_css_modules_compliance(code)
        else:
            return {"error": f"Unknown styling system: {styling_system}"}
    
    def find_similar_components(self, description: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find components similar to the description."""
        
        similar_components = []
        
        # Get all component files
        component_patterns = ["**/*.tsx", "**/*.jsx"]
        component_files = []
        
        for pattern in component_patterns:
            files = list(self.project_path.glob(pattern))
            component_files.extend(files)
        
        # Score each component based on similarity
        for file_path in component_files[:50]:  # Limit search for performance
            if 'node_modules' in str(file_path):
                continue
                
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Simple scoring based on keyword matching
                score = self._calculate_similarity_score(description, content)
                
                if score > 0.3:  # Threshold
                    similar_components.append({
                        "file_path": str(file_path.relative_to(self.project_path)),
                        "score": score,
                        "component_name": file_path.stem,
                        "preview": content[:200] + "..."
                    })
            except:
                continue
        
        # Sort by score and return top matches
        similar_components.sort(key=lambda x: x["score"], reverse=True)
        return similar_components[:limit]
    
    def get_project_structure(self) -> Dict[str, Any]:
        """Get the project structure and key directories."""
        
        structure = {
            "root": str(self.project_path),
            "framework": self._detect_framework(),
            "package_manager": self._detect_package_manager(),
            "key_directories": {},
            "config_files": {}
        }
        
        # Find key directories
        key_dirs = {
            "components": ["src/components", "components", "app/components"],
            "pages": ["src/pages", "pages", "app"],
            "styles": ["src/styles", "styles", "src/css"],
            "utils": ["src/utils", "utils", "src/lib", "lib"],
            "hooks": ["src/hooks", "hooks"],
            "api": ["src/api", "api", "pages/api", "app/api"]
        }
        
        for key, possible_paths in key_dirs.items():
            for path in possible_paths:
                full_path = self.project_path / path
                if full_path.exists():
                    structure["key_directories"][key] = path
                    break
        
        # Find config files
        config_files = [
            "tsconfig.json", "next.config.js", "vite.config.js",
            "tailwind.config.js", ".eslintrc.js", "jest.config.js"
        ]
        
        for config in config_files:
            if (self.project_path / config).exists():
                structure["config_files"][config] = True
        
        return structure
    
    def verify_type_definitions(self, type_name: str, file_context: str) -> Dict[str, Any]:
        """Verify if a type definition exists in the project."""
        
        # Search for type definition
        type_patterns = [
            f"type {type_name}",
            f"interface {type_name}",
            f"export type {type_name}",
            f"export interface {type_name}"
        ]
        
        found_definitions = []
        
        # Search in common type definition locations
        type_locations = [
            "**/*.d.ts",
            "**/types.ts",
            "**/types/*.ts",
            "**/@types/*.ts"
        ]
        
        for pattern in type_locations:
            for file_path in self.project_path.glob(pattern):
                if 'node_modules' in str(file_path):
                    continue
                    
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    for type_pattern in type_patterns:
                        if type_pattern in content:
                            found_definitions.append({
                                "file": str(file_path.relative_to(self.project_path)),
                                "pattern": type_pattern,
                                "context": self._extract_type_context(content, type_pattern)
                            })
                except:
                    continue
        
        return {
            "exists": len(found_definitions) > 0,
            "definitions": found_definitions,
            "type_name": type_name
        }
    
    def run_linter(self, code: str, file_name: str, fix: bool = True) -> Dict[str, Any]:
        """Run ESLint on the provided code."""
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=file_name,
            dir=str(self.project_path),
            delete=False
        ) as tmp_file:
            tmp_file.write(code)
            tmp_path = tmp_file.name
        
        try:
            # Run ESLint
            cmd = ['npx', 'eslint', tmp_path]
            if fix:
                cmd.append('--fix')
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_path),
                timeout=30
            )
            
            # Read potentially fixed code
            fixed_code = code
            if fix and os.path.exists(tmp_path):
                with open(tmp_path, 'r') as f:
                    fixed_code = f.read()
            
            # Parse ESLint output
            issues = self._parse_eslint_output(result.stdout)
            
            return {
                "success": result.returncode == 0,
                "issues": issues,
                "fixed_code": fixed_code if fix else None,
                "has_fixes": fixed_code != code
            }
            
        except subprocess.TimeoutExpired:
            return {"error": "Linting timed out"}
        except Exception as e:
            return {"error": f"Linting failed: {str(e)}"}
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def check_accessibility(self, code: str) -> Dict[str, Any]:
        """Check component for accessibility issues."""
        
        issues = []
        suggestions = []
        
        # Check for alt text on images
        if '<img' in code and 'alt=' not in code:
            issues.append({
                "type": "error",
                "message": "Images must have alt text",
                "suggestion": "Add alt attribute to all img elements"
            })
        
        # Check for button/link accessibility
        button_matches = re.findall(r'<button[^>]*>(.*?)</button>', code, re.DOTALL)
        for match in button_matches:
            if not match.strip() and 'aria-label' not in code:
                issues.append({
                    "type": "error",
                    "message": "Buttons must have accessible text",
                    "suggestion": "Add text content or aria-label to button"
                })
        
        # Check for form labels
        if '<input' in code:
            input_count = code.count('<input')
            label_count = code.count('<label')
            if input_count > label_count:
                issues.append({
                    "type": "warning",
                    "message": "Form inputs should have associated labels",
                    "suggestion": "Add label elements for all inputs"
                })
        
        # Check for ARIA attributes
        aria_patterns = [
            'role=', 'aria-label=', 'aria-labelledby=',
            'aria-describedby=', 'aria-hidden='
        ]
        
        aria_usage = sum(1 for pattern in aria_patterns if pattern in code)
        if aria_usage == 0 and any(tag in code for tag in ['<nav', '<main', '<aside']):
            suggestions.append("Consider adding ARIA landmarks for better screen reader navigation")
        
        # Check for keyboard navigation
        if 'onClick' in code and 'onKeyDown' not in code:
            suggestions.append("Consider adding keyboard event handlers alongside click handlers")
        
        return {
            "accessible": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "score": max(0, 100 - (len(issues) * 20))
        }
    
    def get_component_dependencies(self, code: str) -> Dict[str, Any]:
        """Extract all dependencies from component code."""
        
        dependencies = {
            "imports": [],
            "hooks": [],
            "components": [],
            "utilities": [],
            "types": []
        }
        
        # Extract imports
        import_pattern = r'import\s+(?:{[^}]+}|[\w\s,]+)\s+from\s+[\'"]([^\'"]+)[\'"]'
        imports = re.findall(import_pattern, code)
        dependencies["imports"] = imports
        
        # Extract React hooks
        hook_pattern = r'use[A-Z]\w*'
        hooks = list(set(re.findall(hook_pattern, code)))
        dependencies["hooks"] = hooks
        
        # Extract component usage (JSX tags)
        component_pattern = r'<([A-Z][A-Za-z0-9]*)'
        components = list(set(re.findall(component_pattern, code)))
        dependencies["components"] = components
        
        # Extract type usage
        type_pattern = r':\s*([A-Z][A-Za-z0-9]*(?:<[^>]+>)?)'
        types = list(set(re.findall(type_pattern, code)))
        dependencies["types"] = types
        
        return dependencies
    
    # Helper methods
    
    def _find_tsconfig(self) -> Optional[str]:
        """Find the tsconfig.json file."""
        tsconfig_path = self.project_path / "tsconfig.json"
        if tsconfig_path.exists():
            return str(tsconfig_path)
        return None
    
    def _parse_tsc_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse TypeScript compiler output."""
        errors = []
        
        # TypeScript error format: file(line,col): error TS####: message
        error_pattern = r'(.+?)\((\d+),(\d+)\):\s+error\s+(TS\d+):\s+(.+)'
        
        for match in re.finditer(error_pattern, output):
            errors.append({
                "file": match.group(1),
                "line": int(match.group(2)),
                "column": int(match.group(3)),
                "code": match.group(4),
                "message": match.group(5)
            })
        
        return errors
    
    def _resolve_alias_import(self, import_path: str) -> Optional[str]:
        """Resolve @ alias imports."""
        if import_path.startswith('@/'):
            # Common alias patterns
            return import_path.replace('@/', 'src/')
        return None
    
    def _check_node_module(self, module_name: str) -> Dict[str, Any]:
        """Check if a node module is installed."""
        package_json_path = self.project_path / "package.json"
        
        if package_json_path.exists():
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                
                all_deps = {
                    **package_data.get("dependencies", {}),
                    **package_data.get("devDependencies", {})
                }
                
                # Extract package name from import
                package = module_name.split('/')[0]
                if module_name.startswith('@'):
                    # Scoped package
                    parts = module_name.split('/')
                    package = f"{parts[0]}/{parts[1]}"
                
                return {
                    "available": package in all_deps,
                    "import_type": "node_module",
                    "package": package,
                    "version": all_deps.get(package, None)
                }
            except:
                pass
        
        return {
            "available": False,
            "import_type": "node_module",
            "package": module_name
        }
    
    def _suggest_alternative_import(self, import_path: str) -> Optional[str]:
        """Suggest alternative import paths."""
        # This could be enhanced with fuzzy matching
        return None
    
    def _analyze_component_structure(self, content: str) -> Dict[str, Any]:
        """Analyze the structure of a component."""
        structure = {
            "type": "unknown",
            "has_props": False,
            "has_state": False,
            "hooks_used": [],
            "exported": False
        }
        
        # Detect component type
        if "function" in content and "return" in content:
            structure["type"] = "functional"
        elif "class" in content and "extends Component" in content:
            structure["type"] = "class"
        
        # Check for props
        if "Props" in content or "props:" in content:
            structure["has_props"] = True
        
        # Check for state
        if "useState" in content or "this.state" in content:
            structure["has_state"] = True
        
        # Find hooks
        hook_pattern = r'use[A-Z]\w*'
        hooks = list(set(re.findall(hook_pattern, content)))
        structure["hooks_used"] = hooks
        
        # Check if exported
        if "export default" in content or "export {" in content:
            structure["exported"] = True
        
        return structure
    
    def _analyze_code_patterns(self, content: str) -> List[str]:
        """Extract coding patterns from content."""
        patterns = []
        
        # State management patterns
        if "useState" in content:
            patterns.append("React hooks for state management")
        if "useReducer" in content:
            patterns.append("useReducer for complex state")
        if "useContext" in content:
            patterns.append("Context API for global state")
        
        # Effect patterns
        if "useEffect" in content:
            patterns.append("useEffect for side effects")
        if "useLayoutEffect" in content:
            patterns.append("useLayoutEffect for DOM mutations")
        
        # Performance patterns
        if "useMemo" in content:
            patterns.append("useMemo for expensive computations")
        if "useCallback" in content:
            patterns.append("useCallback for function memoization")
        if "React.memo" in content:
            patterns.append("React.memo for component memoization")
        
        # Error handling
        if "try {" in content and "catch" in content:
            patterns.append("Try-catch error handling")
        if "ErrorBoundary" in content:
            patterns.append("Error boundary component")
        
        return patterns
    
    def _analyze_dependencies(self, content: str) -> Dict[str, List[str]]:
        """Analyze component dependencies."""
        deps = {
            "external": [],
            "internal": [],
            "types": []
        }
        
        # Extract all imports
        import_pattern = r'import\s+(?:{[^}]+}|[\w\s,]+)\s+from\s+[\'"]([^\'"]+)[\'"]'
        imports = re.findall(import_pattern, content)
        
        for imp in imports:
            if imp.startswith('.') or imp.startswith('@/'):
                deps["internal"].append(imp)
            else:
                deps["external"].append(imp)
        
        # Extract type imports
        type_import_pattern = r'import\s+type\s+{[^}]+}\s+from\s+[\'"]([^\'"]+)[\'"]'
        type_imports = re.findall(type_import_pattern, content)
        deps["types"] = type_imports
        
        return deps
    
    def _analyze_styling(self, content: str) -> Dict[str, Any]:
        """Analyze styling approach used in component."""
        styling = {
            "approach": "unknown",
            "classes_used": [],
            "inline_styles": False,
            "css_modules": False,
            "styled_components": False
        }
        
        # Check for Tailwind classes
        tailwind_pattern = r'className=["\']([^"\']+)["\']'
        class_matches = re.findall(tailwind_pattern, content)
        if class_matches:
            all_classes = ' '.join(class_matches).split()
            # Check if they look like Tailwind classes
            tailwind_classes = [c for c in all_classes if re.match(r'^[a-z]+-', c)]
            if tailwind_classes:
                styling["approach"] = "tailwind"
                styling["classes_used"] = tailwind_classes[:10]  # Sample
        
        # Check for inline styles
        if 'style={{' in content or 'style={' in content:
            styling["inline_styles"] = True
            if styling["approach"] == "unknown":
                styling["approach"] = "inline"
        
        # Check for CSS modules
        if 'styles.' in content or 'styles[' in content:
            styling["css_modules"] = True
            styling["approach"] = "css-modules"
        
        # Check for styled-components
        if 'styled.' in content or 'styled(' in content:
            styling["styled_components"] = True
            styling["approach"] = "styled-components"
        
        return styling
    
    def _check_tailwind_compliance(self, code: str) -> Dict[str, Any]:
        """Check Tailwind CSS compliance."""
        issues = []
        
        # Check for inline styles (should use Tailwind classes instead)
        if 'style={{' in code:
            issues.append({
                "type": "warning",
                "message": "Prefer Tailwind classes over inline styles",
                "line": code.find('style={{')
            })
        
        # Check for custom CSS (should use Tailwind utilities)
        if '.css' in code or '<style>' in code:
            issues.append({
                "type": "warning",
                "message": "Consider using Tailwind utilities instead of custom CSS"
            })
        
        # Get design tokens to verify class usage
        tokens = self.get_design_tokens()
        available_colors = tokens.get("colors", {}).get("custom", [])
        
        # Extract all Tailwind classes
        class_pattern = r'className=["\']([^"\']+)["\']'
        all_classes = []
        for match in re.finditer(class_pattern, code):
            classes = match.group(1).split()
            all_classes.extend(classes)
        
        # Check color classes against available colors
        color_classes = [c for c in all_classes if re.match(r'(bg|text|border)-\w+-\d+', c)]
        for color_class in color_classes:
            color_name = re.search(r'(bg|text|border)-(\w+)-\d+', color_class)
            if color_name and color_name.group(2) not in available_colors:
                issues.append({
                    "type": "info",
                    "message": f"Color '{color_name.group(2)}' not in design system",
                    "suggestion": f"Available colors: {', '.join(available_colors[:5])}"
                })
        
        return {
            "compliant": len(issues) == 0,
            "issues": issues,
            "classes_found": len(all_classes),
            "unique_classes": len(set(all_classes))
        }
    
    def _check_styled_components_compliance(self, code: str) -> Dict[str, Any]:
        """Check styled-components compliance."""
        issues = []
        
        # Check for proper styled usage
        if 'styled' not in code:
            issues.append({
                "type": "error",
                "message": "No styled-components usage found"
            })
        
        # Check for theme usage
        if 'theme' not in code and 'styled.' in code:
            issues.append({
                "type": "warning",
                "message": "Consider using theme for consistent styling"
            })
        
        return {
            "compliant": len(issues) == 0,
            "issues": issues
        }
    
    def _check_css_modules_compliance(self, code: str) -> Dict[str, Any]:
        """Check CSS modules compliance."""
        issues = []
        
        # Check for styles import
        if 'styles' not in code:
            issues.append({
                "type": "warning",
                "message": "No CSS module import found"
            })
        
        # Check for proper class usage
        if 'className=' in code and 'styles.' not in code:
            issues.append({
                "type": "warning",
                "message": "Use CSS module classes instead of string classes"
            })
        
        return {
            "compliant": len(issues) == 0,
            "issues": issues
        }
    
    def _calculate_similarity_score(self, description: str, content: str) -> float:
        """Calculate similarity score between description and component content."""
        # Simple keyword-based scoring
        description_words = description.lower().split()
        content_lower = content.lower()
        
        matches = 0
        for word in description_words:
            if word in content_lower:
                matches += 1
        
        # Also check component name in content
        if any(word in content_lower for word in ['button', 'card', 'modal', 'form', 'input']):
            if any(word in description.lower() for word in ['button', 'card', 'modal', 'form', 'input']):
                matches += 2
        
        # Normalize score
        score = matches / max(len(description_words), 1)
        return min(score, 1.0)
    
    def _detect_framework(self) -> str:
        """Detect the project framework."""
        if (self.project_path / "next.config.js").exists():
            return "next.js"
        elif (self.project_path / "vite.config.js").exists():
            return "vite"
        elif (self.project_path / "remix.config.js").exists():
            return "remix"
        else:
            return "react"
    
    def _detect_package_manager(self) -> str:
        """Detect the package manager used."""
        if (self.project_path / "pnpm-lock.yaml").exists():
            return "pnpm"
        elif (self.project_path / "yarn.lock").exists():
            return "yarn"
        elif (self.project_path / "package-lock.json").exists():
            return "npm"
        else:
            return "unknown"
    
    def _extract_type_context(self, content: str, pattern: str) -> str:
        """Extract context around a type definition."""
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if pattern in line:
                # Get 3 lines before and after
                start = max(0, i - 3)
                end = min(len(lines), i + 4)
                return '\n'.join(lines[start:end])
        return ""
    
    def _parse_eslint_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse ESLint output."""
        issues = []
        
        # Try to parse as JSON first (ESLint can output JSON)
        try:
            data = json.loads(output)
            if isinstance(data, list) and data:
                for file_result in data:
                    for message in file_result.get("messages", []):
                        issues.append({
                            "line": message.get("line"),
                            "column": message.get("column"),
                            "severity": message.get("severity"),
                            "message": message.get("message"),
                            "rule": message.get("ruleId")
                        })
        except:
            # Fallback to text parsing
            # ESLint format: line:col severity message rule
            issue_pattern = r'(\d+):(\d+)\s+(error|warning)\s+(.+?)\s+(\S+)$'
            for match in re.finditer(issue_pattern, output, re.MULTILINE):
                issues.append({
                    "line": int(match.group(1)),
                    "column": int(match.group(2)),
                    "severity": match.group(3),
                    "message": match.group(4),
                    "rule": match.group(5)
                })
        
        return issues


# For async support
import asyncio