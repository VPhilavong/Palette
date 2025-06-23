"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ComponentGenerator = void 0;
const openai_1 = __importDefault(require("openai"));
const generative_ai_1 = require("@google/generative-ai");
const vscode = __importStar(require("vscode"));
class ComponentGenerator {
    constructor() {
        const config = vscode.workspace.getConfiguration('ui-copilot');
        const provider = config.get('apiProvider') || 'gemini';
        if (provider === 'openai') {
            const apiKey = config.get('openaiApiKey');
            if (apiKey) {
                this.openai = new openai_1.default({ apiKey });
            }
        }
        else if (provider === 'gemini') {
            const apiKey = config.get('geminiApiKey');
            if (apiKey) {
                this.gemini = new generative_ai_1.GoogleGenerativeAI(apiKey);
            }
        }
    }
    async generateComponent(prompt, workspaceInfo) {
        const config = vscode.workspace.getConfiguration('ui-copilot');
        const provider = config.get('apiProvider') || 'gemini';
        if (provider === 'gemini' && this.gemini) {
            return this.generateWithGemini(prompt, workspaceInfo);
        }
        else if (provider === 'openai' && this.openai) {
            return this.generateWithOpenAI(prompt, workspaceInfo);
        }
        else {
            // Return mock component if no API is configured
            return this.generateMockComponent(prompt, workspaceInfo);
        }
    }
    async generateWithGemini(prompt, workspaceInfo) {
        try {
            const model = this.gemini.getGenerativeModel({ model: 'gemini-pro' });
            const systemPrompt = this.buildSystemPrompt(workspaceInfo);
            const fullPrompt = `${systemPrompt}\n\nGenerate a React component: ${prompt}`;
            const result = await model.generateContent(fullPrompt);
            const response = await result.response;
            const generatedCode = response.text();
            if (!generatedCode) {
                throw new Error('No code generated from Gemini');
            }
            return this.cleanupGeneratedCode(generatedCode);
        }
        catch (error) {
            throw new Error(`Gemini API error: ${error}`);
        }
    }
    async generateWithOpenAI(prompt, workspaceInfo) {
        try {
            const config = vscode.workspace.getConfiguration('ui-copilot');
            const model = config.get('model') || 'gpt-3.5-turbo';
            const systemPrompt = this.buildSystemPrompt(workspaceInfo);
            const response = await this.openai.chat.completions.create({
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
        }
        catch (error) {
            throw new Error(`OpenAI API error: ${error}`);
        }
    }
    async iterateComponent(existingCode, modification, workspaceInfo) {
        const config = vscode.workspace.getConfiguration('ui-copilot');
        const provider = config.get('apiProvider') || 'gemini';
        if (provider === 'gemini' && this.gemini) {
            return this.iterateWithGemini(existingCode, modification, workspaceInfo);
        }
        else if (provider === 'openai' && this.openai) {
            return this.iterateWithOpenAI(existingCode, modification, workspaceInfo);
        }
        else {
            return `${existingCode}\n\n// Modified based on: "${modification}"\n// TODO: Implement the requested changes`;
        }
    }
    async iterateWithGemini(existingCode, modification, workspaceInfo) {
        try {
            const model = this.gemini.getGenerativeModel({ model: 'gemini-pro' });
            const systemPrompt = this.buildSystemPrompt(workspaceInfo);
            const fullPrompt = `${systemPrompt}\n\nModify this React component based on the request: "${modification}"\n\nExisting code:\n${existingCode}`;
            const result = await model.generateContent(fullPrompt);
            const response = await result.response;
            const modifiedCode = response.text();
            if (!modifiedCode) {
                throw new Error('No modified code generated from Gemini');
            }
            return this.cleanupGeneratedCode(modifiedCode);
        }
        catch (error) {
            throw new Error(`Gemini API error: ${error}`);
        }
    }
    async iterateWithOpenAI(existingCode, modification, workspaceInfo) {
        try {
            const config = vscode.workspace.getConfiguration('ui-copilot');
            const model = config.get('model') || 'gpt-3.5-turbo';
            const systemPrompt = this.buildSystemPrompt(workspaceInfo);
            const response = await this.openai.chat.completions.create({
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
        }
        catch (error) {
            throw new Error(`OpenAI API error: ${error}`);
        }
    }
    buildSystemPrompt(workspaceInfo) {
        let prompt = `You are an expert React developer. Generate clean, modern React components based on user requirements.

IMPORTANT RULES:
- Only return the React component code, no explanations or markdown
- Use functional components with hooks
- Follow modern React best practices
- Make components reusable with proper props`;
        // Add styling information
        if (workspaceInfo.styling.hasTailwind) {
            prompt += '\n- Use Tailwind CSS classes for styling';
        }
        else if (workspaceInfo.styling.hasStyledComponents) {
            prompt += '\n- Use styled-components for styling';
        }
        else {
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
    cleanupGeneratedCode(code) {
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
    generateMockComponent(prompt, workspaceInfo) {
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
        }
        else {
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
    extractComponentName(prompt) {
        // Simple extraction - capitalize first word
        const words = prompt.split(' ');
        const firstWord = words[0] || 'Component';
        return firstWord.charAt(0).toUpperCase() + firstWord.slice(1);
    }
}
exports.ComponentGenerator = ComponentGenerator;
//# sourceMappingURL=componentGenerator.js.map