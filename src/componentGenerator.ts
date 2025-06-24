import OpenAI from 'openai';
import { GoogleGenerativeAI } from '@google/generative-ai';
import * as vscode from 'vscode';
import { WorkspaceInfo } from './types';

export class ComponentGenerator {
    private openai?: OpenAI;
    private gemini?: GoogleGenerativeAI;

    constructor() {
        const config = vscode.workspace.getConfiguration('ui-copilot');
        const provider = config.get<string>('apiProvider') || 'gemini';
        
        if (provider === 'openai') {
            const apiKey = config.get<string>('openaiApiKey');
            if (apiKey) {
                this.openai = new OpenAI({ apiKey });
            }
        } else if (provider === 'gemini') {
            const apiKey = config.get<string>('geminiApiKey');
            if (apiKey) {
                this.gemini = new GoogleGenerativeAI(apiKey);
            }
        }
    }

    async generateComponent(prompt: string, workspaceInfo: WorkspaceInfo): Promise<string> {
        const config = vscode.workspace.getConfiguration('ui-copilot');
        const provider = config.get<string>('apiProvider') || 'gemini';

        if (provider === 'gemini' && this.gemini) {
            return this.generateWithIntelligentContext(prompt, workspaceInfo);
        } else if (provider === 'openai' && this.openai) {
            return this.generateWithOpenAI(prompt, workspaceInfo);
        } else {
            // Return mock component if no API is configured
            return this.generateMockComponent(prompt, workspaceInfo);
        }
    }

    private async generateWithIntelligentContext(prompt: string, workspaceInfo: WorkspaceInfo): Promise<string> {
        try {
            // Get intelligent context with timeout protection
            const { CodebaseAnalyzer } = await import('./codebaseAnalyzer');
            const analyzer = new CodebaseAnalyzer();
            
            console.log('🧠 Getting intelligent context...');
            const intelligentContext = await Promise.race([
                analyzer.getIntelligentContext(prompt),
                new Promise<any>((_, reject) => 
                    setTimeout(() => reject(new Error('Intelligent context timeout')), 10000)
                )
            ]);
            
            const model = this.gemini!.getGenerativeModel({ 
                model: 'gemini-2.5-flash',
                generationConfig: {
                    temperature: 0.7,
                    topK: 40,
                    topP: 0.95,
                    maxOutputTokens: 2048,
                }
            });
            
            const enhancedSystemPrompt = this.buildEnhancedSystemPrompt(workspaceInfo, intelligentContext);
            const fullPrompt = `${enhancedSystemPrompt}\n\nGenerate a React component: ${prompt}`;

            const result = await model.generateContent(fullPrompt);
            const response = await result.response;
            const generatedCode = response.text();

            if (!generatedCode) {
                throw new Error('No code generated from Gemini');
            }

            return this.cleanupGeneratedCode(generatedCode);
        } catch (error) {
            console.warn('Intelligent context failed, falling back to basic generation:', error);
            // Fallback to basic generation
            return this.generateWithGemini(prompt, workspaceInfo);
        }
    }

    private async generateWithGemini(prompt: string, workspaceInfo: WorkspaceInfo): Promise<string> {
        try {
            const model = this.gemini!.getGenerativeModel({ model: 'gemini-2.5-flash' });
            const systemPrompt = this.buildSystemPrompt(workspaceInfo);
            const fullPrompt = `${systemPrompt}\n\nGenerate a React component: ${prompt}`;

            const result = await model.generateContent(fullPrompt);
            const response = await result.response;
            const generatedCode = response.text();

            if (!generatedCode) {
                throw new Error('No code generated from Gemini');
            }

            return this.cleanupGeneratedCode(generatedCode);
        } catch (error) {
            throw new Error(`Gemini API error: ${error}`);
        }
    }

    private async generateWithOpenAI(prompt: string, workspaceInfo: WorkspaceInfo): Promise<string> {
        try {
            const config = vscode.workspace.getConfiguration('ui-copilot');
            const model = config.get<string>('model') || 'gpt-3.5-turbo';
            const systemPrompt = this.buildSystemPrompt(workspaceInfo);
            
            const response = await this.openai!.chat.completions.create({
                model: model,
                messages: [
                    { role: 'system', content: systemPrompt },
                    { role: 'user', content: `Generate a React component: ${prompt}` }
                ],
                temperature: 0.7,
                max_tokens: 1000,
            });

            const generatedCode = response.choices[0]?.message?.content;
            if (!generatedCode) {
                throw new Error('No code generated from OpenAI');
            }

            return this.cleanupGeneratedCode(generatedCode);
        } catch (error) {
            throw new Error(`OpenAI API error: ${error}`);
        }
    }

