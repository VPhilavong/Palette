/**
 * AI Integration for Palette Chatbot
 * Handles communication with backend and AI response generation
 */

import * as vscode from 'vscode';
import { AIProviderRegistry } from './ai-providers';
import { ContextConfig, ContextStrategy } from './context-strategy';
import { CodeBlock, ConversationMessage } from './conversation-manager';
// import { SemanticContextEnhancer, SemanticContext } from './semantic-context-enhancer'; // Temporarily disabled

export interface AIResponse {
    content: string;
    codeBlocks?: CodeBlock[];
    intent?: string;
    suggestedActions?: string[];
    stream?: AsyncIterable<string>;
}

export interface ProjectContext {
    projectPath?: string;
    framework?: string;
    dependencies?: string[];
    components?: string[];
    styling?: string[];
    // semanticContext?: SemanticContext; // Temporarily disabled
}

export class AIIntegrationService {
    private static readonly BACKEND_URL = 'http://localhost:8765';
    private static readonly TIMEOUT = 30000; // 30 seconds

    /**
     * Generate AI response with streaming support
     */
    static async generateStreamingResponse(
        userMessage: string,
        conversationHistory: ConversationMessage[],
        customSystemPrompt?: string
    ): Promise<AIResponse> {
        console.log('🔍 generateStreamingResponse() starting...');
        const config = vscode.workspace.getConfiguration('palette');
        const model = config.get<string>('defaultModel') || 'gpt-5-mini-2025-08-07';
        const enableStreaming = config.get<boolean>('enableStreaming') ?? true;
        console.log('🔍 Model:', model, 'Streaming:', enableStreaming);

        if (enableStreaming && AIProviderRegistry.supportsStreaming(model)) {
            console.log('🔍 Using streaming generation...');
            return await this.generateWithStreaming(userMessage, conversationHistory, model, customSystemPrompt);
        } else {
            console.log('🔍 Using non-streaming generation...');
            return await this.generateWithoutStreaming(userMessage, conversationHistory, model, customSystemPrompt);
        }
    }

    /**
     * Generate AI response - prioritizes direct OpenAI calls over backend (legacy)
     */
    static async generateResponse(
        userMessage: string,
        conversationHistory: ConversationMessage[]
    ): Promise<AIResponse> {
        console.log('🔍 AIIntegrationService.generateResponse() called with:', userMessage);
        return await this.generateStreamingResponse(userMessage, conversationHistory);
    }

