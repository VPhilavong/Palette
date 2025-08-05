"""
Advanced Frontend Architecture Understanding System.
Analyzes and understands frontend architecture patterns, best practices,
and generates components that align with modern architectural principles.
"""

import ast
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set, Union
from collections import defaultdict, Counter

from ..errors.decorators import handle_errors


class ArchitecturePattern(Enum):
    """Common frontend architecture patterns."""
    COMPONENT_COMPOSITION = "component_composition"
    RENDER_PROPS = "render_props"
    HIGHER_ORDER_COMPONENTS = "higher_order_components"
    CUSTOM_HOOKS = "custom_hooks"
    COMPOUND_COMPONENTS = "compound_components"
    PROVIDER_PATTERN = "provider_pattern"
    CONTAINER_PRESENTER = "container_presenter"
    ATOMIC_DESIGN = "atomic_design"
    FEATURE_MODULES = "feature_modules"
    LAYER_ARCHITECTURE = "layer_architecture"


class StateManagementPattern(Enum):
    """State management patterns."""
    LOCAL_STATE = "local_state"
    LIFTED_STATE = "lifted_state"
    CONTEXT_API = "context_api"
    REDUX = "redux"
    ZUSTAND = "zustand"
    MOBX = "mobx"
    RECOIL = "recoil"
    SWR = "swr"
    REACT_QUERY = "react_query"
    APOLLO_CLIENT = "apollo_client"


class DataFlowPattern(Enum):
    """Data flow patterns."""
    PROPS_DOWN_EVENTS_UP = "props_down_events_up"
    FLUX_UNIDIRECTIONAL = "flux_unidirectional"
    OBSERVER_PATTERN = "observer_pattern"
    PUBLISH_SUBSCRIBE = "publish_subscribe"
    EVENT_SOURCING = "event_sourcing"
    CQRS = "cqrs"


class ComponentType(Enum):
    """Component types in architecture."""
    PRESENTATIONAL = "presentational"
    CONTAINER = "container" 
    LAYOUT = "layout"
    PAGE = "page"
    FEATURE = "feature"
    SHARED = "shared"
    UTILITY = "utility"
    PROVIDER = "provider"
    HOC = "hoc"
    HOOK = "hook"


class ArchitecturalConcern(Enum):
    """Architectural concerns to analyze."""
    SEPARATION_OF_CONCERNS = "separation_of_concerns"
    SINGLE_RESPONSIBILITY = "single_responsibility"
    DEPENDENCY_INVERSION = "dependency_inversion"
    COMPOSITION_OVER_INHERITANCE = "composition_over_inheritance"
    DRY_PRINCIPLE = "dry_principle"
    KISS_PRINCIPLE = "kiss_principle"
    YAGNI_PRINCIPLE = "yagni_principle"
    PERFORMANCE = "performance"
    SCALABILITY = "scalability"
    MAINTAINABILITY = "maintainability"
    TESTABILITY = "testability"
    ACCESSIBILITY = "accessibility"


@dataclass
class ComponentAnalysis:
    """Analysis of a component's architecture."""
    name: str
    file_path: str
    component_type: ComponentType
    patterns_used: List[ArchitecturePattern] = field(default_factory=list)
    state_management: List[StateManagementPattern] = field(default_factory=list)
    data_flow: List[DataFlowPattern] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    props_interface: Dict[str, str] = field(default_factory=dict)
    hooks_used: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    complexity_score: float = 0.0
    lines_of_code: int = 0
    architectural_issues: List[str] = field(default_factory=list)
    architectural_strengths: List[str] = field(default_factory=list)


@dataclass
class ArchitectureInsight:
    """Insight about the project's architecture."""
    category: str
    title: str
    description: str
    impact: str  # "high", "medium", "low"
    recommendation: str
    code_examples: List[str] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)
    priority: int = 1  # 1 (highest) to 5 (lowest)


@dataclass
class ArchitecturalGuideline:
    """Guidelines for generating architecturally sound components."""
    pattern: ArchitecturePattern
    description: str
    when_to_use: List[str]
    implementation_tips: List[str]
    code_template: str
    anti_patterns: List[str] = field(default_factory=list)
    related_patterns: List[ArchitecturePattern] = field(default_factory=list)


