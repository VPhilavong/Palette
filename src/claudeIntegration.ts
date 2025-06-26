import * as path from 'path';
import axios from 'axios';
import { 
    CodebaseContext, 
    AIRequest, 
    AIResponse, 
    ClaudeConfig,
    ContextWindow,
    AIRequestType
} from './types';

/**
 * Claude API integration with sophisticated prompt engineering
 * Handles context-aware code generation, explanation, and refactoring
 */
export class ClaudeIntegration {
    private readonly apiKey: string;
    private readonly baseURL = 'https://api.anthropic.com/v1/messages';
    private readonly model: string;
    private readonly maxTokens: number;
    
    constructor(config: ClaudeConfig) {
        this.apiKey = config.apiKey;
        this.model = config.model || 'claude-3-sonnet-20240229';
        this.maxTokens = config.maxTokens || 4000;
    }

    /**
     * Process AI request with full codebase context
     */
    async processRequest(request: AIRequest, context: CodebaseContext): Promise<AIResponse> {
        console.log(`🤖 Processing ${request.type} request with Claude...`);
        
        const startTime = Date.now();
        
        try {
            // Build sophisticated prompt based on request type
            const prompt = this.buildContextualPrompt(request, context);
            
            console.log(`📝 Built prompt with ${prompt.length} characters`);
            
            // Make API request to Claude
            const response = await this.callClaudeAPI(prompt, request.type);
            
            const processingTime = Date.now() - startTime;
            
            console.log(`✅ Claude response received in ${processingTime}ms`);
            
            return {
                content: response.content,
                type: request.type,
                confidence: this.calculateConfidence(response, context),
                suggestions: this.extractSuggestions(response.content),
                metadata: {
                    model: this.model,
                    tokensUsed: response.usage?.input_tokens || 0,
                    processingTime,
                    contextSize: context.metadata.totalTokens,
                    contextFiles: context.relatedFiles.length,
                    contextQuality: context.metadata.relevanceScore
                }
            };
            
        } catch (error) {
            console.error('Claude API error:', error);
            throw new Error(`AI request failed: ${error}`);
        }
    }

    /**
     * Build sophisticated context-aware prompt
     */
    private buildContextualPrompt(request: AIRequest, context: CodebaseContext): string {
        const parts: string[] = [];
        
        // System message with codebase understanding
        parts.push(this.buildSystemMessage(context));
        
        // Context information
        parts.push(this.buildContextSection(context));
        
        // Current file context
        if (context.currentFile) {
            parts.push(this.buildCurrentFileSection(context.currentFile));
        }
        
        // Related files and dependencies
        if (context.relatedFiles.length > 0) {
            parts.push(this.buildRelatedFilesSection(context.relatedFiles));
        }
        
        // Code chunks for reference
        if (context.chunks.length > 0) {
            parts.push(this.buildCodeChunksSection(context.chunks));
        }
        
        // User request
        parts.push(this.buildRequestSection(request));
        
        // Request-specific instructions
        parts.push(this.buildInstructionsSection(request.type));
        
        return parts.join('\n\n');
    }

    /**
     * Build system message with codebase context
     */
    private buildSystemMessage(context: CodebaseContext): string {
        const hasTypeScript = context.relatedFiles.some(f => f.language === 'typescript');
        const primaryLanguage = this.detectPrimaryLanguage(context.relatedFiles);
        const frameworks = this.detectFrameworks(context);
        
        return `You are a senior software engineer with deep expertise in ${primaryLanguage}${hasTypeScript ? ' and TypeScript' : ''}.
You have full access to and understanding of the user's codebase, which contains ${context.relatedFiles.length} relevant files.

CODEBASE CONTEXT:
- Primary Language: ${primaryLanguage}
- TypeScript: ${hasTypeScript ? 'Yes' : 'No'}
- Frameworks: ${frameworks.join(', ') || 'None detected'}
- Architecture Patterns: ${this.extractArchitecturePatterns(context)}
- Coding Style: ${this.extractCodingStyle(context)}

Your responses should:
1. Be consistent with the existing codebase patterns and style
2. Follow the established architectural principles
3. Use the same libraries and frameworks already in use
4. Maintain naming conventions and code organization
5. Consider the relationships between files and components
6. Provide production-ready, well-tested code`;
    }

