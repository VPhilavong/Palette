"""
Enhanced UI Library Validator with comprehensive analysis.
Integrates with styling analyzer and Zero-Error system for robust UI library validation.
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set

from .styling_analyzer import StylingSystemAnalyzer, StylingSystem, StylingAnalysis
from .framework_detector import EnhancedFrameworkDetector, Framework
from ..errors.decorators import handle_errors


class UILibraryCompatibility(Enum):
    """UI library compatibility levels."""
    PERFECT = "perfect"      # Full dependency match + usage evidence  
    GOOD = "good"           # Dependencies present, some usage patterns
    WARNING = "warning"     # Dependencies missing but could work
    CONFLICT = "conflict"   # Incompatible with existing setup
    UNKNOWN = "unknown"     # Can't determine compatibility


@dataclass
class UILibraryValidationResult:
    """Result of UI library validation."""
    library: str
    compatibility: UILibraryCompatibility
    confidence: float
    evidence: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    missing_dependencies: List[str] = field(default_factory=list)
    conflicting_systems: List[str] = field(default_factory=list)


class EnhancedUILibraryValidator:
    """
    Enhanced UI library validator that integrates with styling analysis
    and framework detection for comprehensive validation.
    """
    
    def __init__(self):
        self.styling_analyzer = StylingSystemAnalyzer()
        self.framework_detector = EnhancedFrameworkDetector()
        self._initialize_library_mappings()
    
    def _initialize_library_mappings(self):
        """Initialize mappings between UI libraries and styling systems."""
        
        # Map UI library names to StylingSystem enum values
        self.ui_to_styling_map = {
            'chakra-ui': StylingSystem.CHAKRA_UI,
            'material-ui': StylingSystem.MATERIAL_UI,
            'ant-design': StylingSystem.ANT_DESIGN,
            'mantine': StylingSystem.MANTINE,
            'react-bootstrap': StylingSystem.BOOTSTRAP,
            'semantic-ui': StylingSystem.BOOTSTRAP,  # Similar approach
            'grommet': StylingSystem.STYLED_COMPONENTS,  # Uses styled-components
            'headless-ui': StylingSystem.TAILWIND,  # Usually paired with Tailwind
            'shadcn/ui': StylingSystem.SHADCN_UI,
            'none': StylingSystem.VANILLA_CSS
        }
        
        # Define dependency requirements for each UI library
        self.library_dependencies = {
            'chakra-ui': {
                'required': ['@chakra-ui/react'],
                'recommended': ['@emotion/react', '@emotion/styled', 'framer-motion'],
                'conflicts_with': ['@mui/material', 'antd']
            },
            'material-ui': {
                'required': ['@mui/material'],
                'recommended': ['@emotion/react', '@emotion/styled', '@mui/icons-material'],
                'conflicts_with': ['@chakra-ui/react', 'antd']
            },
            'ant-design': {
                'required': ['antd'],
                'recommended': ['@ant-design/icons'],
                'conflicts_with': ['@chakra-ui/react', '@mui/material']
            },
            'mantine': {
                'required': ['@mantine/core'],
                'recommended': ['@mantine/hooks', '@mantine/form', '@mantine/notifications'],
                'conflicts_with': []
            },
            'react-bootstrap': {
                'required': ['react-bootstrap'],
                'recommended': ['bootstrap'],
                'conflicts_with': []
            },
            'semantic-ui': {
                'required': ['semantic-ui-react'],
                'recommended': ['semantic-ui-css'],
                'conflicts_with': []
            },
            'grommet': {
                'required': ['grommet'],
                'recommended': ['grommet-icons', 'styled-components'],
                'conflicts_with': []
            },
            'headless-ui': {
                'required': ['@headlessui/react'],
                'recommended': ['tailwindcss', 'clsx'],
                'conflicts_with': []
            },
            'shadcn/ui': {
                'required': ['@radix-ui/react-slot', 'class-variance-authority'],
                'recommended': ['tailwindcss', 'clsx', 'tailwind-merge', 'lucide-react'],
                'conflicts_with': []
            }
        }
        
        # Framework compatibility matrix
        self.framework_compatibility = {
            'chakra-ui': [Framework.REACT, Framework.NEXT_JS, Framework.VITE_REACT],
            'material-ui': [Framework.REACT, Framework.NEXT_JS, Framework.VITE_REACT, Framework.GATSBY],
            'ant-design': [Framework.REACT, Framework.NEXT_JS, Framework.VITE_REACT],
            'mantine': [Framework.REACT, Framework.NEXT_JS, Framework.VITE_REACT],
            'react-bootstrap': [Framework.REACT, Framework.NEXT_JS, Framework.VITE_REACT],
            'semantic-ui': [Framework.REACT, Framework.NEXT_JS, Framework.VITE_REACT],
            'grommet': [Framework.REACT, Framework.NEXT_JS, Framework.VITE_REACT],
            'headless-ui': [Framework.REACT, Framework.NEXT_JS, Framework.VITE_REACT],
            'shadcn/ui': [Framework.REACT, Framework.NEXT_JS, Framework.VITE_REACT]
        }
    
    @handle_errors(reraise=True)
    def validate_ui_library_choice(self, 
                                  library: str, 
                                  project_path: str) -> UILibraryValidationResult:
        """
        Comprehensively validate a UI library choice against the project.
        
        Args:
            library: UI library to validate ('chakra-ui', 'material-ui', etc.)
            project_path: Path to the project to analyze
            
        Returns:
            Detailed validation result with compatibility assessment
        """
        
        if library == 'none':
            return UILibraryValidationResult(
                library=library,
                compatibility=UILibraryCompatibility.PERFECT,
                confidence=1.0,
                evidence=["No UI library requested - using vanilla components"],
                recommendations=["Consider using utility classes or CSS modules for styling"]
            )
        
        # Perform comprehensive styling analysis
        styling_analysis = self.styling_analyzer.comprehensive_scan(project_path)
        
        # Perform framework analysis
        framework_analysis = self.framework_detector.deep_analyze(project_path)
        
        # Analyze dependencies
        dependency_analysis = self._analyze_dependencies(library, project_path)
        
        # Check for conflicts with existing styling systems
        conflict_analysis = self._analyze_styling_conflicts(library, styling_analysis)
        
        # Check framework compatibility
        framework_compatibility = self._check_framework_compatibility(
            library, framework_analysis.primary_framework
        )
        
        # Determine overall compatibility
        compatibility, confidence = self._determine_compatibility(
            dependency_analysis, conflict_analysis, framework_compatibility, styling_analysis
        )
        
        # Build result
        result = UILibraryValidationResult(
            library=library,
            compatibility=compatibility,
            confidence=confidence
        )
        
        # Populate evidence
        result.evidence.extend(dependency_analysis.get('evidence', []))
        result.evidence.extend(conflict_analysis.get('evidence', []))
        result.evidence.extend(framework_compatibility.get('evidence', []))
        
        # Populate warnings
        result.warnings.extend(dependency_analysis.get('warnings', []))
        result.warnings.extend(conflict_analysis.get('warnings', []))
        result.warnings.extend(framework_compatibility.get('warnings', []))
        
        # Populate missing dependencies
        result.missing_dependencies = dependency_analysis.get('missing', [])
        
        # Populate conflicting systems
        result.conflicting_systems = conflict_analysis.get('conflicts', [])
        
        # Generate recommendations
        result.recommendations = self._generate_recommendations(
            library, styling_analysis, dependency_analysis, conflict_analysis
        )
        
        return result
    
    def _analyze_dependencies(self, library: str, project_path: str) -> Dict[str, Any]:
        """Analyze project dependencies for UI library compatibility."""
        
        result = {
            'evidence': [],
            'warnings': [],
            'missing': [],
            'present': []
        }
        
        if library not in self.library_dependencies:
            result['warnings'].append(f"Unknown UI library: {library}")
            return result
        
        package_json_path = Path(project_path) / "package.json"
        
        if not package_json_path.exists():
            result['warnings'].append("No package.json found - cannot validate dependencies")
            return result
        
        try:
            with open(package_json_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            all_deps = set()
            all_deps.update(package_data.get('dependencies', {}).keys())
            all_deps.update(package_data.get('devDependencies', {}).keys())
            
            lib_config = self.library_dependencies[library]
            
            # Check required dependencies
            required_deps = lib_config['required']
            for dep in required_deps:
                if dep in all_deps:
                    result['present'].append(dep)
                    result['evidence'].append(f"Found required dependency: {dep}")
                else:
                    result['missing'].append(dep)
                    result['warnings'].append(f"Missing required dependency: {dep}")
            
            # Check recommended dependencies
            recommended_deps = lib_config.get('recommended', [])
            for dep in recommended_deps:
                if dep in all_deps:
                    result['present'].append(dep)
                    result['evidence'].append(f"Found recommended dependency: {dep}")
            
            # Check for conflicting dependencies
            conflicting_deps = lib_config.get('conflicts_with', [])
            for dep in conflicting_deps:
                if dep in all_deps:
                    result['warnings'].append(f"Conflicting dependency found: {dep}")
        
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            result['warnings'].append(f"Error reading package.json: {e}")
        
        return result
    
    def _analyze_styling_conflicts(self, library: str, styling_analysis: StylingAnalysis) -> Dict[str, Any]:
        """Analyze conflicts with existing styling systems."""
        
        result = {
            'evidence': [],
            'warnings': [],
            'conflicts': []
        }
        
        if library not in self.ui_to_styling_map:
            result['warnings'].append(f"Unknown styling mapping for library: {library}")
            return result
        
        expected_styling = self.ui_to_styling_map[library]
        detected_styling = styling_analysis.primary_system
        
        # Check if library matches detected styling system
        if expected_styling == detected_styling:
            result['evidence'].append(
                f"Perfect match: {library} aligns with detected {detected_styling.value} system"
            )
        else:
            # Check for critical conflicts
            critical_conflicts = [
                (StylingSystem.CHAKRA_UI, StylingSystem.TAILWIND),
                (StylingSystem.MATERIAL_UI, StylingSystem.CHAKRA_UI),
                (StylingSystem.ANT_DESIGN, StylingSystem.CHAKRA_UI),
                (StylingSystem.ANT_DESIGN, StylingSystem.MATERIAL_UI)
            ]
            
            conflict_pair = (expected_styling, detected_styling)
            reverse_conflict = (detected_styling, expected_styling)
            
            if conflict_pair in critical_conflicts or reverse_conflict in critical_conflicts:
                result['conflicts'].append(detected_styling.value)
                result['warnings'].append(
                    f"CRITICAL CONFLICT: {library} ({expected_styling.value}) conflicts with "
                    f"detected {detected_styling.value} system"
                )
            else:
                result['warnings'].append(
                    f"Styling mismatch: {library} expects {expected_styling.value} but "
                    f"project uses {detected_styling.value}"
                )
        
        # Check secondary systems for additional context
        for secondary_system, confidence in styling_analysis.secondary_systems:
            if secondary_system == expected_styling:
                result['evidence'].append(
                    f"Found {library} patterns as secondary system (confidence: {confidence:.2f})"
                )
        
        return result
    
    def _check_framework_compatibility(self, library: str, framework: Framework) -> Dict[str, Any]:
        """Check if UI library is compatible with the detected framework."""
        
        result = {
            'evidence': [],
            'warnings': []
        }
        
        if library not in self.framework_compatibility:
            result['warnings'].append(f"Unknown framework compatibility for library: {library}")
            return result
        
        compatible_frameworks = self.framework_compatibility[library]
        
        if framework in compatible_frameworks:
            result['evidence'].append(f"{library} is compatible with {framework.value}")
        else:
            result['warnings'].append(
                f"Framework compatibility warning: {library} may not work well with {framework.value}"
            )
            result['warnings'].append(
                f"Recommended frameworks for {library}: {[f.value for f in compatible_frameworks]}"
            )
        
        return result
    
    def _determine_compatibility(self, 
                               dependency_analysis: Dict[str, Any],
                               conflict_analysis: Dict[str, Any], 
                               framework_compatibility: Dict[str, Any],
                               styling_analysis: StylingAnalysis) -> Tuple[UILibraryCompatibility, float]:
        """Determine overall compatibility and confidence score."""
        
        # Start with base compatibility
        base_score = 0.5
        
        # Factor in dependency analysis
        missing_deps = len(dependency_analysis.get('missing', []))
        present_deps = len(dependency_analysis.get('present', []))
        
        if missing_deps == 0 and present_deps > 0:
            base_score += 0.3  # Perfect dependency match
        elif missing_deps > 0 and present_deps > 0:
            base_score += 0.1  # Partial dependency match
        elif missing_deps > 0:
            base_score -= 0.2  # Missing required dependencies
        
        # Factor in styling conflicts
        conflicts = conflict_analysis.get('conflicts', [])
        if conflicts:
            base_score -= 0.4  # Critical styling conflicts
        elif conflict_analysis.get('evidence'):
            base_score += 0.2  # Good styling alignment
        
        # Factor in framework compatibility
        framework_warnings = framework_compatibility.get('warnings', [])
        if not framework_warnings:
            base_score += 0.1  # Good framework compatibility
        else:
            base_score -= 0.1  # Framework compatibility issues
        
        # Factor in styling analysis confidence
        styling_confidence = styling_analysis.confidence
        if styling_confidence > 0.8:
            base_score += 0.1  # High confidence in analysis
        
        # Clamp score between 0 and 1
        confidence = max(0.0, min(1.0, base_score))
        
        # Determine compatibility level
        if conflicts:
            compatibility = UILibraryCompatibility.CONFLICT
        elif missing_deps > 0 and present_deps == 0:
            compatibility = UILibraryCompatibility.WARNING
        elif confidence >= 0.8:
            compatibility = UILibraryCompatibility.PERFECT
        elif confidence >= 0.6:
            compatibility = UILibraryCompatibility.GOOD
        elif confidence >= 0.4:
            compatibility = UILibraryCompatibility.WARNING
        else:
            compatibility = UILibraryCompatibility.UNKNOWN
        
        return compatibility, confidence
    
    def _generate_recommendations(self,
                                library: str,
                                styling_analysis: StylingAnalysis,
                                dependency_analysis: Dict[str, Any],
                                conflict_analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        
        recommendations = []
        
        # Dependency recommendations
        missing_deps = dependency_analysis.get('missing', [])
        if missing_deps:
            recommendations.append(
                f"Install missing dependencies: npm install {' '.join(missing_deps)}"
            )
        
        # Conflict resolution recommendations
        conflicts = conflict_analysis.get('conflicts', [])
        if conflicts:
            for conflict in conflicts:
                if conflict == 'tailwind':
                    recommendations.append(
                        f"Consider using Tailwind with {library} for utility-first styling"
                    )
                else:
                    recommendations.append(
                        f"Resolve conflict with {conflict} by choosing one primary styling system"
                    )
        
        # Styling system recommendations
        primary_system = styling_analysis.primary_system.value
        if library in ['headless-ui', 'shadcn/ui'] and primary_system != 'tailwind':
            recommendations.append(
                "Consider installing Tailwind CSS as it pairs well with headless component libraries"
            )
        
        # Framework-specific recommendations
        if library == 'material-ui':
            recommendations.append(
                "Configure Material-UI theme provider in your app root component"
            )
        elif library == 'chakra-ui':
            recommendations.append(
                "Wrap your app with ChakraProvider and configure custom theme if needed"
            )
        
        return recommendations
    
    @handle_errors(reraise=True)
    def get_recommended_ui_library(self, project_path: str) -> Optional[str]:
        """
        Get the recommended UI library based on comprehensive project analysis.
        
        Args:
            project_path: Path to the project to analyze
            
        Returns:
            Recommended UI library name or None if no clear recommendation
        """
        
        styling_analysis = self.styling_analyzer.comprehensive_scan(project_path)
        framework_analysis = self.framework_detector.deep_analyze(project_path)
        
        # Map detected styling system to UI library
        styling_to_ui = {
            StylingSystem.CHAKRA_UI: 'chakra-ui',
            StylingSystem.MATERIAL_UI: 'material-ui',
            StylingSystem.ANT_DESIGN: 'ant-design',
            StylingSystem.MANTINE: 'mantine',
            StylingSystem.BOOTSTRAP: 'react-bootstrap',
            StylingSystem.SHADCN_UI: 'shadcn/ui',
            StylingSystem.TAILWIND: 'headless-ui',  # Suggest headless UI for Tailwind projects
            StylingSystem.VANILLA_CSS: 'none'
        }
        
        # Get recommendation based on detected styling system
        primary_system = styling_analysis.primary_system
        if primary_system in styling_to_ui:
            return styling_to_ui[primary_system]
        
        # Fallback recommendations based on framework
        framework_defaults = {
            Framework.NEXT_JS: 'shadcn/ui',  # Popular choice for Next.js
            Framework.REACT: 'material-ui',   # Popular general choice
            Framework.VITE_REACT: 'headless-ui'  # Good for modern Vite setups
        }
        
        primary_framework = framework_analysis.primary_framework
        if primary_framework in framework_defaults:
            return framework_defaults[primary_framework]
        
        return None