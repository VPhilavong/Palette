import { GoogleGenerativeAI, GenerativeModel, Part } from '@google/generative-ai';
import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { 
    CodebaseContext, 
    AIRequest, 
    AIResponse, 
    GeminiConfig,
    AIRequestType,
    FileMetadata
} from './types';

/**
 * Gemini 2.0 Flash integration optimized for massive context windows and multimodal capabilities
 * Leverages 2M token context for entire codebase awareness
 */
export class GeminiIntegration {
    private readonly genAI: GoogleGenerativeAI;
    private readonly model: GenerativeModel;
    private readonly modelName: string;
    private readonly maxTokens: number;
    
    constructor(config: GeminiConfig) {
        this.genAI = new GoogleGenerativeAI(config.apiKey);
        this.modelName = config.model || 'gemini-2.0-flash-exp';
        this.maxTokens = config.maxTokens || 100000; // Response tokens, context is 2M
        
        this.model = this.genAI.getGenerativeModel({
            model: this.modelName,
            generationConfig: {
                maxOutputTokens: this.maxTokens,
                temperature: config.temperature || 0.3,
                topP: 0.8,
                topK: 20
            }
        });
    }

    /**
     * Process AI request with massive codebase context (2M tokens!)
     */
    async processRequest(request: AIRequest, context: CodebaseContext): Promise<AIResponse> {
        console.log(`🚀 Processing ${request.type} request with Gemini 2.0 Flash...`);
        
        const startTime = Date.now();
        
        try {
            // Build comprehensive prompt using Gemini's massive context window
            const prompt = this.buildMassiveContextPrompt(request, context);
            
            console.log(`📝 Built prompt with ${prompt.length} characters for 2M token context`);
            
            // Make API request to Gemini
            const response = await this.callGeminiAPI(prompt, request);
            
            const processingTime = Date.now() - startTime;
            
            console.log(`✅ Gemini response received in ${processingTime}ms`);
            
            return {
                content: response.content,
                type: request.type,
                confidence: this.calculateConfidence(response, context),
                suggestions: this.extractSuggestions(response.content),
                metadata: {
                    model: this.modelName,
                    tokensUsed: response.usage?.inputTokens || 0,
                    processingTime,
                    contextSize: context.metadata.totalTokens,
                    contextFiles: context.relatedFiles.length,
                    contextQuality: context.metadata.relevanceScore
                }
            };
            
        } catch (error) {
            console.error('Gemini API error:', error);
            throw new Error(`AI request failed: ${error}`);
        }
    }

    /**
     * Build massive context prompt leveraging Gemini's 2M token window
     * Unlike Claude, we can include the ENTIRE codebase if needed
     */
    private buildMassiveContextPrompt(request: AIRequest, context: CodebaseContext): string {
        const parts: string[] = [];
        
        // System message optimized for Gemini 2.0 Flash
        parts.push(this.buildGeminiSystemMessage(context));
        
        // MASSIVE context section - include way more than Claude could handle
        parts.push(this.buildMassiveContextSection(context));
        
        // Current file with full content
        if (context.currentFile) {
            parts.push(this.buildFullFileSection(context.currentFile));
        }
        
        // ALL related files with full content (Gemini can handle it!)
        if (context.relatedFiles.length > 0) {
            parts.push(this.buildAllRelatedFilesSection(context.relatedFiles));
        }
        
        // ALL code chunks (no need to limit like with Claude)
        if (context.chunks.length > 0) {
            parts.push(this.buildAllCodeChunksSection(context.chunks));
        }
        
        // Dependencies and architecture
        parts.push(this.buildArchitectureSection(context));
        
        // User request
        parts.push(this.buildRequestSection(request));
        
        // Gemini-specific instructions
        parts.push(this.buildGeminiInstructions(request.type));
        
        return parts.join('\n\n');
    }

