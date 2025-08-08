import type { BackendRequest, BackendResponse } from '../types';
import { createOpenAI } from '@ai-sdk/openai';
import { generateText } from 'ai';

const BACKEND_URL = 'http://localhost:8765';

export class PaletteAPI {
  /**
   * Generate AI response using direct AI SDK (following extension-diagnostic.ts pattern)
   */
  static async generateResponse(request: BackendRequest): Promise<BackendResponse> {
    try {
      // Check if API key is provided
      if (!request.api_key) {
        return this.getFallbackResponse(request.message, 'No API key provided');
      }

      // Create OpenAI client with API key (same as extension-diagnostic.ts)
      const openaiClient = createOpenAI({
        apiKey: request.api_key
      });

      // Build conversation messages
      const conversationMessages = request.conversation_history.map(msg => 
        `${msg.role === 'user' ? 'User' : 'Assistant'}: ${msg.content}`
      ).join('\n\n');

      const systemPrompt = this.buildSystemPrompt();
      const fullPrompt = conversationMessages ? 
        `${conversationMessages}\n\nUser: ${request.message}` : 
        request.message;

      // Generate response using AI SDK (same pattern as extension-diagnostic.ts)
      const result = await generateText({
        model: openaiClient(request.model || 'gpt-4.1-2025-04-14'),
        system: systemPrompt,
        prompt: fullPrompt,
        temperature: 0.7
      });

      return {
        content: result.text,
        codeBlocks: this.extractCodeBlocks(result.text),
        intent: this.detectIntent(request.message),
        suggestedActions: this.generateSuggestedActions(request.message)
      };

    } catch (error: any) {
      console.error('AI SDK generation error:', error);
      return this.getFallbackResponse(request.message, error.message);
    }
  }

  /**
   * Test backend connection
   */
  static async testConnection(): Promise<boolean> {
    try {
      const response = await fetch(`${BACKEND_URL}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000)
      });
      return response.ok;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get backend status with version info
   */
  static async getBackendStatus(): Promise<{
    connected: boolean;
    version?: string;
    error?: string;
  }> {
    try {
      const response = await fetch(`${BACKEND_URL}/health`, {
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
        error: error.message || 'Connection failed'
      };
    }
  }

  /**
   * Build system prompt for Palette AI (similar to extension-diagnostic.ts)
   */
  private static buildSystemPrompt(): string {
    return `You are Palette AI, an expert React/TypeScript developer specializing in modern web development with:

🎨 **Core Technologies:**
- Vite + React + TypeScript 
- shadcn/ui components
- Tailwind CSS
- Modern JavaScript/ES6+

🎯 **Your Focus:**
- Generate complete, working React components and pages
- Build full user interfaces and experiences
- Use shadcn/ui components when possible
- Write clean, type-safe TypeScript code
- Apply responsive design with Tailwind CSS
- Follow React best practices and modern patterns

📝 **Response Format:**
- Provide working code with clear explanations
- Include proper TypeScript types
- Use functional components with hooks
- Ensure components are ready to use
- Add helpful comments for complex logic

🚀 **Design Philosophy:**
Focus on creating complete, interactive experiences that users can immediately see and use, not just isolated components. Think like Vercel v0 - build pages and features that demonstrate real functionality.`;
  }

  /**
   * Extract code blocks from AI response text
   */
  private static extractCodeBlocks(text: string): Array<{language: string, code: string, filename?: string}> {
    const codeBlocks: Array<{language: string, code: string, filename?: string}> = [];
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    let match;

    while ((match = codeBlockRegex.exec(text)) !== null) {
      const language = match[1] || 'typescript';
      const code = match[2].trim();
      
      // Try to extract filename from first line if it looks like a comment
      const firstLine = code.split('\n')[0];
      const filename = firstLine.match(/\/\/ (\w+\.\w+)/) ? firstLine.match(/\/\/ (\w+\.\w+)/)![1] : undefined;
      
      codeBlocks.push({
        language,
        code,
        filename
      });
    }

    return codeBlocks;
  }

  /**
   * Detect user intent from message
   */
  private static detectIntent(message: string): string {
    const messageLower = message.toLowerCase();
    
    if (messageLower.includes('create') || messageLower.includes('make') || messageLower.includes('generate')) {
      if (messageLower.includes('page') || messageLower.includes('route')) return 'generate_page';
      if (messageLower.includes('component')) return 'generate_component';
      return 'generate_new';
    }
    
    if (messageLower.includes('fix') || messageLower.includes('improve')) return 'refine_existing';
    if (messageLower.includes('explain') || messageLower.includes('how')) return 'explain_code';
    
    return 'general';
  }

  /**
   * Generate suggested actions based on user message
   */
  private static generateSuggestedActions(message: string): string[] {
    const messageLower = message.toLowerCase();
    const actions = [];
    
    if (messageLower.includes('page') || messageLower.includes('route')) {
      actions.push('Add to Navigation', 'Create Route', 'Add SEO Meta');
    } else if (messageLower.includes('component')) {
      actions.push('Add Props Interface', 'Add Storybook Story', 'Export Component');
    } else {
      actions.push('Refine Design', 'Add Responsiveness', 'Optimize Performance');
    }
    
    return actions;
  }

  /**
   * Fallback response when AI generation fails
   */
  private static getFallbackResponse(userMessage: string, errorMessage?: string): BackendResponse {
    const baseMessage = `I understand you want me to help with: "${userMessage}"`;
    
    if (errorMessage?.includes('API key') || !errorMessage) {
      return {
        content: `${baseMessage}

⚠️ **API Configuration Issue**: ${errorMessage || 'API key not provided'}

To fix this:
1. **Set API Key in VSCode**: 
   - Go to Settings → Extensions → Palette AI Chatbot
   - Enter your OpenAI API key in the "Openai Api Key" field
   - Restart the chatbot

2. **Get an API Key**: 
   - Visit https://platform.openai.com/api-keys
   - Create a new API key
   - Copy and paste it into VSCode settings

**What I can help with once configured:**
- 🎨 Creating React components and pages
- ⚡ Building complete UI experiences  
- 🎯 TypeScript and JavaScript development
- 🌊 Tailwind CSS styling
- 🧩 shadcn/ui component integration
- 📱 Responsive design patterns

I specialize in modern web development with React, TypeScript, Tailwind CSS, and shadcn/ui components.`,
        codeBlocks: [],
        intent: 'configuration_error',
        suggestedActions: [
          'Configure API Key',
          'Check VSCode Settings',
          'Restart Chatbot'
        ]
      };
    }

    return {
      content: `${baseMessage}

❌ **AI Generation Error**: ${errorMessage}

This could be due to:
- Invalid API key
- Network connectivity issues  
- OpenAI service temporarily unavailable
- Rate limiting

Please try again in a moment, or check your API key configuration in VSCode settings.`,
      codeBlocks: [],
      intent: 'error',
      suggestedActions: [
        'Retry Request',
        'Check API Key',
        'Check Network'
      ]
    };
  }
}