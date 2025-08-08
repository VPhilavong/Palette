"""
Cross-Library Compatibility Checker for UI Libraries
Analyzes compatibility between different UI libraries and provides migration guidance.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any
from pathlib import Path

from ..errors.decorators import handle_errors
from ..mcp.ui_library_server_base import UILibraryType
from ..mcp.ui_library_manager import MCPUILibraryManager


class CompatibilityLevel(Enum):
    """Levels of compatibility between UI libraries."""
    COMPATIBLE = "compatible"           # Can work together without issues
    MINOR_CONFLICTS = "minor_conflicts" # Some styling conflicts, mostly workable
    MAJOR_CONFLICTS = "major_conflicts" # Significant conflicts, not recommended
    INCOMPATIBLE = "incompatible"       # Cannot work together


class MigrationComplexity(Enum):
    """Migration complexity levels."""
    TRIVIAL = "trivial"         # Direct 1:1 component mapping
    SIMPLE = "simple"           # Straightforward with minor prop changes
    MODERATE = "moderate"       # Requires some refactoring
    COMPLEX = "complex"         # Significant changes needed
    IMPOSSIBLE = "impossible"   # No direct migration path


@dataclass
class ComponentMapping:
    """Mapping between components in different libraries."""
    source_component: str
    target_component: str
    confidence: float                    # 0.0 to 1.0 confidence in mapping
    migration_complexity: MigrationComplexity
    prop_mappings: Dict[str, str] = field(default_factory=dict)
    required_changes: List[str] = field(default_factory=list)
    migration_notes: str = ""


@dataclass
class LibraryCompatibilityResult:
    """Result of compatibility analysis between two UI libraries."""
    source_library: UILibraryType
    target_library: UILibraryType
    compatibility_level: CompatibilityLevel
    confidence: float
    
    # Compatibility analysis
    compatible_components: List[ComponentMapping] = field(default_factory=list)
    conflicting_components: List[str] = field(default_factory=list)
    missing_components: List[str] = field(default_factory=list)
    
    # Migration guidance
    migration_strategy: str = ""
    migration_steps: List[str] = field(default_factory=list)
    potential_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Technical details
    dependency_conflicts: List[str] = field(default_factory=list)
    styling_conflicts: List[str] = field(default_factory=list)
    bundle_size_impact: Optional[str] = None


class CrossLibraryCompatibilityChecker:
    """
    Analyzes compatibility between different UI libraries and provides
    migration guidance and conflict resolution strategies.
    """
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.library_manager = MCPUILibraryManager(str(project_path))
        
        # Initialize compatibility matrices and component mappings
        self._initialize_compatibility_matrix()
        self._initialize_component_mappings()
        self._initialize_conflict_patterns()
    
    def _initialize_compatibility_matrix(self):
        """Initialize the compatibility matrix between UI libraries."""
        self.compatibility_matrix = {
            # Chakra UI compatibilities
            (UILibraryType.CHAKRA_UI, UILibraryType.MATERIAL_UI): CompatibilityLevel.MAJOR_CONFLICTS,
            (UILibraryType.CHAKRA_UI, UILibraryType.ANT_DESIGN): CompatibilityLevel.MAJOR_CONFLICTS,
            (UILibraryType.CHAKRA_UI, UILibraryType.SHADCN_UI): CompatibilityLevel.MINOR_CONFLICTS,
            (UILibraryType.CHAKRA_UI, UILibraryType.MANTINE): CompatibilityLevel.MINOR_CONFLICTS,
            
            # Material-UI compatibilities
            (UILibraryType.MATERIAL_UI, UILibraryType.CHAKRA_UI): CompatibilityLevel.MAJOR_CONFLICTS,
            (UILibraryType.MATERIAL_UI, UILibraryType.ANT_DESIGN): CompatibilityLevel.MAJOR_CONFLICTS,
            (UILibraryType.MATERIAL_UI, UILibraryType.SHADCN_UI): CompatibilityLevel.MINOR_CONFLICTS,
            (UILibraryType.MATERIAL_UI, UILibraryType.MANTINE): CompatibilityLevel.MINOR_CONFLICTS,
            
            # Ant Design compatibilities
            (UILibraryType.ANT_DESIGN, UILibraryType.CHAKRA_UI): CompatibilityLevel.MAJOR_CONFLICTS,
            (UILibraryType.ANT_DESIGN, UILibraryType.MATERIAL_UI): CompatibilityLevel.MAJOR_CONFLICTS,
            (UILibraryType.ANT_DESIGN, UILibraryType.SHADCN_UI): CompatibilityLevel.MINOR_CONFLICTS,
            (UILibraryType.ANT_DESIGN, UILibraryType.MANTINE): CompatibilityLevel.MINOR_CONFLICTS,
            
            # shadcn/ui compatibilities (more compatible due to Tailwind base)
            (UILibraryType.SHADCN_UI, UILibraryType.CHAKRA_UI): CompatibilityLevel.MINOR_CONFLICTS,
            (UILibraryType.SHADCN_UI, UILibraryType.MATERIAL_UI): CompatibilityLevel.MINOR_CONFLICTS,
            (UILibraryType.SHADCN_UI, UILibraryType.ANT_DESIGN): CompatibilityLevel.MINOR_CONFLICTS,
            (UILibraryType.SHADCN_UI, UILibraryType.TAILWIND_UI): CompatibilityLevel.COMPATIBLE,
            (UILibraryType.SHADCN_UI, UILibraryType.MANTINE): CompatibilityLevel.MINOR_CONFLICTS,
            
            # Tailwind UI compatibilities
            (UILibraryType.TAILWIND_UI, UILibraryType.SHADCN_UI): CompatibilityLevel.COMPATIBLE,
            (UILibraryType.TAILWIND_UI, UILibraryType.CHAKRA_UI): CompatibilityLevel.MINOR_CONFLICTS,
            (UILibraryType.TAILWIND_UI, UILibraryType.MATERIAL_UI): CompatibilityLevel.MINOR_CONFLICTS,
            (UILibraryType.TAILWIND_UI, UILibraryType.ANT_DESIGN): CompatibilityLevel.MINOR_CONFLICTS,
        }
    
    def _initialize_component_mappings(self):
        """Initialize component mapping between different libraries."""
        self.component_mappings = {
            # Chakra UI to Material-UI mappings
            (UILibraryType.CHAKRA_UI, UILibraryType.MATERIAL_UI): {
                "Button": ComponentMapping(
                    source_component="Button",
                    target_component="Button",
                    confidence=0.9,
                    migration_complexity=MigrationComplexity.SIMPLE,
                    prop_mappings={
                        "colorScheme": "color",
                        "variant": "variant",
                        "size": "size",
                        "isDisabled": "disabled",
                        "isLoading": "loading"
                    },
                    required_changes=["Update prop names", "Change color scheme values"],
                    migration_notes="Direct mapping with prop name changes"
                ),
                "Input": ComponentMapping(
                    source_component="Input",
                    target_component="TextField",
                    confidence=0.8,
                    migration_complexity=MigrationComplexity.MODERATE,
                    prop_mappings={
                        "placeholder": "placeholder",
                        "value": "value",
                        "onChange": "onChange",
                        "isDisabled": "disabled",
                        "isInvalid": "error"
                    },
                    required_changes=["Use TextField instead of Input", "Update validation patterns"],
                    migration_notes="TextField provides more features than Chakra Input"
                ),
                "Box": ComponentMapping(
                    source_component="Box",
                    target_component="Box",
                    confidence=0.7,
                    migration_complexity=MigrationComplexity.MODERATE,
                    required_changes=["Convert Chakra props to Material-UI sx prop", "Update styling approach"],
                    migration_notes="Material-UI Box uses different styling system"
                ),
            },
            
            # Chakra UI to Ant Design mappings
            (UILibraryType.CHAKRA_UI, UILibraryType.ANT_DESIGN): {
                "Button": ComponentMapping(
                    source_component="Button",
                    target_component="Button",
                    confidence=0.8,
                    migration_complexity=MigrationComplexity.SIMPLE,
                    prop_mappings={
                        "colorScheme": "type",
                        "size": "size",
                        "isDisabled": "disabled",
                        "isLoading": "loading"
                    },
                    required_changes=["Update color scheme to type", "Adjust size values"],
                    migration_notes="Ant Design uses 'type' instead of 'colorScheme'"
                ),
                "Input": ComponentMapping(
                    source_component="Input",
                    target_component="Input",
                    confidence=0.9,
                    migration_complexity=MigrationComplexity.SIMPLE,
                    prop_mappings={
                        "placeholder": "placeholder",
                        "value": "value",
                        "onChange": "onChange",
                        "isDisabled": "disabled"
                    },
                    required_changes=["Update prop names"],
                    migration_notes="Very similar API between libraries"
                ),
            },
            
            # Material-UI to Ant Design mappings
            (UILibraryType.MATERIAL_UI, UILibraryType.ANT_DESIGN): {
                "Button": ComponentMapping(
                    source_component="Button",
                    target_component="Button",
                    confidence=0.8,
                    migration_complexity=MigrationComplexity.SIMPLE,
                    prop_mappings={
                        "color": "type",
                        "variant": "ghost",
                        "size": "size",
                        "disabled": "disabled"
                    },
                    required_changes=["Map Material-UI colors to Ant Design types"],
                    migration_notes="Different color/type systems between libraries"
                ),
                "TextField": ComponentMapping(
                    source_component="TextField",
                    target_component="Input",
                    confidence=0.7,
                    migration_complexity=MigrationComplexity.MODERATE,
                    required_changes=["Simplify TextField features to Input", "Update validation approach"],
                    migration_notes="Material-UI TextField has more features than Ant Design Input"
                ),
            },
            
            # shadcn/ui mappings (more flexible due to copy-paste nature)
            (UILibraryType.SHADCN_UI, UILibraryType.CHAKRA_UI): {
                "Button": ComponentMapping(
                    source_component="Button",
                    target_component="Button",
                    confidence=0.8,
                    migration_complexity=MigrationComplexity.MODERATE,
                    required_changes=["Convert Tailwind classes to Chakra props", "Update styling system"],
                    migration_notes="Need to convert from utility-first to component props"
                ),
            }
        }
    
    def _initialize_conflict_patterns(self):
        """Initialize patterns that indicate conflicts between libraries."""
        self.conflict_patterns = {
            "css_conflicts": [
                ("chakra-ui", "material-ui", "Both libraries inject global CSS"),
                ("chakra-ui", "ant-design", "Theme provider conflicts"),
                ("material-ui", "ant-design", "CSS-in-JS conflicts"),
            ],
            "bundle_conflicts": [
                ("chakra-ui", "material-ui", "Large bundle size with both libraries"),
                ("material-ui", "ant-design", "Overlapping functionality increases bundle"),
            ],
            "theme_conflicts": [
                ("chakra-ui", "material-ui", "Conflicting theme providers"),
                ("chakra-ui", "ant-design", "Different theming approaches"),
                ("material-ui", "ant-design", "Theme system incompatibilities"),
            ]
        }
    
    @handle_errors(reraise=True)
    async def analyze_compatibility(self, 
                                  source_library: UILibraryType,
                                  target_library: UILibraryType) -> LibraryCompatibilityResult:
        """
        Analyze compatibility between two UI libraries.
        
        Args:
            source_library: The current/source UI library
            target_library: The target UI library to analyze compatibility with
            
        Returns:
            Detailed compatibility analysis result
        """
        
        print(f"🔍 Analyzing compatibility: {source_library.value} → {target_library.value}")
        
        result = LibraryCompatibilityResult(
            source_library=source_library,
            target_library=target_library,
            compatibility_level=self._get_compatibility_level(source_library, target_library),
            confidence=0.0
        )
        
        # Get component mappings
        result.compatible_components = await self._analyze_component_compatibility(
            source_library, target_library
        )
        
        # Analyze conflicts
        result.conflicting_components = self._identify_conflicting_components(
            source_library, target_library
        )
        
        # Find missing components
        result.missing_components = await self._identify_missing_components(
            source_library, target_library
        )
        
        # Analyze technical conflicts
        result.dependency_conflicts = self._analyze_dependency_conflicts(
            source_library, target_library
        )
        result.styling_conflicts = self._analyze_styling_conflicts(
            source_library, target_library
        )
        
        # Generate migration guidance
        result.migration_strategy = self._generate_migration_strategy(result)
        result.migration_steps = self._generate_migration_steps(result)
        result.potential_issues = self._identify_potential_issues(result)
        result.recommendations = self._generate_recommendations(result)
        
        # Calculate bundle size impact
        result.bundle_size_impact = self._estimate_bundle_impact(source_library, target_library)
        
        # Calculate overall confidence
        result.confidence = self._calculate_compatibility_confidence(result)
        
        print(f"   Compatibility: {result.compatibility_level.value}")
        print(f"   Compatible components: {len(result.compatible_components)}")
        print(f"   Conflicting components: {len(result.conflicting_components)}")
        print(f"   Missing components: {len(result.missing_components)}")
        
        return result
    
    def _get_compatibility_level(self, source: UILibraryType, target: UILibraryType) -> CompatibilityLevel:
        """Get base compatibility level between two libraries."""
        if source == target:
            return CompatibilityLevel.COMPATIBLE
        
        return self.compatibility_matrix.get(
            (source, target), 
            CompatibilityLevel.MINOR_CONFLICTS  # Default assumption
        )
    
    async def _analyze_component_compatibility(self, 
                                             source: UILibraryType,
                                             target: UILibraryType) -> List[ComponentMapping]:
        """Analyze component-level compatibility between libraries."""
        mappings = self.component_mappings.get((source, target), {})
        
        # If we don't have predefined mappings, try to generate them
        if not mappings:
            mappings = await self._generate_component_mappings(source, target)
        
        return list(mappings.values())
    
    async def _generate_component_mappings(self, 
                                         source: UILibraryType,
                                         target: UILibraryType) -> Dict[str, ComponentMapping]:
        """Generate component mappings between libraries using MCP data."""
        mappings = {}
        
        try:
            # Get component catalogs from both libraries
            source_context = await self.library_manager.get_library_context(source)
            target_context = await self.library_manager.get_library_context(target)
            
            if not source_context or not target_context:
                return mappings
            
            # Create mappings based on component names and descriptions
            for source_comp in source_context.components:
                best_match = None
                best_score = 0.0
                
                for target_comp in target_context.components:
                    score = self._calculate_component_similarity(source_comp, target_comp)
                    if score > best_score and score > 0.6:  # Minimum threshold
                        best_score = score
                        best_match = target_comp
                
                if best_match:
                    complexity = self._determine_migration_complexity(source_comp, best_match)
                    mappings[source_comp.name] = ComponentMapping(
                        source_component=source_comp.name,
                        target_component=best_match.name,
                        confidence=best_score,
                        migration_complexity=complexity,
                        migration_notes=f"Auto-generated mapping based on {best_score:.1%} similarity"
                    )
        
        except Exception as e:
            print(f"Warning: Failed to generate component mappings: {e}")
        
        return mappings
    
    def _calculate_component_similarity(self, comp1, comp2) -> float:
        """Calculate similarity between two components."""
        # Name similarity
        name_similarity = self._string_similarity(comp1.name.lower(), comp2.name.lower())
        
        # Description similarity (simple keyword matching)
        desc_similarity = self._description_similarity(
            comp1.description.lower(), comp2.description.lower()
        )
        
        # Prop similarity
        props1 = set(prop.lower() for prop in comp1.props)
        props2 = set(prop.lower() for prop in comp2.props)
        if props1 and props2:
            prop_similarity = len(props1 & props2) / len(props1 | props2)
        else:
            prop_similarity = 0.0
        
        # Weighted average
        return (name_similarity * 0.5 + desc_similarity * 0.3 + prop_similarity * 0.2)
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity using simple matching."""
        if s1 == s2:
            return 1.0
        
        # Check if one string contains the other
        if s1 in s2 or s2 in s1:
            return 0.8
        
        # Simple character overlap
        chars1 = set(s1)
        chars2 = set(s2)
        if chars1 and chars2:
            return len(chars1 & chars2) / len(chars1 | chars2)
        
        return 0.0
    
    def _description_similarity(self, desc1: str, desc2: str) -> float:
        """Calculate description similarity using keyword matching."""
        words1 = set(re.findall(r'\w+', desc1))
        words2 = set(re.findall(r'\w+', desc2))
        
        if words1 and words2:
            return len(words1 & words2) / len(words1 | words2)
        
        return 0.0
    
    def _determine_migration_complexity(self, source_comp, target_comp) -> MigrationComplexity:
        """Determine migration complexity between two components."""
        # Simple heuristic based on prop count difference
        source_props = len(source_comp.props)
        target_props = len(target_comp.props)
        prop_diff = abs(source_props - target_props)
        
        if prop_diff == 0:
            return MigrationComplexity.TRIVIAL
        elif prop_diff <= 2:
            return MigrationComplexity.SIMPLE
        elif prop_diff <= 5:
            return MigrationComplexity.MODERATE
        else:
            return MigrationComplexity.COMPLEX
    
    def _identify_conflicting_components(self, source: UILibraryType, target: UILibraryType) -> List[str]:
        """Identify components that have known conflicts between libraries."""
        conflicts = []
        
        # Known problematic combinations
        problematic_combinations = {
            (UILibraryType.CHAKRA_UI, UILibraryType.MATERIAL_UI): ["Theme", "CSSReset", "GlobalStyle"],
            (UILibraryType.MATERIAL_UI, UILibraryType.ANT_DESIGN): ["ThemeProvider", "GlobalStyles"],
            (UILibraryType.CHAKRA_UI, UILibraryType.ANT_DESIGN): ["ConfigProvider", "Theme"],
        }
        
        return problematic_combinations.get((source, target), [])
    
    async def _identify_missing_components(self, source: UILibraryType, target: UILibraryType) -> List[str]:
        """Identify components that exist in source but not in target library."""
        missing = []
        
        try:
            source_context = await self.library_manager.get_library_context(source)
            target_context = await self.library_manager.get_library_context(target)
            
            if source_context and target_context:
                source_names = {comp.name.lower() for comp in source_context.components}
                target_names = {comp.name.lower() for comp in target_context.components}
                
                missing_names = source_names - target_names
                missing = [name.title() for name in missing_names]
        
        except Exception as e:
            print(f"Warning: Failed to identify missing components: {e}")
        
        return missing
    
    def _analyze_dependency_conflicts(self, source: UILibraryType, target: UILibraryType) -> List[str]:
        """Analyze potential dependency conflicts."""
        conflicts = []
        
        # Known dependency conflicts
        dependency_conflicts = {
            (UILibraryType.CHAKRA_UI, UILibraryType.MATERIAL_UI): [
                "Emotion version conflicts",
                "React version requirements may differ"
            ],
            (UILibraryType.MATERIAL_UI, UILibraryType.ANT_DESIGN): [
                "CSS-in-JS library conflicts",
                "Peer dependency version mismatches"
            ],
            (UILibraryType.CHAKRA_UI, UILibraryType.ANT_DESIGN): [
                "Different CSS-in-JS approaches",
                "Theme system conflicts"
            ]
        }
        
        return dependency_conflicts.get((source, target), [])
    
    def _analyze_styling_conflicts(self, source: UILibraryType, target: UILibraryType) -> List[str]:
        """Analyze potential styling conflicts."""
        conflicts = []
        
        # Known styling conflicts
        styling_conflicts = {
            (UILibraryType.CHAKRA_UI, UILibraryType.MATERIAL_UI): [
                "Global CSS resets conflict",
                "Different box-sizing approaches",
                "Theme variable naming conflicts"
            ],
            (UILibraryType.SHADCN_UI, UILibraryType.CHAKRA_UI): [
                "Tailwind CSS vs Chakra styling conflicts",
                "Different responsive breakpoint systems"
            ],
            (UILibraryType.MATERIAL_UI, UILibraryType.ANT_DESIGN): [
                "Material Design vs Ant Design visual conflicts",
                "Different elevation/shadow systems"
            ]
        }
        
        return styling_conflicts.get((source, target), [])
    
    def _generate_migration_strategy(self, result: LibraryCompatibilityResult) -> str:
        """Generate overall migration strategy."""
        if result.compatibility_level == CompatibilityLevel.COMPATIBLE:
            return "PARALLEL_ADOPTION: Libraries can work together with minimal conflicts"
        elif result.compatibility_level == CompatibilityLevel.MINOR_CONFLICTS:
            return "GRADUAL_MIGRATION: Migrate components incrementally while resolving minor conflicts"
        elif result.compatibility_level == CompatibilityLevel.MAJOR_CONFLICTS:
            return "STAGED_REPLACEMENT: Replace entire sections at once to avoid conflicts"
        else:
            return "COMPLETE_REWRITE: Full migration required due to incompatibilities"
    
    def _generate_migration_steps(self, result: LibraryCompatibilityResult) -> List[str]:
        """Generate step-by-step migration guidance."""
        steps = []
        
        if result.compatibility_level == CompatibilityLevel.COMPATIBLE:
            steps = [
                "Install target library alongside existing library",
                "Begin using target library for new components",
                "Gradually migrate existing components when convenient"
            ]
        elif result.compatibility_level == CompatibilityLevel.MINOR_CONFLICTS:
            steps = [
                "Audit existing components for compatibility",
                "Create migration mapping for each component type",
                "Set up isolated testing environment",
                "Migrate components in logical groups",
                "Update styling and theme configurations",
                "Resolve any remaining conflicts"
            ]
        else:
            steps = [
                "Plan comprehensive migration strategy",
                "Set up parallel development environment",
                "Create component migration checklist",
                "Migrate critical path components first",
                "Update all styling and theming",
                "Thoroughly test for conflicts",
                "Remove old library dependencies"
            ]
        
        return steps
    
    def _identify_potential_issues(self, result: LibraryCompatibilityResult) -> List[str]:
        """Identify potential issues during migration."""
        issues = []
        
        # Add dependency-related issues
        if result.dependency_conflicts:
            issues.extend([f"Dependency issue: {conflict}" for conflict in result.dependency_conflicts])
        
        # Add styling-related issues
        if result.styling_conflicts:
            issues.extend([f"Styling issue: {conflict}" for conflict in result.styling_conflicts])
        
        # Add component-specific issues
        if result.missing_components:
            issues.append(f"Missing components in target library: {', '.join(result.missing_components[:5])}")
        
        if result.conflicting_components:
            issues.append(f"Components with known conflicts: {', '.join(result.conflicting_components)}")
        
        return issues
    
    def _generate_recommendations(self, result: LibraryCompatibilityResult) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # General recommendations based on compatibility level
        if result.compatibility_level == CompatibilityLevel.COMPATIBLE:
            recommendations.extend([
                "Consider gradual adoption of new library",
                "Use new library for all new development",
                "Create style guide for consistent usage"
            ])
        elif result.compatibility_level == CompatibilityLevel.MINOR_CONFLICTS:
            recommendations.extend([
                "Plan migration in phases to minimize disruption",
                "Create component mapping documentation",
                "Set up automated testing for visual regressions"
            ])
        else:
            recommendations.extend([
                "Consider if migration benefits justify the effort",
                "Plan for significant development time",
                "Consider hiring specialists for complex migration"
            ])
        
        # Specific recommendations based on analysis
        if len(result.compatible_components) > 10:
            recommendations.append("Good component compatibility - migration should be straightforward")
        
        if result.bundle_size_impact:
            recommendations.append(f"Bundle size consideration: {result.bundle_size_impact}")
        
        return recommendations
    
    def _estimate_bundle_impact(self, source: UILibraryType, target: UILibraryType) -> str:
        """Estimate bundle size impact of using both libraries."""
        # Rough estimates based on library sizes
        library_sizes = {
            UILibraryType.CHAKRA_UI: 150,  # KB
            UILibraryType.MATERIAL_UI: 300,
            UILibraryType.ANT_DESIGN: 400,
            UILibraryType.SHADCN_UI: 50,   # Much smaller due to copy-paste nature
            UILibraryType.TAILWIND_UI: 30,
        }
        
        source_size = library_sizes.get(source, 100)
        target_size = library_sizes.get(target, 100)
        combined_size = source_size + target_size
        
        if combined_size > 500:
            return f"Large impact: ~{combined_size}KB additional bundle size"
        elif combined_size > 300:
            return f"Moderate impact: ~{combined_size}KB additional bundle size"
        else:
            return f"Minor impact: ~{combined_size}KB additional bundle size"
    
    def _calculate_compatibility_confidence(self, result: LibraryCompatibilityResult) -> float:
        """Calculate overall confidence in the compatibility analysis."""
        base_confidence = 0.7
        
        # Boost confidence based on successful component mappings
        if result.compatible_components:
            mapping_confidence = sum(m.confidence for m in result.compatible_components) / len(result.compatible_components)
            base_confidence += (mapping_confidence - 0.5) * 0.3
        
        # Reduce confidence based on conflicts
        conflict_penalty = (len(result.conflicting_components) + len(result.missing_components)) * 0.05
        base_confidence -= conflict_penalty
        
        return max(0.0, min(1.0, base_confidence))
    
    @handle_errors(reraise=True)
    async def analyze_project_compatibility(self, project_path: str = None) -> List[LibraryCompatibilityResult]:
        """
        Analyze compatibility for the current project with all supported libraries.
        
        Args:
            project_path: Path to analyze (uses instance path if not provided)
            
        Returns:
            List of compatibility results for all relevant library combinations
        """
        if project_path:
            self.project_path = Path(project_path)
            self.library_manager = MCPUILibraryManager(project_path)
        
        # Detect current library
        current_library = await self.library_manager.detect_project_ui_library()
        
        if not current_library:
            print("No UI library detected in project")
            return []
        
        print(f"🔍 Analyzing compatibility for current library: {current_library.value}")
        
        results = []
        
        # Analyze compatibility with all other libraries
        all_libraries = [
            UILibraryType.CHAKRA_UI,
            UILibraryType.MATERIAL_UI, 
            UILibraryType.ANT_DESIGN,
            UILibraryType.SHADCN_UI,
            UILibraryType.TAILWIND_UI,
            UILibraryType.MANTINE
        ]
        
        for target_library in all_libraries:
            if target_library != current_library:
                try:
                    result = await self.analyze_compatibility(current_library, target_library)
                    results.append(result)
                except Exception as e:
                    print(f"Warning: Failed to analyze {target_library.value}: {e}")
        
        # Sort by compatibility level and confidence
        results.sort(key=lambda r: (r.compatibility_level.value, -r.confidence))
        
        return results
    
    def generate_compatibility_report(self, results: List[LibraryCompatibilityResult]) -> str:
        """Generate a human-readable compatibility report."""
        if not results:
            return "No compatibility analysis results available."
        
        report_lines = [
            f"# UI Library Compatibility Report",
            f"Source Library: {results[0].source_library.value}",
            "",
            "## Compatibility Summary",
            ""
        ]
        
        for result in results:
            status_emoji = {
                CompatibilityLevel.COMPATIBLE: "✅",
                CompatibilityLevel.MINOR_CONFLICTS: "⚠️",
                CompatibilityLevel.MAJOR_CONFLICTS: "❌", 
                CompatibilityLevel.INCOMPATIBLE: "🚫"
            }.get(result.compatibility_level, "❓")
            
            report_lines.extend([
                f"{status_emoji} **{result.target_library.value}** - {result.compatibility_level.value.title()}",
                f"   Confidence: {result.confidence:.1%}",
                f"   Compatible components: {len(result.compatible_components)}",
                f"   Migration strategy: {result.migration_strategy}",
                ""
            ])
        
        # Add detailed analysis for best option
        if results:
            best_result = results[0]
            report_lines.extend([
                "## Recommended Migration Target",
                f"**{best_result.target_library.value}** ({best_result.compatibility_level.value})",
                "",
                "### Migration Steps:",
            ])
            
            for i, step in enumerate(best_result.migration_steps, 1):
                report_lines.append(f"{i}. {step}")
            
            if best_result.recommendations:
                report_lines.extend([
                    "",
                    "### Recommendations:",
                ])
                for rec in best_result.recommendations:
                    report_lines.append(f"- {rec}")
        
        return "\n".join(report_lines)