    /**
     * Build system message optimized for Gemini's capabilities
     */
    private buildGeminiSystemMessage(context: CodebaseContext): string {
        const hasTypeScript = context.relatedFiles.some(f => f.language === 'typescript');
        const primaryLanguage = this.detectPrimaryLanguage(context.relatedFiles);
        const frameworks = this.detectFrameworks(context);
        
        return `You are an expert software engineer with comprehensive understanding of large codebases.
You have access to the ENTIRE codebase with ${context.relatedFiles.length} files and complete context.

CODEBASE OVERVIEW:
- Primary Language: ${primaryLanguage}
- TypeScript: ${hasTypeScript ? 'Yes' : 'No'}
- Frameworks: ${frameworks.join(', ') || 'None detected'}
- Total Files: ${context.relatedFiles.length}
- Architecture: ${this.extractArchitecturePatterns(context)}
- Context Quality: ${Math.round(context.metadata.relevanceScore * 100)}%

GEMINI 2.0 FLASH CAPABILITIES:
- You can see the ENTIRE codebase context (2M tokens)
- Provide ultra-fast, comprehensive responses
- Understand complex multi-file relationships
- Generate code that perfectly fits existing patterns
- Leverage massive context for superior accuracy

Your responses should be:
1. Extremely accurate due to complete codebase visibility
2. Perfectly consistent with existing patterns
3. Fast and efficient (leverage Gemini's speed)
4. Comprehensive yet concise
5. Production-ready and well-integrated`;
    }

    /**
     * Build massive context section - include everything!
     */
    private buildMassiveContextSection(context: CodebaseContext): string {
        const parts = ['## COMPLETE CODEBASE CONTEXT\n'];
        
        // Project structure with ALL files
        parts.push('### Complete File Structure:');
        const filesByDir = this.groupFilesByDirectory(context.relatedFiles);
        for (const [dir, files] of filesByDir.entries()) {
            parts.push(`- ${dir}/`);
            files.forEach(file => {
                parts.push(`  - ${file.path} (${file.symbols.length} symbols, ${file.lineCount} lines)`);
            });
        }
        
        // ALL dependencies
        if (context.dependencies.length > 0) {
            parts.push('\n### Complete Dependency Map:');
            const uniqueDeps = [...new Set(context.dependencies)];
            const external = uniqueDeps.filter(dep => !dep.startsWith('.'));
            const internal = uniqueDeps.filter(dep => dep.startsWith('.'));
            
            if (external.length > 0) {
                parts.push('External Dependencies:');
                parts.push(external.map(dep => `- ${dep}`).join('\n'));
            }
            
            if (internal.length > 0) {
                parts.push('Internal Dependencies:');
                parts.push(internal.map(dep => `- ${dep}`).join('\n'));
            }
        }
        
        // ALL symbols across the codebase
        if (context.symbols.length > 0) {
            parts.push('\n### Complete Symbol Map:');
            const symbolsByType = this.groupBy(context.symbols, s => s.type);
            for (const [type, symbols] of symbolsByType.entries()) {
                parts.push(`${type}s (${symbols.length}):`);
                symbols.slice(0, 50).forEach(symbol => {
                    parts.push(`- ${symbol.name} (${symbol.filePath}:${symbol.line})`);
                });
                if (symbols.length > 50) {
                    parts.push(`- ... and ${symbols.length - 50} more`);
                }
            }
        }
        
        return parts.join('\n');
    }

    /**
     * Include full file content (Gemini can handle it!)
     */
    private buildFullFileSection(currentFile: FileMetadata): string {
        const parts = [`## CURRENT FILE: ${currentFile.path}\n`];
        
        parts.push('### File Metadata:');
        parts.push(`- Language: ${currentFile.language}`);
        parts.push(`- Size: ${currentFile.lineCount} lines`);
        parts.push(`- Symbols: ${currentFile.symbols.length}`);
        parts.push(`- Imports: ${currentFile.imports.length}`);
        parts.push(`- Exports: ${currentFile.exports.length}`);
        
        // Include ALL chunks (full file content)
        if (currentFile.chunks.length > 0) {
            parts.push('\n### Complete File Content:');
            currentFile.chunks.forEach((chunk, index) => {
                parts.push(`\n#### Section ${index + 1} (lines ${chunk.startLine}-${chunk.endLine}):`);
                parts.push('```' + currentFile.language);
                parts.push(chunk.content);
                parts.push('```');
            });
        }
        
        return parts.join('\n');
    }

