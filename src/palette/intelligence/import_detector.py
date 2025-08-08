"""
Import Detection System for generated React components.
Analyzes code to detect missing imports and suggests appropriate import statements.
"""

import ast
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from ..errors.decorators import handle_errors


class ImportType(Enum):
    """Types of imports that can be detected."""
    REACT_CORE = "react_core"           # React, useState, useEffect, etc.
    REACT_TYPES = "react_types"         # React.FC, JSX.Element, etc.
    UI_LIBRARY = "ui_library"           # Chakra UI, Material-UI, etc.
    UTILITY_LIBRARY = "utility_library" # clsx, classnames, etc.
    CUSTOM_COMPONENT = "custom_component" # Local project components
    NODE_MODULE = "node_module"         # Third-party packages
    RELATIVE_IMPORT = "relative_import" # ./Component, ../utils


class ImportSource(Enum):
    """Sources where imports can come from."""
    REACT = "react"
    REACT_TYPES = "@types/react"
    CHAKRA_UI = "@chakra-ui/react"
    MATERIAL_UI = "@mui/material"
    ANT_DESIGN = "antd"
    MANTINE = "@mantine/core"
    HEADLESS_UI = "@headlessui/react"
    SHADCN_UI = "@/components/ui"
    CLSX = "clsx"
    CLASSNAMES = "classnames"
    TAILWIND_MERGE = "tailwind-merge"
    LUCIDE_REACT = "lucide-react"


@dataclass
class ImportSuggestion:
    """A suggested import statement."""
    name: str                    # Component/function name (e.g., "Button")
    source: str                  # Import source (e.g., "@chakra-ui/react")
    import_type: ImportType      # Type of import
    is_default: bool = False     # Whether it's a default import
    is_type_import: bool = False # Whether it's a type-only import
    confidence: float = 1.0      # Confidence in this suggestion (0-1)
    line_numbers: List[int] = field(default_factory=list)  # Lines where used
    alternatives: List[str] = field(default_factory=list)  # Alternative sources
    reasoning: str = ""          # Why this import is suggested
    
    def to_import_statement(self) -> str:
        """Generate the actual import statement."""
        if self.is_type_import:
            if self.is_default:
                return f"import type {self.name} from '{self.source}'"
            else:
                return f"import type {{ {self.name} }} from '{self.source}'"
        else:
            if self.is_default:
                return f"import {self.name} from '{self.source}'"
            else:
                return f"import {{ {self.name} }} from '{self.source}'"


@dataclass
class ImportAnalysisResult:
    """Result of import analysis."""
    missing_imports: List[ImportSuggestion] = field(default_factory=list)
    existing_imports: Dict[str, str] = field(default_factory=dict)  # name -> source
    unused_imports: List[str] = field(default_factory=list)
    conflicts: List[Tuple[str, List[str]]] = field(default_factory=list)  # name -> conflicting sources
    analysis_confidence: float = 1.0
    errors: List[str] = field(default_factory=list)


