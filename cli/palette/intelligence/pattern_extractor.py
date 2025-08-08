"""
Project Pattern Extractor.
Extracts code patterns, conventions, and usage examples from existing projects.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set

from ..errors.decorators import handle_errors


@dataclass
class CodePattern:
    """Represents a code pattern found in the project."""
    pattern_type: str  # import, component, styling, naming
    pattern: str
    examples: List[str] = field(default_factory=list)
    frequency: int = 0
    confidence: float = 0.0
    files_found: List[str] = field(default_factory=list)


@dataclass
class PatternAnalysis:
    """Complete pattern analysis results."""
    patterns: Dict[str, List[CodePattern]] = field(default_factory=dict)
    conventions: Dict[str, str] = field(default_factory=dict)
    common_imports: List[str] = field(default_factory=list)
    naming_patterns: Dict[str, str] = field(default_factory=dict)
    file_organization: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProjectPatternExtractor:
    """
    Extracts patterns and conventions from existing project code.
    Used to understand project-specific coding styles and practices.
    """
    
    def __init__(self):
        self._initialize_pattern_matchers()
    
    def _initialize_pattern_matchers(self):
        """Initialize pattern matching regex."""
        
        # Import patterns
        self.import_patterns = {
            'react_imports': re.compile(r'import\s+(?:{[^}]+}|\w+)\s+from\s+["\']react["\']'),
            'component_imports': re.compile(r'import\s+(?:{[^}]+}|\w+)\s+from\s+["\'][^"\']*components?[^"\']*["\']'),
            'utility_imports': re.compile(r'import\s+(?:{[^}]+}|\w+)\s+from\s+["\'][^"\']*(?:utils?|helpers?|lib)[^"\']*["\']'),
            'style_imports': re.compile(r'import\s+[^"\']*\s+from\s+["\'][^"\']*\.(?:css|scss|sass|less)["\']'),
            'relative_imports': re.compile(r'import\s+[^"\']*\s+from\s+["\']\.{1,2}/[^"\']*["\']')
        }
        
        # Component patterns
        self.component_patterns = {
            'function_component': re.compile(r'(?:const|function)\s+(\w+)\s*[=:]\s*(?:\([^)]*\)\s*=>\s*{|\([^)]*\)\s*{|function\s*\([^)]*\)\s*{)'),
            'arrow_component': re.compile(r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>\s*{'),
            'class_component': re.compile(r'class\s+(\w+)\s+extends\s+(?:React\.)?Component'),
            'export_default': re.compile(r'export\s+default\s+(\w+)'),
            'named_export': re.compile(r'export\s+(?:const|function)\s+(\w+)')
        }
        
        # Styling patterns
        self.styling_patterns = {
            'tailwind_classes': re.compile(r'className=["\']([^"\']*(?:bg-|text-|p-|m-|w-|h-|flex|grid)[^"\']*)["\']'),
            'css_modules': re.compile(r'className={styles\.(\w+)}'),
            'styled_components': re.compile(r'const\s+(\w+)\s*=\s*styled\.(\w+)'),
            'inline_styles': re.compile(r'style={{([^}]+)}}'),
            'chakra_props': re.compile(r'(?:bg|color|p|m|fontSize|fontWeight|borderRadius)=["\'{]([^"\'}\s]+)["\'}]')
        }
        
        # Naming patterns
        self.naming_patterns = {
            'component_files': re.compile(r'([A-Z]\w*)\.(?:jsx?|tsx?)$'),
            'hook_files': re.compile(r'(use[A-Z]\w*)\.(?:jsx?|tsx?)$'),
            'page_files': re.compile(r'(page|index)\.(?:jsx?|tsx?)$'),
            'camel_case': re.compile(r'([a-z][a-zA-Z0-9]*)'),
            'pascal_case': re.compile(r'([A-Z][a-zA-Z0-9]*)')
        }
    
    @handle_errors(reraise=True)
    def extract_patterns(self, project_path: str) -> PatternAnalysis:
        """
        Extract patterns from the project.
        
        Args:
            project_path: Path to the project
            
        Returns:
            Comprehensive pattern analysis
        """
        project_path = Path(project_path)
        
        # Find source files
        source_files = self._find_source_files(project_path)
        
        # Extract patterns from each category
        patterns = {}
        patterns['imports'] = self._extract_import_patterns(source_files)
        patterns['components'] = self._extract_component_patterns(source_files)
        patterns['styling'] = self._extract_styling_patterns(source_files)
        patterns['naming'] = self._extract_naming_patterns(source_files)
        
        # Extract conventions
        conventions = self._extract_conventions(source_files)
        
        # Analyze file organization
        file_org = self._analyze_file_organization(project_path)
        
        # Get common imports
        common_imports = self._get_common_imports(patterns['imports'])
        
        # Extract naming patterns
        naming_patterns = self._extract_naming_conventions(source_files)
        
        return PatternAnalysis(
            patterns=patterns,
            conventions=conventions,
            common_imports=common_imports,
            naming_patterns=naming_patterns,
            file_organization=file_org,
            metadata={
                'files_analyzed': len(source_files),
                'project_path': str(project_path),
                'total_patterns': sum(len(pattern_list) for pattern_list in patterns.values()),
                'analysis_timestamp': self._get_timestamp()
            }
        )
    
    def _find_source_files(self, project_path: Path) -> List[Path]:
        """Find relevant source files to analyze."""
        source_files = []
        
        # File patterns to include
        patterns = ["**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx"]
        
        for pattern in patterns:
            files = list(project_path.glob(pattern))
            # Filter out node_modules, build directories, etc.
            filtered_files = [
                f for f in files 
                if not any(exclude in str(f) for exclude in [
                    'node_modules', 'build', 'dist', '.next', 
                    'coverage', '.git', '__pycache__', 'test', 'spec'
                ])
            ]
            source_files.extend(filtered_files[:50])  # Limit for performance
        
        return source_files[:100]  # Cap total files
    
    def _extract_import_patterns(self, source_files: List[Path]) -> List[CodePattern]:
        """Extract import patterns from source files."""
        import_patterns = []
        import_frequency = {}
        
        for file_path in source_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    # Read first 30 lines where imports typically are
                    lines = f.readlines()[:30]
                    content = ''.join(lines)
                
                for pattern_name, regex in self.import_patterns.items():
                    matches = regex.findall(content)
                    for match in matches:
                        import_key = f"{pattern_name}:{match}"
                        if import_key not in import_frequency:
                            import_frequency[import_key] = {
                                'pattern': match,
                                'type': pattern_name,
                                'count': 0,
                                'files': []
                            }
                        import_frequency[import_key]['count'] += 1
                        import_frequency[import_key]['files'].append(str(file_path))
            
            except (UnicodeDecodeError, IOError):
                continue
        
        # Convert to CodePattern objects
        for import_data in import_frequency.values():
            if import_data['count'] >= 2:  # Only include patterns seen multiple times
                pattern = CodePattern(
                    pattern_type='import',
                    pattern=import_data['pattern'],
                    examples=[import_data['pattern']],
                    frequency=import_data['count'],
                    confidence=min(1.0, import_data['count'] / len(source_files)),
                    files_found=import_data['files'][:5]  # Limit examples
                )
                import_patterns.append(pattern)
        
        return sorted(import_patterns, key=lambda x: x.frequency, reverse=True)
    
    def _extract_component_patterns(self, source_files: List[Path]) -> List[CodePattern]:
        """Extract component definition patterns."""
        component_patterns = []
        pattern_frequency = {}
        
        for file_path in source_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                for pattern_name, regex in self.component_patterns.items():
                    matches = regex.findall(content)
                    for match in matches:
                        component_name = match if isinstance(match, str) else match[0]
                        pattern_key = f"{pattern_name}:{component_name}"
                        
                        if pattern_key not in pattern_frequency:
                            pattern_frequency[pattern_key] = {
                                'pattern': pattern_name,
                                'example': component_name,
                                'count': 0,
                                'files': []
                            }
                        pattern_frequency[pattern_key]['count'] += 1
                        pattern_frequency[pattern_key]['files'].append(str(file_path))
            
            except (UnicodeDecodeError, IOError):
                continue
        
        # Convert to CodePattern objects
        for pattern_data in pattern_frequency.values():
            if pattern_data['count'] >= 1:  # Include single occurrences for components
                pattern = CodePattern(
                    pattern_type='component',
                    pattern=pattern_data['pattern'],
                    examples=[pattern_data['example']],
                    frequency=pattern_data['count'],
                    confidence=min(1.0, pattern_data['count'] / 10),  # Normalize
                    files_found=pattern_data['files'][:3]
                )
                component_patterns.append(pattern)
        
        return sorted(component_patterns, key=lambda x: x.frequency, reverse=True)
    
    def _extract_styling_patterns(self, source_files: List[Path]) -> List[CodePattern]:
        """Extract styling patterns from source files."""
        styling_patterns = []
        pattern_frequency = {}
        
        for file_path in source_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                for pattern_name, regex in self.styling_patterns.items():
                    matches = regex.findall(content)
                    for match in matches:
                        pattern_key = f"{pattern_name}:{match}"
                        
                        if pattern_key not in pattern_frequency:
                            pattern_frequency[pattern_key] = {
                                'pattern': pattern_name,
                                'example': match,
                                'count': 0,
                                'files': []
                            }
                        pattern_frequency[pattern_key]['count'] += 1
                        pattern_frequency[pattern_key]['files'].append(str(file_path))
            
            except (UnicodeDecodeError, IOError):
                continue
        
        # Convert to CodePattern objects and filter by frequency
        for pattern_data in pattern_frequency.values():
            if pattern_data['count'] >= 2:  # Only include repeated patterns
                pattern = CodePattern(
                    pattern_type='styling',
                    pattern=pattern_data['pattern'],
                    examples=[pattern_data['example']],
                    frequency=pattern_data['count'],
                    confidence=min(1.0, pattern_data['count'] / 20),
                    files_found=pattern_data['files'][:3]
                )
                styling_patterns.append(pattern)
        
        return sorted(styling_patterns, key=lambda x: x.frequency, reverse=True)
    
    def _extract_naming_patterns(self, source_files: List[Path]) -> List[CodePattern]:
        """Extract naming convention patterns."""
        naming_patterns = []
        
        # Analyze file naming patterns
        file_patterns = {}
        
        for file_path in source_files:
            file_name = file_path.name
            
            for pattern_name, regex in self.naming_patterns.items():
                if regex.search(file_name):
                    if pattern_name not in file_patterns:
                        file_patterns[pattern_name] = {
                            'examples': [],
                            'count': 0
                        }
                    file_patterns[pattern_name]['examples'].append(file_name)
                    file_patterns[pattern_name]['count'] += 1
        
        # Convert to CodePattern objects
        for pattern_name, data in file_patterns.items():
            if data['count'] >= 2:
                pattern = CodePattern(
                    pattern_type='naming',
                    pattern=pattern_name,
                    examples=data['examples'][:5],
                    frequency=data['count'],
                    confidence=min(1.0, data['count'] / len(source_files)),
                    files_found=[]
                )
                naming_patterns.append(pattern)
        
        return sorted(naming_patterns, key=lambda x: x.frequency, reverse=True)
    
    def _extract_conventions(self, source_files: List[Path]) -> Dict[str, str]:
        """Extract coding conventions from the project."""
        conventions = {}
        
        # Analyze indentation
        indentation_counts = {'tabs': 0, '2spaces': 0, '4spaces': 0}
        quote_counts = {'single': 0, 'double': 0}
        semicolon_counts = {'with': 0, 'without': 0}
        
        sample_files = source_files[:10]  # Sample for performance
        
        for file_path in sample_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                for line in lines[:50]:  # Sample lines
                    stripped = line.lstrip()
                    if not stripped or stripped.startswith('//'):
                        continue
                    
                    # Check indentation
                    indent = line[:len(line) - len(stripped)]
                    if '\t' in indent:
                        indentation_counts['tabs'] += 1
                    elif indent == '  ':
                        indentation_counts['2spaces'] += 1
                    elif indent == '    ':
                        indentation_counts['4spaces'] += 1
                    
                    # Check quotes
                    if "'" in stripped:
                        quote_counts['single'] += 1
                    if '"' in stripped:
                        quote_counts['double'] += 1
                    
                    # Check semicolons
                    if stripped.endswith(';'):
                        semicolon_counts['with'] += 1
                    elif not stripped.endswith(('{', '}', ';')):
                        semicolon_counts['without'] += 1
            
            except (UnicodeDecodeError, IOError):
                continue
        
        # Determine conventions
        conventions['indentation'] = max(indentation_counts.items(), key=lambda x: x[1])[0]
        conventions['quotes'] = max(quote_counts.items(), key=lambda x: x[1])[0]
        conventions['semicolons'] = max(semicolon_counts.items(), key=lambda x: x[1])[0]
        
        return conventions
    
    def _analyze_file_organization(self, project_path: Path) -> Dict[str, Any]:
        """Analyze project file organization structure."""
        organization = {
            'directories': [],
            'structure_type': 'unknown',
            'common_directories': {},
            'file_distribution': {}
        }
        
        # Common directory patterns
        common_dirs = [
            'src', 'components', 'pages', 'app', 'lib', 'utils', 
            'hooks', 'contexts', 'services', 'api', 'styles',
            'assets', 'public', 'static', 'types'
        ]
        
        found_dirs = {}
        
        for dir_name in common_dirs:
            dir_path = project_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                # Count files in directory
                file_count = len([f for f in dir_path.rglob('*') if f.is_file()])
                found_dirs[dir_name] = file_count
        
        organization['common_directories'] = found_dirs
        organization['directories'] = list(found_dirs.keys())
        
        # Determine structure type
        if 'pages' in found_dirs and 'components' in found_dirs:
            organization['structure_type'] = 'pages_components'
        elif 'app' in found_dirs:
            organization['structure_type'] = 'app_directory'
        elif 'src' in found_dirs:
            organization['structure_type'] = 'src_based'
        else:
            organization['structure_type'] = 'flat'
        
        return organization
    
    def _get_common_imports(self, import_patterns: List[CodePattern]) -> List[str]:
        """Get most common import patterns."""
        return [pattern.pattern for pattern in import_patterns[:10]]
    
    def _extract_naming_conventions(self, source_files: List[Path]) -> Dict[str, str]:
        """Extract naming convention preferences."""
        conventions = {}
        
        # Analyze component naming
        component_files = [f for f in source_files if f.name[0].isupper()]
        if component_files:
            if len(component_files) / len(source_files) > 0.3:
                conventions['component_files'] = 'PascalCase'
            else:
                conventions['component_files'] = 'camelCase'
        
        # Analyze directory naming
        # This would require more sophisticated analysis
        conventions['directories'] = 'kebab-case'  # Default assumption
        
        return conventions
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()