    /**
     * Include ALL related files with full content
     */
    private buildAllRelatedFilesSection(relatedFiles: FileMetadata[]): string {
        const parts = ['## ALL RELATED FILES\n'];
        
        // Include up to 20 files with full content (Gemini can handle it)
        const filesToInclude = relatedFiles.slice(0, 20);
        
        filesToInclude.forEach(file => {
            parts.push(`### ${file.path}`);
            parts.push(`Language: ${file.language} | Lines: ${file.lineCount} | Symbols: ${file.symbols.length}`);
            
            if (file.exports.length > 0) {
                parts.push(`Exports: ${file.exports.join(', ')}`);
            }
            
            if (file.imports.length > 0) {
                parts.push(`Imports: ${file.imports.slice(0, 10).join(', ')}${file.imports.length > 10 ? '...' : ''}`);
            }
            
            // Include significant code chunks
            if (file.chunks.length > 0) {
                parts.push('\n#### Key Code Sections:');
                file.chunks.slice(0, 3).forEach(chunk => {
                    if (chunk.type !== 'general') { // Focus on functions, classes, interfaces
                        parts.push(`\n**${chunk.type} (lines ${chunk.startLine}-${chunk.endLine}):**`);
                        parts.push('```' + file.language);
                        parts.push(chunk.content);
                        parts.push('```');
                    }
                });
            }
            
            parts.push(''); // Separator
        });
        
        if (relatedFiles.length > 20) {
            parts.push(`### Additional Files (${relatedFiles.length - 20} more)`);
            relatedFiles.slice(20).forEach(file => {
                parts.push(`- ${file.path} (${file.language}, ${file.lineCount} lines)`);
            });
        }
        
        return parts.join('\n');
    }

    /**
     * Include ALL code chunks without limitation
     */
    private buildAllCodeChunksSection(chunks: any[]): string {
        const parts = ['## ALL RELEVANT CODE EXAMPLES\n'];
        
        // Sort by relevance and include many more than Claude could handle
        const sortedChunks = chunks
            .sort((a, b) => (b.relevanceScore || 0) - (a.relevanceScore || 0))
            .slice(0, 50); // Much higher limit for Gemini
        
        sortedChunks.forEach((chunk, index) => {
            parts.push(`### Example ${index + 1}: ${chunk.filePath} (lines ${chunk.startLine}-${chunk.endLine})`);
            parts.push(`Type: ${chunk.type} | Relevance: ${Math.round((chunk.relevanceScore || 0) * 100)}%`);
            parts.push('```' + this.getLanguageForFile(chunk.filePath));
            parts.push(chunk.content);
            parts.push('```');
            parts.push(''); // Separator
        });
        
        return parts.join('\n');
    }

    /**
     * Build comprehensive architecture section
     */
    private buildArchitectureSection(context: CodebaseContext): string {
        const parts = ['## COMPLETE ARCHITECTURE ANALYSIS\n'];
        
        // File organization patterns
        parts.push('### Project Organization:');
        const directories = [...new Set(context.relatedFiles.map(f => path.dirname(f.path)))];
        directories.forEach(dir => {
            const filesInDir = context.relatedFiles.filter(f => path.dirname(f.path) === dir);
            parts.push(`- ${dir}/ (${filesInDir.length} files)`);
        });
        
        // Component patterns
        parts.push('\n### Component Patterns:');
        const componentFiles = context.relatedFiles.filter(f => 
            f.path.includes('component') || f.exports.some(exp => exp.includes('Component'))
        );
        parts.push(`- React Components: ${componentFiles.length}`);
        
        // Styling patterns
        parts.push('\n### Styling Approach:');
        const stylingHints = this.detectStylingPatterns(context.relatedFiles);
        stylingHints.forEach(hint => parts.push(`- ${hint}`));
        
        // State management
        parts.push('\n### State Management:');
        const statePatterns = this.detectStateManagement(context.relatedFiles);
        statePatterns.forEach(pattern => parts.push(`- ${pattern}`));
        
        return parts.join('\n');
    }

