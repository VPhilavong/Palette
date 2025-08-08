"""
Production-ready Tree-sitter based AST analyzer for React components.
Replaces SimpleASTAnalyzer with dramatically improved accuracy and reliability.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict

try:
    import tree_sitter_languages as tsl
    import tree_sitter as ts
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


@dataclass
class PropPattern:
    """Represents a prop pattern found in a component."""
    name: str
    type_annotation: Optional[str] = None
    default_value: Optional[str] = None
    is_optional: bool = False
    is_destructured: bool = False


@dataclass
class ComponentPattern:
    """Represents a React component pattern."""
    name: str
    file_path: str
    is_functional: bool = True
    props: List[PropPattern] = None
    styling_patterns: List[str] = None
    imports: List[str] = None
    export_type: str = "default"
    has_typescript: bool = False
    
    def __post_init__(self):
        if self.props is None:
            self.props = []
        if self.styling_patterns is None:
            self.styling_patterns = []
        if self.imports is None:
            self.imports = []


class TreeSitterAnalyzer:
    """High-accuracy Tree-sitter based AST analyzer for React components."""
    
    def __init__(self):
        if not TREE_SITTER_AVAILABLE:
            raise ImportError("tree-sitter and tree-sitter-languages required")
        
        # Initialize parsers with compatible API
        try:
            self.tsx_parser = ts.Parser()
            self.jsx_parser = ts.Parser()
            
            # Get languages
            try:
                tsx_lang = tsl.get_language('tsx')
            except:
                tsx_lang = tsl.get_language('typescript')
            
            js_lang = tsl.get_language('javascript')
            
            self.tsx_parser.set_language(tsx_lang)
            self.jsx_parser.set_language(js_lang)
            
        except Exception as e:
            # Fallback: Use alternative initialization
            print(f"Using alternative tree-sitter initialization: {e}")
            self.tsx_parser = self._create_parser_fallback('typescript')
            self.jsx_parser = self._create_parser_fallback('javascript')
        
        # Common styling utilities
        self.styling_utils = {
            'clsx', 'classnames', 'cn', 'twMerge', 'tailwind-merge',
            'styled', 'css', 'cva', 'tv', 'twcx'
        }
        
        # React hook patterns
        self.react_hooks = {
            'useState', 'useEffect', 'useCallback', 'useMemo',
            'useRef', 'useContext', 'useReducer', 'useImperativeHandle',
            'useLayoutEffect', 'useDebugValue', 'useDeferredValue',
            'useTransition', 'useId', 'useSyncExternalStore'
        }
    
    def _create_parser_fallback(self, language: str):
        """Fallback parser creation method."""
        try:
            if language == 'typescript':
                return tsl.get_parser('typescript')
            else:
                return tsl.get_parser('javascript')
        except:
            raise ImportError(f"Cannot create {language} parser")
    
    def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """Analyze project with enhanced Tree-sitter parsing."""
        project_path = Path(project_path)
        
        # Smart file discovery for large projects
        component_files = self._smart_file_discovery(project_path)
        
        if not component_files:
            return {"error": "No React component files found"}
        
        # Analyze components in batches for large projects
        components = []
        styling_idioms = defaultdict(int)
        import_patterns = defaultdict(int)
        
        batch_size = 50 if len(component_files) > 200 else len(component_files)
        
        for i in range(0, len(component_files), batch_size):
            batch = component_files[i:i + batch_size]
            
            for file_path in batch:
                try:
                    component = self._analyze_component_with_treesitter(file_path)
                    if component:
                        components.append(component)
                        
                        # Collect patterns
                        for pattern in component.styling_patterns:
                            styling_idioms[pattern] += 1
                        
                        for imp in component.imports:
                            import_patterns[imp] += 1
                            
                except Exception as e:
                    print(f"Error analyzing {file_path}: {e}")
                    continue
        
        # Extract common patterns
        common_patterns = self._extract_common_patterns(components)
        
        return {
            "components": [asdict(comp) for comp in components],
            "styling_idioms": dict(styling_idioms),
            "import_patterns": dict(import_patterns),
            "common_patterns": common_patterns,
            "statistics": {
                "total_components": len(components),
                "typescript_components": sum(1 for c in components if c.has_typescript),
                "functional_components": sum(1 for c in components if c.is_functional),
                "files_analyzed": len(component_files),
            }
        }
    
    def _smart_file_discovery(self, project_path: Path) -> List[Path]:
        """Smart file discovery optimized for large projects."""
        extensions = {'.tsx', '.jsx', '.ts', '.js'}
        component_files = []
        
        # Priority-based search for better performance
        search_strategies = [
            # Strategy 1: Monorepo structure
            self._search_monorepo_structure,
            # Strategy 2: Standard React structure  
            self._search_standard_structure,
            # Strategy 3: Full project search (fallback)
            self._search_full_project
        ]
        
        for strategy in search_strategies:
            component_files = strategy(project_path, extensions)
            if component_files:
                break
        
        # Smart filtering and limiting
        component_files = self._filter_and_prioritize_files(component_files)
        
        return component_files
    
    def _search_monorepo_structure(self, project_path: Path, extensions: Set[str]) -> List[Path]:
        """Search monorepo structure efficiently."""
        component_files = []
        
        # Check for monorepo indicators
        monorepo_dirs = ['apps', 'packages', 'libs']
        
        for mono_dir_name in monorepo_dirs:
            mono_dir = project_path / mono_dir_name
            if mono_dir.exists():
                for app_dir in mono_dir.iterdir():
                    if app_dir.is_dir():
                        # Priority paths within each app
                        priority_paths = [
                            'src/components',
                            'src/app',
                            'components',
                            'src',
                            'lib'
                        ]
                        
                        for priority_path in priority_paths:
                            search_path = app_dir / priority_path
                            if search_path.exists():
                                component_files.extend(self._collect_files_in_path(
                                    search_path, extensions, max_files=30
                                ))
        
        return component_files
    
    def _search_standard_structure(self, project_path: Path, extensions: Set[str]) -> List[Path]:
        """Search standard React project structure."""
        component_files = []
        
        priority_dirs = [
            'src/components',
            'src/app', 
            'src/pages',
            'components',
            'src',
            'app',
            'pages',
            'lib'
        ]
        
        for dir_name in priority_dirs:
            search_path = project_path / dir_name
            if search_path.exists():
                component_files.extend(self._collect_files_in_path(
                    search_path, extensions, max_files=50
                ))
        
        return component_files
    
    def _search_full_project(self, project_path: Path, extensions: Set[str]) -> List[Path]:
        """Full project search as fallback."""
        return self._collect_files_in_path(project_path, extensions, max_files=100)
    
    def _collect_files_in_path(self, search_path: Path, extensions: Set[str], max_files: int = 50) -> List[Path]:
        """Collect component files in a specific path."""
        files = []
        
        for file_path in search_path.rglob('*'):
            if len(files) >= max_files:
                break
                
            if (file_path.suffix in extensions and 
                file_path.is_file() and
                self._should_include_file(file_path)):
                files.append(file_path)
        
        return files
    
    def _should_include_file(self, file_path: Path) -> bool:
        """Determine if file should be included in analysis."""
        path_str = str(file_path)
        
        # Exclude patterns
        exclude_patterns = [
            'node_modules', '.next', 'dist', 'build', 'coverage',
            '__tests__', '.test.', '.spec.', '.stories.',
            'babel.config', 'webpack.config', 'vite.config',
            '.eslint', '.prettier', 'jest.config'
        ]
        
        if any(pattern in path_str for pattern in exclude_patterns):
            return False
        
        # Include only if likely to be a component
        return self._quick_component_check(file_path)
    
    def _quick_component_check(self, file_path: Path) -> bool:
        """Quick check if file likely contains React components."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Read first 500 chars for quick check
                sample = f.read(500).lower()
                
                # Must have React indicators
                react_indicators = ['import', 'react', 'export', 'function', 'const', 'jsx']
                has_react = sum(1 for indicator in react_indicators if indicator in sample) >= 3
                
                # Should have JSX-like content
                has_jsx = any(pattern in sample for pattern in ['<', 'return', '=>', '{', '}'])
                
                return has_react and has_jsx
        except:
            return True  # Include if can't read (better to over-include than miss)
    
    def _filter_and_prioritize_files(self, component_files: List[Path]) -> List[Path]:
        """Filter and prioritize files for analysis."""
        if len(component_files) <= 150:
            return component_files
        
        # Prioritize TypeScript files and well-named components
        scored_files = []
        
        for file_path in component_files:
            score = 0
            
            # TypeScript bonus
            if file_path.suffix in ['.tsx', '.ts']:
                score += 3
            
            # Component-like naming bonus
            name = file_path.stem
            if name and name[0].isupper():
                score += 2
            
            # Common component directories bonus
            if any(dir_name in str(file_path) for dir_name in 
                   ['components', 'ui', 'shared', 'common']):
                score += 1
            
            # Smaller files are often cleaner components
            try:
                size = file_path.stat().st_size
                if size < 5000:  # Less than 5KB
                    score += 1
            except:
                pass
            
            scored_files.append((score, file_path))
        
        # Sort by score and take top files
        scored_files.sort(key=lambda x: x[0], reverse=True)
        return [file_path for _, file_path in scored_files[:150]]
    
    def _analyze_component_with_treesitter(self, file_path: Path) -> Optional[ComponentPattern]:
        """Analyze component using Tree-sitter AST parsing."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
        except Exception:
            return None
        
        # Quick validation
        if not self._is_likely_react_component(source_code):
            return None
        
        # Parse with appropriate parser
        has_typescript = file_path.suffix in ['.tsx', '.ts']
        parser = self.tsx_parser if has_typescript else self.jsx_parser
        
        try:
            tree = parser.parse(source_code.encode('utf-8'))
            root_node = tree.root_node
            
            # Extract component information using AST
            component_name = self._extract_component_name_from_ast(root_node, source_code)
            if not component_name:
                return None
            
            props = self._extract_props_from_ast(root_node, source_code)
            imports = self._extract_imports_from_ast(root_node, source_code)
            styling_patterns = self._extract_styling_patterns_from_ast(root_node, source_code)
            export_type = self._determine_export_type_from_ast(root_node, source_code)
            is_functional = self._is_functional_component(root_node, source_code)
            
            return ComponentPattern(
                name=component_name,
                file_path=str(file_path),
                is_functional=is_functional,
                props=props,
                imports=imports,
                styling_patterns=styling_patterns,
                export_type=export_type,
                has_typescript=has_typescript
            )
            
        except Exception as e:
            print(f"Tree-sitter parsing failed for {file_path}: {e}")
            # Fallback to regex-based parsing
            return self._fallback_regex_analysis(file_path, source_code, has_typescript)
    
    def _is_likely_react_component(self, source_code: str) -> bool:
        """Quick check if source code is likely a React component."""
        # Must have React import or usage
        has_react = ('react' in source_code.lower() or 
                    'import' in source_code.lower())
        
        # Must have component-like patterns
        has_component = any(pattern in source_code for pattern in [
            'export default', 'export function', 'export const',
            'function ', 'const ', '=>'
        ])
        
        # Must have JSX-like content
        has_jsx = any(pattern in source_code for pattern in [
            '<', 'return (', 'return<', '{', '}'
        ])
        
        return has_react and has_component and has_jsx
    
    def _extract_component_name_from_ast(self, root_node, source_code: str) -> Optional[str]:
        """Extract component name using AST traversal."""
        def traverse(node):
            # Function declarations
            if node.type == 'function_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = source_code[name_node.start_byte:name_node.end_byte]
                    if name and name[0].isupper():
                        return name
            
            # Variable declarations with arrow functions
            elif node.type == 'variable_declarator':
                name_node = node.child_by_field_name('name')
                value_node = node.child_by_field_name('value')
                
                if name_node and value_node:
                    name = source_code[name_node.start_byte:name_node.end_byte]
                    if name and name[0].isupper():
                        # Check for different patterns
                        if value_node.type in ['arrow_function', 'function_expression']:
                            return name
                        elif value_node.type == 'call_expression':
                            # Check for React.forwardRef
                            function_node = value_node.child_by_field_name('function')
                            if function_node:
                                function_text = source_code[function_node.start_byte:function_node.end_byte]
                                if 'forwardRef' in function_text:
                                    return name
            
            # Recursively check children
            for child in node.children:
                result = traverse(child)
                if result:
                    return result
            
            return None
        
        return traverse(root_node)
    
    def _extract_props_from_ast(self, root_node, source_code: str) -> List[PropPattern]:
        """Enhanced props extraction using comprehensive AST analysis."""
        props = []
        
        # Strategy 1: Extract from TypeScript interfaces and types
        interface_props = self._extract_props_from_interfaces(root_node, source_code)
        props.extend(interface_props)
        
        # Strategy 2: Extract from function parameters (enhanced)
        function_props = self._extract_props_from_function_params(root_node, source_code)
        props.extend(function_props)
        
        # Strategy 3: Extract from prop usage within component
        usage_props = self._extract_props_from_usage(root_node, source_code)
        props.extend(usage_props)
        
        # Strategy 4: Extract from JSDoc comments
        jsdoc_props = self._extract_props_from_jsdoc(source_code)
        props.extend(jsdoc_props)
        
        # Deduplicate props by name while preserving most complete info
        props = self._deduplicate_and_merge_props(props)
        
        # If still no props found, use enhanced regex fallback
        if not props:
            props = self._extract_props_enhanced_regex(source_code)
        
        return props
    
    def _extract_props_from_interfaces(self, root_node, source_code: str) -> List[PropPattern]:
        """Extract props from TypeScript interfaces and type definitions."""
        props = []
        
        def traverse(node):
            # TypeScript interface declarations
            if node.type == 'interface_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    interface_name = source_code[name_node.start_byte:name_node.end_byte]
                    # Look for Props-related interfaces
                    if 'props' in interface_name.lower():
                        # Check if this interface is used in the component
                        if self._is_interface_used_in_component(interface_name, source_code):
                            body_node = node.child_by_field_name('body')
                            if body_node:
                                interface_props = self._parse_interface_body(body_node, source_code)
                                props.extend(interface_props)
            
            # Type alias declarations
            elif node.type == 'type_alias_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    type_name = source_code[name_node.start_byte:name_node.end_byte]
                    if 'props' in type_name.lower():
                        # Check if this type is used in the component
                        if self._is_interface_used_in_component(type_name, source_code):
                            value_node = node.child_by_field_name('value')
                            if value_node and value_node.type == 'object_type':
                                type_props = self._parse_object_type(value_node, source_code)
                                props.extend(type_props)
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
        return props
    
    def _is_interface_used_in_component(self, interface_name: str, source_code: str) -> bool:
        """Check if an interface is actually used in the component function."""
        # Look for the interface being used in function signatures
        patterns = [
            # React.forwardRef<Element, InterfaceName>
            rf'React\.forwardRef<[^,]+,\s*{interface_name}>',
            # function ComponentName(props: InterfaceName)
            rf'function\s+\w+\s*\(\s*props\s*:\s*{interface_name}',
            # = (props: InterfaceName)
            rf'=\s*\(\s*props\s*:\s*{interface_name}',
            # Component<InterfaceName>
            rf'\w+<{interface_name}>',
        ]
        
        import re
        for pattern in patterns:
            if re.search(pattern, source_code):
                return True
        
        return False
    
    def _extract_props_from_type_reference(self, type_name: str, source_code: str) -> List[PropPattern]:
        """Extract props from a type reference by finding its definition."""
        import re
        props = []
        
        # Clean up the type name (remove whitespace, generics)
        clean_type = re.sub(r'<.*>', '', type_name).strip()
        
        # Look for interface definition
        interface_pattern = rf'(?:interface|type)\s+{clean_type}\s*(?:extends\s+[^{{]+)?\s*=?\s*\{{([^}}]+)\}}'
        matches = re.finditer(interface_pattern, source_code, re.DOTALL)
        
        for match in matches:
            interface_body = match.group(1)
            
            # Extract properties from the interface body
            prop_pattern = r'(\w+)\??\s*:\s*([^;,\n]+)'
            prop_matches = re.finditer(prop_pattern, interface_body)
            
            for prop_match in prop_matches:
                prop_name = prop_match.group(1)
                prop_type = prop_match.group(2).strip()
                is_optional = '?' in prop_match.group(0)
                
                props.append(PropPattern(
                    name=prop_name,
                    type_annotation=prop_type,
                    is_optional=is_optional,
                    is_destructured=False
                ))
        
        return props
    
    def _parse_interface_body(self, body_node, source_code: str) -> List[PropPattern]:
        """Parse interface body to extract property definitions."""
        props = []
        
        for child in body_node.children:
            if child.type == 'property_signature':
                prop = self._parse_property_signature(child, source_code)
                if prop:
                    props.append(prop)
        
        return props
    
    def _parse_object_type(self, object_node, source_code: str) -> List[PropPattern]:
        """Parse object type to extract property definitions."""
        props = []
        
        for child in object_node.children:
            if child.type == 'property_signature':
                prop = self._parse_property_signature(child, source_code)
                if prop:
                    props.append(prop)
        
        return props
    
    def _parse_property_signature(self, prop_node, source_code: str) -> Optional[PropPattern]:
        """Parse a property signature to extract prop information."""
        name_node = prop_node.child_by_field_name('name')
        if not name_node:
            return None
        
        prop_name = source_code[name_node.start_byte:name_node.end_byte]
        
        # Check if optional (ends with ?)
        is_optional = False
        if prop_node.children:
            for child in prop_node.children:
                if child.type == '?' or '?' in source_code[child.start_byte:child.end_byte]:
                    is_optional = True
                    break
        
        # Extract type annotation
        type_annotation = None
        type_node = prop_node.child_by_field_name('type')
        if type_node:
            type_annotation = source_code[type_node.start_byte:type_node.end_byte]
        
        return PropPattern(
            name=prop_name,
            type_annotation=type_annotation,
            is_optional=is_optional,
            is_destructured=False
        )
    
    def _extract_props_from_function_params(self, root_node, source_code: str) -> List[PropPattern]:
        """Enhanced function parameter props extraction."""
        props = []
        
        def traverse(node):
            # Function declarations and arrow functions
            if node.type in ['function_declaration', 'arrow_function', 'function_expression']:
                params_node = node.child_by_field_name('parameters')
                if params_node:
                    for param in params_node.children:
                        if param.type in ['required_parameter', 'optional_parameter']:
                            extracted_props = self._parse_enhanced_parameter_node(param, source_code)
                            props.extend(extracted_props)
            
            # React.forwardRef calls
            elif node.type == 'call_expression':
                function_node = node.child_by_field_name('function')
                if function_node:
                    function_text = source_code[function_node.start_byte:function_node.end_byte]
                    if 'forwardRef' in function_text:
                        # Look inside the forwardRef arguments for the actual component function
                        args_node = node.child_by_field_name('arguments')
                        if args_node:
                            for arg in args_node.children:
                                if arg.type in ['function_expression', 'arrow_function']:
                                    # Recursively traverse the inner function
                                    traverse(arg)
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
        return props
    
    def _parse_enhanced_parameter_node(self, param_node, source_code: str) -> List[PropPattern]:
        """Enhanced parameter node parsing with better pattern recognition."""
        props = []
        
        # Get pattern node (the destructuring or identifier)
        pattern_node = param_node.child_by_field_name('pattern')
        if not pattern_node:
            pattern_node = param_node
        
        # Handle object patterns (destructuring)
        if pattern_node.type == 'object_pattern':
            props.extend(self._parse_object_pattern_enhanced(pattern_node, source_code))
        
        # Handle typed parameters
        elif pattern_node.type == 'identifier':
            # Single props parameter with type annotation
            param_name = source_code[pattern_node.start_byte:pattern_node.end_byte]
            if 'props' in param_name.lower():
                type_annotation = None
                type_node = param_node.child_by_field_name('type')
                if type_node:
                    type_annotation = source_code[type_node.start_byte:type_node.end_byte]
                    
                    # If the type annotation is a Props interface, extract its properties
                    if type_annotation and 'props' in type_annotation.lower():
                        # Try to find the interface definition and extract props from it
                        interface_props = self._extract_props_from_type_reference(type_annotation, source_code)
                        if interface_props:
                            props.extend(interface_props)
                        else:
                            # Fallback: create a generic props entry
                            props.append(PropPattern(
                                name=param_name,
                                type_annotation=type_annotation,
                                is_destructured=False
                            ))
                    else:
                        props.append(PropPattern(
                            name=param_name,
                            type_annotation=type_annotation,
                            is_destructured=False
                        ))
        
        return props
    
    def _parse_object_pattern_enhanced(self, pattern_node, source_code: str) -> List[PropPattern]:
        """Enhanced object pattern parsing for destructured props."""
        props = []
        
        for child in pattern_node.children:
            if child.type == 'object_assignment_pattern':
                # Handle { prop = defaultValue }
                key_node = child.child_by_field_name('left')
                value_node = child.child_by_field_name('right')
                
                if key_node:
                    prop_name = source_code[key_node.start_byte:key_node.end_byte]
                    default_value = None
                    if value_node:
                        default_value = source_code[value_node.start_byte:value_node.end_byte]
                    
                    props.append(PropPattern(
                        name=prop_name,
                        default_value=default_value,
                        is_destructured=True
                    ))
            
            elif child.type == 'shorthand_property_identifier_pattern':
                # Handle { prop }
                prop_name = source_code[child.start_byte:child.end_byte]
                props.append(PropPattern(
                    name=prop_name,
                    is_destructured=True
                ))
            
            elif child.type == 'rest_pattern':
                # Handle { ...rest }
                rest_node = child.child_by_field_name('argument')
                if rest_node:
                    rest_name = source_code[rest_node.start_byte:rest_node.end_byte]
                    props.append(PropPattern(
                        name=rest_name,
                        is_destructured=True,
                        type_annotation='...rest'
                    ))
        
        return props
    
    def _extract_props_from_usage(self, root_node, source_code: str) -> List[PropPattern]:
        """Extract props from their usage within the component JSX."""
        props = []
        prop_names = set()
        
        def traverse(node):
            # Look for props.* usage
            if node.type == 'member_expression':
                object_node = node.child_by_field_name('object')
                property_node = node.child_by_field_name('property')
                
                if (object_node and property_node and 
                    source_code[object_node.start_byte:object_node.end_byte] == 'props'):
                    prop_name = source_code[property_node.start_byte:property_node.end_byte]
                    if prop_name not in prop_names:
                        prop_names.add(prop_name)
                        props.append(PropPattern(
                            name=prop_name,
                            is_destructured=False
                        ))
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
        return props
    
    def _extract_props_from_jsdoc(self, source_code: str) -> List[PropPattern]:
        """Extract props from JSDoc comments."""
        import re
        props = []
        
        # Look for @param annotations
        jsdoc_pattern = r'/\*\*[\s\S]*?\*/'
        jsdoc_matches = re.finditer(jsdoc_pattern, source_code)
        
        for match in jsdoc_matches:
            jsdoc_content = match.group(0)
            
            # Extract @param entries
            param_pattern = r'@param\s+\{([^}]+)\}\s+(\w+)(?:\s+-\s*(.+))?'
            param_matches = re.finditer(param_pattern, jsdoc_content)
            
            for param_match in param_matches:
                type_annotation = param_match.group(1)
                prop_name = param_match.group(2)
                description = param_match.group(3) if param_match.group(3) else None
                
                props.append(PropPattern(
                    name=prop_name,
                    type_annotation=type_annotation,
                    is_destructured=False
                ))
        
        return props
    
    def _deduplicate_and_merge_props(self, props: List[PropPattern]) -> List[PropPattern]:
        """Deduplicate props by name and merge information."""
        prop_dict = {}
        
        for prop in props:
            if prop.name in prop_dict:
                # Merge information, preferring more complete data
                existing = prop_dict[prop.name]
                
                # Prefer type annotation if not already set
                if not existing.type_annotation and prop.type_annotation:
                    existing.type_annotation = prop.type_annotation
                
                # Prefer default value if not already set
                if not existing.default_value and prop.default_value:
                    existing.default_value = prop.default_value
                
                # Update optional status
                if prop.is_optional:
                    existing.is_optional = True
                
                # Update destructured status
                if prop.is_destructured:
                    existing.is_destructured = True
            else:
                prop_dict[prop.name] = prop
        
        return list(prop_dict.values())
    
    def _extract_props_enhanced_regex(self, content: str) -> List[PropPattern]:
        """Enhanced regex fallback for prop extraction."""
        import re
        props = []
        
        # Pattern 1: TypeScript interface definitions
        interface_pattern = r'(?:interface|type)\s+(\w*[Pp]rops\w*)\s*=?\s*\{([^}]+)\}'
        interface_matches = re.finditer(interface_pattern, content, re.DOTALL)
        
        for match in interface_matches:
            interface_body = match.group(2)
            # Extract properties
            prop_pattern = r'(\w+)\??\s*:\s*([^;,\n]+)'
            prop_matches = re.finditer(prop_pattern, interface_body)
            
            for prop_match in prop_matches:
                prop_name = prop_match.group(1)
                prop_type = prop_match.group(2).strip()
                is_optional = '?' in prop_match.group(0)
                
                props.append(PropPattern(
                    name=prop_name,
                    type_annotation=prop_type,
                    is_optional=is_optional,
                    is_destructured=False
                ))
        
        # Pattern 2: Enhanced destructured props in function parameters
        destructure_patterns = [
            r'function\s+\w+\s*\(\s*\{\s*([^}]+)\s*\}\s*(?::\s*(\w+))?',
            r'=\s*\(\s*\{\s*([^}]+)\s*\}\s*(?::\s*(\w+))?\s*\)',
            r'const\s+\w+\s*=\s*\(\s*\{\s*([^}]+)\s*\}\s*(?::\s*(\w+))?',
        ]
        
        for pattern in destructure_patterns:
            matches = re.finditer(pattern, content, re.DOTALL)
            for match in matches:
                prop_list = match.group(1)
                type_annotation = match.group(2) if len(match.groups()) > 1 else None
                
                # Enhanced prop parsing with default values
                prop_pattern = r'(\w+)(?:\s*=\s*([^,}]+))?'
                prop_matches = re.finditer(prop_pattern, prop_list)
                
                for prop_match in prop_matches:
                    prop_name = prop_match.group(1).strip()
                    default_value = prop_match.group(2).strip() if prop_match.group(2) else None
                    
                    if prop_name and prop_name not in ['children', 'className', 'style', 'key', 'ref']:
                        props.append(PropPattern(
                            name=prop_name,
                            default_value=default_value,
                            type_annotation=type_annotation,
                            is_destructured=True
                        ))
        
        # Pattern 3: props.* usage patterns
        props_usage_pattern = r'props\.(\w+)'
        usage_matches = re.finditer(props_usage_pattern, content)
        
        existing_names = {prop.name for prop in props}
        for match in usage_matches:
            prop_name = match.group(1)
            if prop_name not in existing_names and prop_name not in ['children', 'className', 'style']:
                props.append(PropPattern(
                    name=prop_name,
                    is_destructured=False
                ))
                existing_names.add(prop_name)
        
        return props
    
    # Removed old _parse_parameter_node method - replaced by enhanced methods above
    
    def _extract_imports_from_ast(self, root_node, source_code: str) -> List[str]:
        """Extract imports using AST."""
        imports = []
        
        def traverse(node):
            if node.type == 'import_statement':
                import_text = source_code[node.start_byte:node.end_byte]
                imports.append(import_text.strip())
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
        return imports
    
    def _extract_styling_patterns_from_ast(self, root_node, source_code: str) -> List[str]:
        """Extract styling patterns using AST."""
        patterns = set()
        
        # Also use regex fallback for better coverage
        regex_patterns = self._extract_styling_patterns_regex(source_code)
        patterns.update(regex_patterns)
        
        def traverse(node):
            # Call expressions (function calls)
            if node.type == 'call_expression':
                function_node = node.child_by_field_name('function')
                if function_node:
                    function_name = source_code[function_node.start_byte:function_node.end_byte]
                    
                    # Check for styling utilities
                    if any(util in function_name for util in self.styling_utils):
                        patterns.add(function_name.split('(')[0])  # Clean function name
            
            # JSX attributes
            elif node.type == 'jsx_attribute':
                name_node = node.child_by_field_name('name')
                if name_node:
                    attr_name = source_code[name_node.start_byte:name_node.end_byte]
                    if attr_name == 'className':
                        value_node = node.child_by_field_name('value')
                        if value_node:
                            value_content = source_code[value_node.start_byte:value_node.end_byte]
                            if self._contains_tailwind_classes(value_content):
                                patterns.add('tailwind_classes')
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
        return list(patterns)
    
    def _extract_styling_patterns_regex(self, content: str) -> List[str]:
        """Regex fallback for styling pattern extraction."""
        import re
        patterns = []
        
        # Look for styling utilities
        for util in self.styling_utils:
            if re.search(rf'\b{util}\s*\(', content):
                patterns.append(util)
        
        # Look for className with Tailwind classes
        if re.search(r'className.*=.*[\'"][^\'\"]*(?:bg-|text-|p-|m-|flex|grid)', content):
            patterns.append('tailwind_classes')
        
        # Look for styled-components
        if re.search(r'styled\.\w+', content):
            patterns.append('styled_components')
        
        return patterns
    
    def _contains_tailwind_classes(self, content: str) -> bool:
        """Check if content contains Tailwind CSS classes."""
        tailwind_patterns = [
            'bg-', 'text-', 'p-', 'm-', 'w-', 'h-', 'flex', 'grid',
            'rounded', 'shadow', 'border', 'hover:', 'focus:', 'md:', 'lg:'
        ]
        return any(pattern in content for pattern in tailwind_patterns)
    
    def _determine_export_type_from_ast(self, root_node, source_code: str) -> str:
        """Determine export type using AST."""
        has_default_export = False
        has_named_export = False
        
        def traverse(node):
            nonlocal has_default_export, has_named_export
            
            if node.type == 'export_statement':
                export_text = source_code[node.start_byte:node.end_byte]
                if 'default' in export_text:
                    has_default_export = True
                else:
                    has_named_export = True
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
        
        if has_default_export and has_named_export:
            return "both"
        elif has_default_export:
            return "default"
        elif has_named_export:
            return "named"
        else:
            return "default"
    
    def _is_functional_component(self, root_node, source_code: str) -> bool:
        """Determine if component is functional (vs class)."""
        # Look for class declarations
        def traverse(node):
            if node.type == 'class_declaration':
                # Check if it extends React.Component
                superclass_node = node.child_by_field_name('superclass')
                if superclass_node:
                    superclass_name = source_code[superclass_node.start_byte:superclass_node.end_byte]
                    if 'Component' in superclass_name:
                        return False  # Class component
            
            for child in node.children:
                result = traverse(child)
                if result is False:
                    return False
            
            return True
        
        return traverse(root_node)
    
    def _fallback_regex_analysis(self, file_path: Path, source_code: str, has_typescript: bool) -> Optional[ComponentPattern]:
        """Fallback to regex-based analysis if Tree-sitter fails."""
        # Simple fallback without external dependencies
        component_name = self._extract_component_name_regex(source_code)
        if not component_name:
            return None
        
        return ComponentPattern(
            name=component_name,
            file_path=str(file_path),
            is_functional=True,
            props=self._extract_props_enhanced_regex(source_code),
            imports=[],
            styling_patterns=[],
            export_type="default",
            has_typescript=has_typescript
        )
    
    def _extract_component_name_regex(self, source_code: str) -> Optional[str]:
        """Extract component name using regex fallback."""
        import re
        
        patterns = [
            r'export\s+default\s+function\s+(\w+)',
            r'export\s+function\s+(\w+)',
            r'export\s+default\s+(\w+)',
            r'const\s+(\w+)\s*=.*=>'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, source_code)
            if match:
                name = match.group(1)
                if name and name[0].isupper():
                    return name
        
        return None
    
    def _extract_common_patterns(self, components: List[ComponentPattern]) -> Dict[str, Any]:
        """Extract common patterns across components."""
        if not components:
            return {}
        
        # Most common prop names
        prop_names = defaultdict(int)
        for comp in components:
            for prop in comp.props:
                prop_names[prop.name] += 1
        
        # Most common imports
        import_patterns = defaultdict(int)
        for comp in components:
            for imp in comp.imports:
                # Extract module name
                if 'from' in imp:
                    module = imp.split('from')[-1].strip().strip('"\'')
                    import_patterns[module] += 1
        
        # Common styling patterns
        styling_frequency = defaultdict(int)
        for comp in components:
            for pattern in comp.styling_patterns:
                styling_frequency[pattern] += 1
        
        return {
            "common_props": dict(sorted(prop_names.items(), key=lambda x: x[1], reverse=True)[:10]),
            "common_imports": dict(sorted(import_patterns.items(), key=lambda x: x[1], reverse=True)[:10]),
            "common_styling": dict(sorted(styling_frequency.items(), key=lambda x: x[1], reverse=True)[:10]),
        }


def analyze_project_treesitter(project_path: str) -> Dict[str, Any]:
    """Convenience function using Tree-sitter analyzer."""
    if not TREE_SITTER_AVAILABLE:
        raise ImportError("Tree-sitter not available, use SimpleASTAnalyzer instead")
    
    analyzer = TreeSitterAnalyzer()
    return analyzer.analyze_project(project_path)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
        try:
            result = analyze_project_treesitter(project_path)
            print(json.dumps(result, indent=2))
        except ImportError as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        print("Usage: python treesitter_analyzer.py <project_path>")