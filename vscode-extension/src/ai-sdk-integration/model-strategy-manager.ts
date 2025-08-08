/**
 * Model Strategy Manager
 * Manages different generation strategies for Core (GPT-5) and Enhanced (GPT-4.1) tiers
 * Implements strategy pattern for AI SDK 5 integration
 */

import { generateText, streamText, tool, stepCountIs } from 'ai';
import { createOpenAI } from '@ai-sdk/openai';
import { ToolRegistry } from '../tools/tool-registry';
import { ToolExecutor } from '../tools/tool-executor';
import * as vscode from 'vscode';
import { 
    GenerationRequest, 
    GenerationResult, 
    ModelCapabilities,
    CodeBlock,
    FileSpec,
    GenerationStrategy as GenerationStrategyType
} from './capability-router';

/**
 * Abstract base strategy class
 */
export abstract class GenerationStrategy {
    abstract execute(request: GenerationRequest): Promise<GenerationResult>;
    
    protected getOpenAIApiKey(): string | undefined {
        const config = vscode.workspace.getConfiguration('palette');
        return config.get<string>('openaiApiKey') || process.env.OPENAI_API_KEY;
    }

    protected validateApiKey(): boolean {
        const apiKey = this.getOpenAIApiKey();
        return !!(apiKey && apiKey.startsWith('sk-'));
    }

    protected createOpenAIClient() {
        const apiKey = this.getOpenAIApiKey();
        if (!apiKey) {
            throw new Error('OpenAI API key not configured');
        }
        return createOpenAI({
            apiKey: apiKey
        });
    }
}

/**
 * Core Strategy for GPT-5 models (Limited capabilities)
 * Uses rich context building + text generation only
 */
export class CoreGenerationStrategy extends GenerationStrategy {
    async execute(request: GenerationRequest): Promise<GenerationResult> {
        if (!this.validateApiKey()) {
            return {
                success: false,
                content: '',
                error: 'OpenAI API key not configured'
            };
        }

        try {
            console.log(`🎨 CoreStrategy: Generating with ${request.model}`);

            // Build rich context for GPT-5 models
            const enhancedPrompt = await this.buildEnhancedPrompt(request);
            
            const openaiClient = this.createOpenAIClient();
            const response = await generateText({
                model: openaiClient(request.model),
                prompt: enhancedPrompt,
                maxRetries: 3,
                temperature: request.options?.temperature || 0.7
            });

            // Parse response manually since no structured generation
            const parseResult = this.parseTextResponse(response.text);

            return {
                success: true,
                content: response.text,
                metadata: {
                    model: request.model,
                    tier: 'core',
                    tokensUsed: response.usage?.totalTokens,
                    codeBlocks: parseResult.codeBlocks,
                    files: parseResult.files,
                    strategy: parseResult.strategy
                }
            };

        } catch (error: any) {
            console.error(`🎨 CoreStrategy error:`, error);
            return {
                success: false,
                content: '',
                error: `Core generation failed: ${error.message}`
            };
        }
    }

    /**
     * Build enhanced prompt with rich context for GPT-5 models
     */
    private async buildEnhancedPrompt(request: GenerationRequest): Promise<string> {
        const context = request.context;
        
        let prompt = `You are Palette AI, an expert React/TypeScript developer specializing in modern web applications using Vite + React + TypeScript + shadcn/ui + Tailwind CSS.

🎨 DESIGN PROTOTYPING FOCUS:
- Generate COMPLETE, VISIBLE pages and features users can interact with
- Think like Vercel v0: Create full experiences, not isolated components
- Focus on landing pages, dashboards, forms, e-commerce pages, blogs
- Avoid generating isolated buttons, cards, or UI elements

PROJECT CONTEXT:`;

        // Add project context if available
        if (context?.framework) {
            prompt += `\nFramework: ${context.framework}`;
        }

        if (context?.components && context.components.length > 0) {
            prompt += `\nExisting Components: ${context.components.slice(0, 10).join(', ')}`;
        }

        if (context?.designTokens) {
            prompt += `\nDesign System: ${JSON.stringify(context.designTokens).substring(0, 200)}...`;
        }

        prompt += `\n\nUSER REQUEST: ${request.message}

GENERATION REQUIREMENTS:
1. Generate production-ready code that users can SEE and INTERACT with
2. Use modern React patterns with TypeScript
3. Follow shadcn/ui component patterns when possible
4. Use Tailwind CSS for styling with responsive design
5. Include proper error handling and loading states
6. Create complete file structures with proper imports

RESPONSE FORMAT:
Provide a brief explanation followed by code blocks with clear filenames:

\`\`\`typescript
// filename: src/components/ComponentName.tsx
[Component code here]
\`\`\`

\`\`\`typescript  
// filename: src/pages/PageName.tsx
[Page code here]
\`\`\`

Focus on creating a complete, working feature that demonstrates the requested functionality.`;

        return prompt;
    }