class FrontendArchitectureAnalyzer:
    """
    Advanced system for understanding and analyzing frontend architecture.
    Provides insights and guidelines for generating architecturally sound components.
    """
    
    def __init__(self):
        self.component_analyses: Dict[str, ComponentAnalysis] = {}
        self.project_patterns: Dict[ArchitecturePattern, int] = Counter()
        self.state_management_usage: Dict[StateManagementPattern, int] = Counter()
        self.architecture_insights: List[ArchitectureInsight] = []
        
        # Initialize architectural guidelines
        self.architectural_guidelines = self._initialize_guidelines()
        
        # Pattern detection rules
        self.pattern_rules = self._initialize_pattern_rules()
        
        # Best practices knowledge base
        self.best_practices = self._initialize_best_practices()
    
    def _initialize_guidelines(self) -> Dict[ArchitecturePattern, ArchitecturalGuideline]:
        """Initialize architectural guidelines."""
        
        guidelines = {}
        
        # Component Composition
        guidelines[ArchitecturePattern.COMPONENT_COMPOSITION] = ArchitecturalGuideline(
            pattern=ArchitecturePattern.COMPONENT_COMPOSITION,
            description="Build complex UIs by composing smaller, reusable components",
            when_to_use=[
                "Creating complex layouts",
                "Building reusable UI patterns", 
                "Implementing flexible component APIs"
            ],
            implementation_tips=[
                "Use children prop for content projection",
                "Implement render props for flexible rendering",
                "Create compound components for related functionality",
                "Use composition over inheritance"
            ],
            code_template="""
interface CardProps {
  children: React.ReactNode;
  header?: React.ReactNode;
  footer?: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({ children, header, footer }) => (
  <div className="card">
    {header && <div className="card-header">{header}</div>}
    <div className="card-content">{children}</div>
    {footer && <div className="card-footer">{footer}</div>}
  </div>
);

// Usage
<Card 
  header={<h2>Title</h2>}
  footer={<Button>Action</Button>}
>
  Content goes here
</Card>
            """,
            anti_patterns=[
                "Deep prop drilling",
                "Monolithic components", 
                "Rigid component APIs"
            ],
            related_patterns=[ArchitecturePattern.COMPOUND_COMPONENTS, ArchitecturePattern.RENDER_PROPS]
        )
        
        # Custom Hooks
        guidelines[ArchitecturePattern.CUSTOM_HOOKS] = ArchitecturalGuideline(
            pattern=ArchitecturePattern.CUSTOM_HOOKS,
            description="Extract stateful logic into reusable custom hooks",
            when_to_use=[
                "Sharing stateful logic between components",
                "Abstracting complex state management",
                "Implementing reusable business logic"
            ],
            implementation_tips=[
                "Start hook names with 'use'",
                "Return consistent data structures",
                "Handle loading and error states",
                "Provide clear TypeScript interfaces"
            ],
            code_template="""
interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useApi<T>(url: string): UseApiState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(url);
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [url]);
  
  useEffect(() => {
    fetchData();
  }, [fetchData]);
  
  return { data, loading, error, refetch: fetchData };
}
            """,
            anti_patterns=[
                "Hooks that do too much",
                "Inconsistent return patterns",
                "Missing error handling"
            ]
        )
        
        # Provider Pattern
        guidelines[ArchitecturePattern.PROVIDER_PATTERN] = ArchitecturalGuideline(
            pattern=ArchitecturePattern.PROVIDER_PATTERN,
            description="Share state and logic across component trees using React Context",
            when_to_use=[
                "Sharing theme or configuration",
                "User authentication state",
                "Global application state"
            ],
            implementation_tips=[
                "Create separate context for different concerns",
                "Provide custom hooks for context consumption",
                "Memoize context values to prevent unnecessary re-renders",
                "Split providers for better performance"
            ],
            code_template="""
interface ThemeContextValue {
  theme: 'light' | 'dark';
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  
  const toggleTheme = useCallback(() => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  }, []);
  
  const value = useMemo(() => ({ theme, toggleTheme }), [theme, toggleTheme]);
  
  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};
            """,
            anti_patterns=[
                "Single massive context",
                "Unnecessary context wrapping",
                "Missing error boundaries"
            ]
        )
        
        # Container-Presenter Pattern
        guidelines[ArchitecturePattern.CONTAINER_PRESENTER] = ArchitecturalGuideline(
            pattern=ArchitecturePattern.CONTAINER_PRESENTER,
            description="Separate data fetching logic from presentation components",
            when_to_use=[
                "Complex data fetching requirements",
                "Reusable presentation components",
                "Testing data logic separately"
            ],
            implementation_tips=[
                "Keep presentational components pure",
                "Handle all side effects in containers",
                "Pass data and handlers as props",
                "Make presentational components testable"
            ],
            code_template="""
// Presentational Component
interface UserListProps {
  users: User[];
  loading: boolean;
  onUserSelect: (user: User) => void;
}

export const UserList: React.FC<UserListProps> = ({ users, loading, onUserSelect }) => {
  if (loading) return <Spinner />;
  
  return (
    <ul>
      {users.map(user => (
        <li key={user.id} onClick={() => onUserSelect(user)}>
          {user.name}
        </li>
      ))}
    </ul>
  );
};

// Container Component
export const UserListContainer: React.FC = () => {
  const { data: users, loading } = useApi<User[]>('/api/users');
  
  const handleUserSelect = useCallback((user: User) => {
    // Handle user selection logic
    navigate(`/users/${user.id}`);
  }, [navigate]);
  
  return (
    <UserList 
      users={users || []} 
      loading={loading} 
      onUserSelect={handleUserSelect} 
    />
  );
};
            """,
            anti_patterns=[
                "Mixing data logic with presentation",
                "Tightly coupled components",
                "Difficult to test components"
            ]
        )
        
        return guidelines
    
    def _initialize_pattern_rules(self) -> Dict[ArchitecturePattern, List[Dict[str, Any]]]:
        """Initialize pattern detection rules."""
        
        return {
            ArchitecturePattern.CUSTOM_HOOKS: [
                {"type": "function_name", "pattern": r"^use[A-Z]", "confidence": 0.9},
                {"type": "content", "pattern": r"useState|useEffect|useCallback", "confidence": 0.7},
            ],
            ArchitecturePattern.PROVIDER_PATTERN: [
                {"type": "content", "pattern": r"createContext|Provider|useContext", "confidence": 0.8},
                {"type": "component_name", "pattern": r"Provider$", "confidence": 0.9},
            ],
            ArchitecturePattern.HIGHER_ORDER_COMPONENTS: [
                {"type": "content", "pattern": r"return\s+\([^)]*\)\s*=>\s*<", "confidence": 0.7},
                {"type": "function_name", "pattern": r"^with[A-Z]", "confidence": 0.8},
            ],
            ArchitecturePattern.RENDER_PROPS: [
                {"type": "content", "pattern": r"children\s*\([^)]*\)", "confidence": 0.8},
                {"type": "content", "pattern": r"render\s*\([^)]*\)", "confidence": 0.8},
            ],
            ArchitecturePattern.COMPOUND_COMPONENTS: [
                {"type": "content", "pattern": r"Component\.[A-Z][a-zA-Z]*\s*=", "confidence": 0.9},
                {"type": "content", "pattern": r"displayName\s*=", "confidence": 0.6},
            ]
        }
    
    def _initialize_best_practices(self) -> Dict[str, Dict[str, Any]]:
        """Initialize best practices knowledge base."""
        
        return {
            "component_design": {
                "single_responsibility": [
                    "Each component should have one clear purpose",
                    "Break down complex components into smaller ones",
                    "Separate concerns (data, UI, business logic)"
                ],
                "composition": [
                    "Prefer composition over inheritance",
                    "Use children prop for flexible content",
                    "Create reusable, composable building blocks"
                ],
                "props_interface": [
                    "Use TypeScript interfaces for all props",
                    "Make props as specific as possible",
                    "Avoid boolean props when enums are clearer"
                ]
            },
            "state_management": {
                "local_first": [
                    "Start with local state (useState)",
                    "Lift state up when needed by multiple components",
                    "Consider Context API for widely shared state"
                ],
                "immutability": [
                    "Never mutate state directly",
                    "Use functional updates for complex state",
                    "Consider useReducer for complex state logic"
                ]
            },
            "performance": {
                "memoization": [
                    "Use React.memo for expensive re-renders",
                    "Memoize expensive calculations with useMemo",
                    "Memoize event handlers with useCallback"
                ],
                "code_splitting": [
                    "Use lazy loading for route components",
                    "Split large bundles with dynamic imports",
                    "Implement progressive loading strategies"
                ]
            },
            "testing": {
                "testability": [
                    "Write components that are easy to test",
                    "Avoid deep nesting and complex logic",
                    "Use dependency injection for testability"
                ],
                "test_structure": [
                    "Test behavior, not implementation",
                    "Use testing-library best practices",
                    "Write integration tests for user flows"
                ]
            }
        }
    
    @handle_errors(reraise=True)
    def analyze_project_architecture(self, project_path: str) -> Dict[str, Any]:
        """
        Analyze the architecture of a frontend project.
        
        Args:
            project_path: Path to the project root
            
        Returns:
            Comprehensive architecture analysis
        """
        project_path = Path(project_path)
        
        print("🏗️ Analyzing project architecture...")
        
        analysis_results = {
            "components_analyzed": 0,
            "patterns_detected": {},
            "state_management": {},
            "architectural_insights": [],
            "recommendations": [],
            "structure_analysis": {},
            "quality_metrics": {}
        }
        
        # Find and analyze components
        component_files = self._find_component_files(project_path)
        
        for file_path in component_files:
            try:
                component_analysis = self._analyze_component_file(file_path)
                if component_analysis:
                    self.component_analyses[component_analysis.name] = component_analysis
                    analysis_results["components_analyzed"] += 1
                    
                    # Update pattern counters
                    for pattern in component_analysis.patterns_used:
                        self.project_patterns[pattern] += 1
                    
                    for state_pattern in component_analysis.state_management:
                        self.state_management_usage[state_pattern] += 1
                        
            except Exception as e:
                print(f"⚠️ Failed to analyze {file_path}: {e}")
        
        # Analyze project structure
        analysis_results["structure_analysis"] = self._analyze_project_structure(project_path)
        
        # Detect architectural patterns
        analysis_results["patterns_detected"] = {
            pattern.value: count for pattern, count in self.project_patterns.items()
        }
        
        # Analyze state management
        analysis_results["state_management"] = {
            pattern.value: count for pattern, count in self.state_management_usage.items()
        }
        
        # Generate insights
        insights = self._generate_architecture_insights()
        analysis_results["architectural_insights"] = [
            {
                "category": insight.category,
                "title": insight.title,
                "description": insight.description,
                "impact": insight.impact,
                "recommendation": insight.recommendation,
                "priority": insight.priority
            }
            for insight in insights
        ]
        
        # Calculate quality metrics
        analysis_results["quality_metrics"] = self._calculate_quality_metrics()
        
        # Generate recommendations
        analysis_results["recommendations"] = self._generate_architecture_recommendations()
        
        print(f"✅ Analyzed {analysis_results['components_analyzed']} components")
        print(f"🔍 Detected {len(analysis_results['patterns_detected'])} architectural patterns")
        print(f"💡 Generated {len(insights)} insights")
        
        return analysis_results
    
    def _find_component_files(self, project_path: Path) -> List[Path]:
        """Find React/frontend component files in the project."""
        
        component_files = []
        
        # Common patterns for component files
        patterns = [
            "**/*.tsx",
            "**/*.jsx", 
            "**/*.ts",
            "**/*.js"
        ]
        
        # Exclude common non-component directories
        exclude_dirs = {
            "node_modules", ".git", "dist", "build", "public", 
            ".next", "coverage", "__pycache__", ".pytest_cache"
        }
        
        for pattern in patterns:
            for file_path in project_path.glob(pattern):
                # Skip if in excluded directory
                if any(excluded in file_path.parts for excluded in exclude_dirs):
                    continue
                
                # Skip test files
                if any(test_pattern in file_path.name for test_pattern in [".test.", ".spec.", "__tests__"]):
                    continue
                
                # Skip config files
                if any(config_pattern in file_path.name for config_pattern in ["config", "setup", "webpack", "babel"]):
                    continue
                
                component_files.append(file_path)
        
        return component_files
    
    def _analyze_component_file(self, file_path: Path) -> Optional[ComponentAnalysis]:
        """Analyze a single component file."""
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return None
        
        # Basic metrics
        lines_of_code = len([line for line in content.split('\n') if line.strip()])
        
        # Extract component information
        component_name = self._extract_component_name(file_path, content)
        if not component_name:
            return None
        
        analysis = ComponentAnalysis(
            name=component_name,
            file_path=str(file_path),
            component_type=self._classify_component_type(file_path, content),
            lines_of_code=lines_of_code,
            complexity_score=self._calculate_complexity_score(content)
        )
        
        # Detect patterns
        analysis.patterns_used = self._detect_patterns(content)
        analysis.state_management = self._detect_state_management(content)
        analysis.data_flow = self._detect_data_flow_patterns(content)
        
        # Extract dependencies and interfaces
        analysis.imports = self._extract_imports(content)
        analysis.exports = self._extract_exports(content)
        analysis.hooks_used = self._extract_hooks_used(content)
        analysis.props_interface = self._extract_props_interface(content)
        analysis.dependencies = self._extract_dependencies(content)
        
        # Analyze architectural quality
        analysis.architectural_issues = self._identify_architectural_issues(content, analysis)
        analysis.architectural_strengths = self._identify_architectural_strengths(content, analysis)
        
        return analysis
    
    def _extract_component_name(self, file_path: Path, content: str) -> Optional[str]:
        """Extract the main component name from the file."""
        
        # Try to find export default or named exports
        patterns = [
            r"export\s+default\s+(?:function\s+)?([A-Z][a-zA-Z0-9]*)",
            r"export\s+(?:const|function)\s+([A-Z][a-zA-Z0-9]*)",
            r"(?:const|function)\s+([A-Z][a-zA-Z0-9]*)\s*[=:]",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        # Fallback to filename
        name = file_path.stem
        if name == "index":
            name = file_path.parent.name
        
        # Convert to PascalCase
        return ''.join(word.capitalize() for word in name.replace('-', '_').split('_'))
    
    def _classify_component_type(self, file_path: Path, content: str) -> ComponentType:
        """Classify the type of component."""
        
        path_str = str(file_path).lower()
        content_lower = content.lower()
        
        # Check path patterns
        if any(pattern in path_str for pattern in ["page", "pages"]):
            return ComponentType.PAGE
        elif any(pattern in path_str for pattern in ["layout", "layouts"]):
            return ComponentType.LAYOUT
        elif any(pattern in path_str for pattern in ["container", "containers"]):
            return ComponentType.CONTAINER
        elif any(pattern in path_str for pattern in ["provider", "providers", "context"]):
            return ComponentType.PROVIDER
        elif any(pattern in path_str for pattern in ["hook", "hooks"]):
            return ComponentType.HOOK
        elif any(pattern in path_str for pattern in ["util", "utils", "helper", "helpers"]):
            return ComponentType.UTILITY
        elif any(pattern in path_str for pattern in ["shared", "common", "components"]):
            return ComponentType.SHARED
        elif any(pattern in path_str for pattern in ["feature", "features"]):
            return ComponentType.FEATURE
        
        # Check content patterns
        if "useeffect" in content_lower and "fetch" in content_lower:
            return ComponentType.CONTAINER
        elif "createcontext" in content_lower or "provider" in content_lower:
            return ComponentType.PROVIDER
        elif content_lower.startswith("use") and "function" in content_lower:
            return ComponentType.HOOK
        elif "higher-order" in content_lower or "withcomponent" in content_lower:
            return ComponentType.HOC
        
        # Default to presentational
        return ComponentType.PRESENTATIONAL
    
    def _detect_patterns(self, content: str) -> List[ArchitecturePattern]:
        """Detect architectural patterns in the component."""
        
        detected_patterns = []
        
        for pattern, rules in self.pattern_rules.items():
            confidence = 0.0
            
            for rule in rules:
                if rule["type"] == "content":
                    if re.search(rule["pattern"], content, re.IGNORECASE | re.MULTILINE):
                        confidence += rule["confidence"]
                elif rule["type"] == "function_name":
                    if re.search(rule["pattern"], content, re.MULTILINE):
                        confidence += rule["confidence"]
                elif rule["type"] == "component_name":
                    if re.search(rule["pattern"], content, re.MULTILINE):
                        confidence += rule["confidence"]
            
            if confidence >= 0.7:  # Threshold for pattern detection
                detected_patterns.append(pattern)
        
        return detected_patterns
    
    def _detect_state_management(self, content: str) -> List[StateManagementPattern]:
        """Detect state management patterns."""
        
        patterns = []
        content_lower = content.lower()
        
        if "usestate" in content_lower:
            patterns.append(StateManagementPattern.LOCAL_STATE)
        
        if "usecontext" in content_lower or "createcontext" in content_lower:
            patterns.append(StateManagementPattern.CONTEXT_API)
        
        if any(redux_pattern in content_lower for redux_pattern in ["useselector", "usedispatch", "connect"]):
            patterns.append(StateManagementPattern.REDUX)
        
        if "zustand" in content_lower:
            patterns.append(StateManagementPattern.ZUSTAND)
        
        if "mobx" in content_lower:
            patterns.append(StateManagementPattern.MOBX)
        
        if any(query_pattern in content_lower for query_pattern in ["usequery", "usemutation", "react-query"]):
            patterns.append(StateManagementPattern.REACT_QUERY)
        
        if "swr" in content_lower:
            patterns.append(StateManagementPattern.SWR)
        
        if "recoil" in content_lower:
            patterns.append(StateManagementPattern.RECOIL)
        
        if "apollo" in content_lower:
            patterns.append(StateManagementPattern.APOLLO_CLIENT)
        
        return patterns
    
    def _detect_data_flow_patterns(self, content: str) -> List[DataFlowPattern]:
        """Detect data flow patterns."""
        
        patterns = []
        
        # Props down, events up
        if re.search(r"on[A-Z][a-zA-Z]*\s*[=:]", content) and "props" in content:
            patterns.append(DataFlowPattern.PROPS_DOWN_EVENTS_UP)
        
        # Flux unidirectional
        if any(flux_pattern in content.lower() for flux_pattern in ["dispatch", "action", "reducer"]):
            patterns.append(DataFlowPattern.FLUX_UNIDIRECTIONAL)
        
        # Observer pattern
        if any(observer_pattern in content.lower() for observer_pattern in ["observer", "observable", "subscribe"]):
            patterns.append(DataFlowPattern.OBSERVER_PATTERN)
        
        return patterns
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements."""
        
        imports = []
        import_pattern = r"import\s+(?:{[^}]+}|\*\s+as\s+\w+|\w+)(?:\s*,\s*{[^}]+})?\s+from\s+['\"]([^'\"]+)['\"]"
        
        for match in re.finditer(import_pattern, content):
            imports.append(match.group(1))
        
        return imports
    
    def _extract_exports(self, content: str) -> List[str]:
        """Extract export statements."""
        
        exports = []
        
        # Export patterns
        patterns = [
            r"export\s+(?:default\s+)?(?:const|function|class)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)",
            r"export\s+default\s+([a-zA-Z_$][a-zA-Z0-9_$]*)",
            r"export\s+{\s*([^}]+)\s*}"
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, content):
                export_name = match.group(1)
                if "," in export_name:  # Multiple exports
                    exports.extend([name.strip() for name in export_name.split(",")])
                else:
                    exports.append(export_name)
        
        return exports
    
    def _extract_hooks_used(self, content: str) -> List[str]:
        """Extract React hooks used in the component."""
        
        hooks = []
        hook_pattern = r"\b(use[A-Z][a-zA-Z0-9]*)\s*\("
        
        for match in re.finditer(hook_pattern, content):
            hooks.append(match.group(1))
        
        return list(set(hooks))  # Remove duplicates
    
    def _extract_props_interface(self, content: str) -> Dict[str, str]:
        """Extract props interface definition."""
        
        props_interface = {}
        
        # Look for interface definitions
        interface_pattern = r"interface\s+(\w*Props?)\s*{([^}]+)}"
        
        for match in re.finditer(interface_pattern, content, re.MULTILINE | re.DOTALL):
            interface_body = match.group(2)
            
            # Extract properties
            prop_pattern = r"(\w+)(?:\?)?\s*:\s*([^;,\n]+)"
            for prop_match in re.finditer(prop_pattern, interface_body):
                prop_name = prop_match.group(1)
                prop_type = prop_match.group(2).strip()
                props_interface[prop_name] = prop_type
        
        return props_interface
    
    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract external dependencies used."""
        
        dependencies = []
        
        # Look for imports from node_modules
        import_pattern = r"from\s+['\"]([^'\"./][^'\"]*)['\"]"
        
        for match in re.finditer(import_pattern, content):
            dep = match.group(1)
            # Get root package name
            root_dep = dep.split('/')[0]
            dependencies.append(root_dep)
        
        return list(set(dependencies))
    
    def _calculate_complexity_score(self, content: str) -> float:
        """Calculate complexity score for the component."""
        
        score = 0.0
        
        # Cyclomatic complexity indicators
        complexity_indicators = [
            (r"\bif\b", 1),
            (r"\belse\b", 1),
            (r"\bfor\b", 2),
            (r"\bwhile\b", 2),
            (r"\bswitch\b", 2),
            (r"\bcatch\b", 1),
            (r"\?\s*:", 1),  # Ternary operator
            (r"&&|\|\|", 0.5),  # Logical operators
        ]
        
        for pattern, weight in complexity_indicators:
            matches = len(re.findall(pattern, content))
            score += matches * weight
        
        # Nested function/component complexity
        nested_functions = len(re.findall(r"(?:function|const\s+\w+\s*=.*=>)", content))
        score += nested_functions * 0.5
        
        # Long functions penalty
        lines = content.split('\n')
        function_lines = 0
        in_function = False
        brace_count = 0
        
        for line in lines:
            if re.search(r"(?:function|const\s+\w+\s*=.*=>)", line):
                in_function = True
                function_lines = 1
                brace_count = line.count('{') - line.count('}')
            elif in_function:
                function_lines += 1
                brace_count += line.count('{') - line.count('}')
                
                if brace_count <= 0:
                    in_function = False
                    if function_lines > 50:  # Long function penalty
                        score += (function_lines - 50) * 0.1
        
        return min(score, 100.0)  # Cap at 100
    
    def _identify_architectural_issues(self, content: str, analysis: ComponentAnalysis) -> List[str]:
        """Identify architectural issues in the component."""
        
        issues = []
        
        # Long component (too many lines)
        if analysis.lines_of_code > 300:
            issues.append(f"Component is too long ({analysis.lines_of_code} lines). Consider breaking it down.")
        
        # High complexity
        if analysis.complexity_score > 20:
            issues.append(f"High complexity score ({analysis.complexity_score:.1f}). Simplify the logic.")
        
        # Too many hooks
        if len(analysis.hooks_used) > 10:
            issues.append(f"Too many hooks ({len(analysis.hooks_used)}). Consider extracting custom hooks.")
        
        # Too many props
        if len(analysis.props_interface) > 15:
            issues.append(f"Too many props ({len(analysis.props_interface)}). Consider grouping related props.")
        
        # Missing TypeScript interfaces
        if not analysis.props_interface and "interface" not in content and "type" not in content:
            issues.append("Missing TypeScript interfaces. Add proper type definitions.")
        
        # Inline styles
        if re.search(r"style\s*=\s*{{", content):
            issues.append("Inline styles detected. Consider using CSS classes or styled components.")
        
        # Large JSX returns
        jsx_return_match = re.search(r"return\s*\((.*?)\);", content, re.DOTALL)
        if jsx_return_match:
            jsx_content = jsx_return_match.group(1)
            jsx_lines = len(jsx_content.split('\n'))
            if jsx_lines > 100:
                issues.append(f"Large JSX return ({jsx_lines} lines). Break into smaller components.")
        
        # Deeply nested JSX
        max_nesting = self._calculate_jsx_nesting_depth(content)
        if max_nesting > 8:
            issues.append(f"Deeply nested JSX (depth: {max_nesting}). Flatten the structure.")
        
        # Missing error boundaries
        if analysis.component_type == ComponentType.PAGE and "ErrorBoundary" not in content:
            issues.append("Page component missing error boundary. Add error handling.")
        
        return issues
    
    def _identify_architectural_strengths(self, content: str, analysis: ComponentAnalysis) -> List[str]:
        """Identify architectural strengths in the component."""
        
        strengths = []
        
        # Good TypeScript usage
        if analysis.props_interface:
            strengths.append("Well-defined TypeScript interfaces")
        
        # Custom hooks usage
        if any("use" in hook for hook in analysis.hooks_used if not hook.startswith("use")):
            strengths.append("Uses custom hooks for logic abstraction")
        
        # Good component size
        if 50 <= analysis.lines_of_code <= 200:
            strengths.append("Appropriate component size")
        
        # Low complexity
        if analysis.complexity_score < 10:
            strengths.append("Low complexity, easy to understand")
        
        # Proper separation of concerns
        if analysis.component_type == ComponentType.PRESENTATIONAL and not any(
            hook in analysis.hooks_used for hook in ["useEffect", "useState"] 
            if "fetch" in content.lower()
        ):
            strengths.append("Good separation of concerns (presentational)")
        
        # Memoization usage
        if any(memo in content for memo in ["React.memo", "useMemo", "useCallback"]):
            strengths.append("Performance optimized with memoization")
        
        # Accessibility considerations
        if any(a11y in content for a11y in ["aria-", "role=", "alt=", "tabIndex"]):
            strengths.append("Includes accessibility considerations")
        
        return strengths
    
    def _calculate_jsx_nesting_depth(self, content: str) -> int:
        """Calculate maximum JSX nesting depth."""
        
        # Simple heuristic: count opening tags vs closing tags
        jsx_content = ""
        in_jsx = False
        brace_count = 0
        
        for line in content.split('\n'):
            if "return" in line and "(" in line:
                in_jsx = True
            
            if in_jsx:
                jsx_content += line + "\n"
                brace_count += line.count('(') - line.count(')')
                
                if brace_count <= 0 and ");" in line:
                    break
        
        # Count nesting depth by XML-like tags
        max_depth = 0
        current_depth = 0
        
        tag_pattern = r"<(/?)(\w+)"
        for match in re.finditer(tag_pattern, jsx_content):
            is_closing = match.group(1) == "/"
            
            if is_closing:
                current_depth -= 1
            else:
                current_depth += 1
                max_depth = max(max_depth, current_depth)
        
        return max_depth
    
    def _analyze_project_structure(self, project_path: Path) -> Dict[str, Any]:
        """Analyze the overall project structure."""
        
        structure = {
            "directory_structure": {},
            "organization_pattern": "unknown",
            "structure_score": 0.0,
            "structure_issues": [],
            "structure_strengths": []
        }
        
        # Analyze directory structure
        src_dir = project_path / "src"
        if src_dir.exists():
            structure["directory_structure"] = self._analyze_directory_structure(src_dir)
            structure["organization_pattern"] = self._detect_organization_pattern(src_dir)
            structure["structure_score"] = self._calculate_structure_score(src_dir)
            structure["structure_issues"] = self._identify_structure_issues(src_dir)
            structure["structure_strengths"] = self._identify_structure_strengths(src_dir)
        
        return structure
    
    def _analyze_directory_structure(self, src_dir: Path) -> Dict[str, Any]:
        """Analyze the directory structure."""
        
        structure = {
            "total_directories": 0,
            "max_depth": 0,
            "common_directories": [],
            "directory_counts": {}
        }
        
        def analyze_recursive(path: Path, current_depth: int = 0):
            structure["max_depth"] = max(structure["max_depth"], current_depth)
            
            for item in path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    structure["total_directories"] += 1
                    
                    dir_name = item.name.lower()
                    if dir_name not in structure["directory_counts"]:
                        structure["directory_counts"][dir_name] = 0
                    structure["directory_counts"][dir_name] += 1
                    
                    analyze_recursive(item, current_depth + 1)
        
        analyze_recursive(src_dir)
        
        # Find common directory patterns
        common_dirs = ["components", "pages", "hooks", "utils", "services", "types", "styles"]
        structure["common_directories"] = [
            dir_name for dir_name in common_dirs 
            if dir_name in structure["directory_counts"]
        ]
        
        return structure
    
    def _detect_organization_pattern(self, src_dir: Path) -> str:
        """Detect the organization pattern used in the project."""
        
        dirs = [item.name.lower() for item in src_dir.iterdir() if item.is_dir()]
        
        # Feature-based organization
        if any(feature_indicator in dirs for feature_indicator in ["features", "modules", "domains"]):
            return "feature_based"
        
        # Atomic design
        if any(atomic_level in dirs for atomic_level in ["atoms", "molecules", "organisms", "templates"]):
            return "atomic_design"
        
        # Layer-based
        if any(layer in dirs for layer in ["components", "containers", "views", "pages"]):
            return "layer_based"
        
        # Flat structure
        if len(dirs) <= 5:
            return "flat"
        
        return "mixed"
    
    def _calculate_structure_score(self, src_dir: Path) -> float:
        """Calculate a score for the project structure quality."""
        
        score = 5.0  # Base score
        
        structure = self._analyze_directory_structure(src_dir)
        
        # Penalize excessive depth
        if structure["max_depth"] > 5:
            score -= (structure["max_depth"] - 5) * 0.5
        
        # Reward common directories
        common_dir_bonus = len(structure["common_directories"]) * 0.5
        score += min(common_dir_bonus, 3.0)
        
        # Penalize too many directories at root
        root_dirs = len([item for item in src_dir.iterdir() if item.is_dir()])
        if root_dirs > 10:
            score -= (root_dirs - 10) * 0.2
        
        return max(0.0, min(10.0, score))
    
    def _identify_structure_issues(self, src_dir: Path) -> List[str]:
        """Identify structural issues in the project."""
        
        issues = []
        structure = self._analyze_directory_structure(src_dir)
        
        if structure["max_depth"] > 6:
            issues.append(f"Directory structure is too deep (max depth: {structure['max_depth']})")
        
        if "components" not in structure["common_directories"]:
            issues.append("Missing 'components' directory for reusable components")
        
        if "utils" not in structure["common_directories"] and "helpers" not in structure["common_directories"]:
            issues.append("Missing utility/helper directory for shared functions")
        
        if structure["total_directories"] > 50:
            issues.append(f"Too many directories ({structure['total_directories']}). Consider consolidation.")
        
        return issues
    
    def _identify_structure_strengths(self, src_dir: Path) -> List[str]:
        """Identify structural strengths in the project."""
        
        strengths = []
        structure = self._analyze_directory_structure(src_dir)
        
        if len(structure["common_directories"]) >= 4:
            strengths.append("Well-organized with standard directory structure")
        
        if 3 <= structure["max_depth"] <= 5:
            strengths.append("Appropriate directory depth for maintainability")
        
        if "types" in structure["common_directories"]:
            strengths.append("Dedicated types directory for TypeScript definitions")
        
        if "hooks" in structure["common_directories"]:
            strengths.append("Custom hooks are properly organized")
        
        return strengths
    
    def _generate_architecture_insights(self) -> List[ArchitectureInsight]:
        """Generate insights about the project architecture."""
        
        insights = []
        
        # Pattern usage insights
        if self.project_patterns:
            most_used_pattern = max(self.project_patterns, key=self.project_patterns.get)
            pattern_count = self.project_patterns[most_used_pattern]
            
            insights.append(ArchitectureInsight(
                category="Patterns",
                title=f"Heavy use of {most_used_pattern.value}",
                description=f"Project heavily uses {most_used_pattern.value} pattern ({pattern_count} occurrences)",
                impact="medium",
                recommendation=f"Consider documenting {most_used_pattern.value} usage patterns for consistency",
                priority=3
            ))
        
        # State management insights  
        if self.state_management_usage:
            state_patterns = list(self.state_management_usage.keys())
            if len(state_patterns) > 3:
                insights.append(ArchitectureInsight(
                    category="State Management",
                    title="Multiple state management approaches",
                    description=f"Project uses {len(state_patterns)} different state management patterns",
                    impact="high",
                    recommendation="Standardize on 1-2 state management approaches for consistency",
                    priority=1
                ))
        
        # Component complexity insights
        if self.component_analyses:
            avg_complexity = sum(comp.complexity_score for comp in self.component_analyses.values()) / len(self.component_analyses)
            high_complexity_count = len([comp for comp in self.component_analyses.values() if comp.complexity_score > 20])
            
            if avg_complexity > 15:
                insights.append(ArchitectureInsight(
                    category="Complexity",
                    title="High component complexity",
                    description=f"Average component complexity is {avg_complexity:.1f} with {high_complexity_count} highly complex components",
                    impact="high",
                    recommendation="Refactor complex components into smaller, more focused components",
                    priority=1
                ))
        
        # TypeScript usage insights
        typed_components = len([comp for comp in self.component_analyses.values() if comp.props_interface])
        total_components = len(self.component_analyses)
        
        if total_components > 0:
            typescript_coverage = typed_components / total_components
            if typescript_coverage < 0.7:
                insights.append(ArchitectureInsight(
                    category="TypeScript",
                    title="Low TypeScript coverage",
                    description=f"Only {typescript_coverage:.1%} of components have proper TypeScript interfaces",
                    impact="medium",
                    recommendation="Add TypeScript interfaces to all components for better type safety",
                    priority=2
                ))
        
        return insights
    
    def _calculate_quality_metrics(self) -> Dict[str, float]:
        """Calculate overall quality metrics for the architecture."""
        
        if not self.component_analyses:
            return {}
        
        components = list(self.component_analyses.values())
        
        metrics = {
            "average_complexity": sum(comp.complexity_score for comp in components) / len(components),
            "typescript_coverage": len([comp for comp in components if comp.props_interface]) / len(components),
            "average_lines_per_component": sum(comp.lines_of_code for comp in components) / len(components),
            "pattern_consistency": self._calculate_pattern_consistency(),
            "separation_of_concerns": self._calculate_separation_score(),
            "reusability_score": self._calculate_reusability_score(),
            "maintainability_score": self._calculate_maintainability_score()
        }
        
        return metrics
    
    def _calculate_pattern_consistency(self) -> float:
        """Calculate how consistently patterns are used across the project."""
        
        if not self.project_patterns:
            return 0.0
        
        total_patterns = sum(self.project_patterns.values())
        pattern_distribution = [count / total_patterns for count in self.project_patterns.values()]
        
        # Higher entropy means more inconsistent usage
        import math
        entropy = -sum(p * math.log2(p) for p in pattern_distribution if p > 0)
        max_entropy = math.log2(len(self.project_patterns))
        
        # Convert to consistency score (lower entropy = higher consistency)
        consistency = 1.0 - (entropy / max_entropy) if max_entropy > 0 else 1.0
        
        return consistency
    
    def _calculate_separation_score(self) -> float:
        """Calculate how well concerns are separated."""
        
        if not self.component_analyses:
            return 0.0
        
        # Good separation indicators
        container_count = len([comp for comp in self.component_analyses.values() 
                              if comp.component_type == ComponentType.CONTAINER])
        presentational_count = len([comp for comp in self.component_analyses.values() 
                                   if comp.component_type == ComponentType.PRESENTATIONAL])
        
        total_components = len(self.component_analyses)
        
        # Ideal ratio is around 30% containers, 70% presentational
        if total_components == 0:
            return 0.0
        
        container_ratio = container_count / total_components
        ideal_container_ratio = 0.3
        
        # Score based on how close to ideal ratio
        ratio_score = 1.0 - abs(container_ratio - ideal_container_ratio) / ideal_container_ratio
        
        return max(0.0, ratio_score)
    
    def _calculate_reusability_score(self) -> float:
        """Calculate how reusable the components are."""
        
        if not self.component_analyses:
            return 0.0
        
        reusability_indicators = 0
        total_components = len(self.component_analyses)
        
        for comp in self.component_analyses.values():
            # Components with TypeScript interfaces are more reusable
            if comp.props_interface:
                reusability_indicators += 1
            
            # Components with reasonable complexity are more reusable
            if comp.complexity_score < 15:
                reusability_indicators += 1
            
            # Presentational components are typically more reusable
            if comp.component_type == ComponentType.PRESENTATIONAL:
                reusability_indicators += 1
        
        max_possible_score = total_components * 3
        return reusability_indicators / max_possible_score if max_possible_score > 0 else 0.0
    
    def _calculate_maintainability_score(self) -> float:
        """Calculate overall maintainability score."""
        
        if not self.component_analyses:
            return 0.0
        
        maintainability_factors = []
        
        for comp in self.component_analyses.values():
            component_score = 0.0
            
            # Low complexity is more maintainable
            if comp.complexity_score < 10:
                component_score += 0.3
            elif comp.complexity_score < 20:
                component_score += 0.1
            
            # Reasonable size is more maintainable
            if 50 <= comp.lines_of_code <= 200:
                component_score += 0.2
            
            # TypeScript helps maintainability
            if comp.props_interface:
                component_score += 0.2
            
            # Few architectural issues
            if len(comp.architectural_issues) <= 2:
                component_score += 0.2
            
            # Good architectural strengths
            component_score += min(len(comp.architectural_strengths) * 0.05, 0.1)
            
            maintainability_factors.append(component_score)
        
        return sum(maintainability_factors) / len(maintainability_factors)
    
    def _generate_architecture_recommendations(self) -> List[str]:
        """Generate architecture recommendations based on analysis."""
        
        recommendations = []
        
        # Component complexity recommendations
        high_complexity_components = [
            comp for comp in self.component_analyses.values() 
            if comp.complexity_score > 20
        ]
        
        if high_complexity_components:
            recommendations.append(
                f"Refactor {len(high_complexity_components)} high-complexity components: "
                f"{', '.join([comp.name for comp in high_complexity_components[:3]])}"
            )
        
        # TypeScript recommendations
        untyped_components = [
            comp for comp in self.component_analyses.values() 
            if not comp.props_interface
        ]
        
        if len(untyped_components) > len(self.component_analyses) * 0.3:
            recommendations.append(
                f"Add TypeScript interfaces to {len(untyped_components)} components for better type safety"
            )
        
        # Pattern consistency recommendations
        if len(self.project_patterns) > 5:
            recommendations.append(
                "Consider standardizing on fewer architectural patterns for better consistency"
            )
        
        # State management recommendations
        if len(self.state_management_usage) > 3:
            recommendations.append(
                "Consolidate state management approaches - currently using "
                f"{len(self.state_management_usage)} different patterns"
            )
        
        # Component size recommendations
        large_components = [
            comp for comp in self.component_analyses.values() 
            if comp.lines_of_code > 300
        ]
        
        if large_components:
            recommendations.append(
                f"Break down {len(large_components)} large components into smaller, focused components"
            )
        
        return recommendations[:10]  # Top 10 recommendations
    
    def get_architecture_guidelines_for_context(self, context: Dict[str, Any]) -> List[ArchitecturalGuideline]:
        """Get relevant architectural guidelines for a given context."""
        
        relevant_guidelines = []
        
        # Extract context information
        component_type = context.get("component_type", "").lower()
        framework = context.get("framework", "").lower()
        complexity = context.get("complexity", "medium").lower()
        
        # Recommend patterns based on context
        if "hook" in component_type or context.get("needs_state_logic"):
            relevant_guidelines.append(self.architectural_guidelines[ArchitecturePattern.CUSTOM_HOOKS])
        
        if "complex" in complexity or "layout" in component_type:
            relevant_guidelines.append(self.architectural_guidelines[ArchitecturePattern.COMPONENT_COMPOSITION])
        
        if context.get("needs_global_state") or "provider" in component_type:
            relevant_guidelines.append(self.architectural_guidelines[ArchitecturePattern.PROVIDER_PATTERN])
        
        if context.get("needs_data_fetching") or "container" in component_type:
            relevant_guidelines.append(self.architectural_guidelines[ArchitecturePattern.CONTAINER_PRESENTER])
        
        return relevant_guidelines
    
    def get_best_practices_for_component(self, component_type: str) -> Dict[str, List[str]]:
        """Get best practices for a specific component type."""
        
        practices = {}
        
        # Get general best practices
        for category, practice_list in self.best_practices.items():
            practices[category] = []
            for practice_type, tips in practice_list.items():
                practices[category].extend(tips)
        
        # Add component-specific practices
        if component_type.lower() == "hook":
            practices["custom_hooks"] = [
                "Always start custom hook names with 'use'",
                "Return consistent data structures",
                "Handle loading and error states",
                "Use TypeScript for better developer experience"
            ]
        elif component_type.lower() == "provider":
            practices["provider_pattern"] = [
                "Split large contexts into smaller, focused ones",
                "Memoize context values to prevent unnecessary re-renders",
                "Provide custom hooks for consuming context",
                "Add proper error boundaries"
            ]
        elif component_type.lower() == "page":
            practices["page_components"] = [
                "Keep page components lean - delegate to feature components",
                "Implement proper error boundaries",
                "Handle loading states appropriately",
                "Use SEO-friendly patterns"
            ]
        
        return practices
    
    def export_architecture_analysis(self) -> Dict[str, Any]:
        """Export comprehensive architecture analysis."""
        
        return {
            "components_analyzed": len(self.component_analyses),
            "patterns_detected": {pattern.value: count for pattern, count in self.project_patterns.items()},
            "state_management": {pattern.value: count for pattern, count in self.state_management_usage.items()},
            "quality_metrics": self._calculate_quality_metrics(),
            "architectural_insights": [
                {
                    "category": insight.category,
                    "title": insight.title,
                    "description": insight.description,
                    "impact": insight.impact,
                    "recommendation": insight.recommendation,
                    "priority": insight.priority
                }
                for insight in self.architecture_insights
            ],
            "component_distribution": {
                comp_type.value: len([comp for comp in self.component_analyses.values() 
                                    if comp.component_type == comp_type])
                for comp_type in ComponentType
            },
            "recommendations": self._generate_architecture_recommendations()
        }


# Global instance
_architecture_analyzer_instance = None

def get_frontend_architecture_analyzer() -> FrontendArchitectureAnalyzer:
    """Get the global frontend architecture analyzer instance."""
    global _architecture_analyzer_instance
    if _architecture_analyzer_instance is None:
        _architecture_analyzer_instance = FrontendArchitectureAnalyzer()
    return _architecture_analyzer_instance