    /**
     * Build request section
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
     * Build Gemini-specific instructions
     */
    private buildGeminiInstructions(requestType: AIRequestType): string {
        const instructions: Record<AIRequestType, string> = {
            'completion': `## GEMINI 2.0 FLASH CODE COMPLETION

With your massive 2M token context window, you can see the ENTIRE codebase. Use this to:

1. **Perfect Context Awareness**: Reference any file, function, or pattern in the codebase
2. **Ultra-Fast Response**: Leverage Gemini's speed for real-time completion
3. **Pattern Matching**: Use the complete codebase to match exact patterns
4. **Type Safety**: Reference actual TypeScript types from across the project
5. **Import Intelligence**: Suggest exact import paths from the codebase

COMPLETION REQUIREMENTS:
- Provide ONLY the completion code (no explanations)
- Match exact naming conventions from the codebase
- Use consistent styling and patterns
- Reference actual functions/components that exist
- Maintain perfect type safety`,

            'explanation': `## GEMINI 2.0 FLASH CODE EXPLANATION

Leverage your complete codebase visibility to provide comprehensive explanations:

1. **Multi-File Context**: Explain how code relates to other files
2. **Architecture Understanding**: Show how it fits in the overall system
3. **Pattern Recognition**: Identify and explain architectural patterns
4. **Dependency Mapping**: Show relationships and data flow
5. **Design Decisions**: Explain why code is structured this way

EXPLANATION FORMAT:
- **What it does**: Core functionality
- **How it works**: Implementation details  
- **Where it fits**: Architecture role
- **Related code**: References to other files
- **Patterns used**: Design patterns identified
- **Suggestions**: Potential improvements`,

            'refactor': `## GEMINI 2.0 FLASH CODE REFACTORING

Use complete codebase awareness for intelligent refactoring:

1. **Global Impact Analysis**: Understand refactoring effects across all files
2. **Pattern Consistency**: Ensure refactoring matches project patterns
3. **Breaking Change Detection**: Identify potential breaking changes
4. **Performance Optimization**: Leverage codebase knowledge for optimization
5. **Best Practice Application**: Apply patterns used elsewhere in the codebase

REFACTORING APPROACH:
- Analyze current code in full context
- Identify improvement opportunities
- Ensure consistency with existing patterns
- Provide migration strategy if needed
- Consider performance implications`,

            'generation': `## GEMINI 2.0 FLASH CODE GENERATION

Generate code with perfect codebase integration:

1. **Pattern Replication**: Copy exact patterns from similar components
2. **Library Usage**: Use the same libraries and utilities as existing code
3. **Style Consistency**: Match exact naming, structure, and formatting
4. **Type Integration**: Use existing TypeScript interfaces and types
5. **Architecture Compliance**: Follow established architectural patterns

GENERATION REQUIREMENTS:
- Perfect integration with existing codebase
- Use actual imports and dependencies from the project
- Follow exact naming conventions
- Match styling approach (CSS modules, styled-components, etc.)
- Include proper TypeScript types
- Add appropriate error handling`,

            'debug': `## GEMINI 2.0 FLASH DEBUGGING ASSISTANCE

Use complete codebase visibility for advanced debugging:

1. **Cross-File Analysis**: Find issues spanning multiple files
2. **Data Flow Tracing**: Track data flow through the entire system
3. **Pattern Violations**: Identify where code breaks established patterns
4. **Performance Bottlenecks**: Spot performance issues using codebase knowledge
5. **Integration Issues**: Find problems with component integration

DEBUGGING APPROACH:
- Analyze issue in complete context
- Trace data flow across files
- Identify root cause using codebase knowledge
- Provide specific fix with code examples
- Suggest prevention strategies`
        };

        return instructions[requestType] || instructions['generation'];
    }

    /**
     * Make API call to Gemini 2.0 Flash
     */
    private async callGeminiAPI(prompt: string, request: AIRequest): Promise<any> {
        try {
            const result = await this.model.generateContent([{ text: prompt }]);
            const response = result.response;
            
            return {
                content: response.text(),
                usage: {
                    inputTokens: (response as any).usageMetadata?.promptTokenCount || 0,
                    outputTokens: (response as any).usageMetadata?.candidatesTokenCount || 0
                }
            };
        } catch (error) {
            console.error('Gemini API call failed:', error);
            throw error;
        }
    }