    async iterateComponent(existingCode: string, modification: string, workspaceInfo: WorkspaceInfo): Promise<string> {
        const config = vscode.workspace.getConfiguration('ui-copilot');
        const provider = config.get<string>('apiProvider') || 'gemini';

        if (provider === 'gemini' && this.gemini) {
            return this.iterateWithGemini(existingCode, modification, workspaceInfo);
        } else if (provider === 'openai' && this.openai) {
            return this.iterateWithOpenAI(existingCode, modification, workspaceInfo);
        } else {
            return `${existingCode}\n\n// Modified based on: "${modification}"\n// TODO: Implement the requested changes`;
        }
    }

    private async iterateWithGemini(existingCode: string, modification: string, workspaceInfo: WorkspaceInfo): Promise<string> {
        try {
            const model = this.gemini!.getGenerativeModel({ model: 'gemini-2.5-flash' });
            const systemPrompt = this.buildSystemPrompt(workspaceInfo);
            const fullPrompt = `${systemPrompt}\n\nModify this React component based on the request: "${modification}"\n\nExisting code:\n${existingCode}`;

            const result = await model.generateContent(fullPrompt);
            const response = await result.response;
            const modifiedCode = response.text();

            if (!modifiedCode) {
                throw new Error('No modified code generated from Gemini');
            }

            return this.cleanupGeneratedCode(modifiedCode);
        } catch (error) {
            throw new Error(`Gemini API error: ${error}`);
        }
    }

    private async iterateWithOpenAI(existingCode: string, modification: string, workspaceInfo: WorkspaceInfo): Promise<string> {
        try {
            const config = vscode.workspace.getConfiguration('ui-copilot');
            const model = config.get<string>('model') || 'gpt-3.5-turbo';
            const systemPrompt = this.buildSystemPrompt(workspaceInfo);
            
            const response = await this.openai!.chat.completions.create({
                model: model,
                messages: [
                    { role: 'system', content: systemPrompt },
                    { role: 'user', content: `Modify this React component based on the request: "${modification}"\n\nExisting code:\n${existingCode}` }
                ],
                temperature: 0.7,
                max_tokens: 1500,
            });

            const modifiedCode = response.choices[0]?.message?.content;
            if (!modifiedCode) {
                throw new Error('No modified code generated from OpenAI');
            }

            return this.cleanupGeneratedCode(modifiedCode);
        } catch (error) {
            throw new Error(`OpenAI API error: ${error}`);
        }
    }

