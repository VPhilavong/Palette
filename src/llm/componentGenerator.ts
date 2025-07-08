import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { WorkspaceIndex, ComponentInfo, Framework } from '../types';
import { PromptBuilder } from './promptBuilder';
import { ModelClient, ModelClientFactory } from './modelClient';
import { CodebaseAnalyzer, CodebasePatterns } from '../codebase/codebaseAnalyzer';
import { CodeValidator } from './codeValidator';

export class ComponentGenerator {
    private promptBuilder: PromptBuilder;
    private modelClient: ModelClient;
    private codebaseAnalyzer: CodebaseAnalyzer;
    private codeValidator: CodeValidator;

    constructor() {
        this.promptBuilder = new PromptBuilder();
        this.modelClient = ModelClientFactory.createClient();
        this.codebaseAnalyzer = new CodebaseAnalyzer();
        this.codeValidator = new CodeValidator();
    }

    async generateComponentCode(
        userPrompt: string, 
        workspaceIndex?: WorkspaceIndex | null
    ): Promise<string | null> {
        try {
            if (!workspaceIndex) {
                vscode.window.showWarningMessage('Please analyze project first for better context-aware generation');
                return null;
            }

            // Analyze codebase patterns for intelligent generation
            const patterns = await this.codebaseAnalyzer.analyzeCodebasePatterns(workspaceIndex);
            
            // Find similar components for context
            const similarComponents = this.codebaseAnalyzer.findSimilarComponents(userPrompt, workspaceIndex.components);
            
            // Build intelligent context-aware prompt
            const contextInfo = this.codebaseAnalyzer.buildContextFromSimilar(similarComponents, patterns);
            const systemPrompt = this.buildSystemPrompt(workspaceIndex, patterns);
            
            const fullPrompt = this.promptBuilder.buildComponentGenerationPrompt(
                userPrompt,
                similarComponents,
                workspaceIndex.project,
                patterns,
                contextInfo
            );

            // Generate component code with context
            const generatedCode = await this.modelClient.generateCompletion(
                `${systemPrompt}\n\n${fullPrompt}`
            );

            if (!generatedCode) {
                return null;
            }

            // Validate and fix the generated code
            const validationResult = await this.codeValidator.validateAndFixGeneratedCode(
                generatedCode, 
                workspaceIndex
            );

            if (!validationResult.isValid) {
                return null;
            }

            // Return the fixed code
            return validationResult.fixedCode || generatedCode;

        } catch (error) {
            console.error('Component generation failed:', error);
            return null;
        }
    }

    async generateComponent(
        userPrompt: string,
        workspaceIndex?: WorkspaceIndex | null
      ): Promise<string | undefined> {
        try {
            if (!workspaceIndex) {
                vscode.window.showWarningMessage('Please analyze project first for better context-aware generation');
                return;
            }

            vscode.window.showInformationMessage('🧠 Analyzing codebase patterns...');

            // Analyze codebase patterns for intelligent generation
            const patterns = await this.codebaseAnalyzer.analyzeWorkspace(workspaceIndex);
            
            // Find similar components for context
            const similarComponents = this.codebaseAnalyzer.findSimilarComponents(userPrompt, workspaceIndex.components);
            
            // Detect target directory based on patterns
            const targetDir = await this.determineTargetDirectory(patterns);
            if (!targetDir) {
                vscode.window.showErrorMessage('Could not determine target directory for component');
                return;
            }

            // Build intelligent context-aware prompt
            const contextInfo = this.codebaseAnalyzer.buildContextFromSimilar(similarComponents, patterns);
            const systemPrompt = this.buildSystemPrompt(workspaceIndex, patterns);
            
            const fullPrompt = this.promptBuilder.buildComponentGenerationPrompt(
                userPrompt,
                similarComponents,
                workspaceIndex.project,
                patterns,
                contextInfo
            );

            vscode.window.showInformationMessage('🎨 Generating context-aware component...');

            // Generate component code with context
            const generatedCode = await this.modelClient.generateCompletion(
                `${systemPrompt}\n\n${fullPrompt}`
            );

            if (!generatedCode) {
                vscode.window.showErrorMessage('Failed to generate component code');
                return;
            }

            vscode.window.showInformationMessage('🔍 Validating and fixing generated code...');

            // Validate and fix the generated code
            const validationResult = await this.codeValidator.validateAndFixGeneratedCode(
                generatedCode, 
                workspaceIndex
            );

            // Show validation summary
            const validationSummary = this.codeValidator.getValidationSummary(validationResult);
            if (validationResult.warnings.length > 0 || validationResult.errors.length > 0) {
                vscode.window.showInformationMessage(validationSummary);
            }

            if (!validationResult.isValid) {
                vscode.window.showErrorMessage('Generated code has errors that could not be fixed automatically');
                return;
            }

            // Use the fixed code
            const finalCode = validationResult.fixedCode || generatedCode;

            // Parse and create component file(s) based on patterns
            await this.createIntelligentComponent(finalCode, targetDir, patterns, userPrompt);
            return finalCode;

            

        } catch (error) {
            console.error('Component generation failed:', error);
            vscode.window.showErrorMessage(`Component generation failed: ${error}`);
        }
    }

