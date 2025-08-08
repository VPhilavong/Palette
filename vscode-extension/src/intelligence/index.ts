/**
 * TypeScript Intelligence Engine
 * Replicates Python backend intelligence capabilities in pure TypeScript
 * Provides context-aware code analysis, pattern recognition, and generation suggestions
 */

export { TypeScriptIntelligenceEngine } from './intelligence-engine';
export { ProjectAnalyzer } from './project-analyzer';
export { CodePatternRecognizer } from './code-pattern-recognizer';
export { ComponentSuggestionEngine } from './component-suggestion-engine';
export { DesignSystemAnalyzer } from './design-system-analyzer';
export type { 
    IntelligenceContext, 
    AnalysisResult, 
    PatternMatch, 
    ComponentSuggestion,
    DesignSystemInfo 
} from './types';