    private buildEnhancedSystemPrompt(workspaceInfo: WorkspaceInfo, intelligentContext: any): string {
        const basePrompt = this.buildSystemPrompt(workspaceInfo);
        
        // Add sophisticated intelligent context integration
        let enhancedPrompt = basePrompt + '\n\n🧠 SOPHISTICATED CODEBASE ANALYSIS:\n';
        
        // Add design system context
        if (intelligentContext.designSystemContext) {
            enhancedPrompt += this.buildDesignSystemContext(intelligentContext.designSystemContext);
        }
        
        // Add TypeScript patterns
        if (intelligentContext.typeScriptContext) {
            enhancedPrompt += this.buildTypeScriptContext(intelligentContext.typeScriptContext);
        }
        
        // Add state management context
        if (intelligentContext.stateManagementContext) {
            enhancedPrompt += this.buildStateManagementContext(intelligentContext.stateManagementContext);
        }
        
        // Add relevant components with deep analysis
        if (intelligentContext.relevantComponents && intelligentContext.relevantComponents.length > 0) {
            enhancedPrompt += '\n📚 RELEVANT EXISTING COMPONENTS:\n';
            intelligentContext.relevantComponents.slice(0, 3).forEach((comp: any, index: number) => {
                enhancedPrompt += `${index + 1}. ${comp.name} (${comp.category})\n`;
                enhancedPrompt += `   - Path: ${comp.path}\n`;
                enhancedPrompt += `   - Description: ${comp.description}\n`;
                enhancedPrompt += `   - Complexity: ${comp.complexity}\n`;
                if (comp.props) {
                    enhancedPrompt += `   - Props: ${comp.props}\n`;
                }
                if (comp.ast?.hooks && comp.ast.hooks.length > 0) {
                    enhancedPrompt += `   - Hooks: ${comp.ast.hooks.map((h: any) => h.name).join(', ')}\n`;
                }
                if (comp.ast?.styling) {
                    enhancedPrompt += `   - Styling: ${comp.ast.styling.approach}\n`;
                    if (comp.ast.styling.classes.length > 0) {
                        enhancedPrompt += `   - Classes: ${comp.ast.styling.classes.slice(0, 5).join(', ')}\n`;
                    }
                }
                enhancedPrompt += '\n';
            });
        }
        
        // Add code examples
        if (intelligentContext.codeExamples && intelligentContext.codeExamples.length > 0) {
            enhancedPrompt += '\n💡 RELEVANT CODE EXAMPLES:\n';
            intelligentContext.codeExamples.slice(0, 2).forEach((example: any, index: number) => {
                enhancedPrompt += `${index + 1}. ${example.componentName} (${example.category}):\n`;
                enhancedPrompt += '```typescript\n';
                enhancedPrompt += example.snippet.substring(0, 500) + (example.snippet.length > 500 ? '...' : '');
                enhancedPrompt += '\n```\n\n';
            });
        }
        
        // Add pattern suggestions
        if (intelligentContext.patternSuggestions && intelligentContext.patternSuggestions.length > 0) {
            enhancedPrompt += '\n🎯 RECOMMENDED PATTERNS:\n';
            intelligentContext.patternSuggestions.slice(0, 4).forEach((pattern: any, index: number) => {
                enhancedPrompt += `${index + 1}. ${pattern.name} (${pattern.type})\n`;
                enhancedPrompt += `   - ${pattern.description}\n`;
                enhancedPrompt += `   - Confidence: ${Math.round(pattern.confidence * 100)}%\n`;
                enhancedPrompt += `   - Best Practice: ${pattern.usage.bestPractice ? 'Yes' : 'No'}\n`;
                if (pattern.examples && pattern.examples.length > 0) {
                    enhancedPrompt += `   - Example: ${pattern.examples[0]}\n`;
                }
                enhancedPrompt += '\n';
            });
        }
        
        // Add architectural guidance
        if (workspaceInfo.architecture) {
            enhancedPrompt += '\n🏗️ ARCHITECTURAL GUIDANCE:\n';
            if (workspaceInfo.architecture.patterns.length > 0) {
                enhancedPrompt += `- Follow existing patterns: ${workspaceInfo.architecture.patterns.join(', ')}\n`;
            }
            if (workspaceInfo.architecture.layering.length > 0) {
                enhancedPrompt += `- Respect layering: ${workspaceInfo.architecture.layering.map(l => l.name).join(' → ')}\n`;
            }
        }
        
        // Add context summary
        if (intelligentContext.contextSummary) {
            enhancedPrompt += `\n📋 CONTEXT SUMMARY:\n${intelligentContext.contextSummary}\n`;
        }
        
        enhancedPrompt += '\n🚀 GENERATION STRATEGY:\n';
        enhancedPrompt += '- CRITICAL: Generate code that looks like it belongs in this specific codebase\n';
        enhancedPrompt += '- Follow the exact styling patterns shown in the examples\n';
        enhancedPrompt += '- Use the same TypeScript patterns and return types\n';
        enhancedPrompt += '- Implement the same state management approaches\n';
        enhancedPrompt += '- Match the naming conventions and component structure\n';
        enhancedPrompt += '- Include proper error handling and loading states if patterns exist\n';
        enhancedPrompt += '- Ensure accessibility features match existing components\n';
        enhancedPrompt += '- Generate professional, production-ready code\n';
        
        return enhancedPrompt;
    }
    