    /**
     * Build context section with file overview
     */
    private buildContextSection(context: CodebaseContext): string {
        const parts = ['## CODEBASE OVERVIEW\n'];
        
        // File structure
        parts.push('### Project Structure:');
        const filesByDir = this.groupFilesByDirectory(context.relatedFiles);
        for (const [dir, files] of filesByDir.entries()) {
            parts.push(`- ${dir}/`);
            files.slice(0, 5).forEach(file => {
                parts.push(`  - ${file.path} (${file.symbols.length} exports)`);
            });
            if (files.length > 5) {
                parts.push(`  - ... and ${files.length - 5} more files`);
            }
        }
        
        // Key dependencies
        if (context.dependencies.length > 0) {
            parts.push('\n### Key Dependencies:');
            const uniqueDeps = [...new Set(context.dependencies)]
                .filter(dep => !dep.startsWith('.'))
                .slice(0, 10);
            parts.push(uniqueDeps.map(dep => `- ${dep}`).join('\n'));
        }
        
        // Important symbols
        if (context.symbols.length > 0) {
            parts.push('\n### Key Symbols:');
            const importantSymbols = context.symbols
                .filter(s => s.type === 'class' || s.type === 'function' || s.type === 'interface')
                .slice(0, 15);
            
            const symbolsByType = this.groupBy(importantSymbols, s => s.type);
            for (const [type, symbols] of symbolsByType.entries()) {
                parts.push(`- ${type}s: ${symbols.map(s => s.name).join(', ')}`);
            }
        }
        
        return parts.join('\n');
    }

    /**
     * Build current file context
     */
    private buildCurrentFileSection(currentFile: any): string {
        const parts = [`## CURRENT FILE: ${currentFile.path}\n`];
        
        parts.push('### File Overview:');
        parts.push(`- Language: ${currentFile.language}`);
        parts.push(`- Lines of Code: ${currentFile.lineCount}`);
        parts.push(`- Exports: ${currentFile.exports.length}`);
        parts.push(`- Imports: ${currentFile.imports.length}`);
        
        if (currentFile.symbols.length > 0) {
            parts.push('\n### Symbols in this file:');
            currentFile.symbols.forEach((symbol: any) => {
                parts.push(`- ${symbol.type} ${symbol.name} (line ${symbol.line})`);
            });
        }
        
        return parts.join('\n');
    }

    /**
     * Build related files section
     */
    private buildRelatedFilesSection(relatedFiles: any[]): string {
        const parts = ['## RELATED FILES\n'];
        
        relatedFiles.slice(0, 8).forEach(file => {
            parts.push(`### ${file.path}`);
            parts.push(`Language: ${file.language} | Symbols: ${file.symbols.length} | Size: ${file.lineCount} lines`);
            
            if (file.exports.length > 0) {
                parts.push(`Exports: ${file.exports.slice(0, 5).join(', ')}${file.exports.length > 5 ? '...' : ''}`);
            }
        });
        
        return parts.join('\n');
    }

    /**
     * Build code chunks section
     */
    private buildCodeChunksSection(chunks: any[]): string {
        const parts = ['## RELEVANT CODE EXAMPLES\n'];
        
        // Group chunks by relevance and type
        const sortedChunks = chunks
            .sort((a, b) => (b.relevanceScore || 0) - (a.relevanceScore || 0))
            .slice(0, 12); // Limit to most relevant
        
        sortedChunks.forEach((chunk, index) => {
            parts.push(`### Example ${index + 1}: ${chunk.filePath} (lines ${chunk.startLine}-${chunk.endLine})`);
            parts.push('```' + this.getLanguageForFile(chunk.filePath));
            parts.push(chunk.content);
            parts.push('```');
            parts.push(''); // Empty line for separation
        });
        
        return parts.join('\n');
    }

    /**
     * Build user request section
     */
    private buildRequestSection(request: AIRequest): string {
        const parts = ['## USER REQUEST\n'];
        
        parts.push(`**Type:** ${request.type}`);
        parts.push(`**Query:** ${request.query}`);
        
        if (request.selectedCode) {
            parts.push('\n**Selected Code:**');
            parts.push('```' + (request.language || 'typescript'));
            parts.push(request.selectedCode);
            parts.push('```');
        }
        
        if (request.cursorPosition) {
            parts.push(`\n**Cursor Position:** Line ${request.cursorPosition.line}, Column ${request.cursorPosition.character}`);
        }
        
        return parts.join('\n');
    }

