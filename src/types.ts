export interface WorkspaceInfo {
    hasTypeScript: boolean;
    styling: StylingInfo;
    existingComponents: ComponentInfo[];
    projectStructure: string[];
    // Enhanced analysis data
    dependencyGraph?: DependencyGraph;
    patterns?: CodePatterns;
    architecture?: ArchitectureInfo;
}

export interface StylingInfo {
    hasTailwind: boolean;
    hasStyledComponents: boolean;
    hasCSSModules: boolean;
    hasEmotion: boolean;
    // Enhanced styling analysis
    primaryApproach?: 'tailwind' | 'styled-components' | 'css-modules' | 'emotion' | 'inline';
    customTheme?: boolean;
    responsivePatterns?: string[];
    // Framework and UI library detection
    uiLibrary?: string;
    hasNextJS?: boolean;
    hasLucideIcons?: boolean;
    hasShadcnUI?: boolean;
}

export interface ComponentInfo {
    name: string;
    path: string;
    description: string;
    props?: string;
    // Enhanced component analysis
    ast?: ComponentAST;
    dependencies?: string[];
    complexity?: 'simple' | 'medium' | 'complex';
    category?: ComponentCategory;
}

export interface GenerationContext {
    prompt: string;
    workspaceInfo: WorkspaceInfo;
    selectedCode?: string;
    // Enhanced context
    relevantComponents?: RelevantComponent[];
    suggestedPatterns?: string[];
    contextScore?: number;
}

// Enhanced AST Analysis Types
export interface ComponentAST {
    name: string;
    type: 'functional' | 'class';
    props: PropAnalysis[];
    hooks: HookUsage[];
    imports: ImportInfo[];
    exports: ExportInfo[];
    jsx: JSXAnalysis;
    styling: ComponentStyling;
    complexity: ComplexityMetrics;
}

export interface PropAnalysis {
    name: string;
    type: string;
    optional: boolean;
    defaultValue?: string;
    description?: string;
    validation?: string;
}

export interface HookUsage {
    name: string;
    type: 'state' | 'effect' | 'context' | 'callback' | 'memo' | 'ref' | 'custom';
    dependencies?: string[];
    complexity: number;
}

export interface ImportInfo {
    source: string;
    type: 'default' | 'named' | 'namespace';
    imports: string[];
    isExternal: boolean;
    category?: 'react' | 'library' | 'component' | 'utility' | 'style';
}

export interface ExportInfo {
    name: string;
    type: 'default' | 'named';
    isComponent: boolean;
}

export interface JSXAnalysis {
    elementCount: number;
    complexity: number;
    patterns: string[];
    accessibility: AccessibilityInfo;
    interactivity: InteractivityInfo;
}

export interface ComponentStyling {
    approach: string;
    classes: string[];
    inlineStyles: boolean;
    responsive: boolean;
    variants: string[];
    animations: boolean;
}

export interface ComplexityMetrics {
    cyclomaticComplexity: number;
    cognitiveComplexity: number;
    linesOfCode: number;
    depth: number;
}

export interface AccessibilityInfo {
    ariaAttributes: string[];
    semanticElements: string[];
    keyboardHandling: boolean;
    focusManagement: boolean;
    score: number;
}

export interface InteractivityInfo {
    eventHandlers: string[];
    formElements: boolean;
    animations: boolean;
    stateManagement: 'none' | 'simple' | 'complex';
}

// Pattern Recognition Types
export interface CodePatterns {
    namingConventions: NamingConventions;
    architecturalPatterns: string[];
    stylePatterns: StylePatterns;
    stateManagementPatterns: string[];
    testingPatterns: string[];
}

export interface NamingConventions {
    components: 'PascalCase' | 'camelCase';
    files: 'PascalCase' | 'kebab-case' | 'camelCase';
    props: 'camelCase' | 'snake_case';
    constants: 'UPPER_CASE' | 'camelCase';
}

export interface StylePatterns {
    classNaming: 'BEM' | 'utility' | 'semantic' | 'mixed';
    organization: 'atomic' | 'component-based' | 'utility-first';
    responsiveStrategy: 'mobile-first' | 'desktop-first' | 'mixed';
}

// Dependency Analysis Types
export interface DependencyGraph {
    nodes: ComponentNode[];
    edges: DependencyEdge[];
    clusters: ComponentCluster[];
    metrics: GraphMetrics;
}

export interface ComponentNode {
    id: string;
    name: string;
    path: string;
    type: ComponentCategory;
    weight: number;
    connections: number;
}

export interface DependencyEdge {
    from: string;
    to: string;
    type: 'import' | 'composition' | 'prop-passing';
    weight: number;
}

export interface ComponentCluster {
    id: string;
    components: string[];
    category: ComponentCategory;
    cohesion: number;
}

export interface GraphMetrics {
    density: number;
    modularity: number;
    avgPathLength: number;
    centralityScores: Record<string, number>;
}

// Context Ranking Types
export interface RelevantComponent {
    component: ComponentInfo;
    relevanceScore: number;
    reasons: RelevanceReason[];
    similarity: SimilarityMetrics;
}

export interface RelevanceReason {
    type: 'pattern-match' | 'dependency' | 'naming' | 'structure' | 'styling';
    confidence: number;
    description: string;
}

export interface SimilarityMetrics {
    structural: number;
    semantic: number;
    stylistic: number;
    functional: number;
    overall: number;
}

// Architecture Analysis Types
export interface ArchitectureInfo {
    patterns: string[];
    layering: LayerInfo[];
    componentHierarchy: HierarchyInfo;
    dataFlow: DataFlowInfo;
}

export interface LayerInfo {
    name: string;
    components: string[];
    responsibilities: string[];
}