    private buildDesignSystemContext(designSystem: any): string {
        let context = '\n🎨 DESIGN SYSTEM:\n';
        
        if (designSystem.componentLibrary) {
            context += `- Component Library: ${designSystem.componentLibrary}\n`;
        }
        
        if (designSystem.colorPalette) {
            if (designSystem.colorPalette.primary.length > 0) {
                context += `- Primary Colors: ${designSystem.colorPalette.primary.slice(0, 3).join(', ')}\n`;
            }
            if (designSystem.colorPalette.semantic && Object.keys(designSystem.colorPalette.semantic).length > 0) {
                context += `- Semantic Colors: ${Object.keys(designSystem.colorPalette.semantic).join(', ')}\n`;
            }
        }
        
        if (designSystem.spacingSystem) {
            context += `- Spacing Unit: ${designSystem.spacingSystem.unit}\n`;
            const commonSpacing = Object.keys(designSystem.spacingSystem.scale).slice(0, 5);
            if (commonSpacing.length > 0) {
                context += `- Common Spacing: ${commonSpacing.join(', ')}\n`;
            }
        }
        
        if (designSystem.typographySystem) {
            const fontFamilies = Object.keys(designSystem.typographySystem.fontFamilies);
            if (fontFamilies.length > 0) {
                context += `- Font Families: ${fontFamilies.join(', ')}\n`;
            }
        }
        
        return context;
    }
    
    private buildTypeScriptContext(tsContext: any): string {
        let context = '\n📝 TYPESCRIPT PATTERNS:\n';
        
        context += `- Strict Mode: ${tsContext.strictMode ? 'Enabled' : 'Disabled'}\n`;
        
        if (tsContext.returnTypes && tsContext.returnTypes.length > 0) {
            const mostUsed = tsContext.returnTypes.sort((a: any, b: any) => b.usage - a.usage)[0];
            context += `- Preferred Return Type: ${mostUsed.pattern}\n`;
        }
        
        if (tsContext.interfaceUsage && tsContext.interfaceUsage.length > 0) {
            context += `- Interface Usage: ${tsContext.interfaceUsage.length} interfaces found\n`;
        }
        
        if (tsContext.utilityTypes && tsContext.utilityTypes.length > 0) {
            context += `- Utility Types: ${tsContext.utilityTypes.join(', ')}\n`;
        }
        
        return context;
    }
    
    private buildStateManagementContext(stateContext: any): string {
        let context = '\n📊 STATE MANAGEMENT:\n';
        
        context += `- Primary Approach: ${stateContext.primary}\n`;
        
        if (stateContext.patterns && stateContext.patterns.length > 0) {
            const topPatterns = stateContext.patterns.slice(0, 3);
            context += `- Common Patterns: ${topPatterns.map((p: any) => p.name).join(', ')}\n`;
        }
        
        return context;
    }