    /**
     * Parse text response to extract code blocks and files
     */
    private parseTextResponse(text: string): {
        codeBlocks: CodeBlock[];
        files: FileSpec[];
        strategy: GenerationStrategyType;
    } {
        const codeBlocks: CodeBlock[] = [];
        const files: FileSpec[] = [];
        
        // Extract code blocks using regex
        const codeBlockRegex = /```(\w+)?\s*(?:\/\/\s*filename:\s*(.+))?\n([\s\S]*?)```/g;
        let match;

        while ((match = codeBlockRegex.exec(text)) !== null) {
            const [, language = 'text', filename, content] = match;
            
            const codeBlock: CodeBlock = {
                language,
                code: content.trim(),
                filename: filename?.trim()
            };
            
            codeBlocks.push(codeBlock);

            // Create file spec if filename is provided
            if (filename) {
                files.push({
                    path: filename.trim(),
                    content: content.trim(),
                    type: this.inferFileType(filename)
                });
            }
        }

        // Infer generation strategy based on content analysis
        const strategy = this.inferGenerationStrategy(text);

        return { codeBlocks, files, strategy };
    }

    private inferFileType(filename: string): FileSpec['type'] {
        if (filename.includes('component') || filename.includes('Component')) return 'component';
        if (filename.includes('hook') || filename.includes('use')) return 'hook';
        if (filename.includes('util') || filename.includes('lib')) return 'util';
        if (filename.includes('test') || filename.includes('spec')) return 'test';
        if (filename.includes('.css') || filename.includes('.scss')) return 'style';
        return 'component'; // Default
    }

    private inferGenerationStrategy(text: string): GenerationStrategyType {
        const lowerText = text.toLowerCase();
        
        if (lowerText.includes('reuse') || lowerText.includes('existing')) return 'REUSE';
        if (lowerText.includes('compose') || lowerText.includes('combine')) return 'COMPOSE';
        if (lowerText.includes('extend') || lowerText.includes('modify')) return 'EXTEND';
        return 'GENERATE'; // Default for new components
    }
}

/**
 * Enhanced Strategy for GPT-4.1 models (Full AI SDK 5 capabilities)
 * Uses tools, structured generation, and streaming
 */
export class EnhancedGenerationStrategy extends GenerationStrategy {
    async execute(request: GenerationRequest): Promise<GenerationResult> {
        if (!this.validateApiKey()) {
            return {
                success: false,
                content: '',
                error: 'OpenAI API key not configured'
            };
        }

        try {
            console.log(`🎨 EnhancedStrategy: Generating with ${request.model}`);

            if (request.options?.stream) {
                return await this.executeStreaming(request);
            } else {
                return await this.executeStructured(request);
            }

        } catch (error: any) {
            console.error(`🎨 EnhancedStrategy error:`, error);
            return {
                success: false,
                content: '',
                error: `Enhanced generation failed: ${error.message}`
            };
        }
    }

    /**
     * Execute with tool calling and structured data generation
     */
    private async executeStructured(request: GenerationRequest): Promise<GenerationResult> {
        const openaiClient = this.createOpenAIClient();
        const toolRegistry = ToolRegistry.getInstance();
        const toolExecutor = ToolExecutor.getInstance();
        
        // Get available tools for AI SDK
        const availableTools = toolRegistry.getToolsForAISDK();
        
        const response = await generateText({
            model: openaiClient(request.model),
            system: this.buildSystemPromptWithTools(),
            prompt: request.message,
            tools: availableTools,
            toolChoice: 'auto', // Let the model decide when to use tools
            maxRetries: 3,
            temperature: request.options?.temperature || 0.7,
            stopWhen: stepCountIs(5) // Allow multiple tool calls and responses
        });

        // Process tool calls if any were made
        const toolResults: any[] = [];
        const allToolCalls = response.steps?.flatMap(step => step.toolCalls || []) || [];
        
        if (allToolCalls.length > 0) {
            console.log(`🎨 EnhancedStrategy: Processing ${allToolCalls.length} tool calls`);
            
            for (const toolCall of allToolCalls) {
                try {
                    const result = await toolExecutor.executeTool(
                        toolCall.toolName,
                        toolCall.input,
                        this.buildToolContext(request)
                    );
                    
                    toolResults.push({
                        toolName: toolCall.toolName,
                        args: toolCall.input,
                        result
                    });
                    
                } catch (error) {
                    console.error(`🎨 Tool execution failed: ${toolCall.toolName}`, error);
                    toolResults.push({
                        toolName: toolCall.toolName,
                        args: toolCall.input,
                        result: {
                            success: false,
                            error: `Tool execution failed: ${error}`
                        }
                    });
                }
            }
        }

        // Parse the text response for code blocks
        const coreStrategy = new CoreGenerationStrategy();
        const parseResult = (coreStrategy as any).parseTextResponse(response.text);

        // Collect files from both parsing and tool results
        const allFiles = [
            ...(parseResult.files || []),
            ...toolResults
                .filter(tr => tr.result.success && tr.result.filesChanged)
                .flatMap(tr => tr.result.filesChanged.map((path: string) => ({ path, type: 'generated' })))
        ];

        return {
            success: true,
            content: response.text,
            metadata: {
                model: request.model,
                tier: 'enhanced',
                tokensUsed: response.usage?.totalTokens,
                codeBlocks: parseResult.codeBlocks,
                files: allFiles,
                strategy: parseResult.strategy,
                toolResults: toolResults,
                stepsUsed: response.steps?.length || 1
            }
        };
    }

