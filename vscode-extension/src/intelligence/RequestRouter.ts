/**
 * RequestRouter - Intelligent routing and fallback orchestration
 * Routes requests between AI SDK and Python backend with fallback strategies
 */

import * as vscode from 'vscode';
import { ComplexityAnalyzer, RequestComplexity, DesignRequest, ClassificationResult } from './ComplexityAnalyzer';
import { PythonServerManager, ServerStatus } from '../services/PythonServerManager';
import { SimpleAISDKAgent, createSimpleAISDKAgent, AgentResponse } from '../SimpleAISDKAgent';

export interface RoutingDecision {
    primaryProvider: GenerationProvider;
    fallbackProviders: GenerationProvider[];
    reasoning: string[];
    estimatedDuration: 'fast' | 'medium' | 'slow';
    requiresAnalysis: boolean;
}

export interface GenerationResult {
    content: string;
    provider: GenerationProvider;
    duration: number;
    metadata: {
        complexity: RequestComplexity;
        fallbackUsed: boolean;
        analysisData?: any;
        quality?: {
            score: number;
            issues: string[];
        };
    };
}

export interface StreamingCallback {
    onChunk: (chunk: string, metadata?: any) => void;
    onStatusUpdate: (status: string, phase?: string) => void;
    onError: (error: string) => void;
    onComplete: (result: GenerationResult) => void;
}

export enum GenerationProvider {
    AI_SDK_OPENAI = 'ai_sdk_openai',
    AI_SDK_ANTHROPIC = 'ai_sdk_anthropic', 
    PYTHON_BACKEND = 'python_backend',
    HYBRID = 'hybrid',
    STATIC_TEMPLATES = 'static_templates'
}

export class RequestRouter {
    private static instance: RequestRouter | null = null;
    
    private complexityAnalyzer: ComplexityAnalyzer;
    private pythonServerManager: PythonServerManager;
    private aiSdkAgent: SimpleAISDKAgent | null = null;
    private outputChannel: vscode.OutputChannel;
    
    private routingStats = {
        totalRequests: 0,
        aiSdkRequests: 0,
        pythonBackendRequests: 0,
        hybridRequests: 0,
        fallbacksUsed: 0,
        averageResponseTime: 0
    };

    private constructor() {
        this.complexityAnalyzer = ComplexityAnalyzer.getInstance();
        this.pythonServerManager = PythonServerManager.getInstance();
        this.outputChannel = vscode.window.createOutputChannel('Palette Request Router');
    }

    public static getInstance(): RequestRouter {
        if (!RequestRouter.instance) {
            RequestRouter.instance = new RequestRouter();
        }
        return RequestRouter.instance;
    }

    /**
     * Main routing method - determines how to handle a request
     */
    public async routeRequest(request: DesignRequest): Promise<RoutingDecision> {
        this.outputChannel.appendLine(`🎯 Routing request: "${request.message.substring(0, 50)}..."`);
        
        // Classify request complexity
        const classification = await this.complexityAnalyzer.classifyRequest(request);
        
        this.outputChannel.appendLine(`📊 Classification: ${classification.complexity} (confidence: ${classification.confidence})`);
        this.outputChannel.appendLine(`💭 Reasoning: ${classification.reasoning.join('; ')}`);

        // Check provider availability
        const providerStatus = await this.checkProviderAvailability();

        // Make routing decision
        const decision = this.makeRoutingDecision(classification, providerStatus);
        
        this.outputChannel.appendLine(`🚀 Primary provider: ${decision.primaryProvider}`);
        this.outputChannel.appendLine(`🔄 Fallbacks: ${decision.fallbackProviders.join(', ')}`);

        return decision;
    }