    /**
     * Process multimodal content (screenshots, diagrams, etc.)
     */
    async processMultimodalRequest(
        request: AIRequest, 
        context: CodebaseContext, 
        imagePaths: string[]
    ): Promise<AIResponse> {
        console.log(`🖼️ Processing multimodal request with ${imagePaths.length} images...`);
        
        const startTime = Date.now();
        
        try {
            const textPrompt = this.buildMassiveContextPrompt(request, context);
            const parts: Part[] = [{ text: textPrompt }];
            
            // Add image parts
            for (const imagePath of imagePaths) {
                if (fs.existsSync(imagePath)) {
                    const imageData = fs.readFileSync(imagePath);
                    const mimeType = this.getMimeType(imagePath);
                    
                    parts.push({
                        inlineData: {
                            data: imageData.toString('base64'),
                            mimeType
                        }
                    });
                }
            }
            
            const result = await this.model.generateContent(parts);
            const response = result.response;
            
            const processingTime = Date.now() - startTime;
            
            return {
                content: response.text(),
                type: request.type,
                confidence: 0.9, // Higher confidence with visual context
                suggestions: this.extractSuggestions(response.text()),
                metadata: {
                    model: this.modelName,
                    tokensUsed: (response as any).usageMetadata?.promptTokenCount || 0,
                    processingTime,
                    contextSize: context.metadata.totalTokens,
                    contextFiles: context.relatedFiles.length,
                    contextQuality: context.metadata.relevanceScore
                }
            };
            
        } catch (error) {
            console.error('Multimodal Gemini request failed:', error);
            throw error;
        }
    }

    /**
     * Helper methods
     */
    private detectPrimaryLanguage(files: FileMetadata[]): string {
        const langCounts = new Map<string, number>();
        const extensionCounts = new Map<string, number>();
        
        files.forEach(file => {
            // Count by detected language
            const lang = file.language || 'unknown';
            langCounts.set(lang, (langCounts.get(lang) || 0) + 1);
            
            // Count by file extension for accuracy
            const ext = file.extension || '';
            extensionCounts.set(ext, (extensionCounts.get(ext) || 0) + 1);
        });
        
        // Check for TypeScript dominance
        const tsFiles = (extensionCounts.get('.ts') || 0) + (extensionCounts.get('.tsx') || 0);
        const jsFiles = (extensionCounts.get('.js') || 0) + (extensionCounts.get('.jsx') || 0);
        const totalFiles = files.length;
        
        // If majority are TypeScript files, return TypeScript
        if (tsFiles > jsFiles && tsFiles > totalFiles * 0.3) {
            return 'TypeScript';
        }
        
        // Check by language detection
        const primary = Array.from(langCounts.entries())
            .sort(([,a], [,b]) => b - a)[0];
        
        if (primary) {
            // Prefer TypeScript over JavaScript if detected
            if (primary[0] === 'typescript' || langCounts.get('typescript')) {
                return 'TypeScript';
            }
            return primary[0] === 'javascript' ? 'JavaScript' : primary[0];
        }
        
        return 'JavaScript';
    }

    private detectFrameworks(context: CodebaseContext): string[] {
        const frameworks: string[] = [];
        const deps = context.dependencies;
        const depSet = new Set(deps);
        
        // React ecosystem
        if (depSet.has('react') || deps.some(d => d.includes('react'))) {
            frameworks.push('React');
        }
        
        // Meta frameworks
        if (depSet.has('next') || deps.some(d => d.includes('next'))) {
            frameworks.push('Next.js');
        }
        if (depSet.has('gatsby')) frameworks.push('Gatsby');
        if (depSet.has('remix')) frameworks.push('Remix');
        
        // Other frameworks
        if (deps.some(d => d.includes('vue'))) frameworks.push('Vue');
        if (deps.some(d => d.includes('angular'))) frameworks.push('Angular');
        if (depSet.has('svelte')) frameworks.push('Svelte');
        
        // State management & routing
        if (depSet.has('@tanstack/react-query') || depSet.has('react-query')) {
            frameworks.push('TanStack Query');
        }
        if (depSet.has('@tanstack/react-router')) {
            frameworks.push('TanStack Router');
        }
        if (depSet.has('react-router-dom')) {
            frameworks.push('React Router');
        }
        
        // Styling frameworks
        if (deps.some(d => d.includes('tailwind'))) frameworks.push('Tailwind CSS');
        if (deps.some(d => d.includes('styled-components'))) frameworks.push('Styled Components');
        if (depSet.has('@chakra-ui/react')) frameworks.push('Chakra UI');
        if (depSet.has('@mui/material')) frameworks.push('Material-UI');
        if (depSet.has('antd')) frameworks.push('Ant Design');
        
        // Build tools
        if (depSet.has('vite')) frameworks.push('Vite');
        if (depSet.has('webpack')) frameworks.push('Webpack');
        if (depSet.has('parcel')) frameworks.push('Parcel');
        
        // Testing
        if (depSet.has('@playwright/test') || depSet.has('playwright')) {
            frameworks.push('Playwright');
        }
        if (depSet.has('cypress')) frameworks.push('Cypress');
        if (depSet.has('jest')) frameworks.push('Jest');
        if (depSet.has('vitest')) frameworks.push('Vitest');
        
        return frameworks;
    }