    private buildSystemPrompt(workspaceInfo: WorkspaceInfo): string {
        let prompt = `You are an expert React developer specializing in modern, production-ready components. Generate clean, accessible, and performant React components.

CORE REQUIREMENTS:
- Return ONLY the React component code, no explanations or markdown blocks
- Use functional components with React hooks
- Follow React best practices and modern patterns
- Make components reusable with well-defined props
- Include proper accessibility attributes (ARIA labels, roles, etc.)
- Use semantic HTML elements
- Handle loading and error states when appropriate
- Include proper TypeScript types and interfaces

CODING STANDARDS:
- Use descriptive prop names and component names
- Include default props when sensible
- Add proper event handlers with TypeScript types
- Use React.forwardRef for components that need ref access
- Implement proper keyboard navigation for interactive elements
- Use React.memo for performance optimization when needed`;

        // Add framework-specific patterns
        if (workspaceInfo.styling.hasNextJS) {
            prompt += '\n\nNEXT.JS PATTERNS:\n- Add "use client" directive for client components\n- Use Next.js Image component for images\n- Follow Next.js 13+ app router patterns\n- Use proper TypeScript interfaces with JSX.Element return type';
        }

        // Add UI library patterns
        if (workspaceInfo.styling.hasShadcnUI) {
            prompt += '\n\nSHADCN/UI COMPONENTS:\n- Import components from "@/components/ui/[component]"\n- Use Button, Input, Dialog, Card components when appropriate\n- Follow shadcn/ui component patterns and props\n- Use className prop for styling customization';
        }

        if (workspaceInfo.styling.hasLucideIcons) {
            prompt += '\n\nICONS:\n- Import icons from "lucide-react"\n- Use semantic icon names (Play, Heart, Users, etc.)\n- Apply consistent sizing (w-4 h-4, w-5 h-5)';
        }

        // Enhanced styling guidelines
        if (workspaceInfo.styling.hasTailwind) {
            prompt += '\n\nADVANCED TAILWIND:\n- Use complex responsive patterns (sm:, md:, lg:, xl:, 2xl:)\n- Apply design system colors (primary, secondary, accent, muted)\n- Use advanced layouts (grid-cols-1 sm:grid-cols-2 lg:grid-cols-3)\n- Include hover states and transitions\n- Use backdrop-blur, shadows, and modern effects\n- Support dark mode with dark: prefix\n- Use semantic spacing and typography scales';
        } else if (workspaceInfo.styling.hasStyledComponents) {
            prompt += '\n\nSTYLING:\n- Use styled-components for all styling\n- Create properly typed styled components\n- Use theme variables if available\n- Include hover and focus states\n- Make responsive with media queries';
        } else if (workspaceInfo.styling.hasCSSModules) {
            prompt += '\n\nSTYLING:\n- Use CSS modules with descriptive class names\n- Import styles object and use styles.className\n- Follow BEM naming convention in CSS';
        } else {
            prompt += '\n\nSTYLING:\n- Use inline styles or CSS-in-JS\n- Create clean, semantic class names if using CSS\n- Ensure mobile-responsive design';
        }

        // Enhanced TypeScript support
        if (workspaceInfo.hasTypeScript) {
            prompt += '\n\nTYPESCRIPT:\n- Define comprehensive Props interface with JSDoc comments\n- Use proper React types (React.FC, React.ReactNode, etc.)\n- Type all event handlers correctly\n- Export both the component and its Props interface\n- Use generic types when appropriate';
        } else {
            prompt += '\n\nJAVASCRIPT:\n- Use PropTypes for prop validation\n- Include defaultProps where appropriate\n- Use JSDoc comments for documentation';
        }

        // Add state management patterns
        const statePatterns = workspaceInfo.patterns?.stateManagementPatterns || [];
        if (statePatterns.length > 0) {
            prompt += '\n\nSTATE MANAGEMENT PATTERNS:';
            if (statePatterns.includes('client-side-caching')) {
                prompt += '\n- Implement localStorage caching with expiration timestamps\n- Use cache keys with prefixes and time ranges';
            }
            if (statePatterns.includes('promise-racing')) {
                prompt += '\n- Use Promise.race for timeout handling\n- Implement graceful fallbacks for timeouts';
            }
            if (statePatterns.includes('loading-states')) {
                prompt += '\n- Use sophisticated loading states: "idle" | "loading" | "success" | "error"\n- Include skeleton loading components';
            }
            if (statePatterns.includes('callback-optimization')) {
                prompt += '\n- Use useCallback for function memoization\n- Optimize re-renders with proper dependencies';
            }
            if (statePatterns.includes('error-handling')) {
                prompt += '\n- Implement comprehensive error handling with user feedback\n- Use error boundaries and fallback UI states';
            }
        }

        // Add existing components context
        if (workspaceInfo.existingComponents.length > 0) {
            prompt += '\n\nEXISTING CODEBASE CONTEXT:';
            workspaceInfo.existingComponents.slice(0, 5).forEach(comp => {
                prompt += `\n- ${comp.name}: ${comp.description}`;
            });
            prompt += '\nEnsure your component follows similar patterns and naming conventions.';
        }

        prompt += '\n\nQUALITY CHECKLIST:\n- Component is accessible (WCAG compliant)\n- Responsive design included\n- Proper error boundaries and loading states\n- Clean, readable code structure\n- Follows React performance best practices\n- Ready for production use\n\nGenerate the complete component code now:';

        return prompt;
    }

    private cleanupGeneratedCode(code: string): string {
        // Remove markdown code blocks if present
        let cleaned = code.replace(/```[a-z]*\n?/g, '').replace(/```\n?/g, '').trim();
        
        // Remove common AI explanatory prefixes
        cleaned = cleaned.replace(/^(Here's|Here is|This is|I'll create|Let me create).*?:\s*\n*/i, '');
        
        // Split into lines for processing
        const lines = cleaned.split('\n');
        let codeStartIndex = 0;
        let codeEndIndex = lines.length;
        
        // Find the start of actual code
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            if (line.startsWith('import') || 
                line.startsWith('const') || 
                line.startsWith('function') ||
                line.startsWith('export') ||
                line.startsWith('interface') ||
                line.startsWith('type ') ||
                line.startsWith('//') && line.includes('import')) {
                codeStartIndex = i;
                break;
            }
        }
        