    private async determineTargetDirectory(patterns?: CodebasePatterns): Promise<string | null> {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
            return null;
        }

        const rootPath = workspaceFolders[0].uri.fsPath;

        // Use patterns to find the best directory
        if (patterns) {
            // Look where existing components are located
            const componentDirs = new Map<string, number>();
            patterns.existingComponents.forEach(comp => {
                const dir = path.dirname(comp.path);
                componentDirs.set(dir, (componentDirs.get(dir) || 0) + 1);
            });

            // Find the most common component directory
            if (componentDirs.size > 0) {
                const mostCommonDir = Array.from(componentDirs.entries())
                    .sort(([,a], [,b]) => b - a)[0][0];
                
                const fullPath = path.join(rootPath, mostCommonDir);
                if (fs.existsSync(fullPath)) {
                    return fullPath;
                }
            }
        }

        // Fallback to common component directories
        const commonDirs = [
            'src/components',
            'components', 
            'src/ui',
            'ui',
            'app/components',
            'src'
        ];

        for (const dir of commonDirs) {
            const fullPath = path.join(rootPath, dir);
            if (fs.existsSync(fullPath)) {
                return fullPath;
            }
        }

        // Final fallback
        const srcPath = path.join(rootPath, 'src');
        if (fs.existsSync(srcPath)) {
            return srcPath;
        }