    /**
     * Execute with streaming for real-time responses
     */
    private async executeStreaming(request: GenerationRequest): Promise<GenerationResult> {
        const openaiClient = this.createOpenAIClient();
        const { textStream } = await streamText({
            model: openaiClient(request.model),
            system: this.buildSystemPrompt(),
            prompt: request.message,
            temperature: request.options?.temperature || 0.7
        });

        let fullContent = '';
        
        // Note: In actual implementation, you'd stream this to the UI
        // For now, we'll collect all chunks
        for await (const chunk of textStream) {
            fullContent += chunk;
        }

        // Parse the streamed content
        const coreStrategy = new CoreGenerationStrategy();
        const parseResult = (coreStrategy as any).parseTextResponse(fullContent);

        return {
            success: true,
            content: fullContent,
            metadata: {
                model: request.model,
                tier: 'enhanced',
                codeBlocks: parseResult.codeBlocks,
                files: parseResult.files,
                strategy: parseResult.strategy
            }
        };
    }

    private buildSystemPrompt(): string {
        return `You are Palette AI, an expert React/TypeScript developer specializing in modern web applications.

🎨 DESIGN PROTOTYPING FOCUS:
- Generate COMPLETE, VISIBLE pages and features users can interact with
- Think like Vercel v0: Create full experiences, not isolated components
- Focus on landing pages, dashboards, forms, e-commerce pages, blogs

TECHNICAL STACK:
- React 18+ with TypeScript
- Vite for build tooling
- Tailwind CSS for styling
- shadcn/ui component library
- Modern hooks and patterns

GENERATION REQUIREMENTS:
1. Always generate complete, working features
2. Include proper TypeScript types and interfaces
3. Use shadcn/ui components when appropriate
4. Implement responsive design with Tailwind
5. Add proper error handling and loading states
6. Follow modern React best practices`;
    }

    private buildSystemPromptWithTools(): string {
        return `You are Palette AI, an expert React/TypeScript developer with access to powerful development tools.

🎨 DESIGN PROTOTYPING FOCUS:
- Generate COMPLETE, VISIBLE pages and features users can interact with
- Think like Vercel v0: Create full experiences, not isolated components
- Focus on landing pages, dashboards, forms, e-commerce pages, blogs

🛠️ TOOL USAGE GUIDELINES:
- Use tools to analyze the current project structure and existing components
- Install shadcn/ui components as needed for the design
- Create files directly in the workspace when generating code
- Check for existing similar components before creating new ones
- Use Git operations when appropriate for version control

TECHNICAL STACK:
- React 18+ with TypeScript
- Vite for build tooling
- Tailwind CSS for styling
- shadcn/ui component library
- Modern hooks and patterns

GENERATION REQUIREMENTS:
1. Analyze the project first using available tools
2. Generate complete, working features with proper file structure
3. Use tools to create files directly in the workspace
4. Include proper TypeScript types and interfaces
5. Install shadcn/ui components if not already available
6. Implement responsive design with Tailwind
7. Add proper error handling and loading states
8. Follow modern React best practices

When creating files, use the available file operation tools to ensure they are properly created in the user's workspace.`;
    }

    private buildToolContext(request: GenerationRequest): any {
        return {
            workspacePath: request.context?.workspacePath,
            extensionContext: vscode.extensions.getExtension('palette')?.exports,
            outputChannel: vscode.window.createOutputChannel('Palette Tools')
        };
    }

}

/**
 * Model Strategy Manager
 * Factory for creating appropriate strategy based on model tier
 */
export class ModelStrategyManager {
    private static strategies: Map<string, GenerationStrategy> = new Map();

    /**
     * Get strategy instance for given tier
     */
    static getStrategy(tier: 'core' | 'enhanced'): GenerationStrategy {
        const strategyKey = tier;
        
        if (!this.strategies.has(strategyKey)) {
            const strategy = tier === 'enhanced' 
                ? new EnhancedGenerationStrategy()
                : new CoreGenerationStrategy();
            
            this.strategies.set(strategyKey, strategy);
        }

        return this.strategies.get(strategyKey)!;
    }

    /**
     * Clear strategy cache (useful for testing)
     */
    static clearCache(): void {
        this.strategies.clear();
    }

    /**
     * Get all available strategy types
     */
    static getAvailableStrategies(): Array<'core' | 'enhanced'> {
        return ['core', 'enhanced'];
    }
}