    /**
     * Process request with intelligent routing and fallbacks
     */
    public async processRequest(
        request: DesignRequest, 
        callback: StreamingCallback
    ): Promise<GenerationResult> {
        const startTime = Date.now();
        this.routingStats.totalRequests++;
        
        try {
            // Get routing decision
            const decision = await this.routeRequest(request);
            
            // Try primary provider first
            let result: GenerationResult | null = null;
            let fallbackUsed = false;

            // Attempt primary provider
            try {
                callback.onStatusUpdate(`Using ${decision.primaryProvider}`, 'routing');
                result = await this.tryProvider(decision.primaryProvider, request, callback);
            } catch (primaryError) {
                this.outputChannel.appendLine(`❌ Primary provider ${decision.primaryProvider} failed: ${primaryError instanceof Error ? primaryError.message : String(primaryError)}`);
                callback.onStatusUpdate(`Primary provider failed, trying fallback...`, 'fallback');
                
                // Try fallback providers
                for (const fallbackProvider of decision.fallbackProviders) {
                    try {
                        this.outputChannel.appendLine(`🔄 Trying fallback: ${fallbackProvider}`);
                        callback.onStatusUpdate(`Trying ${fallbackProvider}`, 'fallback');
                        
                        result = await this.tryProvider(fallbackProvider, request, callback);
                        fallbackUsed = true;
                        this.routingStats.fallbacksUsed++;
                        break;
                    } catch (fallbackError) {
                        this.outputChannel.appendLine(`❌ Fallback ${fallbackProvider} failed: ${fallbackError instanceof Error ? fallbackError.message : String(fallbackError)}`);
                        continue;
                    }
                }
                
                if (!result) {
                    throw new Error('All providers failed');
                }
            }

            // Update metadata
            result.metadata.fallbackUsed = fallbackUsed;
            result.duration = Date.now() - startTime;
            
            // Update stats
            this.updateRoutingStats(result);
            
            this.outputChannel.appendLine(`✅ Request completed in ${result.duration}ms using ${result.provider}`);
            callback.onComplete(result);
            
            return result;

        } catch (error) {
            const errorMessage = `Request failed: ${error instanceof Error ? error.message : String(error)}`;
            this.outputChannel.appendLine(`💥 ${errorMessage}`);
            callback.onError(errorMessage);
            throw error;
        }
    }

    /**
     * Try a specific provider
     */
    private async tryProvider(
        provider: GenerationProvider, 
        request: DesignRequest, 
        callback: StreamingCallback
    ): Promise<GenerationResult> {
        switch (provider) {
            case GenerationProvider.PYTHON_BACKEND:
                return this.tryPythonBackend(request, callback);
                
            case GenerationProvider.AI_SDK_OPENAI:
                return this.tryAISDK(request, callback, 'openai');
                
            case GenerationProvider.AI_SDK_ANTHROPIC:
                return this.tryAISDK(request, callback, 'anthropic');
                
            case GenerationProvider.HYBRID:
                return this.tryHybridApproach(request, callback);
                
            case GenerationProvider.STATIC_TEMPLATES:
                return this.tryStaticTemplates(request, callback);
                
            default:
                throw new Error(`Unknown provider: ${provider}`);
        }
    }

