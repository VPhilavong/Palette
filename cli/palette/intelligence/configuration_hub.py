"""
Configuration Intelligence Hub - Central system for comprehensive project analysis.
Addresses critical framework detection issues through multi-source analysis
and intelligent conflict resolution.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set

from .styling_analyzer import StylingSystemAnalyzer, StylingSystem, StylingAnalysis
from .framework_detector import EnhancedFrameworkDetector, FrameworkAnalysis, Framework
from .pattern_extractor import ProjectPatternExtractor, PatternAnalysis
from .compatibility_checker import CompatibilityChecker, ValidationResult
from ..errors.decorators import handle_errors


class ComponentLibrary(Enum):
    """Supported component libraries."""
    CHAKRA_UI = "chakra-ui"
    MATERIAL_UI = "material-ui"
    ANT_DESIGN = "ant-design"
    MANTINE = "mantine"
    SHADCN_UI = "shadcn/ui"
    REACT_BOOTSTRAP = "react-bootstrap"
    SEMANTIC_UI = "semantic-ui"
    HEADLESS_UI = "headless-ui"
    NONE = "none"


class BuildTool(Enum):
    """Build tools and bundlers."""
    WEBPACK = "webpack"
    VITE = "vite" 
    PARCEL = "parcel"
    ROLLUP = "rollup"
    TURBOPACK = "turbopack"
    SWC = "swc"


@dataclass
class ProjectConfiguration:
    """Complete project configuration analysis."""
    framework: Framework
    styling_system: StylingSystem
    component_library: ComponentLibrary
    build_tool: Optional[BuildTool] = None
    typescript: bool = False
    confidence_score: float = 0.0
    
    # Analysis details
    pattern_library: Dict[str, Any] = field(default_factory=dict)
    compatibility_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Generation strategy info
    generation_strategy: Optional[str] = None
    context_priorities: Dict[str, float] = field(default_factory=dict)
    
    # Metadata
    analysis_metadata: Dict[str, Any] = field(default_factory=dict)


class ConfigurationIntelligenceHub:
    """
    Central intelligence system for comprehensive project configuration detection.
    
    This system addresses the critical framework detection issues by:
    1. Multi-source analysis with weighted confidence scoring
    2. Cross-validation between different detection methods
    3. Conflict resolution with intelligent prioritization
    4. Generation strategy selection based on detected configuration
    """
    
    def __init__(self):
        # Initialize component analyzers
        self.framework_detector = EnhancedFrameworkDetector()
        self.styling_analyzer = StylingSystemAnalyzer()
        self.pattern_extractor = ProjectPatternExtractor()
        self.compatibility_checker = CompatibilityChecker()
        
        # Configuration mappings for strategy selection
        self._initialize_strategy_mappings()
        self._initialize_context_priorities()
    
    def _initialize_strategy_mappings(self):
        """Initialize mappings from configurations to generation strategies."""
        self.strategy_mappings = {
            # Chakra UI configurations
            (Framework.NEXT_JS, StylingSystem.CHAKRA_UI): "NextJSChakraUI",
            (Framework.REACT, StylingSystem.CHAKRA_UI): "ReactChakraUI", 
            (Framework.VITE_REACT, StylingSystem.CHAKRA_UI): "ViteReactChakraUI",
            
            # Tailwind configurations
            (Framework.NEXT_JS, StylingSystem.TAILWIND): "NextJSTailwind",
            (Framework.REACT, StylingSystem.TAILWIND): "ReactTailwind",
            (Framework.VITE_REACT, StylingSystem.TAILWIND): "ViteReactTailwind",
            
            # Shadcn/ui configurations (uses Tailwind)
            (Framework.NEXT_JS, StylingSystem.SHADCN_UI): "NextJSShadcnUI",
            (Framework.REACT, StylingSystem.SHADCN_UI): "ReactShadcnUI",
            
            # Material-UI configurations  
            (Framework.NEXT_JS, StylingSystem.MATERIAL_UI): "NextJSMaterialUI",
            (Framework.REACT, StylingSystem.MATERIAL_UI): "ReactMaterialUI",
            
            # Mantine configurations
            (Framework.REACT, StylingSystem.MANTINE): "ReactMantine",
            (Framework.NEXT_JS, StylingSystem.MANTINE): "NextJSMantine",
        }
    
    def _initialize_context_priorities(self):
        """Initialize context priorities for different configurations."""
        self.context_priorities = {
            # Chakra UI prioritizes component examples over utility classes
            StylingSystem.CHAKRA_UI: {
                'component_examples': 0.9,
                'design_tokens': 0.4,
                'framework_patterns': 0.8,
                'styling_patterns': 0.3,
                'accessibility_patterns': 0.7
            },
            
            # Tailwind prioritizes utility classes and design tokens
            StylingSystem.TAILWIND: {
                'component_examples': 0.5,
                'design_tokens': 0.9,
                'framework_patterns': 0.8,
                'styling_patterns': 0.9,
                'accessibility_patterns': 0.6
            },
            
            # Shadcn/ui uses Tailwind but with specific component patterns
            StylingSystem.SHADCN_UI: {
                'component_examples': 0.8,
                'design_tokens': 0.7,
                'framework_patterns': 0.8,
                'styling_patterns': 0.8,
                'accessibility_patterns': 0.7
            },
            
            # Material-UI prioritizes component library patterns
            StylingSystem.MATERIAL_UI: {
                'component_examples': 0.9,
                'design_tokens': 0.5,
                'framework_patterns': 0.8,
                'styling_patterns': 0.4,
                'accessibility_patterns': 0.7
            }
        }
    
    @handle_errors(reraise=True)
    def analyze_configuration(self, project_path: str) -> ProjectConfiguration:
        """
        Comprehensive project configuration analysis.
        
        This is the main method that addresses framework detection issues
        through multi-layer analysis and intelligent conflict resolution.
        
        Args:
            project_path: Path to the project to analyze
            
        Returns:
            Complete project configuration with confidence scoring
        """
        project_path = Path(project_path)
        
        print(f"🔍 Starting comprehensive configuration analysis for {project_path}")
        
        # Phase 1: Multi-source detection
        print("📊 Phase 1: Multi-source detection...")
        
        framework_analysis = self.framework_detector.deep_analyze(str(project_path))
        styling_analysis = self.styling_analyzer.comprehensive_scan(str(project_path))
        pattern_analysis = self.pattern_extractor.extract_patterns(str(project_path))
        
        print(f"   Framework: {framework_analysis.primary_framework.value} (confidence: {framework_analysis.confidence:.2f})")
        print(f"   Styling: {styling_analysis.primary_system.value} (confidence: {styling_analysis.confidence:.2f})")
        print(f"   Patterns: {len(pattern_analysis.patterns)} patterns extracted")
        
        # Phase 2: Cross-validation and conflict resolution
        print("🔗 Phase 2: Cross-validation...")
        
        validated_config = self.compatibility_checker.validate_compatibility(
            framework_analysis, styling_analysis, pattern_analysis
        )
        
        # Phase 3: Configuration assembly
        print("⚙️ Phase 3: Configuration assembly...")
        
        config = ProjectConfiguration(
            framework=validated_config.framework,
            styling_system=validated_config.styling_system,
            component_library=self._detect_component_library(project_path, styling_analysis),
            build_tool=self._detect_build_tool(project_path),
            typescript=self._detect_typescript(project_path),
            confidence_score=validated_config.confidence,
            pattern_library=pattern_analysis.patterns,
            compatibility_issues=validated_config.issues,
            recommendations=validated_config.recommendations
        )
        
        # Phase 4: Strategy selection and context prioritization
        print("🎯 Phase 4: Strategy selection...")
        
        config.generation_strategy = self._select_generation_strategy(config)
        config.context_priorities = self._get_context_priorities(config)
        
        # Phase 5: Final validation and metadata
        print("✨ Phase 5: Final validation...")
        
        config.analysis_metadata = {
            'analysis_timestamp': self._get_timestamp(),
            'project_size': self._estimate_project_size(project_path),
            'complexity_score': self._calculate_complexity_score(config),
            'framework_confidence': framework_analysis.confidence,
            'styling_confidence': styling_analysis.confidence,
            'total_files_analyzed': self._count_analyzed_files(project_path),
            'critical_issues': [issue for issue in config.compatibility_issues if 'CRITICAL' in issue]
        }
        
        self._print_analysis_summary(config)
        
        return config
    
    def _detect_component_library(self, project_path: Path, styling_analysis: StylingAnalysis) -> ComponentLibrary:
        """Detect component library from styling analysis and package.json."""
        
        # First check if styling system implies component library
        if styling_analysis.primary_system == StylingSystem.CHAKRA_UI:
            return ComponentLibrary.CHAKRA_UI
        elif styling_analysis.primary_system == StylingSystem.MATERIAL_UI:
            return ComponentLibrary.MATERIAL_UI
        elif styling_analysis.primary_system == StylingSystem.MANTINE:
            return ComponentLibrary.MANTINE
        elif styling_analysis.primary_system == StylingSystem.ANT_DESIGN:
            return ComponentLibrary.ANT_DESIGN
        elif styling_analysis.primary_system == StylingSystem.SHADCN_UI:
            return ComponentLibrary.SHADCN_UI
        
        # Check package.json for additional component libraries
        package_json = project_path / "package.json"
        if package_json.exists():
            try:
                import json
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
                
                all_deps = {}
                all_deps.update(package_data.get('dependencies', {}))
                all_deps.update(package_data.get('devDependencies', {}))
                
                # Check for component libraries
                if 'react-bootstrap' in all_deps:
                    return ComponentLibrary.REACT_BOOTSTRAP
                elif '@headlessui/react' in all_deps:
                    return ComponentLibrary.HEADLESS_UI
                elif 'semantic-ui-react' in all_deps:
                    return ComponentLibrary.SEMANTIC_UI
                    
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return ComponentLibrary.NONE
    
    def _detect_build_tool(self, project_path: Path) -> Optional[BuildTool]:
        """Detect build tool from configuration files."""
        
        # Check for Vite
        if (project_path / "vite.config.js").exists() or (project_path / "vite.config.ts").exists():
            return BuildTool.VITE
        
        # Check for Webpack config
        if (project_path / "webpack.config.js").exists():
            return BuildTool.WEBPACK
        
        # Check for Next.js (uses Webpack/Turbopack)
        if (project_path / "next.config.js").exists() or (project_path / "next.config.ts").exists():
            return BuildTool.TURBOPACK  # Next.js 13+ prefers Turbopack
        
        # Check for Parcel
        if (project_path / ".parcelrc").exists():
            return BuildTool.PARCEL
        
        # Check package.json scripts for build tool hints
        package_json = project_path / "package.json"
        if package_json.exists():
            try:
                import json
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
                
                scripts = package_data.get('scripts', {})
                
                if any('vite' in script for script in scripts.values()):
                    return BuildTool.VITE
                elif any('webpack' in script for script in scripts.values()):
                    return BuildTool.WEBPACK
                elif any('parcel' in script for script in scripts.values()):
                    return BuildTool.PARCEL
                    
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return None
    
    def _detect_typescript(self, project_path: Path) -> bool:
        """Detect if project uses TypeScript."""
        
        # Check for TypeScript config
        if (project_path / "tsconfig.json").exists():
            return True
        
        # Check for .ts/.tsx files
        ts_files = list(project_path.glob("**/*.ts")) + list(project_path.glob("**/*.tsx"))
        if ts_files:
            return True
        
        # Check package.json for TypeScript dependencies
        package_json = project_path / "package.json"
        if package_json.exists():
            try:
                import json
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
                
                all_deps = {}
                all_deps.update(package_data.get('dependencies', {}))
                all_deps.update(package_data.get('devDependencies', {}))
                
                ts_deps = ['typescript', '@types/react', '@types/node']
                if any(dep in all_deps for dep in ts_deps):
                    return True
                    
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return False
    
    def _select_generation_strategy(self, config: ProjectConfiguration) -> str:
        """Select optimal generation strategy based on configuration."""
        
        # Try exact mapping first
        strategy_key = (config.framework, config.styling_system)
        if strategy_key in self.strategy_mappings:
            return self.strategy_mappings[strategy_key]
        
        # Fallback based on styling system
        styling_strategies = {
            StylingSystem.CHAKRA_UI: "ChakraUI",
            StylingSystem.TAILWIND: "Tailwind", 
            StylingSystem.SHADCN_UI: "ShadcnUI",
            StylingSystem.MATERIAL_UI: "MaterialUI",
            StylingSystem.MANTINE: "Mantine",
            StylingSystem.ANT_DESIGN: "AntDesign"
        }
        
        fallback_strategy = styling_strategies.get(config.styling_system, "Generic")
        
        # For now, return the registered strategy name since only ChakraUI is implemented
        if config.styling_system == StylingSystem.CHAKRA_UI:
            return "ChakraUI"
            
        return fallback_strategy
    
    def _get_context_priorities(self, config: ProjectConfiguration) -> Dict[str, float]:
        """Get context priorities for the configuration."""
        
        base_priorities = self.context_priorities.get(config.styling_system, {
            'component_examples': 0.6,
            'design_tokens': 0.6,
            'framework_patterns': 0.8,
            'styling_patterns': 0.6,
            'accessibility_patterns': 0.6
        })
        
        # Adjust based on framework
        if config.framework == Framework.NEXT_JS:
            base_priorities['framework_patterns'] = 0.9
        
        # Adjust based on TypeScript
        if config.typescript:
            base_priorities['type_definitions'] = 0.7
        
        return base_priorities
    
    def _estimate_project_size(self, project_path: Path) -> str:
        """Estimate project size based on file count."""
        try:
            # Count relevant files
            js_files = len(list(project_path.glob("**/*.js")))
            ts_files = len(list(project_path.glob("**/*.ts")))
            jsx_files = len(list(project_path.glob("**/*.jsx")))
            tsx_files = len(list(project_path.glob("**/*.tsx")))
            
            total_files = js_files + ts_files + jsx_files + tsx_files
            
            if total_files < 10:
                return "small"
            elif total_files < 50:
                return "medium"
            elif total_files < 200:
                return "large"
            else:
                return "enterprise"
                
        except Exception:
            return "unknown"
    
    def _calculate_complexity_score(self, config: ProjectConfiguration) -> float:
        """Calculate project complexity score."""
        complexity = 0.0
        
        # Base complexity from framework
        framework_complexity = {
            Framework.NEXT_JS: 0.8,
            Framework.REACT: 0.5,
            Framework.VITE_REACT: 0.6,
            Framework.CREATE_REACT_APP: 0.4,
            Framework.GATSBY: 0.7,
            Framework.REMIX: 0.7
        }
        
        complexity += framework_complexity.get(config.framework, 0.5)
        
        # Add complexity from styling system
        styling_complexity = {
            StylingSystem.CHAKRA_UI: 0.6,
            StylingSystem.TAILWIND: 0.4,
            StylingSystem.MATERIAL_UI: 0.7,
            StylingSystem.SHADCN_UI: 0.5,
            StylingSystem.STYLED_COMPONENTS: 0.6
        }
        
        complexity += styling_complexity.get(config.styling_system, 0.5)
        
        # Add for TypeScript
        if config.typescript:
            complexity += 0.2
        
        # Add for component library
        if config.component_library != ComponentLibrary.NONE:
            complexity += 0.2
        
        # Normalize to 0-1 range
        return min(1.0, complexity / 2.0)
    
    def _count_analyzed_files(self, project_path: Path) -> int:
        """Count the number of files that were analyzed."""
        try:
            patterns = ["**/*.js", "**/*.ts", "**/*.jsx", "**/*.tsx", "**/package.json", "**/*.config.js"]
            total = 0
            for pattern in patterns:
                total += len(list(project_path.glob(pattern)))
            return min(total, 100)  # Cap for performance
        except Exception:
            return 0
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for metadata."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _print_analysis_summary(self, config: ProjectConfiguration):
        """Print analysis summary."""
        print("\n" + "="*60)
        print("📋 CONFIGURATION ANALYSIS SUMMARY")
        print("="*60)
        print(f"🔧 Framework: {config.framework.value}")
        print(f"🎨 Styling: {config.styling_system.value}")
        print(f"📦 Component Library: {config.component_library.value}")
        print(f"🏗️ Build Tool: {config.build_tool.value if config.build_tool else 'Unknown'}")
        print(f"📝 TypeScript: {config.typescript}")
        print(f"📊 Confidence: {config.confidence_score:.1%}")
        print(f"🎯 Strategy: {config.generation_strategy}")
        
        if config.compatibility_issues:
            print(f"\n⚠️ Issues ({len(config.compatibility_issues)}):")
            for issue in config.compatibility_issues[:3]:  # Show top 3
                print(f"   • {issue}")
        
        if config.recommendations:
            print(f"\n💡 Recommendations ({len(config.recommendations)}):")
            for rec in config.recommendations[:3]:  # Show top 3
                print(f"   • {rec}")
        
        print("="*60)
    
    def validate_configuration(self, config: ProjectConfiguration, project_path: str) -> bool:
        """Validate that the detected configuration is correct."""
        
        # Basic sanity checks
        if config.confidence_score < 0.3:
            print(f"⚠️ Low confidence score: {config.confidence_score:.1%}")
            return False
        
        # Check for critical conflicts
        critical_issues = [issue for issue in config.compatibility_issues if 'CRITICAL' in issue]
        if critical_issues:
            print(f"❌ Critical configuration issues detected: {len(critical_issues)}")
            return False
        
        # Validate framework-specific requirements
        if config.framework == Framework.NEXT_JS:
            next_config = Path(project_path) / "next.config.js"
            if not next_config.exists():
                print("⚠️ Next.js detected but no next.config.js found")
                return False
        
        # Validate styling system dependencies
        if config.styling_system == StylingSystem.CHAKRA_UI:
            package_json = Path(project_path) / "package.json"
            if package_json.exists():
                try:
                    import json
                    with open(package_json, 'r') as f:
                        data = json.load(f)
                    
                    all_deps = {}
                    all_deps.update(data.get('dependencies', {}))
                    all_deps.update(data.get('devDependencies', {}))
                    
                    if '@chakra-ui/react' not in all_deps:
                        print("⚠️ Chakra UI detected but dependency not found")
                        return False
                except Exception:
                    pass
        
        print("✅ Configuration validation passed")
        return True
    
    def get_generation_guidance(self, config: ProjectConfiguration) -> Dict[str, Any]:
        """Get specific guidance for code generation based on configuration."""
        
        guidance = {
            'strategy_name': config.generation_strategy,
            'context_priorities': config.context_priorities,
            'forbidden_patterns': [],
            'required_patterns': [],
            'import_patterns': [],
            'component_examples': [],
            'validation_rules': []
        }
        
        # Add styling system specific guidance
        if config.styling_system == StylingSystem.CHAKRA_UI:
            guidance.update({
                'forbidden_patterns': [
                    'className with CSS utility classes',
                    'Tailwind CSS classes', 
                    'inline styles'
                ],
                'required_patterns': [
                    'Chakra UI component imports',
                    'theme-aware props'
                ],
                'import_patterns': [
                    "import { Box, Button, Text } from '@chakra-ui/react'"
                ],
                'validation_rules': [
                    'Must import from @chakra-ui/react',
                    'No Tailwind classes allowed',
                    'Use component props for styling'
                ]
            })
        
        elif config.styling_system == StylingSystem.TAILWIND:
            guidance.update({
                'forbidden_patterns': [
                    'inline styles',
                    'CSS-in-JS styling'
                ],
                'required_patterns': [
                    'Tailwind utility classes',
                    'responsive prefixes'
                ],
                'validation_rules': [
                    'Use valid Tailwind classes',
                    'Follow utility-first approach'
                ]
            })
        
        # Add framework specific guidance
        if config.framework == Framework.NEXT_JS:
            guidance['framework_patterns'] = [
                'Use "use client" for client components',
                'Follow App Router conventions',
                'Use Next.js Image component'
            ]
        
        return guidance