export interface HierarchyInfo {
    depth: number;
    fanOut: Record<string, number>;
    abstractionLevels: string[];
}

export interface DataFlowInfo {
    stateManagement: 'local' | 'context' | 'redux' | 'zustand' | 'mixed';
    propDrilling: boolean;
    eventPatterns: string[];
}

// Component Categories
export type ComponentCategory = 
    | 'layout'
    | 'ui-primitive' 
    | 'form'
    | 'data-display'
    | 'navigation'
    | 'feedback'
    | 'overlay'
    | 'business-logic'
    | 'page'
    | 'utility';

// Advanced Pattern Analysis Types
export interface CodeSnippet {
    id: string;
    componentName: string;
    category: ComponentCategory;
    snippet: string;
    context: SnippetContext;
    patterns: DetectedPattern[];
    usageFrequency: number;
}

export interface SnippetContext {
    filePath: string;
    startLine: number;
    endLine: number;
    surrounding: string[];
    imports: string[];
    exports: string[];
}

export interface DetectedPattern {
    type: PatternType;
    name: string;
    description: string;
    examples: string[];
    confidence: number;
    usage: PatternUsage;
}

export type PatternType = 
    | 'hook-pattern'
    | 'state-management'
    | 'styling-pattern'
    | 'composition-pattern'
    | 'error-handling'
    | 'loading-state'
    | 'api-integration'
    | 'typescript-pattern'
    | 'accessibility-pattern'
    | 'performance-pattern';

export interface PatternUsage {
    frequency: number;
    components: string[];
    evolution: 'stable' | 'growing' | 'declining';
    bestPractice: boolean;
}

export interface DesignSystemAnalysis {
    componentLibrary?: string;
    themeStructure?: ThemeStructure;
    colorPalette?: ColorPalette;
    spacingSystem?: SpacingSystem;
    typographySystem?: TypographySystem;
    iconSystem?: IconSystem;
    designTokens?: DesignToken[];
}

export interface ThemeStructure {
    provider: string;
    themePath?: string;
    variables: ThemeVariable[];
    breakpoints: Record<string, string>;
    darkMode: boolean;
}

export interface ThemeVariable {
    name: string;
    value: string;
    category: 'color' | 'spacing' | 'typography' | 'shadow' | 'border' | 'other';
    usage: string[];
}

export interface ColorPalette {
    primary: string[];
    secondary: string[];
    semantic: Record<string, string[]>;
    neutral: string[];
}

export interface SpacingSystem {
    unit: string;
    scale: Record<string, string>;
    customValues: string[];
}

export interface TypographySystem {
    fontFamilies: Record<string, string>;
    fontSizes: Record<string, string>;
    fontWeights: Record<string, string>;
    lineHeights: Record<string, string>;
}

export interface IconSystem {
    library: string;
    usage: IconUsage[];
    customIcons: boolean;
}

export interface IconUsage {
    name: string;
    frequency: number;
    contexts: string[];
}

export interface DesignToken {
    name: string;
    value: string;
    type: string;
    description?: string;
    aliases?: string[];
}

export interface StateManagementAnalysis {
    primary: StateManagementType;
    patterns: StatePattern[];
    stores: StoreInfo[];
    reducers: ReducerInfo[];
    contexts: ContextInfo[];
}

export type StateManagementType = 'redux' | 'zustand' | 'context' | 'jotai' | 'recoil' | 'local' | 'mixed';

export interface StatePattern {
    name: string;
    type: 'action' | 'selector' | 'middleware' | 'reducer' | 'hook';
    usage: number;
    examples: string[];
}

export interface StoreInfo {
    name: string;
    path: string;
    slices: string[];
    actions: string[];
    selectors: string[];
}

export interface ReducerInfo {
    name: string;
    actions: string[];
    complexity: number;
}

export interface ContextInfo {
    name: string;
    provides: string[];
    consumers: string[];
}

export interface TypeScriptPatterns {
    strictMode: boolean;
    interfaceUsage: InterfaceUsage[];
    genericUsage: GenericUsage[];
    utilityTypes: string[];
    customTypes: CustomType[];
    returnTypes: ReturnTypeAnalysis[];
}

export interface InterfaceUsage {
    name: string;
    category: 'props' | 'api' | 'state' | 'config' | 'other';
    complexity: number;
    usage: number;
}

export interface GenericUsage {
    pattern: string;
    frequency: number;
    complexity: number;
}

export interface CustomType {
    name: string;
    definition: string;
    usage: number;
}

export interface ReturnTypeAnalysis {
    pattern: string;
    usage: number;
    examples: string[];
}

export interface ExampleLibrary {
    snippets: Record<string, CodeSnippet[]>;
    patterns: Record<PatternType, DetectedPattern[]>;
    templates: ComponentTemplate[];
    bestPractices: BestPractice[];
}

export interface ComponentTemplate {
    id: string;
    name: string;
    category: ComponentCategory;
    template: string;
    variables: TemplateVariable[];
    score: number;
}

export interface TemplateVariable {
    name: string;
    type: string;
    defaultValue?: string;
    required: boolean;
}

export interface BestPractice {
    id: string;
    pattern: string;
    description: string;
    examples: string[];
    antiPatterns: string[];
    score: number;
}

export interface IntelligentContext {
    relevantComponents: ComponentInfo[];
    codeExamples: CodeSnippet[];
    patternSuggestions: DetectedPattern[];
    designSystemContext: DesignSystemAnalysis;
    stateManagementContext: StateManagementAnalysis;
    typeScriptContext: TypeScriptPatterns;
    contextSummary: string;
    confidenceScore: number;
}