        // Find the end of code (remove trailing explanations)
        for (let i = lines.length - 1; i >= 0; i--) {
            const line = lines[i].trim();
            if (line && !line.startsWith('//') && 
                !line.toLowerCase().includes('this component') &&
                !line.toLowerCase().includes('usage:') &&
                !line.toLowerCase().includes('example:')) {
                codeEndIndex = i + 1;
                break;
            }
        }
        
        let result = lines.slice(codeStartIndex, codeEndIndex).join('\n');
        
        // Ensure proper formatting
        result = result.trim();
        
        // Add final newline if not present
        if (result && !result.endsWith('\n')) {
            result += '\n';
        }
        
        return result;
    }

    private generateMockComponent(prompt: string, workspaceInfo: WorkspaceInfo): string {
        const componentName = this.extractComponentName(prompt);
        const useTS = workspaceInfo.hasTypeScript;
        const hasTailwind = workspaceInfo.styling.hasTailwind;
        
        if (useTS) {
            const tailwindClasses = hasTailwind ? 
                'className="p-4 border border-gray-200 rounded-lg bg-white shadow-sm"' : 
                'style={{ padding: "1rem", border: "1px solid #e5e7eb", borderRadius: "0.5rem", backgroundColor: "white", boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)" }}';
                
            return `interface ${componentName}Props {
  /**
   * Additional CSS classes to apply to the component
   */
  className?: string;
  /**
   * Content to display inside the component
   */
  children?: React.ReactNode;
}

/**
 * ${componentName} component generated from: "${prompt}"
 * TODO: Implement the actual functionality based on requirements
 */
const ${componentName}: React.FC<${componentName}Props> = ({ 
  className = "",
  children,
  ...props 
}) => {
  return (
    <div 
      ${tailwindClasses}
      {...props}
    >
      <h2 ${hasTailwind ? 'className="text-lg font-semibold text-gray-900 mb-2"' : 'style={{ fontSize: "1.125rem", fontWeight: "600", color: "#111827", marginBottom: "0.5rem" }}'}>
        ${componentName}
      </h2>
      <p ${hasTailwind ? 'className="text-gray-600 text-sm"' : 'style={{ color: "#6b7280", fontSize: "0.875rem" }}'}>
        Generated from prompt: "${prompt}"
      </p>
      {children && (
        <div ${hasTailwind ? 'className="mt-4"' : 'style={{ marginTop: "1rem" }}'}>
          {children}
        </div>
      )}
      {/* TODO: Add your component content here */}
    </div>
  );
};

export default ${componentName};
export type { ${componentName}Props };`;
        } else {
            const tailwindClasses = hasTailwind ? 
                'className="p-4 border border-gray-200 rounded-lg bg-white shadow-sm"' : 
                'style={{ padding: "1rem", border: "1px solid #e5e7eb", borderRadius: "0.5rem", backgroundColor: "white", boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)" }}';
                
            return `/**
 * ${componentName} component generated from: "${prompt}"
 * TODO: Implement the actual functionality based on requirements
 */
const ${componentName} = ({ 
  className = "",
  children,
  ...props 
}) => {
  return (
    <div 
      ${tailwindClasses}
      {...props}
    >
      <h2 ${hasTailwind ? 'className="text-lg font-semibold text-gray-900 mb-2"' : 'style={{ fontSize: "1.125rem", fontWeight: "600", color: "#111827", marginBottom: "0.5rem" }}'}>
        ${componentName}
      </h2>
      <p ${hasTailwind ? 'className="text-gray-600 text-sm"' : 'style={{ color: "#6b7280", fontSize: "0.875rem" }}'}>
        Generated from prompt: "${prompt}"
      </p>
      {children && (
        <div ${hasTailwind ? 'className="mt-4"' : 'style={{ marginTop: "1rem" }}'}>
          {children}
        </div>
      )}
      {/* TODO: Add your component content here */}
    </div>
  );
};

export default ${componentName};`;
        }
    }

    private extractComponentName(prompt: string): string {
        // Simple extraction - capitalize first word
        const words = prompt.split(' ');
        const firstWord = words[0] || 'Component';
        return firstWord.charAt(0).toUpperCase() + firstWord.slice(1);
    }
}