    /**
     * Build request-specific instructions
     */
    private buildInstructionsSection(requestType: AIRequestType): string {
        const instructions: Record<AIRequestType, string> = {
            'completion': `## INSTRUCTIONS FOR CODE COMPLETION

Provide intelligent code completion based on:
1. The cursor position and surrounding context
2. Existing patterns in the codebase
3. TypeScript types and interfaces
4. Import statements and available symbols

Requirements:
- Provide only the completion code, no explanations
- Match the existing code style and formatting
- Use appropriate TypeScript types
- Consider the function/method signature context
- Respect the established patterns`,

            'explanation': `## INSTRUCTIONS FOR CODE EXPLANATION

Provide a clear, comprehensive explanation that covers:
1. What the code does and how it works
2. Its role within the larger codebase architecture
3. Dependencies and relationships with other components
4. Design patterns and architectural decisions
5. Potential improvements or considerations

Format:
- Use clear, non-technical language when possible
- Include code examples where helpful
- Explain the business logic and technical implementation
- Reference related files and components`,

            'refactor': `## INSTRUCTIONS FOR CODE REFACTORING

Analyze the selected code and provide refactoring suggestions that:
1. Improve code quality, readability, and maintainability
2. Follow established patterns in the codebase
3. Maintain backward compatibility
4. Consider performance implications
5. Use appropriate design patterns

Provide:
- The refactored code with clear improvements
- Explanation of changes and benefits
- Migration notes if necessary
- Tests that should be updated`,

            'generation': `## INSTRUCTIONS FOR CODE GENERATION

Generate new code that:
1. Follows the established patterns and architecture
2. Uses the same libraries and frameworks
3. Matches the existing code style and conventions
4. Integrates seamlessly with the current codebase
5. Includes appropriate TypeScript types and documentation

Provide:
- Complete, production-ready code
- Proper imports and dependencies
- Type definitions where needed
- Basic error handling
- Comments for complex logic`,

            'debug': `## INSTRUCTIONS FOR DEBUGGING ASSISTANCE

Analyze the code and provide debugging assistance by:
1. Identifying potential issues and bugs
2. Explaining the likely root cause
3. Providing step-by-step debugging approach
4. Suggesting fixes with code examples
5. Recommending prevention strategies

Focus on:
- Common patterns that lead to bugs in this codebase
- Type-related issues (if TypeScript)
- Async/await and Promise handling
- State management problems
- Performance bottlenecks`
        };

        return instructions[requestType] || instructions['generation'];
    }

    /**
     * Make actual API call to Claude
     */
    private async callClaudeAPI(prompt: string, requestType: AIRequestType): Promise<any> {
        const headers = {
            'Content-Type': 'application/json',
            'x-api-key': this.apiKey,
            'anthropic-version': '2023-06-01'
        };

        const data = {
            model: this.model,
            max_tokens: this.maxTokens,
            messages: [
                {
                    role: 'user',
                    content: prompt
                }
            ],
            temperature: requestType === 'completion' ? 0.1 : 0.3, // Lower temperature for completion
            stop_sequences: requestType === 'completion' ? ['\n\n', '```'] : undefined
        };

        const response = await axios.post(this.baseURL, data, { headers });
        
        if (response.status !== 200) {
            throw new Error(`Claude API error: ${response.status} ${response.statusText}`);
        }

        return {
            content: response.data.content[0].text,
            usage: response.data.usage
        };
    }

    /**
     * Helper methods
     */
    private detectPrimaryLanguage(files: any[]): string {
        const langCounts = new Map<string, number>();
        files.forEach(file => {
            const lang = file.language || 'unknown';
            langCounts.set(lang, (langCounts.get(lang) || 0) + 1);
        });
        
        const primary = Array.from(langCounts.entries())
            .sort(([,a], [,b]) => b - a)[0];
        
        return primary ? primary[0] : 'JavaScript';
    }