        return rootPath;
    }

    private buildSystemPrompt(workspaceIndex?: WorkspaceIndex | null, patterns?: CodebasePatterns): string {
        let frameworks = 'React';
        let styleInfo = '';
        
        if (workspaceIndex?.project?.frameworks) {
            frameworks = workspaceIndex.project.frameworks.map(f => f.name).join(', ');
            
            // Add styling information if detected
            const stylingFrameworks = workspaceIndex.project.frameworks.filter(f => 
                ['Tailwind CSS', 'styled-components', 'emotion', 'CSS Modules'].includes(f.name)
            );
            
            if (stylingFrameworks.length > 0) {
                styleInfo = `\nStyling: Use ${stylingFrameworks.map(f => f.name).join(', ')} for styling.`;
            }
        }

        let prompt = `You are an expert UI component generator that integrates seamlessly with existing codebases.

Framework: ${frameworks}${styleInfo}

CRITICAL: ${patterns ? this.getStylingInstructions(patterns) : 'Use modern CSS approaches'}

Requirements:
- Generate complete, functional components matching existing patterns
- Use modern best practices and patterns from this specific codebase
- Include proper TypeScript types when applicable
- Add meaningful props and proper prop validation
- Include responsive design considerations
- Follow accessibility guidelines (ARIA attributes, semantic HTML)
- Use appropriate component composition patterns
- Match the existing code style and conventions

${patterns ? this.getCodebaseSpecificInstructions(patterns) : ''}

Response format: Generate ONLY the component code without markdown blocks or explanations.`;

        return prompt;
    }

    private getStylingInstructions(patterns: CodebasePatterns): string {
        switch (patterns.stylingApproach) {
            case 'css-modules':
                return 'Import styles using CSS Modules (import styles from "./Component.module.css"). Reference styles using styles.className';
            case 'tailwind':
                return 'Use Tailwind CSS classes for styling. Apply responsive design with Tailwind breakpoints (sm:, md:, lg:, xl:)';
            case 'styled-components':
                return 'Use styled-components for styling. Create styled components using styled.div`...`';
            case 'scss':
                return 'Import SCSS files and use class names for styling';
            default:
                return 'Import CSS files and use class names for styling';
        }
    }

    private getCodebaseSpecificInstructions(patterns: CodebasePatterns): string {
        let instructions = '';
        
        if (patterns.commonProps.length > 0) {
            instructions += `Common props in this codebase: ${patterns.commonProps.join(', ')}\n`;
        }
        
        if (patterns.importPatterns.length > 0) {
            const reactImports = patterns.importPatterns.filter(p => p.includes('react'));
            if (reactImports.length > 0) {
                instructions += `Common import patterns: ${reactImports.slice(0, 3).join(', ')}\n`;
            }
        }
        
        return instructions;
    }

    private async createIntelligentComponent(
        generatedCode: string, 
        targetDir: string, 
        patterns: CodebasePatterns,
        userPrompt: string
    ): Promise<void> {
        const componentData = this.parseGeneratedComponent(generatedCode);
        
        // For CSS modules, we need to create both component and CSS file
        if (patterns.stylingApproach === 'css-modules') {
            await this.createComponentWithStyles(componentData, targetDir, patterns, userPrompt);
        } else {
            await this.createComponentFile(componentData, targetDir);
        }
    }

    private async createComponentWithStyles(
        componentData: { name: string; code: string; extension: string },
        targetDir: string,
        patterns: CodebasePatterns,
        userPrompt: string
    ): Promise<void> {
        // Extract style references from generated code
        const styleReferences = this.extractStyleReferences(componentData.code);
        
        // Create CSS module file if needed
        if (patterns.stylingApproach === 'css-modules' && styleReferences.length > 0) {
            const cssContent = await this.generateStylesForComponent(userPrompt, styleReferences);
            const cssFileName = `${componentData.name}.module.css`;
            const cssFilePath = path.join(targetDir, cssFileName);
            
            await this.writeFile(cssFilePath, cssContent);
        }
        
        // Create the component file
        await this.createComponentFile(componentData, targetDir);
    }

    private extractStyleReferences(code: string): string[] {
        const styleMatches = code.match(/styles\.(\w+)/g);
        if (!styleMatches) return [];
        
        return Array.from(new Set(
            styleMatches.map(match => match.replace('styles.', ''))
        ));
    }

    private async generateStylesForComponent(userPrompt: string, styleClasses: string[]): Promise<string> {
        const prompt = `Generate CSS module styles for these classes: ${styleClasses.join(', ')}

Component context: ${userPrompt}

Requirements:
- Use modern CSS with flexbox/grid
- Include responsive design
- Add hover and focus states
- Use semantic naming
- Include proper spacing and typography

Generate only the CSS code:`;

        try {
            const cssCode = await this.modelClient.generateCompletion(prompt);
            return cssCode || this.generateFallbackCSS(styleClasses);
        } catch (error) {
            console.error('Failed to generate CSS:', error);
            return this.generateFallbackCSS(styleClasses);
        }
    }

    private generateFallbackCSS(styleClasses: string[]): string {
        return styleClasses.map(className => `.${className} {\n  /* Add styles for ${className} */\n}`).join('\n\n');
    }

    private parseGeneratedComponent(generatedCode: string): {
        name: string;
        code: string;
        extension: string;
    } {
        // Extract component name from code
        const componentNameMatch = generatedCode.match(/(?:function|const|class)\s+(\w+)/);
        const componentName = componentNameMatch?.[1] || 'GeneratedComponent';

        // Determine file extension based on content
        const hasTypeScript = generatedCode.includes('interface ') || 
                             generatedCode.includes(': React.') ||
                             generatedCode.includes('type ');
        const hasJSX = generatedCode.includes('<') && generatedCode.includes('>');

        let extension = '.js';
        if (hasTypeScript && hasJSX) {
            extension = '.tsx';
        } else if (hasTypeScript) {
            extension = '.ts';
        } else if (hasJSX) {
            extension = '.jsx';
        }

        // Clean up the generated code
        let cleanCode = generatedCode;
        
        // Remove markdown code blocks if present
        cleanCode = cleanCode.replace(/```[\w]*\n/, '').replace(/\n```$/, '');
        
        // Ensure proper imports
        if (hasJSX && !cleanCode.includes("import React")) {
            cleanCode = "import React from 'react';\n\n" + cleanCode;
        }

        // Add export default if missing
        if (!cleanCode.includes('export default') && !cleanCode.includes('export {')) {
            cleanCode += `\n\nexport default ${componentName};`;
        }

        return {
            name: componentName,
            code: cleanCode,
            extension
        };
    }

    private async createComponentFile(
        componentData: { name: string; code: string; extension: string },
        targetDir: string
    ): Promise<void> {
        const fileName = `${componentData.name}${componentData.extension}`;
        const filePath = path.join(targetDir, fileName);

        // Check if file already exists
        if (fs.existsSync(filePath)) {
            const choice = await vscode.window.showWarningMessage(
                `File ${fileName} already exists. What would you like to do?`,
                'Overwrite',
                'Create with suffix',
                'Cancel'
            );

            if (choice === 'Cancel') {
                return;
            } else if (choice === 'Create with suffix') {
                const timestamp = Date.now();
                const newFileName = `${componentData.name}_${timestamp}${componentData.extension}`;
                const newFilePath = path.join(targetDir, newFileName);
                await this.writeFile(newFilePath, componentData.code);
                await this.openGeneratedFile(newFilePath);
                return;
            }
        }

        await this.writeFile(filePath, componentData.code);
        await this.openGeneratedFile(filePath);
    }

    private async writeFile(filePath: string, content: string): Promise<void> {
        try {
            fs.writeFileSync(filePath, content, 'utf8');
            
            const relativePath = vscode.workspace.asRelativePath(filePath);
            vscode.window.showInformationMessage(
                `✅ Component created: ${relativePath}`,
                'Open File'
            ).then(selection => {
                if (selection === 'Open File') {
                    this.openGeneratedFile(filePath);
                }
            });
        } catch (error) {
            throw new Error(`Failed to write file: ${error}`);
        }
    }

    private async openGeneratedFile(filePath: string): Promise<void> {
        try {
            const uri = vscode.Uri.file(filePath);
            const document = await vscode.workspace.openTextDocument(uri);
            await vscode.window.showTextDocument(document);
        } catch (error) {
            console.error('Failed to open generated file:', error);
        }
    }

    async generateComponentVariation(
        baseComponent: ComponentInfo,
        variationPrompt: string
    ): Promise<void> {
        try {
            const systemPrompt = `You are an expert at creating component variations. 
            
Base component: ${baseComponent.name}
Hooks used: ${baseComponent.hooks?.join(', ') || 'None'}
Exports: ${baseComponent.exports.join(', ')}

Create a variation of this component with the requested changes while maintaining the core structure and patterns.`;

            const fullPrompt = `Here's the base component to modify:

\`\`\`
// Base component content not available in current structure
\`\`\`

Requested variation: ${variationPrompt}

Generate the modified component:`;

            vscode.window.showInformationMessage('🔄 Creating component variation...');

            const generatedCode = await this.modelClient.generateCompletion(`${systemPrompt}\n\n${fullPrompt}`);
            
            if (generatedCode) {
                const componentData = this.parseGeneratedComponent(generatedCode);
                const targetDir = path.dirname(baseComponent.path);
                await this.createComponentFile(componentData, targetDir);
            }

        } catch (error) {
            console.error('Variation generation failed:', error);
            vscode.window.showErrorMessage(`Variation generation failed: ${error}`);
        }
    }
}