    private detectStylingPatterns(files: FileMetadata[]): string[] {
        const patterns: string[] = [];
        const allContent = files.flatMap(f => f.chunks.map(c => c.content)).join(' ');
        
        if (allContent.includes('className=')) patterns.push('CSS Classes');
        if (allContent.includes('styled.')) patterns.push('Styled Components');
        if (allContent.includes('css`')) patterns.push('CSS-in-JS');
        if (allContent.includes('.module.css')) patterns.push('CSS Modules');
        if (allContent.includes('tw-')) patterns.push('Tailwind CSS');
        
        return patterns;
    }

    private detectStateManagement(files: FileMetadata[]): string[] {
        const patterns: string[] = [];
        const allContent = files.flatMap(f => f.chunks.map(c => c.content)).join(' ');
        
        if (allContent.includes('useState')) patterns.push('React State');
        if (allContent.includes('useContext')) patterns.push('Context API');
        if (allContent.includes('useReducer')) patterns.push('Reducer Pattern');
        if (allContent.includes('redux') || allContent.includes('store')) patterns.push('Redux');
        if (allContent.includes('zustand')) patterns.push('Zustand');
        if (allContent.includes('jotai')) patterns.push('Jotai');
        
        return patterns;
    }

    private extractArchitecturePatterns(context: CodebaseContext): string {
        const patterns: string[] = [];
        const fileNames = context.relatedFiles.map(f => f.path.toLowerCase());
        
        if (fileNames.some(name => name.includes('component'))) patterns.push('Component Architecture');
        if (fileNames.some(name => name.includes('service'))) patterns.push('Service Layer');
        if (fileNames.some(name => name.includes('hook'))) patterns.push('Custom Hooks');
        if (fileNames.some(name => name.includes('util'))) patterns.push('Utility Functions');
        if (fileNames.some(name => name.includes('store'))) patterns.push('State Management');
        
        return patterns.join(', ') || 'Standard React';
    }

    private groupFilesByDirectory(files: FileMetadata[]): Map<string, FileMetadata[]> {
        const groups = new Map<string, FileMetadata[]>();
        
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

    private getMimeType(filePath: string): string {
        const ext = path.extname(filePath).toLowerCase();
        const mimeTypes: Record<string, string> = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        };
        return mimeTypes[ext] || 'image/png';
    }

    private calculateConfidence(response: any, context: CodebaseContext): number {
        let confidence = 0.8; // Higher base confidence for Gemini
        
        // Higher confidence with massive context
        if (context.relatedFiles.length > 10) confidence += 0.1;
        if (context.metadata.relevanceScore > 0.8) confidence += 0.1;
        
        return Math.min(confidence, 1.0);
    }

    private extractSuggestions(content: string): string[] {
        const suggestions: string[] = [];
        const lines = content.split('\n');
        
        lines.forEach(line => {
            if (line.includes('consider') || line.includes('suggest') || line.includes('recommend')) {
                suggestions.push(line.trim());
            }
        });
        
        return suggestions.slice(0, 5);
    }

    /**
     * Validate Gemini configuration
     */
    static validateConfig(config: GeminiConfig): boolean {
        return !!(config.apiKey && config.apiKey.length > 0);
    }

    /**
     * Get available Gemini models
     */
    static getAvailableModels(): string[] {
        return [
            'gemini-2.0-flash-exp',
            'gemini-1.5-pro',
            'gemini-1.5-flash'
        ];
    }
}