    private detectFrameworks(context: CodebaseContext): string[] {
        const frameworks: string[] = [];
        const deps = context.dependencies;
        
        if (deps.some(d => d.includes('react'))) frameworks.push('React');
        if (deps.some(d => d.includes('vue'))) frameworks.push('Vue');
        if (deps.some(d => d.includes('angular'))) frameworks.push('Angular');
        if (deps.some(d => d.includes('express'))) frameworks.push('Express');
        if (deps.some(d => d.includes('next'))) frameworks.push('Next.js');
        if (deps.some(d => d.includes('tailwind'))) frameworks.push('Tailwind CSS');
        
        return frameworks;
    }

    private extractArchitecturePatterns(context: CodebaseContext): string {
        // This would analyze the codebase structure to identify patterns
        const patterns: string[] = [];
        
        // Check for common patterns based on file structure
        const hasComponents = context.relatedFiles.some(f => f.path.includes('component'));
        const hasServices = context.relatedFiles.some(f => f.path.includes('service'));
        const hasUtils = context.relatedFiles.some(f => f.path.includes('util'));
        
        if (hasComponents) patterns.push('Component-based');
        if (hasServices) patterns.push('Service Layer');
        if (hasUtils) patterns.push('Utility Functions');
        
        return patterns.join(', ') || 'Standard';
    }

    private extractCodingStyle(context: CodebaseContext): string {
        // Analyze code chunks to determine style preferences
        const styles: string[] = [];
        
        // Check for TypeScript usage
        if (context.relatedFiles.some(f => f.language === 'typescript')) {
            styles.push('TypeScript');
        }
        
        // Check for functional vs OOP
        const hasFunctions = context.chunks.some(c => c.type === 'function');
        const hasClasses = context.chunks.some(c => c.type === 'class');
        
        if (hasFunctions && !hasClasses) styles.push('Functional');
        else if (hasClasses && !hasFunctions) styles.push('Object-Oriented');
        else if (hasFunctions && hasClasses) styles.push('Mixed Paradigm');
        
        return styles.join(', ') || 'Standard';
    }

    private groupFilesByDirectory(files: any[]): Map<string, any[]> {
        const groups = new Map<string, any[]>();
        
        files.forEach(file => {
            const dir = path.dirname(file.path) || 'root';
            if (!groups.has(dir)) {
                groups.set(dir, []);
            }
            groups.get(dir)!.push(file);
        });
        
        return groups;
    }

    private groupBy<T, K>(array: T[], keyFn: (item: T) => K): Map<K, T[]> {
        const groups = new Map<K, T[]>();
        array.forEach(item => {
            const key = keyFn(item);
            if (!groups.has(key)) {
                groups.set(key, []);
            }
            groups.get(key)!.push(item);
        });
        return groups;
    }

    private getLanguageForFile(filePath: string): string {
        const ext = path.extname(filePath);
        const langMap: Record<string, string> = {
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.py': 'python',
            '.java': 'java'
        };
        return langMap[ext] || 'text';
    }

    private calculateConfidence(response: any, context: CodebaseContext): number {
        let confidence = 0.7; // Base confidence
        
        // Higher confidence with more context
        if (context.relatedFiles.length > 5) confidence += 0.1;
        if (context.metadata.relevanceScore > 0.8) confidence += 0.1;
        if (context.chunks.length > 8) confidence += 0.1;
        
        return Math.min(confidence, 1.0);
    }

    private extractSuggestions(content: string): string[] {
        const suggestions: string[] = [];
        
        // Extract suggestions from common patterns in Claude responses
        const lines = content.split('\n');
        lines.forEach(line => {
            if (line.includes('consider') || line.includes('suggest') || line.includes('recommend')) {
                suggestions.push(line.trim());
            }
        });
        
        return suggestions.slice(0, 5); // Limit to 5 suggestions
    }

    /**
     * Validate API configuration
     */
    static validateConfig(config: ClaudeConfig): boolean {
        return !!(config.apiKey && config.apiKey.length > 0);
    }

    /**
     * Get available models
     */
    static getAvailableModels(): string[] {
        return [
            'claude-3-opus-20240229',
            'claude-3-sonnet-20240229',
            'claude-3-haiku-20240307'
        ];
    }
}