    /**
     * Generate response with streaming using AI SDK
     */
    private static async generateWithStreaming(
        userMessage: string,
        conversationHistory: ConversationMessage[],
        model: string,
        customSystemPrompt?: string
    ): Promise<AIResponse> {
        try {
            console.log('🔍 generateWithStreaming() starting with model:', model);
            
            // Validate provider setup
            console.log('🔍 Validating provider...');
            const validation = AIProviderRegistry.validateProvider(model);
            console.log('🔍 Provider validation result:', validation);
            
            if (!validation.valid) {
                console.log('🔍 Provider validation failed, returning error');
                return {
                    content: `⚠️ ${validation.error}\n\nPlease configure your API key in VS Code settings.`,
                    codeBlocks: [],
                    intent: 'setup',
                    suggestedActions: ['Configure API key', 'Check settings']
                };
            }

            // Get provider and strategy
            console.log('🔍 Getting provider and strategy...');
            const provider = await AIProviderRegistry.getProvider(model);
            const strategy = ContextStrategy.getStrategy(model);
            console.log('🔍 Provider obtained, logging strategy...');
            ContextStrategy.logStrategy(model, strategy);

            // Set API key in environment if needed
            const providerConfig = AIProviderRegistry.getProviderConfig(model);
            const apiKey = AIProviderRegistry.getApiKey(providerConfig.provider);
            if (providerConfig.provider === 'openai' && apiKey) {
                process.env.OPENAI_API_KEY = apiKey;
            }

            // Build context and messages (use custom prompt if provided)
            console.log('🔍 Building contextual messages...');
            let systemPrompt: string;
            let messages: Array<{role: 'user' | 'assistant', content: string}>;
            
            if (customSystemPrompt) {
                console.log('🔍 Using custom system prompt, length:', customSystemPrompt.length);
                systemPrompt = customSystemPrompt;
                // Build messages directly without additional context
                messages = conversationHistory.map(msg => ({
                    role: msg.role as 'user' | 'assistant',
                    content: msg.content
                }));
                messages.push({
                    role: 'user',
                    content: userMessage
                });
            } else {
                const contextResult = await this.buildContextualMessages(
                    userMessage, 
                    conversationHistory, 
                    strategy, 
                    model
                );
                systemPrompt = contextResult.systemPrompt;
                messages = contextResult.messages;
            }
            
            console.log('🔍 Context built, system prompt length:', systemPrompt.length, 'messages:', messages.length);

            // Use AI SDK streaming
            console.log('🔍 Importing AI SDK streamText...');
            const { streamText } = await import('ai');
            const generationParams = AIProviderRegistry.getGenerationParams(model);
            console.log('🔍 Generation params:', generationParams);

            console.log('🎨 Starting streaming response with AI SDK:', model);

            const result = await streamText({
                model: provider,
                system: systemPrompt,
                messages: messages,
                ...generationParams,
            });
            
            console.log('🔍 StreamText call completed, starting to consume stream...');

            // Collect streaming response
            let fullResponse = '';
            for await (const chunk of result.textStream) {
                fullResponse += chunk;
                console.log('🔍 Received chunk, total length:', fullResponse.length);
            }
            
            console.log('🔍 Stream consumption completed, full response length:', fullResponse.length);

            const codeBlocks = this.extractCodeBlocks(fullResponse);
            
            return {
                content: fullResponse,
                codeBlocks: codeBlocks,
                intent: this.detectIntent(userMessage),
                suggestedActions: this.generateSuggestedActions(userMessage)
            };

        } catch (error: any) {
            console.error('🎨 AI SDK streaming failed:', error);
            return await this.generateWithoutStreaming(userMessage, conversationHistory, model, customSystemPrompt);
        }
    }

    /**
     * Generate response without streaming using AI SDK
     */
    private static async generateWithoutStreaming(
        userMessage: string,
        conversationHistory: ConversationMessage[],
        model: string,
        customSystemPrompt?: string
    ): Promise<AIResponse> {
        try {
            // Validate provider setup
            const validation = AIProviderRegistry.validateProvider(model);
            if (!validation.valid) {
                return {
                    content: `⚠️ ${validation.error}\n\nPlease configure your API key in VS Code settings.`,
                    codeBlocks: [],
                    intent: 'setup',
                    suggestedActions: ['Configure API key', 'Check settings']
                };
            }

            // Get provider and strategy
            const provider = await AIProviderRegistry.getProvider(model);
            const strategy = ContextStrategy.getStrategy(model);

            // Set API key in environment if needed
            const providerConfig = AIProviderRegistry.getProviderConfig(model);
            const apiKey = AIProviderRegistry.getApiKey(providerConfig.provider);
            if (providerConfig.provider === 'openai' && apiKey) {
                process.env.OPENAI_API_KEY = apiKey;
            }

            // Build context and messages (use custom prompt if provided)
            let systemPrompt: string;
            let messages: Array<{role: 'user' | 'assistant', content: string}>;
            
            if (customSystemPrompt) {
                systemPrompt = customSystemPrompt;
                messages = conversationHistory.map(msg => ({
                    role: msg.role as 'user' | 'assistant',
                    content: msg.content
                }));
                messages.push({
                    role: 'user',
                    content: userMessage
                });
            } else {
                const contextResult = await this.buildContextualMessages(
                    userMessage, 
                    conversationHistory, 
                    strategy, 
                    model
                );
                systemPrompt = contextResult.systemPrompt;
                messages = contextResult.messages;
            }

            // Use AI SDK generateText
            const { generateText } = await import('ai');
            const generationParams = AIProviderRegistry.getGenerationParams(model);

            console.log('🎨 Generating response with AI SDK:', model);

            const result = await generateText({
                model: provider,
                system: systemPrompt,
                messages: messages,
                ...generationParams,
            });

            const codeBlocks = this.extractCodeBlocks(result.text);
            
            return {
                content: result.text,
                codeBlocks: codeBlocks,
                intent: this.detectIntent(userMessage),
                suggestedActions: this.generateSuggestedActions(userMessage)
            };

        } catch (error: any) {
            console.error('🎨 AI SDK generation failed:', error);
            
            return {
                content: `❌ AI generation failed: ${error.message}\n\n**Troubleshooting:**\n- Check your API key configuration\n- Try a different model\n- Verify your internet connection`,
                codeBlocks: [],
                intent: 'error',
                suggestedActions: ['Check API key', 'Try different model', 'Check connection']
            };
        }
    }

