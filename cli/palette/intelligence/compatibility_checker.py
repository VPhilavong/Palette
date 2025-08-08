"""
Compatibility Checker for cross-validating framework and styling system detection.
Ensures detected configurations are compatible and resolves conflicts intelligently.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

from .framework_detector import Framework, FrameworkAnalysis
from .styling_analyzer import StylingSystem, StylingAnalysis
from .pattern_extractor import PatternAnalysis
from ..errors.decorators import handle_errors


@dataclass
class ValidationResult:
    """Result of compatibility validation."""
    framework: Framework
    styling_system: StylingSystem
    confidence: float
    compatibility_score: float
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    resolution_applied: Optional[str] = None


@dataclass
class CompatibilityRule:
    """Rule for checking framework/styling system compatibility."""
    name: str
    framework: Framework
    styling_system: StylingSystem
    compatibility_score: float  # 0.0 to 1.0
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class CompatibilityChecker:
    """
    Cross-validates framework and styling system detection results.
    Resolves conflicts and ensures detected configurations make sense.
    """
    
    def __init__(self):
        self._initialize_compatibility_rules()
        self._initialize_conflict_resolution()
    
    def _initialize_compatibility_rules(self):
        """Initialize compatibility rules between frameworks and styling systems."""
        
        self.compatibility_rules = [
            # Next.js compatibilities
            CompatibilityRule(
                name="NextJS_Tailwind",
                framework=Framework.NEXT_JS,
                styling_system=StylingSystem.TAILWIND,
                compatibility_score=0.95,
                recommendations=["Excellent combination - widely used and well supported"]
            ),
            CompatibilityRule(
                name="NextJS_ChakraUI",
                framework=Framework.NEXT_JS,
                styling_system=StylingSystem.CHAKRA_UI,
                compatibility_score=0.9,
                recommendations=["Great combination with good SSR support"]
            ),
            CompatibilityRule(
                name="NextJS_MaterialUI",
                framework=Framework.NEXT_JS,
                styling_system=StylingSystem.MATERIAL_UI,
                compatibility_score=0.85,
                recommendations=["Good combination, ensure proper SSR configuration"]
            ),
            CompatibilityRule(
                name="NextJS_ShadcnUI",
                framework=Framework.NEXT_JS,
                styling_system=StylingSystem.SHADCN_UI,
                compatibility_score=0.95,
                recommendations=["Excellent modern combination with great DX"]
            ),
            CompatibilityRule(
                name="NextJS_StyledComponents",
                framework=Framework.NEXT_JS,
                styling_system=StylingSystem.STYLED_COMPONENTS,
                compatibility_score=0.7,
                issues=["Requires babel configuration for SSR"],
                recommendations=["Consider switching to Tailwind or CSS modules for better Next.js integration"]
            ),
            
            # React compatibilities
            CompatibilityRule(
                name="React_Tailwind",
                framework=Framework.REACT,
                styling_system=StylingSystem.TAILWIND,
                compatibility_score=0.9,
                recommendations=["Popular and well-supported combination"]
            ),
            CompatibilityRule(
                name="React_ChakraUI", 
                framework=Framework.REACT,
                styling_system=StylingSystem.CHAKRA_UI,
                compatibility_score=0.95,
                recommendations=["Excellent React-first component library"]
            ),
            CompatibilityRule(
                name="React_MaterialUI",
                framework=Framework.REACT,
                styling_system=StylingSystem.MATERIAL_UI,
                compatibility_score=0.9,
                recommendations=["Mature and feature-rich component library"]
            ),
            CompatibilityRule(
                name="React_Mantine",
                framework=Framework.REACT,
                styling_system=StylingSystem.MANTINE,
                compatibility_score=0.85,
                recommendations=["Modern component library with good TypeScript support"]
            ),
            CompatibilityRule(
                name="React_StyledComponents",
                framework=Framework.REACT,
                styling_system=StylingSystem.STYLED_COMPONENTS,
                compatibility_score=0.8,
                recommendations=["Popular CSS-in-JS solution for React"]
            ),
            
            # Vite React compatibilities
            CompatibilityRule(
                name="ViteReact_Tailwind",
                framework=Framework.VITE_REACT,
                styling_system=StylingSystem.TAILWIND,
                compatibility_score=0.95,
                recommendations=["Perfect combination with fast build times"]
            ),
            CompatibilityRule(
                name="ViteReact_ChakraUI",
                framework=Framework.VITE_REACT,
                styling_system=StylingSystem.CHAKRA_UI,
                compatibility_score=0.9,
                recommendations=["Great development experience with Vite's fast refresh"]
            ),
            
            # Create React App compatibilities
            CompatibilityRule(
                name="CRA_Tailwind",
                framework=Framework.CREATE_REACT_APP,
                styling_system=StylingSystem.TAILWIND,
                compatibility_score=0.8,
                issues=["May require CRACO for full Tailwind configuration"],
                recommendations=["Consider ejecting or switching to Vite for better Tailwind support"]
            ),
            CompatibilityRule(
                name="CRA_ChakraUI",
                framework=Framework.CREATE_REACT_APP,
                styling_system=StylingSystem.CHAKRA_UI,
                compatibility_score=0.85,
                recommendations=["Works well out of the box"]
            ),
            
            # Problematic combinations
            CompatibilityRule(
                name="NextJS_Emotion_Conflict",
                framework=Framework.NEXT_JS,
                styling_system=StylingSystem.EMOTION,
                compatibility_score=0.6,
                issues=["Requires specific SSR configuration", "May have hydration issues"],
                recommendations=["Ensure proper _document.js configuration", "Consider Tailwind for simpler setup"]
            )
        ]
        
        # Create lookup map for quick access
        self.compatibility_map = {}
        for rule in self.compatibility_rules:
            key = (rule.framework, rule.styling_system)
            self.compatibility_map[key] = rule
    
    def _initialize_conflict_resolution(self):
        """Initialize conflict resolution strategies."""
        
        self.conflict_resolvers = {
            # Chakra UI + Tailwind conflict (CRITICAL)
            frozenset([StylingSystem.CHAKRA_UI, StylingSystem.TAILWIND]): self._resolve_chakra_tailwind_conflict,
            
            # Material UI + Tailwind conflict
            frozenset([StylingSystem.MATERIAL_UI, StylingSystem.TAILWIND]): self._resolve_mui_tailwind_conflict,
            
            # Multiple component libraries
            frozenset([StylingSystem.CHAKRA_UI, StylingSystem.MATERIAL_UI]): self._resolve_multiple_component_libs,
            
            # CSS-in-JS conflicts
            frozenset([StylingSystem.STYLED_COMPONENTS, StylingSystem.EMOTION]): self._resolve_css_in_js_conflict,
        }
    
    @handle_errors(reraise=True)
    def validate_compatibility(
        self, 
        framework_analysis: FrameworkAnalysis,
        styling_analysis: StylingAnalysis,
        pattern_analysis: PatternAnalysis
    ) -> ValidationResult:
        """
        Validate compatibility between detected framework and styling system.
        
        Args:
            framework_analysis: Framework detection results
            styling_analysis: Styling system detection results  
            pattern_analysis: Code pattern analysis results
            
        Returns:
            Validation result with resolved configuration
        """
        
        # Check for critical conflicts first
        conflicts = self._detect_conflicts(styling_analysis)
        
        if conflicts:
            # Apply conflict resolution
            resolved_styling = self._resolve_conflicts(conflicts, styling_analysis, pattern_analysis)
            styling_analysis = resolved_styling
        
        # Get compatibility rule
        compatibility_rule = self._get_compatibility_rule(
            framework_analysis.primary_framework, 
            styling_analysis.primary_system
        )
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(
            framework_analysis, styling_analysis, compatibility_rule
        )
        
        # Collect issues and recommendations
        issues = []
        recommendations = []
        
        # Add framework-specific issues
        if framework_analysis.confidence < 0.7:
            issues.append(f"Low framework detection confidence: {framework_analysis.confidence:.1%}")
        
        # Add styling-specific issues
        if styling_analysis.confidence < 0.7:
            issues.append(f"Low styling system detection confidence: {styling_analysis.confidence:.1%}")
        
        # Add compatibility issues
        if compatibility_rule:
            issues.extend(compatibility_rule.issues)
            recommendations.extend(compatibility_rule.recommendations)
        
        # Add conflict-related issues
        if conflicts:
            issues.extend([f"Conflict detected: {conflict}" for conflict in conflicts])
        
        # Add pattern-based recommendations
        pattern_recommendations = self._get_pattern_recommendations(pattern_analysis)
        recommendations.extend(pattern_recommendations)
        
        return ValidationResult(
            framework=framework_analysis.primary_framework,
            styling_system=styling_analysis.primary_system,
            confidence=overall_confidence,
            compatibility_score=compatibility_rule.compatibility_score if compatibility_rule else 0.5,
            issues=issues,
            recommendations=recommendations,
            resolution_applied="conflict_resolution" if conflicts else None
        )
    
    def _detect_conflicts(self, styling_analysis: StylingAnalysis) -> List[str]:
        """Detect conflicts in styling system detection."""
        conflicts = []
        
        # Check for Chakra UI + Tailwind conflict (CRITICAL)
        systems = [styling_analysis.primary_system] + [sys for sys, _ in styling_analysis.secondary_systems]
        
        if (StylingSystem.CHAKRA_UI in systems and StylingSystem.TAILWIND in systems):
            conflicts.append("CRITICAL: Both Chakra UI and Tailwind detected")
        
        if (StylingSystem.MATERIAL_UI in systems and StylingSystem.TAILWIND in systems):
            conflicts.append("Material UI and Tailwind both detected")
        
        if (StylingSystem.CHAKRA_UI in systems and StylingSystem.MATERIAL_UI in systems):
            conflicts.append("Multiple component libraries detected: Chakra UI and Material UI")
        
        if (StylingSystem.STYLED_COMPONENTS in systems and StylingSystem.EMOTION in systems):
            conflicts.append("Multiple CSS-in-JS libraries detected")
        
        return conflicts
    
    def _resolve_conflicts(
        self, 
        conflicts: List[str], 
        styling_analysis: StylingAnalysis,
        pattern_analysis: PatternAnalysis
    ) -> StylingAnalysis:
        """Resolve detected conflicts using intelligent strategies."""
        
        # Identify conflict type
        systems = [styling_analysis.primary_system] + [sys for sys, _ in styling_analysis.secondary_systems]
        conflict_set = frozenset(systems)
        
        # Apply appropriate resolver
        for conflict_key, resolver in self.conflict_resolvers.items():
            if conflict_key.issubset(conflict_set):
                return resolver(styling_analysis, pattern_analysis)
        
        # Default: return original analysis
        return styling_analysis
    
    def _resolve_chakra_tailwind_conflict(
        self, 
        styling_analysis: StylingAnalysis,
        pattern_analysis: PatternAnalysis
    ) -> StylingAnalysis:
        """
        Resolve Chakra UI + Tailwind conflict.
        This is the CRITICAL conflict that causes wrong code generation.
        """
        
        # Look for evidence in patterns
        chakra_evidence = 0
        tailwind_evidence = 0
        
        # Check styling patterns
        for pattern_list in pattern_analysis.patterns.get('styling', []):
            for pattern in pattern_list:
                if 'chakra' in pattern.pattern.lower():
                    chakra_evidence += pattern.frequency
                elif 'tailwind' in pattern.pattern.lower():
                    tailwind_evidence += pattern.frequency
        
        # Check component patterns  
        for pattern_list in pattern_analysis.patterns.get('components', []):
            for pattern in pattern_list:
                if any(comp in pattern.pattern.lower() for comp in ['box', 'button', 'text', 'flex']):
                    # These could be Chakra components
                    chakra_evidence += pattern.frequency
        
        # Check import patterns
        for pattern_list in pattern_analysis.patterns.get('imports', []):
            for pattern in pattern_list:
                if '@chakra-ui' in pattern.pattern:
                    chakra_evidence += pattern.frequency * 2  # Strong evidence
                elif 'tailwindcss' in pattern.pattern:
                    tailwind_evidence += pattern.frequency * 2
        
        # Prefer Chakra UI if there's component usage evidence
        if chakra_evidence > tailwind_evidence:
            resolved_analysis = StylingAnalysis(
                primary_system=StylingSystem.CHAKRA_UI,
                confidence=max(0.8, styling_analysis.confidence),
                secondary_systems=[(StylingSystem.TAILWIND, 0.3)],  # Demote Tailwind
                conflicts_detected=styling_analysis.conflicts_detected + [
                    "RESOLVED: Chakra UI chosen over Tailwind based on component usage patterns"
                ],
                recommendations=styling_analysis.recommendations + [
                    "Ensure no Tailwind classes are used in component generation",
                    "Use Chakra UI component props for all styling"
                ]
            )
        else:
            # Default to Tailwind but add strong warnings
            resolved_analysis = StylingAnalysis(
                primary_system=StylingSystem.TAILWIND,
                confidence=max(0.7, styling_analysis.confidence),
                secondary_systems=[(StylingSystem.CHAKRA_UI, 0.3)],  # Demote Chakra
                conflicts_detected=styling_analysis.conflicts_detected + [
                    "RESOLVED: Tailwind chosen but Chakra UI presence detected"
                ],
                recommendations=styling_analysis.recommendations + [
                    "WARNING: Mixed styling systems detected",
                    "Consider removing unused Chakra UI dependencies",
                    "Ensure consistent styling approach throughout project"
                ]
            )
        
        return resolved_analysis
    
    def _resolve_mui_tailwind_conflict(
        self, 
        styling_analysis: StylingAnalysis,
        pattern_analysis: PatternAnalysis
    ) -> StylingAnalysis:
        """Resolve Material UI + Tailwind conflict."""
        
        # Material UI is usually primary when detected with Tailwind
        # as Tailwind might be used for custom styling alongside MUI
        return StylingAnalysis(
            primary_system=StylingSystem.MATERIAL_UI,
            confidence=styling_analysis.confidence,
            secondary_systems=[(StylingSystem.TAILWIND, 0.4)],
            conflicts_detected=styling_analysis.conflicts_detected + [
                "RESOLVED: Material UI chosen as primary, Tailwind as utility"
            ],
            recommendations=styling_analysis.recommendations + [
                "Use Material UI components as primary",
                "Use Tailwind for custom utilities when needed"
            ]
        )
    
    def _resolve_multiple_component_libs(
        self, 
        styling_analysis: StylingAnalysis,
        pattern_analysis: PatternAnalysis
    ) -> StylingAnalysis:
        """Resolve multiple component libraries conflict."""
        
        # This is unusual - prefer the one with higher confidence
        if styling_analysis.primary_system in [StylingSystem.CHAKRA_UI, StylingSystem.MATERIAL_UI]:
            return StylingAnalysis(
                primary_system=styling_analysis.primary_system,
                confidence=styling_analysis.confidence * 0.8,  # Reduce confidence
                secondary_systems=[],
                conflicts_detected=styling_analysis.conflicts_detected + [
                    "RESOLVED: Multiple component libraries detected - using highest confidence"
                ],
                recommendations=styling_analysis.recommendations + [
                    "WARNING: Multiple component libraries detected",
                    "Consider consolidating to a single component library"
                ]
            )
        
        return styling_analysis
    
    def _resolve_css_in_js_conflict(
        self, 
        styling_analysis: StylingAnalysis,
        pattern_analysis: PatternAnalysis
    ) -> StylingAnalysis:
        """Resolve CSS-in-JS library conflicts."""
        
        # Usually not a major issue - both can coexist
        return StylingAnalysis(
            primary_system=styling_analysis.primary_system,
            confidence=styling_analysis.confidence,
            secondary_systems=styling_analysis.secondary_systems,
            conflicts_detected=styling_analysis.conflicts_detected + [
                "INFO: Multiple CSS-in-JS libraries detected - usually not problematic"
            ],
            recommendations=styling_analysis.recommendations + [
                "Multiple CSS-in-JS libraries can coexist",
                "Consider standardizing on one for consistency"
            ]
        )
    
    def _get_compatibility_rule(
        self, 
        framework: Framework, 
        styling_system: StylingSystem
    ) -> Optional[CompatibilityRule]:
        """Get compatibility rule for framework/styling system combination."""
        return self.compatibility_map.get((framework, styling_system))
    
    def _calculate_overall_confidence(
        self, 
        framework_analysis: FrameworkAnalysis,
        styling_analysis: StylingAnalysis,
        compatibility_rule: Optional[CompatibilityRule]
    ) -> float:
        """Calculate overall confidence score."""
        
        # Base confidence from individual analyses
        base_confidence = (framework_analysis.confidence + styling_analysis.confidence) / 2
        
        # Adjust based on compatibility
        if compatibility_rule:
            compatibility_boost = compatibility_rule.compatibility_score * 0.2
            base_confidence += compatibility_boost
        
        # Penalize for low individual confidence
        if framework_analysis.confidence < 0.5 or styling_analysis.confidence < 0.5:
            base_confidence *= 0.8
        
        return min(1.0, base_confidence)
    
    def _get_pattern_recommendations(self, pattern_analysis: PatternAnalysis) -> List[str]:
        """Get recommendations based on code patterns."""
        recommendations = []
        
        # Check TypeScript usage
        ts_files = sum(1 for f in pattern_analysis.patterns.get('naming', []) 
                      if any('.tsx' in ex or '.ts' in ex for ex in f.examples))
        
        if ts_files > 5:
            recommendations.append("TypeScript detected - ensure proper type definitions in generated components")
        
        # Check for testing patterns
        test_patterns = sum(1 for pattern_list in pattern_analysis.patterns.values()
                           for pattern in pattern_list
                           for example in pattern.examples
                           if 'test' in example.lower() or 'spec' in example.lower())
        
        if test_patterns > 0:
            recommendations.append("Testing patterns detected - consider generating test files alongside components")
        
        return recommendations