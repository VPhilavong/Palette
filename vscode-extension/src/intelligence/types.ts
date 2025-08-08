/**
 * TypeScript Intelligence Engine Types
 * Defines interfaces and types for the intelligence system
 */

import * as vscode from 'vscode';

export interface IntelligenceContext {
    workspace: WorkspaceInfo;
    project: ProjectInfo;
    codebase: CodebaseInfo;
    designSystem: DesignSystemInfo;
}

export interface WorkspaceInfo {
    path: string;
    name?: string;
    folders: string[];
    settings?: vscode.WorkspaceConfiguration;
}

export interface ProjectInfo {
    framework: string;
    buildTool: string;
    packageManager: string;
    dependencies: Record<string, string>;
    devDependencies: Record<string, string>;
    scripts: Record<string, string>;
    tsConfig?: any;
    structure: ProjectStructure;
}

export interface ProjectStructure {
    srcDir: string;
    componentsDir?: string;
    pagesDir?: string;
    libDir?: string;
    utilsDir?: string;
    stylesDir?: string;
    testsDir?: string;
    publicDir?: string;
}

export interface CodebaseInfo {
    components: ComponentInfo[];
    hooks: HookInfo[];
    utilities: UtilityInfo[];
    types: TypeInfo[];
    patterns: PatternMatch[];
    conventions: CodingConventions;
}

export interface ComponentInfo {
    name: string;
    path: string;
    type: 'functional' | 'class' | 'forwardRef';
    props?: PropDefinition[];
    hooks?: string[];
    dependencies: string[];
    stylingApproach: 'tailwind' | 'css' | 'styled-components' | 'emotion' | 'other';
    complexity: 'simple' | 'medium' | 'complex';
}

export interface PropDefinition {
    name: string;
    type: string;
    required: boolean;
    defaultValue?: any;
    description?: string;
}

export interface HookInfo {
    name: string;
    path: string;
    type: 'built-in' | 'custom';
    usage: string[];
    dependencies: string[];
}

export interface UtilityInfo {
    name: string;
    path: string;
    type: 'function' | 'class' | 'constant';
    usage: string[];
    dependencies: string[];
}

export interface TypeInfo {
    name: string;
    path: string;
    type: 'interface' | 'type' | 'enum' | 'class';
    definition: string;
    usage: string[];
}

export interface CodingConventions {
    naming: {
        components: 'PascalCase' | 'camelCase' | 'kebab-case';
        files: 'PascalCase' | 'camelCase' | 'kebab-case';
        variables: 'camelCase' | 'snake_case';
    };
    structure: {
        fileOrganization: 'feature-based' | 'type-based' | 'atomic' | 'mixed';
        importStyle: 'absolute' | 'relative' | 'mixed';
        exportStyle: 'named' | 'default' | 'mixed';
    };
    styling: {
        approach: 'tailwind' | 'css-modules' | 'styled-components' | 'emotion' | 'mixed';
        conventions: string[];
    };
}

export interface DesignSystemInfo {
    library?: 'shadcn/ui' | 'material-ui' | 'antd' | 'chakra-ui' | 'mantine' | 'custom';
    theme?: any;
    tokens: DesignTokens;
    components: DesignSystemComponent[];
    patterns: DesignPattern[];
}

export interface DesignTokens {
    colors: Record<string, string>;
    spacing: Record<string, string>;
    typography: Record<string, any>;
    breakpoints: Record<string, string>;
    shadows: Record<string, string>;
    borderRadius: Record<string, string>;
}

export interface DesignSystemComponent {
    name: string;
    variants?: string[];
    props?: Record<string, any>;
    usage: ComponentUsage[];
}

export interface ComponentUsage {
    component: string;
    frequency: number;
    context: string[];
    patterns: string[];
}

export interface DesignPattern {
    name: string;
    description: string;
    components: string[];
    structure: string;
    frequency: number;
}

export interface PatternMatch {
    type: PatternType;
    name: string;
    confidence: number;
    locations: string[];
    usage: PatternUsage;
    suggestion?: string;
}

export type PatternType = 
    | 'component-structure'
    | 'prop-pattern'
    | 'state-management'
    | 'data-fetching'
    | 'error-handling'
    | 'styling-pattern'
    | 'layout-pattern'
    | 'business-logic';

export interface PatternUsage {
    frequency: number;
    contexts: string[];
    variations: string[];
}

export interface AnalysisResult {
    context: IntelligenceContext;
    suggestions: ComponentSuggestion[];
    patterns: PatternMatch[];
    insights: ProjectInsight[];
    confidence: number;
    cached: boolean;
    timestamp: string;
}

export interface ComponentSuggestion {
    type: SuggestionType;
    name: string;
    description: string;
    rationale: string;
    confidence: number;
    priority: 'high' | 'medium' | 'low';
    implementation?: {
        strategy: 'reuse' | 'compose' | 'extend' | 'generate' | 'refactor';
        baseComponents?: string[];
        requiredProps?: PropDefinition[];
        suggestedStructure?: string;
        dependencies?: string[];
    };
}

export type SuggestionType = 
    | 'reuse-existing'
    | 'compose-multiple'
    | 'extend-component'
    | 'generate-new'
    | 'refactor-existing'
    | 'pattern-application';

export interface ProjectInsight {
    category: 'architecture' | 'patterns' | 'performance' | 'maintainability' | 'design-system';
    title: string;
    description: string;
    impact: 'high' | 'medium' | 'low';
    actionable: boolean;
    recommendation?: string;
}

export interface IntelligenceOptions {
    includePatterns?: boolean;
    includeSuggestions?: boolean;
    includeInsights?: boolean;
    maxCacheAge?: number;
    analysisDepth?: 'shallow' | 'medium' | 'deep';
    focusAreas?: IntelligenceFocus[];
}

export type IntelligenceFocus = 
    | 'components'
    | 'patterns'
    | 'design-system'
    | 'performance'
    | 'architecture'
    | 'conventions';

export interface CacheEntry<T> {
    data: T;
    timestamp: number;
    version: string;
    dependencies: string[];
}