    /**
     * Build contextual messages using ContextStrategy and AI SDK format with semantic enhancement
     */
    private static async buildContextualMessages(
        userMessage: string,
        conversationHistory: ConversationMessage[],
        strategy: ContextConfig,
        model: string
    ): Promise<{ systemPrompt: string; messages: Array<{role: 'user' | 'assistant', content: string}> }> {
        // TODO: Re-enable semantic context enhancer once stable
        // Initialize semantic context enhancer if not already done
        // const semanticEnhancer = SemanticContextEnhancer.getInstance();
        // if (!semanticEnhancer.isReady()) {
        //     console.log('🎨 Initializing semantic context enhancer...');
        //     await semanticEnhancer.initialize();
        // }

        // Get semantic context for the user message
        // let semanticContext: SemanticContext | null = null;
        // if (semanticEnhancer.isReady()) {
        //     semanticContext = await semanticEnhancer.enhanceContext(userMessage, strategy.componentsLimit);
        // }

        // Analyze project with strategy constraints
        const projectContext = await this.analyzeLocalProjectWithStrategy(strategy);
        // if (semanticContext) {
        //     projectContext.semanticContext = semanticContext;
        // }
        
        // Build system prompt
        const systemPrompt = model.startsWith('gpt-5') 
            ? this.getCondensedSystemPrompt(projectContext)
            : this.buildEnhancedSystemPrompt(projectContext);
        
        // Ensure system prompt fits within token budget
        const truncatedSystemPrompt = ContextStrategy.truncateToTokenLimit(
            systemPrompt, 
            strategy.maxSystemPrompt
        );
        
        // Build AI SDK compatible messages
        const messages: Array<{role: 'user' | 'assistant', content: string}> = [];
        
        // Add conversation history with strategy limits
        const recentHistory = conversationHistory.slice(-strategy.historyMessageLimit);
        let historyTokens = 0;
        
        for (const msg of recentHistory) {
            const msgTokens = ContextStrategy.estimateTokens(msg.content);
            if (historyTokens + msgTokens <= strategy.maxConversationHistory) {
                messages.push({
                    role: msg.role as 'user' | 'assistant',
                    content: msg.content
                });
                historyTokens += msgTokens;
            } else {
                // Truncate this message to fit
                const remainingTokens = strategy.maxConversationHistory - historyTokens;
                const truncatedContent = ContextStrategy.truncateToTokenLimit(msg.content, remainingTokens);
                if (truncatedContent.length > 10) {
                    messages.push({
                        role: msg.role as 'user' | 'assistant',
                        content: truncatedContent
                    });
                }
                break;
            }
        }
        
        // Add current user message
        messages.push({
            role: 'user',
            content: userMessage
        });
        
        return { systemPrompt: truncatedSystemPrompt, messages };
    }

    /**
     * Get project context from Python backend
     */
    private static async getProjectContext(): Promise<ProjectContext> {
        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                return {};
            }

