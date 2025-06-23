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
            const model = this.gemini!.getGenerativeModel({ model: 'gemini-pro' });
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
            const model = this.gemini!.getGenerativeModel({ model: 'gemini-pro' });
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
        let prompt = `You are an expert React developer. Generate clean, modern React components based on user requirements.

IMPORTANT RULES:
- Only return the React component code, no explanations or markdown
- Use functional components with hooks
- Follow modern React best practices
- Make components reusable with proper props`;

        // Add styling information
        if (workspaceInfo.styling.hasTailwind) {
            prompt += '\n- Use Tailwind CSS classes for styling';
        } else if (workspaceInfo.styling.hasStyledComponents) {
            prompt += '\n- Use styled-components for styling';
        } else {
            prompt += '\n- Use CSS modules or inline styles for styling';
        }

        // Add TypeScript info
        if (workspaceInfo.hasTypeScript) {
            prompt += '\n- Use TypeScript with proper type definitions';
            prompt += '\n- Define Props interface for the component';
        }

        // Add existing components context
        if (workspaceInfo.existingComponents.length > 0) {
            prompt += '\n\nExisting components in this codebase you can reference:';
            workspaceInfo.existingComponents.slice(0, 5).forEach(comp => {
                prompt += `\n- ${comp.name}: ${comp.description}`;
            });
        }

        prompt += '\n\nGenerate production-ready code only.';

        return prompt;
    }

    private cleanupGeneratedCode(code: string): string {
        // Remove markdown code blocks if present
        let cleaned = code.replace(/```[a-z]*\n?/g, '').trim();
        
        // Remove any explanatory text before the code
        const lines = cleaned.split('\n');
        let codeStartIndex = 0;
        
        for (let i = 0; i < lines.length; i++) {
            if (lines[i].trim().startsWith('import') || 
                lines[i].trim().startsWith('const') || 
                lines[i].trim().startsWith('function') ||
                lines[i].trim().startsWith('export')) {
                codeStartIndex = i;
                break;
            }
        }
        
        return lines.slice(codeStartIndex).join('\n');
    }

    private generateMockComponent(prompt: string, workspaceInfo: WorkspaceInfo): string {
        const componentName = this.extractComponentName(prompt);
        const useTS = workspaceInfo.hasTypeScript;
        
        if (useTS) {
            return `interface ${componentName}Props {
  // Add your props here
}

const ${componentName}: React.FC<${componentName}Props> = () => {
  return (
    <div>
      <h2>${componentName}</h2>
      <p>Generated from prompt: "${prompt}"</p>
      {/* Add your component content here */}
    </div>
  );
};

export default ${componentName};`;
        } else {
            return `const ${componentName} = () => {
  return (
    <div>
      <h2>${componentName}</h2>
      <p>Generated from prompt: "${prompt}"</p>
      {/* Add your component content here */}
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