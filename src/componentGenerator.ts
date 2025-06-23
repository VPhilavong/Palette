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
            return this.generateWithGemini(prompt, workspaceInfo);
        } else if (provider === 'openai' && this.openai) {
            return this.generateWithOpenAI(prompt, workspaceInfo);
        } else {
            // Return mock component if no API is configured
            return this.generateMockComponent(prompt, workspaceInfo);
        }
    }

    private async generateWithGemini(prompt: string, workspaceInfo: WorkspaceInfo): Promise<string> {
        try {
            const model = this.gemini!.getGenerativeModel({ model: 'gemini-1.5-flash' });
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
            const model = this.gemini!.getGenerativeModel({ model: 'gemini-1.5-flash' });
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

        // Add styling information with specific guidelines
        if (workspaceInfo.styling.hasTailwind) {
            prompt += '\n\nSTYLING:\n- Use Tailwind CSS classes exclusively\n- Use responsive design classes (sm:, md:, lg:)\n- Leverage Tailwind color palette and spacing scale\n- Use hover:, focus:, and active: states\n- Include dark mode support with dark: prefix when relevant';
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