            const response = await fetch(`${this.BACKEND_URL}/api/context`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    projectPath: workspaceFolder.uri.fsPath
                }),
                signal: AbortSignal.timeout(this.TIMEOUT)
            });

            if (!response.ok) {
                throw new Error(`Backend context API error: ${response.status}`);
            }

            const context = await response.json();
            console.log('🎨 Retrieved project context:', context);
            
            return {
                projectPath: context.project_path,
                framework: context.framework,
                dependencies: context.dependencies,
                components: context.components,
                styling: context.styling
            };

        } catch (error: any) {
            console.warn('🎨 Could not get project context from backend:', error.message || error);
            return {};
        }
    }

    /**
     * Call backend generation endpoint
     */
    private static async callBackendGenerate(
        userMessage: string,
        messages: any[],
        projectContext: ProjectContext,
        apiKey: string,
        model: string
    ): Promise<AIResponse> {
        const response = await fetch(`${this.BACKEND_URL}/api/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: userMessage,
                conversation_history: messages,
                project_context: projectContext,
                api_key: apiKey,
                model: model
            }),
            signal: AbortSignal.timeout(this.TIMEOUT)
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Backend generation error: ${response.status} - ${errorText}`);
        }

        const result = await response.json();
        
        return {
            content: result.content,
            codeBlocks: result.code_blocks || [],
            intent: result.intent,
            suggestedActions: result.suggested_actions
        };
    }

    /**
     * Generate response directly using OpenAI API (no backend required)
     */
    private static async generateDirectResponse(
        userMessage: string,
        conversationHistory: ConversationMessage[]
    ): Promise<AIResponse> {
        try {
            // Get API configuration
            const config = vscode.workspace.getConfiguration('palette');
            const apiKey = config.get<string>('openaiApiKey');
            const model = config.get<string>('defaultModel') || 'gpt-5-mini-2025-08-07';

            if (!apiKey) {
                throw new Error('OpenAI API key not configured. Please set it in VS Code settings (Palette > OpenAI API Key).');
            }

            // Get context strategy based on model
            const strategy = ContextStrategy.getStrategy(model);
            ContextStrategy.logStrategy(model, strategy);

            // Analyze local project with token constraints
            const projectContext = await this.analyzeLocalProjectWithStrategy(strategy);
            
            // Build system prompt based on strategy
            const systemPrompt = model.startsWith('gpt-5') 
                ? this.getCondensedSystemPrompt(projectContext)
                : this.buildEnhancedSystemPrompt(projectContext);
            
            // Ensure system prompt fits within token budget
            const truncatedSystemPrompt = ContextStrategy.truncateToTokenLimit(
                systemPrompt, 
                strategy.maxSystemPrompt
            );
            
            // Prepare messages for OpenAI
            const messages: Array<{role: 'system' | 'user' | 'assistant', content: string}> = [
                { role: 'system', content: truncatedSystemPrompt }
            ];
            
            // Add conversation history with strategy limits
            const recentHistory = conversationHistory.slice(-strategy.historyMessageLimit);
            let historyTokens = 0;
            
            for (const msg of recentHistory) {
                const msgTokens = ContextStrategy.estimateTokens(msg.content);
                if (historyTokens + msgTokens <= strategy.maxConversationHistory) {
                    messages.push({
                        role: msg.role as 'user' | 'assistant',
                        content: msg.content
                    });
                    historyTokens += msgTokens;
                } else {
                    // Truncate this message to fit
                    const remainingTokens = strategy.maxConversationHistory - historyTokens;
                    const truncatedContent = ContextStrategy.truncateToTokenLimit(msg.content, remainingTokens);
                    if (truncatedContent.length > 10) { // Only add if meaningful
                        messages.push({
                            role: msg.role as 'user' | 'assistant',
                            content: truncatedContent
                        });
                    }
                    break; // Stop adding more history
                }
            }
            
            // Add current user message
            messages.push({
                role: 'user',
                content: userMessage
            });

            // Import AI SDK for standardized chat interface
            const { generateText } = await import('ai');
            const { openai } = await import('@ai-sdk/openai');

            console.log('🎨 Using AI SDK with model:', model);
            
            // Map conversation history to AI SDK format
            const aiSdkMessages = messages.slice(1).map(msg => ({
                role: msg.role,
                content: msg.content
            }));

            // Generate response using AI SDK
            const result = await generateText({
                model: openai(model),
                system: truncatedSystemPrompt,
                messages: aiSdkMessages,
                temperature: model.startsWith('gpt-5') ? undefined : 0.7, // GPT-5 uses default temperature
            });

            const responseContent = result.text;
            
            // Extract code blocks
            const codeBlocks = this.extractCodeBlocks(responseContent);
            
            console.log('🎨 Generated response with', codeBlocks.length, 'code blocks');

            return {
                content: responseContent,
                codeBlocks: codeBlocks,
                intent: this.detectIntent(userMessage),
                suggestedActions: this.generateSuggestedActions(userMessage)
            };

        } catch (error: any) {
            console.error('🎨 Direct OpenAI generation failed:', error);
            
            // Provide helpful error message
            let errorMessage = 'Failed to generate response. ';
            
            if (error.message?.includes('API key')) {
                errorMessage += 'Please configure your OpenAI API key in VS Code settings.';
            } else if (error.message?.includes('rate limit')) {
                errorMessage += 'Rate limit reached. Please try again in a moment or switch to a different model.';
            } else if (error.message?.includes('model')) {
                errorMessage += `Model error: ${error.message}. Try using gpt-5-mini-2025-08-07 or gpt-5-nano-2025-08-07.`;
            } else {
                errorMessage += error.message || 'Unknown error occurred.';
            }

            return {
                content: errorMessage,
                codeBlocks: [],
                intent: 'error',
                suggestedActions: [
                    'Check your API key configuration',
                    'Try a different model',
                    'Verify your OpenAI account status'
                ]
            };
        }
    }

    /**
     * Get system prompt for AI
     */
    private static getSystemPrompt(): string {
        return `You are Palette AI, a helpful assistant for React developers. You specialize in:

1. **Component Generation**: Create React components using TypeScript, Tailwind CSS, and shadcn/ui
2. **Page Creation**: Build complete page layouts and experiences
3. **Code Improvement**: Refactor and enhance existing code
4. **UI/UX Guidance**: Provide design system advice and best practices

Guidelines:
- Always use TypeScript for React components
- Prefer functional components with hooks
- Use Tailwind CSS for styling
- Integrate shadcn/ui components when appropriate
- Write accessible, production-ready code
- Provide clear explanations with your code

When generating code:
- Use proper TypeScript interfaces
- Include proper imports
- Add meaningful component names
- Use semantic HTML elements
- Implement responsive design patterns
- Follow React best practices

Be conversational, helpful, and focus on creating high-quality UI components and experiences.`;
    }

    /**
     * Get condensed system prompt for GPT-5 models (ultra-minimal for 10K token limit)
     */
    private static getCondensedSystemPrompt(context: ProjectContext): string {
        // Ultra-minimal: ~50 tokens total
        let prompt = `Create TypeScript React components with Tailwind CSS.`;

        // Only add essential context if available
        if (context.components?.length) {
            const topComponents = context.components.slice(0, 3);
            prompt += ` Use: ${topComponents.join(', ')}.`;
        }

        return prompt;
    }


    /**
     * Build enhanced system prompt with semantic context
     */
    private static buildEnhancedSystemPrompt(context: ProjectContext): string {
        let prompt = this.getSystemPrompt();
        
        // Add project-specific context
        if (context.framework) {
            prompt += `\n\nProject Framework: ${context.framework}`;
        }
        
        if (context.styling?.length) {
            prompt += `\nStyling: ${context.styling.join(', ')}`;
        }
        
        // Use semantic context for better component recommendations (temporarily disabled)
        // if (context.semanticContext?.relevantComponents?.length) {
        //     const relevantComponents = context.semanticContext.relevantComponents.slice(0, 10);
        //     prompt += `\nRelevant components found for your request:`;
        //     
        //     for (const component of relevantComponents) {
        //         prompt += `\n- ${component.name} (${component.category}): ${component.description}`;
        //     }
        //     
        //     // Add design patterns if available
        //     if (context.semanticContext.designPatterns?.length) {
        //         prompt += `\nDesign patterns: ${context.semanticContext.designPatterns.join(', ')}`;
        //     }
        // } else 
        if (context.components?.length) {
            // Fallback to basic component listing
            const relevantComponents = context.components.slice(0, 10);
            prompt += `\nAvailable shadcn/ui components: ${relevantComponents.join(', ')}`;
            if (context.components.length > 10) {
                prompt += ` (and ${context.components.length - 10} more)`;
            }
        }

        prompt += `\n\nIMPORTANT: 
- Use the relevant components listed above when appropriate
- Follow the project's established patterns
- Use TypeScript for all components
- Include proper imports from "@/components/ui/*"
- Use Tailwind CSS classes for styling
- Create components that work well together`;

        return prompt;
    }

    /**
     * Extract code blocks from AI response
     */
    private static extractCodeBlocks(content: string): CodeBlock[] {
        const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
        const codeBlocks: CodeBlock[] = [];
        let match;

        while ((match = codeBlockRegex.exec(content)) !== null) {
            const language = match[1] || 'text';
            const code = match[2].trim();
            
            codeBlocks.push({
                language,
                code,
                filename: this.inferFilename(code, language)
            });
        }

        return codeBlocks;
    }

    /**
     * Infer filename from code content
     */
    private static inferFilename(code: string, language: string): string | undefined {
        // Try to extract component name for React files
        if (language === 'tsx' || language === 'jsx') {
            // Look for export default ComponentName or const ComponentName
            const componentMatch = code.match(/(?:export\s+default\s+function\s+(\w+)|const\s+(\w+):\s*React\.FC|export\s+default\s+(\w+))/);
            if (componentMatch) {
                const componentName = componentMatch[1] || componentMatch[2] || componentMatch[3];
                return `${componentName}.${language}`;
            }
        }

        // Default filenames based on language
        const extensions: Record<string, string> = {
            'tsx': 'Component.tsx',
            'jsx': 'Component.jsx',
            'ts': 'index.ts',
            'js': 'index.js',
            'css': 'styles.css',
            'html': 'index.html',
            'json': 'config.json'
        };

        return extensions[language];
    }

    /**
     * Detect intent from user message
     */
    private static detectIntent(message: string): string {
        const lowerMessage = message.toLowerCase();
        
        if (lowerMessage.includes('generate') || lowerMessage.includes('create') || lowerMessage.includes('make')) {
            if (lowerMessage.includes('page')) return 'generate_page';
            if (lowerMessage.includes('component')) return 'generate_component';
            return 'generate_new';
        }
        
        if (lowerMessage.includes('fix') || lowerMessage.includes('improve') || lowerMessage.includes('refactor')) {
            return 'improve_code';
        }
        
        if (lowerMessage.includes('explain') || lowerMessage.includes('how') || lowerMessage.includes('what')) {
            return 'explain';
        }
        
        return 'general';
    }

    /**
     * Analyze local project with strategy constraints
     */
    private static async analyzeLocalProjectWithStrategy(strategy: ContextConfig): Promise<ProjectContext> {
        const context = await this.analyzeLocalProject();
        
        // Apply strategy constraints
        if (context.components) {
            context.components = context.components.slice(0, strategy.componentsLimit);
        }
        
        return context;
    }

    /**
     * Analyze local project by reading files directly from workspace
     */
    private static async analyzeLocalProject(): Promise<ProjectContext> {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            return {};
        }

        const context: ProjectContext = {
            projectPath: workspaceFolder.uri.fsPath
        };

        try {
            // Read package.json
            const packageJsonUri = vscode.Uri.joinPath(workspaceFolder.uri, 'package.json');
            try {
                const packageJsonContent = await vscode.workspace.fs.readFile(packageJsonUri);
                const packageJson = JSON.parse(Buffer.from(packageJsonContent).toString('utf8'));
                
                // Extract dependencies
                context.dependencies = Object.keys({
                    ...packageJson.dependencies,
                    ...packageJson.devDependencies
                });

                // Detect framework
                if (context.dependencies?.includes('react')) {
                    context.framework = 'react';
                    if (context.dependencies.includes('next')) {
                        context.framework = 'nextjs';
                    } else if (context.dependencies.includes('vite')) {
                        context.framework = 'vite-react';
                    }
                }

                // Detect styling
                context.styling = [];
                if (context.dependencies?.includes('tailwindcss')) {
                    context.styling.push('tailwind');
                }
                if (context.dependencies?.some(dep => dep.includes('shadcn'))) {
                    context.styling.push('shadcn-ui');
                }
            } catch (e) {
                console.log('🎨 No package.json found');
            }

            // Scan for components
            const componentsUri = vscode.Uri.joinPath(workspaceFolder.uri, 'src', 'components', 'ui');
            try {
                const entries = await vscode.workspace.fs.readDirectory(componentsUri);
                context.components = entries
                    .filter(([name, type]) => type === vscode.FileType.File && (name.endsWith('.tsx') || name.endsWith('.jsx')))
                    .map(([name]) => name.replace(/\.(tsx|jsx)$/, ''));
                
                console.log('🎨 Found components:', context.components);
            } catch (e) {
                console.log('🎨 No components/ui directory found');
                context.components = [];
            }

        } catch (error) {
            console.error('🎨 Error analyzing local project:', error);
        }

        return context;
    }


    /**
     * Generate suggested actions based on user message
     */
    private static generateSuggestedActions(message: string): string[] {
        const lowerMessage = message.toLowerCase();
        
        if (lowerMessage.includes('page')) {
            return [
                'Add routing for the page',
                'Create additional page sections',
                'Add navigation menu'
            ];
        }
        
        if (lowerMessage.includes('component')) {
            return [
                'Create variations of this component',
                'Add props interface',
                'Write tests for the component'
            ];
        }
        
        if (lowerMessage.includes('form')) {
            return [
                'Add form validation',
                'Connect to backend API',
                'Add error handling'
            ];
        }
        
        return [
            'Create another component',
            'Improve the design',
            'Add more functionality'
        ];
    }

    /**
     * Test backend connection
     */
    static async testConnection(): Promise<boolean> {
        try {
            const response = await fetch(`${this.BACKEND_URL}/health`, {
                method: 'GET',
                signal: AbortSignal.timeout(5000)
            });
            return response.ok;
        } catch (error: any) {
            console.warn('🎨 Backend connection test failed:', error);
            return false;
        }
    }

    /**
     * Get backend status
     */
    static async getBackendStatus(): Promise<{
        connected: boolean;
        version?: string;
        error?: string;
    }> {
        try {
            const response = await fetch(`${this.BACKEND_URL}/health`, {
                method: 'GET',
                signal: AbortSignal.timeout(5000)
            });

            if (response.ok) {
                const data = await response.json();
                return {
                    connected: true,
                    version: data.version
                };
            } else {
                return {
                    connected: false,
                    error: `HTTP ${response.status}`
                };
            }
        } catch (error: any) {
            return {
                connected: false,
                error: error.message || 'Unknown error'
            };
        }
    }
}

/**
 * Main function to generate AI response (backwards compatibility)
 */
export async function generateAIResponse(
    userMessage: string,
    conversationHistory: ConversationMessage[]
): Promise<AIResponse> {
    return await AIIntegrationService.generateResponse(userMessage, conversationHistory);
}