class ImportDetector:
    """
    Advanced import detection system that analyzes React component code
    and suggests missing imports with high accuracy.
    """
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self._initialize_detection_patterns()
        self._load_project_dependencies()
    
    def _initialize_detection_patterns(self):
        """Initialize patterns for detecting different types of imports."""
        
        # React core patterns
        self.react_patterns = {
            'React': [r'\bReact\.', r'<[A-Z]'],  # React.Fragment, JSX usage
            'useState': [r'\buseState\s*\('],
            'useEffect': [r'\buseEffect\s*\('],
            'useContext': [r'\buseContext\s*\('],
            'useCallback': [r'\buseCallback\s*\('],
            'useMemo': [r'\buseMemo\s*\('],
            'useRef': [r'\buseRef\s*\('],
            'useReducer': [r'\buseReducer\s*\('],
            'Component': [r'extends\s+Component'],
            'Fragment': [r'<Fragment[>\s]', r'<React\.Fragment[>\s]'],
        }
        
        # React TypeScript patterns
        self.react_types_patterns = {
            'FC': [r':\s*React\.FC', r':\s*FC\s*<'],
            'ComponentProps': [r':\s*React\.ComponentProps', r':\s*ComponentProps\s*<'],
            'ReactNode': [r':\s*React\.ReactNode', r':\s*ReactNode'],
            'JSX': [r':\s*JSX\.Element'],
            'MouseEvent': [r':\s*React\.MouseEvent', r':\s*MouseEvent\s*<'],
            'ChangeEvent': [r':\s*React\.ChangeEvent', r':\s*ChangeEvent\s*<'],
        }
        
        # UI Library patterns
        self.ui_library_patterns = {
            ImportSource.CHAKRA_UI.value: {
                'Box': [r'<Box[>\s]'],
                'Button': [r'<Button[>\s]'],
                'Text': [r'<Text[>\s]'],
                'Input': [r'<Input[>\s]'],
                'VStack': [r'<VStack[>\s]'],
                'HStack': [r'<HStack[>\s]'],
                'Flex': [r'<Flex[>\s]'],
                'Card': [r'<Card[>\s]'],
                'CardBody': [r'<CardBody[>\s]'],
                'CardHeader': [r'<CardHeader[>\s]'],
                'useColorModeValue': [r'\buseColorModeValue\s*\('],
                'useDisclosure': [r'\buseDisclosure\s*\('],
            },
            ImportSource.MATERIAL_UI.value: {
                'Button': [r'<Button[>\s]'],
                'TextField': [r'<TextField[>\s]'],
                'Typography': [r'<Typography[>\s]'],
                'Paper': [r'<Paper[>\s]'],
                'Card': [r'<Card[>\s]'],
                'CardContent': [r'<CardContent[>\s]'],
                'CardActions': [r'<CardActions[>\s]'],
                'Grid': [r'<Grid[>\s]'],
                'Box': [r'<Box[>\s]'],
                'Stack': [r'<Stack[>\s]'],
            },
            ImportSource.ANT_DESIGN.value: {
                'Button': [r'<Button[>\s]'],
                'Input': [r'<Input[>\s]'],
                'Card': [r'<Card[>\s]'],
                'Row': [r'<Row[>\s]'],
                'Col': [r'<Col[>\s]'],
                'Space': [r'<Space[>\s]'],
                'Typography': [r'<Typography[>\s]'],
                'Form': [r'<Form[>\s]'],
            },
        }
        
        # Utility patterns
        self.utility_patterns = {
            'clsx': [r'\bclsx\s*\(', r'\bcx\s*\('],
            'classnames': [r'\bclassnames\s*\(', r'\bcn\s*\('],
            'cn': [r'\bcn\s*\('],  # Common shadcn/ui utility
            'twMerge': [r'\btwMerge\s*\('],
        }
    
    def _load_project_dependencies(self):
        """Load project dependencies from package.json."""
        self.available_packages = set()
        package_json_path = self.project_path / "package.json"
        
        if package_json_path.exists():
            try:
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                
                # Collect all dependencies
                for dep_type in ['dependencies', 'devDependencies', 'peerDependencies']:
                    deps = package_data.get(dep_type, {})
                    self.available_packages.update(deps.keys())
                    
            except (json.JSONDecodeError, FileNotFoundError):
                pass
    
    @handle_errors(reraise=True)
    def analyze_imports(self, code: str, file_path: str = "Component.tsx") -> ImportAnalysisResult:
        """
        Analyze code for missing imports and return suggestions.
        
        Args:
            code: The component code to analyze
            file_path: Path where the component will be saved
            
        Returns:
            Comprehensive import analysis result
        """
        result = ImportAnalysisResult()
        
        try:
            # Extract existing imports
            result.existing_imports = self._extract_existing_imports(code)
            
            # Detect missing React core imports
            react_suggestions = self._detect_react_imports(code, result.existing_imports)
            result.missing_imports.extend(react_suggestions)
            
            # Detect missing React TypeScript imports
            if file_path.endswith(('.tsx', '.ts')):
                react_types_suggestions = self._detect_react_types_imports(code, result.existing_imports)
                result.missing_imports.extend(react_types_suggestions)
            
            # Detect missing UI library imports
            ui_suggestions = self._detect_ui_library_imports(code, result.existing_imports)
            result.missing_imports.extend(ui_suggestions)
            
            # Detect missing utility imports
            utility_suggestions = self._detect_utility_imports(code, result.existing_imports)
            result.missing_imports.extend(utility_suggestions)
            
            # Detect conflicts and duplicates
            result.conflicts = self._detect_import_conflicts(result.missing_imports)
            
            # Remove duplicates and sort by confidence
            result.missing_imports = self._deduplicate_suggestions(result.missing_imports)
            result.missing_imports.sort(key=lambda x: (x.confidence, x.name), reverse=True)
            
            # Calculate overall confidence
            if result.missing_imports:
                result.analysis_confidence = sum(s.confidence for s in result.missing_imports) / len(result.missing_imports)
            
        except Exception as e:
            result.errors.append(f"Import analysis failed: {str(e)}")
            result.analysis_confidence = 0.0
        
        return result
    
    def _extract_existing_imports(self, code: str) -> Dict[str, str]:
        """Extract existing import statements from code."""
        existing = {}
        
        # Regex patterns for different import styles
        import_patterns = [
            # import React from 'react'
            r"import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]",
            # import { Button, Input } from '@chakra-ui/react'
            r"import\s+\{\s*([^}]+)\s*\}\s+from\s+['\"]([^'\"]+)['\"]",
            # import * as React from 'react'
            r"import\s+\*\s+as\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]",
            # import type { FC } from 'react'
            r"import\s+type\s+\{\s*([^}]+)\s*\}\s+from\s+['\"]([^'\"]+)['\"]",
        ]
        
        for pattern in import_patterns:
            matches = re.finditer(pattern, code, re.MULTILINE)
            for match in matches:
                imported_items = match.group(1)
                source = match.group(2)
                
                # Handle named imports (comma-separated)
                if '{' in imported_items or ',' in imported_items:
                    # Split and clean named imports
                    items = [item.strip() for item in imported_items.split(',')]
                    for item in items:
                        # Handle aliases (e.g., "Button as CustomButton")
                        if ' as ' in item:
                            item = item.split(' as ')[0].strip()
                        existing[item] = source
                else:
                    # Single import
                    existing[imported_items] = source
        
        return existing
    
    def _detect_react_imports(self, code: str, existing: Dict[str, str]) -> List[ImportSuggestion]:
        """Detect missing React core imports."""
        suggestions = []
        
        for name, patterns in self.react_patterns.items():
            if name in existing:
                continue
                
            # Check if any pattern matches
            used = False
            line_numbers = []
            
            for pattern in patterns:
                matches = list(re.finditer(pattern, code, re.MULTILINE))
                if matches:
                    used = True
                    line_numbers.extend([code[:m.start()].count('\n') + 1 for m in matches])
            
            if used:
                suggestions.append(ImportSuggestion(
                    name=name,
                    source="react",
                    import_type=ImportType.REACT_CORE,
                    is_default=(name == 'React'),
                    confidence=0.95,
                    line_numbers=sorted(set(line_numbers)),
                    reasoning=f"Used {len(line_numbers)} times in component"
                ))
        
        return suggestions
    
    def _detect_react_types_imports(self, code: str, existing: Dict[str, str]) -> List[ImportSuggestion]:
        """Detect missing React TypeScript imports."""
        suggestions = []
        
        for name, patterns in self.react_types_patterns.items():
            if name in existing:
                continue
                
            used = False
            line_numbers = []
            
            for pattern in patterns:
                matches = list(re.finditer(pattern, code, re.MULTILINE))
                if matches:
                    used = True
                    line_numbers.extend([code[:m.start()].count('\n') + 1 for m in matches])
            
            if used:
                suggestions.append(ImportSuggestion(
                    name=name,
                    source="react",
                    import_type=ImportType.REACT_TYPES,
                    is_type_import=True,
                    confidence=0.9,
                    line_numbers=sorted(set(line_numbers)),
                    reasoning=f"TypeScript type used {len(line_numbers)} times"
                ))
        
        return suggestions
    
    def _detect_ui_library_imports(self, code: str, existing: Dict[str, str]) -> List[ImportSuggestion]:
        """Detect missing UI library imports."""
        suggestions = []
        
        for source, components in self.ui_library_patterns.items():
            # Check if this UI library is available in the project
            if source not in self.available_packages:
                continue
                
            for name, patterns in components.items():
                if name in existing:
                    continue
                    
                used = False
                line_numbers = []
                
                for pattern in patterns:
                    matches = list(re.finditer(pattern, code, re.MULTILINE))
                    if matches:
                        used = True
                        line_numbers.extend([code[:m.start()].count('\n') + 1 for m in matches])
                
                if used:
                    # Determine confidence based on UI library usage context
                    confidence = 0.9
                    if source == ImportSource.CHAKRA_UI.value and 'className=' in code and 'bg-' in code:
                        confidence = 0.7  # Mixed with Tailwind, lower confidence
                    
                    suggestions.append(ImportSuggestion(
                        name=name,
                        source=source,
                        import_type=ImportType.UI_LIBRARY,
                        confidence=confidence,
                        line_numbers=sorted(set(line_numbers)),
                        reasoning=f"{source} component used {len(line_numbers)} times"
                    ))
        
        return suggestions
    
    def _detect_utility_imports(self, code: str, existing: Dict[str, str]) -> List[ImportSuggestion]:
        """Detect missing utility library imports."""
        suggestions = []
        
        for name, patterns in self.utility_patterns.items():
            if name in existing:
                continue
                
            used = False
            line_numbers = []
            
            for pattern in patterns:
                matches = list(re.finditer(pattern, code, re.MULTILINE))
                if matches:
                    used = True
                    line_numbers.extend([code[:m.start()].count('\n') + 1 for m in matches])
            
            if used:
                # Determine source based on available packages
                source = None
                if name in ['clsx', 'cx'] and 'clsx' in self.available_packages:
                    source = 'clsx'
                elif name in ['classnames', 'cn'] and 'classnames' in self.available_packages:
                    source = 'classnames'
                elif name == 'cn':
                    # Common shadcn/ui pattern
                    source = '@/lib/utils'
                elif name == 'twMerge' and 'tailwind-merge' in self.available_packages:
                    source = 'tailwind-merge'
                
                if source:
                    suggestions.append(ImportSuggestion(
                        name=name,
                        source=source,
                        import_type=ImportType.UTILITY_LIBRARY,
                        confidence=0.85,
                        line_numbers=sorted(set(line_numbers)),
                        reasoning=f"Utility function used {len(line_numbers)} times"
                    ))
        
        return suggestions
    
    def _detect_import_conflicts(self, suggestions: List[ImportSuggestion]) -> List[Tuple[str, List[str]]]:
        """Detect conflicts between import suggestions."""
        conflicts = []
        name_to_sources = {}
        
        # Group suggestions by name
        for suggestion in suggestions:
            if suggestion.name not in name_to_sources:
                name_to_sources[suggestion.name] = []
            name_to_sources[suggestion.name].append(suggestion.source)
        
        # Find conflicts (same name from different sources)
        for name, sources in name_to_sources.items():
            if len(set(sources)) > 1:
                conflicts.append((name, list(set(sources))))
        
        return conflicts
    
    def _deduplicate_suggestions(self, suggestions: List[ImportSuggestion]) -> List[ImportSuggestion]:
        """Remove duplicate suggestions, keeping the highest confidence one."""
        seen = {}
        deduplicated = []
        
        for suggestion in suggestions:
            key = (suggestion.name, suggestion.source)
            
            if key not in seen or suggestion.confidence > seen[key].confidence:
                seen[key] = suggestion
        
        return list(seen.values())
    
    @handle_errors(reraise=True)  
    def get_import_suggestions_summary(self, suggestions: List[ImportSuggestion]) -> str:
        """Generate a human-readable summary of import suggestions."""
        if not suggestions:
            return "No missing imports detected."
        
        summary_lines = [f"Found {len(suggestions)} missing imports:"]
        
        # Group by source
        by_source = {}
        for suggestion in suggestions:
            if suggestion.source not in by_source:
                by_source[suggestion.source] = []
            by_source[suggestion.source].append(suggestion.name)
        
        for source, names in by_source.items():
            names_str = ", ".join(sorted(names))
            summary_lines.append(f"  • {names_str} from '{source}'")
        
        return "\n".join(summary_lines)
    
    def apply_import_suggestions(self, code: str, suggestions: List[ImportSuggestion]) -> str:
        """
        Apply import suggestions to code by adding import statements.
        
        Args:
            code: Original code
            suggestions: List of import suggestions to apply
            
        Returns:
            Code with import statements added
        """
        if not suggestions:
            return code
        
        # Group suggestions by source for cleaner import statements
        by_source = {}
        for suggestion in suggestions:
            if suggestion.source not in by_source:
                by_source[suggestion.source] = {
                    'default': [],
                    'named': [],
                    'type': []
                }
            
            if suggestion.is_type_import:
                by_source[suggestion.source]['type'].append(suggestion.name)
            elif suggestion.is_default:
                by_source[suggestion.source]['default'].append(suggestion.name)
            else:
                by_source[suggestion.source]['named'].append(suggestion.name)
        
        # Generate import statements
        import_statements = []
        for source, imports in by_source.items():
            # Default imports
            for default_import in imports['default']:
                import_statements.append(f"import {default_import} from '{source}';")
            
            # Named imports
            if imports['named']:
                named_imports = ", ".join(sorted(imports['named']))
                import_statements.append(f"import {{ {named_imports} }} from '{source}';")
            
            # Type imports
            if imports['type']:
                type_imports = ", ".join(sorted(imports['type']))
                import_statements.append(f"import type {{ {type_imports} }} from '{source}';")
        
        # Find the position to insert imports (after existing imports or at the top)
        lines = code.split('\n')
        insert_position = 0
        
        # Find the last import line
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') or line.strip().startswith('import{'):
                insert_position = i + 1
        
        # Insert import statements
        for statement in reversed(import_statements):  # Reverse to maintain order
            lines.insert(insert_position, statement)
        
        # Add an empty line after imports if there isn't one
        if insert_position + len(import_statements) < len(lines):
            next_line = lines[insert_position + len(import_statements)]
            if next_line.strip() and not next_line.startswith('import'):
                lines.insert(insert_position + len(import_statements), '')
        
        return '\n'.join(lines)