    /**
     * Try Python backend
     */
    private async tryPythonBackend(
        request: DesignRequest, 
        callback: StreamingCallback
    ): Promise<GenerationResult> {
        // Ensure server is running
        callback.onStatusUpdate('Starting Python intelligence server...', 'server_startup');
        const serverStatus = await this.pythonServerManager.ensureServerRunning();
        
        if (!serverStatus.isRunning) {
            throw new Error('Python server failed to start');
        }

        callback.onStatusUpdate('Analyzing project context...', 'analysis');
        
        // Make streaming request to Python backend
        const serverUrl = this.pythonServerManager.getServerUrl();
        const response = await fetch(`${serverUrl}/api/generate/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: request.message,
                projectPath: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '',
                conversationHistory: request.conversationHistory || [],
                requestMetadata: {
                    timestamp: new Date().toISOString(),
                    source: 'vscode_extension'
                }
            })
        });

        if (!response.ok) {
            throw new Error(`Python backend request failed: ${response.statusText}`);
        }

        const { conversationId, streamUrl } = await response.json();
        
        // Connect to SSE stream
        return this.consumeSSEStream(`${serverUrl}${streamUrl}`, callback, GenerationProvider.PYTHON_BACKEND);
    }

    /**
     * Try AI SDK (OpenAI or Anthropic)
     */
    private async tryAISDK(
        request: DesignRequest, 
        callback: StreamingCallback,
        provider: 'openai' | 'anthropic'
    ): Promise<GenerationResult> {
        if (!this.aiSdkAgent) {
            this.aiSdkAgent = createSimpleAISDKAgent({
                provider: provider,
                enableStreaming: true,
                temperature: 0.7
            });
        }

        callback.onStatusUpdate(`Generating with ${provider}...`, 'generation');
        
        let fullContent = '';
        const response = await this.aiSdkAgent.processMessage(
            request.message,
            (chunk: string) => {
                fullContent += chunk;
                callback.onChunk(chunk, { provider, streaming: true });
            }
        );

        return {
            content: response.content || fullContent,
            provider: provider === 'openai' ? GenerationProvider.AI_SDK_OPENAI : GenerationProvider.AI_SDK_ANTHROPIC,
            duration: 0, // Will be set by caller
            metadata: {
                complexity: RequestComplexity.SIMPLE_UI_TASK,
                fallbackUsed: false
            }
        };
    }

    /**
     * Try hybrid approach (AI SDK + Python validation)
     */
    private async tryHybridApproach(
        request: DesignRequest, 
        callback: StreamingCallback
    ): Promise<GenerationResult> {
        callback.onStatusUpdate('Using hybrid approach...', 'hybrid_start');
        
        // First, get quick result from AI SDK
        callback.onStatusUpdate('Getting initial result from AI SDK...', 'ai_sdk_phase');
        const aiResult = await this.tryAISDK(request, callback, 'openai');
        
        // Then enhance with Python backend analysis
        try {
            callback.onStatusUpdate('Enhancing with Python intelligence...', 'python_enhancement');
            
            const serverStatus = await this.pythonServerManager.ensureServerRunning();
            if (serverStatus.isRunning) {
                const serverUrl = this.pythonServerManager.getServerUrl();
                
                // Send for quality analysis
                const analysisResponse = await fetch(`${serverUrl}/api/analyze`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        projectPath: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '',
                        analysisType: 'quality'
                    })
                });

                if (analysisResponse.ok) {
                    const analysis = await analysisResponse.json();
                    aiResult.metadata.analysisData = analysis.analysis;
                    callback.onStatusUpdate('Analysis complete', 'analysis_complete');
                }
            }
        } catch (error) {
            // Python enhancement failed, but we have AI result
            this.outputChannel.appendLine(`Hybrid enhancement failed: ${error instanceof Error ? error.message : String(error)}`);
        }

        aiResult.provider = GenerationProvider.HYBRID;
        return aiResult;
    }

    /**
     * Try static templates as last resort
     */
    private async tryStaticTemplates(
        request: DesignRequest, 
        callback: StreamingCallback
    ): Promise<GenerationResult> {
        callback.onStatusUpdate('Using static templates...', 'templates');
        
        // Very basic template matching
        const message = request.message.toLowerCase();
        let template = '';
        
        if (message.includes('button')) {
            template = `<button className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
  Button
</button>`;
        } else if (message.includes('input')) {
            template = `<input 
  type="text" 
  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
  placeholder="Enter text..."
/>`;
        } else {
            template = `<div className="p-4 bg-gray-100 rounded">
  <!-- Generated component -->
  <p>Component generated from template</p>
</div>`;
        }

        // Simulate streaming
        callback.onChunk(template);
        
        return {
            content: template,
            provider: GenerationProvider.STATIC_TEMPLATES,
            duration: 0,
            metadata: {
                complexity: RequestComplexity.SIMPLE_UI_TASK,
                fallbackUsed: true
            }
        };
    }

    /**
     * Consume SSE stream from Python backend
     */
    private async consumeSSEStream(
        streamUrl: string,
        callback: StreamingCallback,
        provider: GenerationProvider
    ): Promise<GenerationResult> {
        return new Promise((resolve, reject) => {
            const eventSource = new EventSource(streamUrl);
            let fullContent = '';
            let metadata: any = {};

            eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    
                    switch (event.type || 'chunk') {
                        case 'connected':
                            callback.onStatusUpdate('Connected to Python backend', 'connected');
                            break;
                            
                        case 'analysis_start':
                            callback.onStatusUpdate(data.message, 'analysis');
                            break;
                            
                        case 'analysis_complete':
                            callback.onStatusUpdate(data.message, 'analysis_complete');
                            metadata.analysisData = data;
                            break;
                            
                        case 'generation_start':
                            callback.onStatusUpdate(data.message, 'generation');
                            break;
                            
                        case 'generation_chunk':
                            fullContent += data.content;
                            callback.onChunk(data.content, data.metadata);
                            break;
                            
                        case 'generation_complete':
                            metadata = { ...metadata, ...data.metadata };
                            break;
                            
                        case 'complete':
                            eventSource.close();
                            resolve({
                                content: fullContent,
                                provider,
                                duration: 0,
                                metadata: {
                                    complexity: RequestComplexity.COMPLEX_FEATURE,
                                    fallbackUsed: false,
                                    ...metadata
                                }
                            });
                            break;
                            
                        case 'error':
                            eventSource.close();
                            reject(new Error(data.error || 'Python backend error'));
                            break;
                    }
                } catch (parseError) {
                    console.warn('Failed to parse SSE data:', parseError);
                }
            };

            eventSource.onerror = (error) => {
                eventSource.close();
                reject(new Error('SSE connection failed'));
            };

            // Timeout after 5 minutes
            setTimeout(() => {
                if (eventSource.readyState !== EventSource.CLOSED) {
                    eventSource.close();
                    reject(new Error('Request timeout'));
                }
            }, 300000);
        });
    }

    /**
     * Check availability of all providers
     */
    private async checkProviderAvailability(): Promise<Record<GenerationProvider, boolean>> {
        const status = {
            [GenerationProvider.AI_SDK_OPENAI]: false,
            [GenerationProvider.AI_SDK_ANTHROPIC]: false,
            [GenerationProvider.PYTHON_BACKEND]: false,
            [GenerationProvider.HYBRID]: false,
            [GenerationProvider.STATIC_TEMPLATES]: true // Always available
        };

        // Check AI SDK availability (API keys)
        const config = vscode.workspace.getConfiguration('palette');
        status[GenerationProvider.AI_SDK_OPENAI] = !!(config.get('openaiApiKey') || process.env.OPENAI_API_KEY);
        status[GenerationProvider.AI_SDK_ANTHROPIC] = !!(config.get('anthropicApiKey') || process.env.ANTHROPIC_API_KEY);

        // Check Python backend
        try {
            const serverStatus = await this.pythonServerManager.getServerStatus();
            status[GenerationProvider.PYTHON_BACKEND] = serverStatus.isRunning;
        } catch {
            status[GenerationProvider.PYTHON_BACKEND] = false;
        }

        // Hybrid requires both AI SDK and Python
        status[GenerationProvider.HYBRID] = 
            status[GenerationProvider.PYTHON_BACKEND] && 
            (status[GenerationProvider.AI_SDK_OPENAI] || status[GenerationProvider.AI_SDK_ANTHROPIC]);

        return status;
    }

    /**
     * Make intelligent routing decision
     */
    private makeRoutingDecision(
        classification: ClassificationResult,
        availability: Record<GenerationProvider, boolean>
    ): RoutingDecision {
        const decision: RoutingDecision = {
            primaryProvider: GenerationProvider.STATIC_TEMPLATES,
            fallbackProviders: [],
            reasoning: [...classification.reasoning],
            estimatedDuration: classification.estimatedDuration,
            requiresAnalysis: classification.complexity === RequestComplexity.ANALYSIS_REQUIRED
        };

        // Determine primary provider based on complexity and availability
        switch (classification.complexity) {
            case RequestComplexity.SIMPLE_UI_TASK:
                if (availability[GenerationProvider.AI_SDK_OPENAI]) {
                    decision.primaryProvider = GenerationProvider.AI_SDK_OPENAI;
                    decision.fallbackProviders = [
                        GenerationProvider.AI_SDK_ANTHROPIC,
                        GenerationProvider.PYTHON_BACKEND,
                        GenerationProvider.STATIC_TEMPLATES
                    ].filter(p => availability[p]);
                } else if (availability[GenerationProvider.AI_SDK_ANTHROPIC]) {
                    decision.primaryProvider = GenerationProvider.AI_SDK_ANTHROPIC;
                    decision.fallbackProviders = [
                        GenerationProvider.PYTHON_BACKEND,
                        GenerationProvider.STATIC_TEMPLATES
                    ].filter(p => availability[p]);
                } else {
                    decision.primaryProvider = GenerationProvider.STATIC_TEMPLATES;
                }
                break;

            case RequestComplexity.HYBRID_TASK:
                if (availability[GenerationProvider.HYBRID]) {
                    decision.primaryProvider = GenerationProvider.HYBRID;
                    decision.fallbackProviders = [
                        GenerationProvider.PYTHON_BACKEND,
                        GenerationProvider.AI_SDK_OPENAI,
                        GenerationProvider.STATIC_TEMPLATES
                    ].filter(p => availability[p]);
                } else if (availability[GenerationProvider.PYTHON_BACKEND]) {
                    decision.primaryProvider = GenerationProvider.PYTHON_BACKEND;
                    decision.fallbackProviders = [
                        GenerationProvider.AI_SDK_OPENAI,
                        GenerationProvider.STATIC_TEMPLATES
                    ].filter(p => availability[p]);
                }
                break;

            case RequestComplexity.COMPLEX_FEATURE:
            case RequestComplexity.ANALYSIS_REQUIRED:
                if (availability[GenerationProvider.PYTHON_BACKEND]) {
                    decision.primaryProvider = GenerationProvider.PYTHON_BACKEND;
                    decision.fallbackProviders = [
                        GenerationProvider.AI_SDK_OPENAI,
                        GenerationProvider.STATIC_TEMPLATES
                    ].filter(p => availability[p]);
                } else {
                    decision.primaryProvider = GenerationProvider.AI_SDK_OPENAI;
                    decision.fallbackProviders = [GenerationProvider.STATIC_TEMPLATES];
                    decision.reasoning.push('Python backend not available, using AI SDK as fallback');
                }
                break;
        }

        return decision;
    }

    /**
     * Update routing statistics
     */
    private updateRoutingStats(result: GenerationResult): void {
        switch (result.provider) {
            case GenerationProvider.AI_SDK_OPENAI:
            case GenerationProvider.AI_SDK_ANTHROPIC:
                this.routingStats.aiSdkRequests++;
                break;
            case GenerationProvider.PYTHON_BACKEND:
                this.routingStats.pythonBackendRequests++;
                break;
            case GenerationProvider.HYBRID:
                this.routingStats.hybridRequests++;
                break;
        }

        // Update average response time
        const currentAvg = this.routingStats.averageResponseTime;
        const count = this.routingStats.totalRequests;
        this.routingStats.averageResponseTime = 
            (currentAvg * (count - 1) + result.duration) / count;
    }

    /**
     * Get routing statistics
     */
    public getRoutingStats() {
        return { ...this.routingStats };
    }

    /**
     * Reset routing statistics
     */
    public resetStats(): void {
        this.routingStats = {
            totalRequests: 0,
            aiSdkRequests: 0,
            pythonBackendRequests: 0,
            hybridRequests: 0,
            fallbacksUsed: 0,
            averageResponseTime: 0
        };
    }

    /**
     * Dispose of resources
     */
    public dispose(): void {
        this.outputChannel.dispose();
    }
}