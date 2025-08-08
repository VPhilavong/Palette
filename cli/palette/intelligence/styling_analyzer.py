"""
Advanced Styling System Analyzer with conflict resolution.
Addresses critical framework detection issues by implementing comprehensive
styling system detection with conflict resolution and validation.
"""

import os
import re
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set, Union

from ..errors.decorators import handle_errors


class StylingSystem(Enum):
    """Supported styling systems."""
    TAILWIND = "tailwind"
    CHAKRA_UI = "chakra-ui"
    MATERIAL_UI = "material-ui"
    STYLED_COMPONENTS = "styled-components"
    EMOTION = "emotion"
    MANTINE = "mantine"
    ANT_DESIGN = "ant-design"
    BOOTSTRAP = "bootstrap"
    SASS_SCSS = "sass"
    CSS_MODULES = "css-modules"
    VANILLA_CSS = "vanilla-css"
    SHADCN_UI = "shadcn/ui"


class DetectionSource(Enum):
    """Sources for styling system detection."""
    PACKAGE_JSON = "package_json"
    CONFIG_FILES = "config_files"
    COMPONENT_USAGE = "component_usage"
    IMPORT_PATTERNS = "import_patterns"
    CLASS_PATTERNS = "class_patterns"
    FILE_STRUCTURE = "file_structure"


@dataclass
class StylingHint:
    """A hint about detected styling system from a specific source."""
    source: DetectionSource
    detected_systems: Dict[StylingSystem, float]  # system -> confidence
    evidence: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)


@dataclass
class StylingAnalysis:
    """Complete styling system analysis results."""
    primary_system: StylingSystem
    confidence: float
    secondary_systems: List[Tuple[StylingSystem, float]] = field(default_factory=list)
    conflicts_detected: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    evidence_summary: Dict[DetectionSource, List[str]] = field(default_factory=dict)


class StylingSystemAnalyzer:
    """
    Advanced styling system analyzer with conflict detection and resolution.
    Addresses critical issues in framework detection by implementing multi-source
    analysis with weighted confidence scoring and conflict resolution.
    """
    
    def __init__(self):
        self.package_patterns = self._initialize_package_patterns()
        self.config_file_patterns = self._initialize_config_patterns()
        self.import_patterns = self._initialize_import_patterns()
        self.class_patterns = self._initialize_class_patterns()
        self.file_structure_patterns = self._initialize_file_structure_patterns()
    
    def _initialize_package_patterns(self) -> Dict[StylingSystem, List[str]]:
        """Initialize package.json dependency patterns for each styling system."""
        return {
            StylingSystem.TAILWIND: [
                "tailwindcss", "@tailwindcss/forms", "@tailwindcss/typography",
                "@tailwindcss/aspect-ratio", "tailwind-merge", "clsx"
            ],
            StylingSystem.CHAKRA_UI: [
                "@chakra-ui/react", "@chakra-ui/next-js", "@chakra-ui/theme",
                "@chakra-ui/icons", "@emotion/react", "@emotion/styled"
            ],
            StylingSystem.MATERIAL_UI: [
                "@mui/material", "@mui/icons-material", "@mui/lab", "@mui/x-data-grid",
                "@mui/styles", "@emotion/react", "@emotion/styled"
            ],
            StylingSystem.STYLED_COMPONENTS: [
                "styled-components", "@types/styled-components"
            ],
            StylingSystem.EMOTION: [
                "@emotion/react", "@emotion/styled", "@emotion/css", "@emotion/core"
            ],
            StylingSystem.MANTINE: [
                "@mantine/core", "@mantine/hooks", "@mantine/dates",
                "@mantine/notifications", "@mantine/form"
            ],
            StylingSystem.ANT_DESIGN: [
                "antd", "@ant-design/icons", "@ant-design/colors", "@ant-design/charts"
            ],
            StylingSystem.BOOTSTRAP: [
                "bootstrap", "react-bootstrap", "@types/bootstrap"
            ],
            StylingSystem.SASS_SCSS: [
                "sass", "node-sass", "@types/sass"
            ],
            StylingSystem.SHADCN_UI: [
                "@radix-ui/react-slot", "@radix-ui/react-dialog", "class-variance-authority",
                "clsx", "tailwind-merge", "lucide-react"
            ]
        }
    
    def _initialize_config_patterns(self) -> Dict[StylingSystem, List[str]]:
        """Initialize configuration file patterns."""
        return {
            StylingSystem.TAILWIND: [
                "tailwind.config.js", "tailwind.config.ts", "tailwind.config.cjs"
            ],
            StylingSystem.SASS_SCSS: [
                "sass.config.js", ".sassrc", "scss.config.js"
            ],
            StylingSystem.STYLED_COMPONENTS: [
                "babel-plugin-styled-components"  # in babel config
            ]
        }
    
    def _initialize_import_patterns(self) -> Dict[StylingSystem, List[re.Pattern]]:
        """Initialize import pattern regex for each styling system."""
        return {
            StylingSystem.CHAKRA_UI: [
                re.compile(r'from ["\']@chakra-ui/'),
                re.compile(r'import.*{.*}.*from ["\']@chakra-ui/'),
                re.compile(r'<ChakraProvider|<Box|<Button|<Text|<Flex|<Stack')
            ],
            StylingSystem.MATERIAL_UI: [
                re.compile(r'from ["\']@mui/'),
                re.compile(r'import.*{.*}.*from ["\']@mui/'),
                re.compile(r'<ThemeProvider|<Container|<Grid|<Paper|<Typography')
            ],
            StylingSystem.STYLED_COMPONENTS: [
                re.compile(r'import styled from ["\']styled-components'),
                re.compile(r'const \w+ = styled\.\w+'),
                re.compile(r'styled\([A-Z]\w*\)')
            ],
            StylingSystem.TAILWIND: [
                re.compile(r'className="[^"]*(?:bg-|text-|p-|m-|w-|h-|flex|grid)'),
                re.compile(r'import.*{.*}.*from ["\']tailwindcss'),
                re.compile(r'@tailwind base|@tailwind components|@tailwind utilities')
            ],
            StylingSystem.MANTINE: [
                re.compile(r'from ["\']@mantine/'),
                re.compile(r'<MantineProvider|<Button|<TextInput|<Group|<Stack')
            ],
            StylingSystem.ANT_DESIGN: [
                re.compile(r'from ["\']antd'),
                re.compile(r'import.*{.*}.*from ["\']antd'),
                re.compile(r'<ConfigProvider|<Layout|<Menu|<Button')
            ],
            StylingSystem.SHADCN_UI: [
                re.compile(r'from ["\']@/components/ui/'),
                re.compile(r'import.*{.*cn.*}.*from ["\']@/lib/utils'),
                re.compile(r'className={cn\(')
            ]
        }
    
    def _initialize_class_patterns(self) -> Dict[StylingSystem, List[re.Pattern]]:
        """Initialize CSS class pattern recognition."""
        return {
            StylingSystem.TAILWIND: [
                re.compile(r'className="[^"]*(?:bg-(?:red|blue|green|gray|slate)-\d+)'),
                re.compile(r'className="[^"]*(?:text-(?:sm|lg|xl|2xl|3xl))'),
                re.compile(r'className="[^"]*(?:p-\d+|m-\d+|px-\d+|py-\d+)'),
                re.compile(r'className="[^"]*(?:w-full|h-full|flex|grid)'),
                re.compile(r'className="[^"]*(?:hover:|focus:|active:)'),
                re.compile(r'className="[^"]*(?:sm:|md:|lg:|xl:)')
            ],
            StylingSystem.BOOTSTRAP: [
                re.compile(r'className="[^"]*(?:container|row|col-)'),
                re.compile(r'className="[^"]*(?:btn|btn-primary|btn-secondary)'),
                re.compile(r'className="[^"]*(?:d-flex|justify-content|align-items)')
            ],
            StylingSystem.CSS_MODULES: [
                re.compile(r'import.*styles.*from ["\'].*\.module\.css'),
                re.compile(r'className={styles\.\w+}')
            ]
        }
    
    def _initialize_file_structure_patterns(self) -> Dict[StylingSystem, List[str]]:
        """Initialize file structure patterns."""
        return {
            StylingSystem.SASS_SCSS: [
                "**/*.scss", "**/*.sass", "styles/**/*.scss"
            ],
            StylingSystem.CSS_MODULES: [
                "**/*.module.css", "**/*.module.scss"
            ],
            StylingSystem.STYLED_COMPONENTS: [
                "**/styled.js", "**/styled.ts", "**/*.styled.js"
            ],
            StylingSystem.SHADCN_UI: [
                "components/ui/**/*.tsx", "lib/utils.ts"
            ]
        }
    
    @handle_errors(reraise=True)
    def comprehensive_scan(self, project_path: str) -> StylingAnalysis:
        """
        Comprehensive styling system analysis with conflict resolution.
        
        This is the main method that addresses the critical framework detection
        issues by analyzing multiple sources and resolving conflicts.
        
        Args:
            project_path: Path to the project to analyze
            
        Returns:
            Complete styling analysis with confidence scores and conflict resolution
        """
        project_path = Path(project_path)
        
        # Collect hints from all sources
        hints = []
        
        # 1. Package.json analysis (high confidence when present)
        package_hint = self._analyze_package_dependencies(project_path)
        if package_hint.detected_systems:
            hints.append(package_hint)
        
        # 2. Configuration files analysis  
        config_hint = self._scan_config_files(project_path)
        if config_hint.detected_systems:
            hints.append(config_hint)
        
        # 3. Component usage analysis (highest confidence - actual usage)
        component_hint = self._analyze_existing_components(project_path)
        if component_hint.detected_systems:
            hints.append(component_hint)
        
        # 4. Import patterns analysis
        import_hint = self._analyze_import_patterns(project_path)
        if import_hint.detected_systems:
            hints.append(import_hint)
        
        # 5. CSS class usage analysis
        class_hint = self._analyze_class_usage_patterns(project_path)
        if class_hint.detected_systems:
            hints.append(class_hint)
        
        # 6. File structure analysis
        structure_hint = self._analyze_file_structure(project_path)
        if structure_hint.detected_systems:
            hints.append(structure_hint)
        
        # Resolve conflicts and determine primary system
        return self._resolve_styling_conflicts(hints)
    
    def _analyze_package_dependencies(self, project_path: Path) -> StylingHint:
        """Analyze package.json dependencies for styling systems."""
        package_json_path = project_path / "package.json"
        hint = StylingHint(
            source=DetectionSource.PACKAGE_JSON,
            detected_systems={},
            evidence=[]
        )
        
        if not package_json_path.exists():
            return hint
        
        try:
            with open(package_json_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            all_deps = {}
            all_deps.update(package_data.get('dependencies', {}))
            all_deps.update(package_data.get('devDependencies', {}))
            all_deps.update(package_data.get('peerDependencies', {}))
            
            dep_names = set(all_deps.keys())
            
            # Score each styling system based on dependencies
            for system, patterns in self.package_patterns.items():
                matches = []
                for pattern in patterns:
                    if pattern in dep_names:
                        matches.append(pattern)
                
                if matches:
                    # Calculate confidence based on number of matches and specificity
                    confidence = min(0.9, len(matches) * 0.3 + 0.4)
                    hint.detected_systems[system] = confidence
                    hint.evidence.extend([f"Found {pattern}" for pattern in matches])
            
            # Special handling for conflicting systems
            if (StylingSystem.CHAKRA_UI in hint.detected_systems and 
                StylingSystem.TAILWIND in hint.detected_systems):
                hint.conflicts.append("Both Chakra UI and Tailwind detected - this is problematic")
                # Boost Chakra UI confidence as it's more explicit
                if hint.detected_systems[StylingSystem.CHAKRA_UI] >= 0.5:
                    hint.detected_systems[StylingSystem.CHAKRA_UI] += 0.2
            
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            hint.evidence.append(f"Error reading package.json: {e}")
        
        return hint
    
    def _scan_config_files(self, project_path: Path) -> StylingHint:
        """Scan for styling system configuration files."""
        hint = StylingHint(
            source=DetectionSource.CONFIG_FILES,
            detected_systems={},
            evidence=[]
        )
        
        for system, config_files in self.config_file_patterns.items():
            for config_file in config_files:
                config_path = project_path / config_file
                if config_path.exists():
                    hint.detected_systems[system] = 0.8  # High confidence
                    hint.evidence.append(f"Found {config_file}")
        
        return hint
    
    def _analyze_existing_components(self, project_path: Path) -> StylingHint:
        """Analyze existing React components for styling system usage."""
        hint = StylingHint(
            source=DetectionSource.COMPONENT_USAGE,
            detected_systems={},
            evidence=[]
        )
        
        # Find React component files
        component_files = []
        for pattern in ["**/*.tsx", "**/*.jsx", "**/*.ts", "**/*.js"]:
            component_files.extend(project_path.glob(pattern))
        
        # Limit to reasonable number for performance
        component_files = component_files[:50]
        
        system_usage_counts = {}
        total_files_analyzed = 0
        
        for file_path in component_files:
            if self._is_component_file(file_path):
                total_files_analyzed += 1
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Check each styling system's patterns
                    for system, patterns in self.import_patterns.items():
                        matches = 0
                        for pattern in patterns:
                            if pattern.search(content):
                                matches += 1
                        
                        if matches > 0:
                            if system not in system_usage_counts:
                                system_usage_counts[system] = 0
                            system_usage_counts[system] += matches
                            
                            hint.evidence.append(
                                f"Found {system.value} usage in {file_path.name} ({matches} patterns)"
                            )
                
                except (UnicodeDecodeError, IOError):
                    continue
        
        # Convert usage counts to confidence scores
        if total_files_analyzed > 0:
            for system, count in system_usage_counts.items():
                # Confidence based on usage frequency
                confidence = min(0.95, (count / total_files_analyzed) * 0.5 + 0.3)
                hint.detected_systems[system] = confidence
        
        return hint
    
    def _analyze_import_patterns(self, project_path: Path) -> StylingHint:
        """Analyze import patterns in JavaScript/TypeScript files."""
        hint = StylingHint(
            source=DetectionSource.IMPORT_PATTERNS,
            detected_systems={},
            evidence=[]
        )
        
        # Find all JS/TS files
        files = []
        for pattern in ["**/*.tsx", "**/*.jsx", "**/*.ts", "**/*.js"]:
            files.extend(project_path.glob(pattern))
        
        # Limit for performance
        files = files[:30]
        
        import_counts = {}
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    # Only read first 100 lines for imports
                    lines = f.readlines()[:100]
                    content = ''.join(lines)
                
                for system, patterns in self.import_patterns.items():
                    for pattern in patterns:
                        matches = pattern.findall(content)
                        if matches:
                            if system not in import_counts:
                                import_counts[system] = 0
                            import_counts[system] += len(matches)
                            hint.evidence.append(
                                f"Import pattern for {system.value} in {file_path.name}"
                            )
            
            except (UnicodeDecodeError, IOError):
                continue
        
        # Convert to confidence scores
        total_imports = sum(import_counts.values())
        if total_imports > 0:
            for system, count in import_counts.items():
                confidence = min(0.8, (count / total_imports) * 0.6 + 0.2)
                hint.detected_systems[system] = confidence
        
        return hint
    
    def _analyze_class_usage_patterns(self, project_path: Path) -> StylingHint:
        """Analyze CSS class usage patterns."""
        hint = StylingHint(
            source=DetectionSource.CLASS_PATTERNS,
            detected_systems={},
            evidence=[]
        )
        
        # Find component files
        files = list(project_path.glob("**/*.tsx")) + list(project_path.glob("**/*.jsx"))
        files = files[:20]  # Limit for performance
        
        class_counts = {}
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                for system, patterns in self.class_patterns.items():
                    for pattern in patterns:
                        matches = pattern.findall(content)
                        if matches:
                            if system not in class_counts:
                                class_counts[system] = 0
                            class_counts[system] += len(matches)
                            hint.evidence.append(
                                f"Class pattern for {system.value} in {file_path.name} ({len(matches)} matches)"
                            )
            
            except (UnicodeDecodeError, IOError):
                continue
        
        # Convert to confidence scores
        total_classes = sum(class_counts.values())
        if total_classes > 0:
            for system, count in class_counts.items():
                confidence = min(0.7, (count / total_classes) * 0.5 + 0.2)
                hint.detected_systems[system] = confidence
        
        return hint
    
    def _analyze_file_structure(self, project_path: Path) -> StylingHint:
        """Analyze file structure patterns."""
        hint = StylingHint(
            source=DetectionSource.FILE_STRUCTURE,
            detected_systems={},
            evidence=[]
        )
        
        for system, patterns in self.file_structure_patterns.items():
            matches = []
            for pattern in patterns:
                found_files = list(project_path.glob(pattern))
                if found_files:
                    matches.extend(found_files)
            
            if matches:
                confidence = min(0.6, len(matches) * 0.2 + 0.3)
                hint.detected_systems[system] = confidence
                hint.evidence.append(f"Found {len(matches)} files matching {system.value} patterns")
        
        return hint
    
    def _is_component_file(self, file_path: Path) -> bool:
        """Check if file is likely a React component."""
        # Skip node_modules and test files
        if 'node_modules' in str(file_path) or 'test' in str(file_path).lower():
            return False
        
        # Check file extension
        if file_path.suffix not in ['.tsx', '.jsx']:
            return False
        
        # Check if filename suggests it's a component (starts with capital letter)
        return file_path.stem[0].isupper() if file_path.stem else False
    
    def _resolve_styling_conflicts(self, hints: List[StylingHint]) -> StylingAnalysis:
        """
        Resolve conflicts between different styling system indicators.
        This is the critical method that addresses framework detection issues.
        """
        if not hints:
            return StylingAnalysis(
                primary_system=StylingSystem.VANILLA_CSS,
                confidence=0.1,
                recommendations=["No styling system detected - defaulting to vanilla CSS"]
            )
        
        # Weight each detection source
        source_weights = {
            DetectionSource.COMPONENT_USAGE: 0.5,    # Highest weight - actual usage
            DetectionSource.PACKAGE_JSON: 0.3,       # High weight - explicit dependencies
            DetectionSource.CONFIG_FILES: 0.4,       # High weight - configuration
            DetectionSource.IMPORT_PATTERNS: 0.3,    # Medium weight - import usage
            DetectionSource.CLASS_PATTERNS: 0.2,     # Lower weight - could be misleading
            DetectionSource.FILE_STRUCTURE: 0.1      # Lowest weight - structural hints
        }
        
        # Aggregate scores across all sources
        system_scores = {}
        evidence_by_source = {}
        all_conflicts = []
        
        for hint in hints:
            evidence_by_source[hint.source] = hint.evidence
            all_conflicts.extend(hint.conflicts)
            
            weight = source_weights[hint.source]
            
            for system, confidence in hint.detected_systems.items():
                if system not in system_scores:
                    system_scores[system] = 0
                system_scores[system] += confidence * weight
        
        if not system_scores:
            return StylingAnalysis(
                primary_system=StylingSystem.VANILLA_CSS,
                confidence=0.1,
                recommendations=["No styling systems detected in analysis"]
            )
        
        # Sort systems by score
        sorted_systems = sorted(system_scores.items(), key=lambda x: x[1], reverse=True)
        primary_system, primary_score = sorted_systems[0]
        
        # Get secondary systems
        secondary_systems = [(system, score) for system, score in sorted_systems[1:] if score > 0.2]
        
        # Detect and resolve critical conflicts
        conflicts_detected = list(all_conflicts)
        recommendations = []
        
        # Critical conflict: Chakra UI + Tailwind
        if (StylingSystem.CHAKRA_UI in system_scores and 
            StylingSystem.TAILWIND in system_scores):
            
            chakra_score = system_scores[StylingSystem.CHAKRA_UI]
            tailwind_score = system_scores[StylingSystem.TAILWIND]
            
            if abs(chakra_score - tailwind_score) < 0.2:
                conflicts_detected.append(
                    "CRITICAL: Both Chakra UI and Tailwind detected with similar confidence"
                )
                
                # Prefer Chakra UI if it has component usage evidence
                component_evidence = evidence_by_source.get(DetectionSource.COMPONENT_USAGE, [])
                if any("chakra-ui" in evidence.lower() for evidence in component_evidence):
                    primary_system = StylingSystem.CHAKRA_UI
                    primary_score = max(chakra_score, tailwind_score)
                    recommendations.append(
                        "Resolved conflict in favor of Chakra UI based on component usage evidence"
                    )
                else:
                    recommendations.append(
                        "CONFLICT: Cannot reliably determine primary styling system. Manual review needed."
                    )
        
        # Material UI + Tailwind conflict
        if (StylingSystem.MATERIAL_UI in system_scores and 
            StylingSystem.TAILWIND in system_scores):
            conflicts_detected.append("Material UI and Tailwind both detected")
            recommendations.append("Consider if Tailwind is only used for custom styling alongside Material UI")
        
        # Add system-specific recommendations
        if primary_system == StylingSystem.CHAKRA_UI:
            recommendations.extend([
                "Use Chakra UI components and theme system",
                "Avoid CSS classes - use component props for styling",
                "Leverage Chakra's responsive props and color mode"
            ])
        elif primary_system == StylingSystem.TAILWIND:
            recommendations.extend([
                "Use Tailwind utility classes consistently",
                "Follow Tailwind's design system approach",
                "Consider using Tailwind's component layer for reusable styles"
            ])
        elif primary_system == StylingSystem.SHADCN_UI:
            recommendations.extend([
                "Use shadcn/ui components with Tailwind classes",
                "Leverage the cn() utility for conditional styling",
                "Follow the established component patterns"
            ])
        
        return StylingAnalysis(
            primary_system=primary_system,
            confidence=min(1.0, primary_score),
            secondary_systems=secondary_systems,
            conflicts_detected=conflicts_detected,
            recommendations=recommendations,
            evidence_summary=evidence_by_source
        )
    
    def validate_styling_selection(self, 
                                  system: StylingSystem, 
                                  project_path: str) -> bool:
        """Validate that a styling system selection makes sense for the project."""
        project_path = Path(project_path)
        
        # Quick validation checks
        package_json = project_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
                
                all_deps = {}
                all_deps.update(package_data.get('dependencies', {}))
                all_deps.update(package_data.get('devDependencies', {}))
                
                # Check if the selected system has supporting dependencies
                required_deps = self.package_patterns.get(system, [])
                if required_deps:
                    has_any_deps = any(dep in all_deps for dep in required_deps)
                    return has_any_deps
                
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return True  # Default to valid if we can't verify
    
    def get_system_specific_guidance(self, system: StylingSystem) -> Dict[str, Any]:
        """Get system-specific guidance for code generation."""
        guidance = {
            'import_patterns': [],
            'component_patterns': [],
            'forbidden_patterns': [],
            'validation_rules': []
        }
        
        if system == StylingSystem.CHAKRA_UI:
            guidance.update({
                'import_patterns': [
                    "import { Box, Button, Text, Flex, Stack } from '@chakra-ui/react'",
                    "import { ChakraProvider } from '@chakra-ui/react'"
                ],
                'component_patterns': [
                    "Use Box for containers instead of div",
                    "Use Chakra components with props for styling",
                    "Use colorScheme, variant, size props"
                ],
                'forbidden_patterns': [
                    "className with CSS utility classes",
                    "Tailwind CSS classes",
                    "Direct CSS styling"
                ],
                'validation_rules': [
                    "Must import from @chakra-ui/react",
                    "Should use Chakra components",
                    "No Tailwind classes allowed"
                ]
            })
        
        elif system == StylingSystem.TAILWIND:
            guidance.update({
                'import_patterns': [
                    "className with Tailwind utilities",
                    "import clsx or cn utility for conditional classes"
                ],
                'component_patterns': [
                    "Use utility classes for styling",
                    "Follow mobile-first responsive design",
                    "Use Tailwind's color palette"
                ],
                'forbidden_patterns': [
                    "Inline styles",
                    "CSS-in-JS styling",
                    "Component library styling props"
                ],
                'validation_rules': [
                    "Must use valid Tailwind classes",
                    "Should follow utility-first approach",
                    "Use consistent spacing scale"
                ]
            })
        
        elif system == StylingSystem.SHADCN_UI:
            guidance.update({
                'import_patterns': [
                    "import { Button } from '@/components/ui/button'",
                    "import { cn } from '@/lib/utils'"
                ],
                'component_patterns': [
                    "Use shadcn/ui components with Tailwind",
                    "Use cn() for conditional styling",
                    "Follow established variant patterns"
                ],
                'forbidden_patterns': [
                    "Direct Radix UI imports without shadcn wrapper",
                    "CSS-in-JS styling"
                ],
                'validation_rules': [
                    "Must use shadcn/ui component imports",
                    "Should use cn() utility",
                    "Follow Tailwind conventions"
                ]
            })
        
        return guidance