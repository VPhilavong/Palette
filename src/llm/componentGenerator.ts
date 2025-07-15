/**
 * Component Generator
 * 
 * This is the core component generation engine that:
 * - Analyzes codebase patterns and existing components
 * - Generates intelligent, context-aware React components
 * - Determines optimal file placement based on project structure
 * - Handles multiple styling approaches (CSS modules, Tailwind, etc.)
 * - Validates generated code for syntax errors
 * - Creates components with proper imports and exports
 * 
 * Uses OpenAI for intelligent code generation with rich context.
 */

import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { WorkspaceIndex, ComponentInfo } from '../types';
import { PromptBuilder } from './promptBuilder';
import { ModelClient, ModelClientFactory } from './modelClient';
import { CodebaseAnalyzer, CodebasePatterns } from '../codebase/codebaseAnalyzer';
import { CodeValidator } from './codeValidator';
import { CodebaseAnalysisTool, IntentAnalysis, StructuredRequest } from '../extension/tools/node/codebaseAnalysisTool';
import { ILogService } from '../platform/log/common/logService';
import { ConsoleLogService } from '../platform/log/node/consoleLogService';

/**
 * Removes legacy / disallowed patterns from generated output.
 * - Strips `import React …`
 * - Removes `React.` namespace usages (e.g. React.FC)
 * - Throws if run-time PropTypes appear.
 */
function sanitize(code: string): string {
    code = code.replace(/^import\s+React.*\n?/m, "");
    code = code.replace(/\bReact\./g, "");
    if (/prop-types|PropTypes/.test(code)) {
        throw new Error("Generation aborted: prop-types detected in output");
    }
    return code.trimStart();
}

export class ComponentGenerator {
    private promptBuilder: PromptBuilder;
    private modelClient: ModelClient;
    private codebaseAnalyzer: CodebaseAnalyzer;
    private codeValidator: CodeValidator;
    private codebaseAnalysisTool: CodebaseAnalysisTool;
    private logService: ILogService;

    constructor() {
        this.logService = new ConsoleLogService();
        this.promptBuilder = new PromptBuilder();
        this.modelClient = ModelClientFactory.createClient();
        this.codebaseAnalyzer = new CodebaseAnalyzer();
        this.codeValidator = new CodeValidator();
        this.codebaseAnalysisTool = new CodebaseAnalysisTool(this.logService);
    }

    /**
     * NEW: "Ask-to-Build" workflow with NLU intent parsing and clarification
     */
    async askToBuild(
        userPrompt: string,
        workspaceIndex?: WorkspaceIndex | null
    ): Promise<{ 
        success: boolean; 
        needsClarification?: boolean; 
        questions?: string[]; 
        files?: { path: string; content: string; }[];
        structuredRequest?: StructuredRequest;
    }> {
        try {
            if (!workspaceIndex) {
                return {
                    success: false,
                    needsClarification: true,
                    questions: ['Please analyze the project first to enable context-aware generation.']
                };
            }

            this.logService.info('ComponentGenerator: Starting ask-to-build workflow', { prompt: userPrompt.substring(0, 100) });

            // Step 1: Parse natural language into structured request using NLU
            vscode.window.showInformationMessage('🧠 Understanding your request...');
            const structuredRequest = await this.codebaseAnalysisTool.parseStructuredRequest(userPrompt);
            
            this.logService.info('ComponentGenerator: Parsed structured request', { 
                intent: structuredRequest.intent,
                component_name: structuredRequest.component_name,
                confidence: structuredRequest.confidence
            });

            // Step 2: Check if clarification is needed
            const clarificationCheck = await this.codebaseAnalysisTool.needsClarification(structuredRequest);
            
            if (clarificationCheck.needs) {
                this.logService.info('ComponentGenerator: Clarification needed', { questions: clarificationCheck.questions });
                return {
                    success: false,
                    needsClarification: true,
                    questions: clarificationCheck.questions,
                    structuredRequest
                };
            }

            // Step 3: Generate component with structured data
            vscode.window.showInformationMessage(`🎯 Building ${structuredRequest.component_name} (${structuredRequest.component_type})...`);
            
            const files = await this.generateFromStructuredRequest(structuredRequest, workspaceIndex);

            if (files && files.length > 0) {
                // Step 4: Create files on disk
                for (const file of files) {
                    await this.ensureDirectoryExists(path.dirname(file.path));
                    await this.writeFileWithConfirmation(file.path, file.content);
                }

                vscode.window.showInformationMessage(
                    `✅ Created ${structuredRequest.component_name} with ${files.length} file(s)`,
                    'Open Files'
                ).then(selection => {
                    if (selection === 'Open Files' && files.length > 0) {
                        this.openGeneratedFile(files[0].path);
                    }
                });

                return {
                    success: true,
                    files,
                    structuredRequest
                };
            } else {
                return {
                    success: false,
                    needsClarification: true,
                    questions: ['I couldn\'t generate the component. Could you provide more specific details?'],
                    structuredRequest
                };
            }

        } catch (error) {
            this.logService.error('Ask-to-build workflow failed', error);
            return {
                success: false,
                needsClarification: true,
                questions: ['Something went wrong. Could you rephrase your request?']
            };
        }
    }

    /**
     * Generates component files from structured NLU request
     */
    private async generateFromStructuredRequest(
        structuredRequest: StructuredRequest,
        workspaceIndex: WorkspaceIndex
    ): Promise<{ path: string; content: string; }[]> {
        const files: { path: string; content: string; }[] = [];

        try {
            // Analyze codebase patterns for context
            const patterns = await this.codebaseAnalyzer.analyzeWorkspace(workspaceIndex);
            
            // Find similar components for context
            const similarComponents = await this.codebaseAnalyzer.findSimilarComponents(
                `${structuredRequest.component_type} ${structuredRequest.component_name}`, 
                workspaceIndex.components
            );
            
            // Build context information
            const contextInfo = this.codebaseAnalyzer.buildContextFromSimilar(similarComponents, patterns);
            
            // Build system prompt
            const systemPrompt = this.buildSystemPrompt(workspaceIndex, patterns);
            
            // Use the new structured prompt builder
            const fullPrompt = this.promptBuilder.buildStructuredComponentPrompt(
                structuredRequest,
                similarComponents,
                workspaceIndex.project,
                patterns,
                contextInfo
            );

            // Generate component code
            const generatedCode = await this.modelClient.generateCompletion(`${systemPrompt}\n\n${fullPrompt}`);

            if (!generatedCode) {
                this.logService.error('No code generated from model');
                return [];
            }

            // Sanitize and validate the generated code
            const sanitizedCode = sanitize(generatedCode);
            const validationResult = await this.codeValidator.validateAndFixGeneratedCode(sanitizedCode, workspaceIndex);

            if (!validationResult.isValid) {
                this.logService.error('Generated code validation failed', { errors: validationResult.errors });
                return [];
            }

            const finalCode = sanitize(validationResult.fixedCode || sanitizedCode);
            
            // Determine file placement using intent analysis
            const intent = await this.codebaseAnalysisTool.analyzeIntent(
                `${structuredRequest.intent} ${structuredRequest.component_type} ${structuredRequest.component_name}`
            );

            const componentPath = path.join(intent.suggestedPath, intent.fileName);
            files.push({ path: componentPath, content: finalCode });

            // Generate additional files if needed
            if (structuredRequest.styling?.approach === 'css-modules') {
                const styleFile = await this.generateStyleFile(
                    `${structuredRequest.component_type} with ${structuredRequest.styling?.classes?.join(', ') || 'default styling'}`, 
                    intent, 
                    finalCode
                );
                if (styleFile) files.push(styleFile);
            }

            return files;

        } catch (error) {
            this.logService.error('Structured generation failed', error);
            return [];
        }
    }

    /**
     * Generate code **only** (does not write a file).
     */
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
            const patterns = await this.codebaseAnalyzer.analyzeWorkspace(workspaceIndex);
            
            // Find similar components for context using embeddings
            const similarComponents = await this.codebaseAnalyzer.findSimilarComponents(userPrompt, workspaceIndex.components);
            
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

            // Sanitize the generated code
            const sanitizedCode = sanitize(generatedCode);

            // Validate and fix the generated code
            const validationResult = await this.codeValidator.validateAndFixGeneratedCode(
                sanitizedCode, 
                workspaceIndex
            );

            if (!validationResult.isValid) {
                return null;
            }

            // Return the fixed code
            return validationResult.fixedCode || sanitizedCode;

        } catch (error) {
            console.error('Component generation failed:', error);
            return null;
        }
    }

    /**
     * Enhanced generation flow with multi-file support and intelligent file placement.
     */
    async generateComponentWithAnalysis(
        userPrompt: string,
        workspaceIndex?: WorkspaceIndex | null
    ): Promise<{ files: { path: string; content: string; }[]; intent: IntentAnalysis } | undefined> {
        try {
            if (!workspaceIndex) {
                vscode.window.showWarningMessage('Please analyze project first for better context-aware generation');
                return;
            }

            // Analyze intent and determine file placement
            const intent = await this.codebaseAnalysisTool.analyzeIntent(userPrompt);
            
            vscode.window.showInformationMessage(`🎯 Detected intent: ${intent.type} - ${intent.rationale}`);

            // Analyze codebase patterns
            const patterns = await this.codebaseAnalyzer.analyzeWorkspace(workspaceIndex);
            const similarComponents = await this.codebaseAnalyzer.findSimilarComponents(userPrompt, workspaceIndex.components);
            
            // Generate files based on intent
            const files = await this.generateMultipleFiles(userPrompt, intent, patterns, similarComponents, workspaceIndex);
            
            if (files.length === 0) {
                vscode.window.showErrorMessage('Failed to generate any files');
                return;
            }

            // Create all files
            for (const file of files) {
                await this.ensureDirectoryExists(path.dirname(file.path));
                await this.writeFileWithConfirmation(file.path, file.content);
            }

            return { files, intent };

        } catch (error) {
            console.error('Enhanced component generation failed:', error);
            vscode.window.showErrorMessage(`Generation failed: ${error}`);
        }
    }

    /**
     * Full generation flow – creates files on disk.
     */
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
            
            // Find similar components for context using embeddings
            const similarComponents = await this.codebaseAnalyzer.findSimilarComponents(userPrompt, workspaceIndex.components);
            
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

            // Sanitize the generated code
            let sanitizedCode: string;
            try {
                sanitizedCode = sanitize(generatedCode);
            } catch (e: any) {
                vscode.window.showErrorMessage(e.message);
                return;
            }

            vscode.window.showInformationMessage('🔍 Validating and fixing generated code...');

            // Validate and fix the generated code
            const validationResult = await this.codeValidator.validateAndFixGeneratedCode(
                sanitizedCode, 
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

            // Use the fixed code and sanitize it again
            const finalCode = sanitize(validationResult.fixedCode || sanitizedCode);

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
                
                // Handle both relative and absolute paths
                const fullPath = path.isAbsolute(mostCommonDir) 
                    ? mostCommonDir 
                    : path.join(rootPath, mostCommonDir);
                    
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

    private async generateMultipleFiles(
        userPrompt: string,
        intent: IntentAnalysis,
        patterns: CodebasePatterns,
        similarComponents: ComponentInfo[],
        workspaceIndex: WorkspaceIndex
    ): Promise<{ path: string; content: string; }[]> {
        const files: { path: string; content: string; }[] = [];
        
        // Build context for generation
        const contextInfo = this.codebaseAnalyzer.buildContextFromSimilar(similarComponents, patterns);
        const systemPrompt = this.buildSystemPrompt(workspaceIndex, patterns);
        
        switch (intent.type) {
            case 'component':
                const componentFiles = await this.generateComponentFiles(userPrompt, intent, patterns, contextInfo, systemPrompt, workspaceIndex);
                files.push(...componentFiles);
                break;
                
            case 'feature':
                const featureFiles = await this.generateFeatureFiles(userPrompt, intent, patterns, contextInfo, systemPrompt, workspaceIndex);
                files.push(...featureFiles);
                break;
                
            case 'page':
                const pageFiles = await this.generatePageFiles(userPrompt, intent, patterns, contextInfo, systemPrompt, workspaceIndex);
                files.push(...pageFiles);
                break;
                
            default:
                // Single file generation
                const singleFile = await this.generateSingleFile(userPrompt, intent, patterns, contextInfo, systemPrompt, workspaceIndex);
                if (singleFile) files.push(singleFile);
        }
        
        return files;
    }

    private async generateComponentFiles(
        userPrompt: string,
        intent: IntentAnalysis,
        patterns: CodebasePatterns,
        contextInfo: any,
        systemPrompt: string,
        workspaceIndex: WorkspaceIndex
    ): Promise<{ path: string; content: string; }[]> {
        const files: { path: string; content: string; }[] = [];
        
        // Generate main component
        const componentPrompt = this.promptBuilder.buildComponentGenerationPrompt(
            userPrompt,
            [],
            {} as any,
            patterns,
            contextInfo
        );
        
        const componentCode = await this.modelClient.generateCompletion(`${systemPrompt}\n\n${componentPrompt}`);
        
        if (componentCode) {
            const sanitizedCode = sanitize(componentCode);
            const validationResult = await this.codeValidator.validateAndFixGeneratedCode(sanitizedCode, workspaceIndex);
            
            if (validationResult.isValid) {
                const finalCode = sanitize(validationResult.fixedCode || sanitizedCode);
                const componentPath = path.join(intent.suggestedPath, intent.fileName);
                files.push({ path: componentPath, content: finalCode });
                
                // Generate styles if needed
                if (patterns.stylingApproach === 'css-modules') {
                    const styleFile = await this.generateStyleFile(userPrompt, intent, finalCode);
                    if (styleFile) files.push(styleFile);
                }
                
                // Generate stories file if Storybook is detected
                if (this.shouldGenerateStories(patterns)) {
                    const storiesFile = await this.generateStoriesFile(userPrompt, intent, finalCode);
                    if (storiesFile) files.push(storiesFile);
                }
                
                // Generate test file if testing framework is detected
                if (this.shouldGenerateTests(patterns)) {
                    const testFile = await this.generateTestFile(userPrompt, intent, finalCode);
                    if (testFile) files.push(testFile);
                }
            }
        }
        
        return files;
    }

    private async generateFeatureFiles(
        userPrompt: string,
        intent: IntentAnalysis,
        _patterns: CodebasePatterns,
        _contextInfo: any,
        systemPrompt: string,
        _workspaceIndex: WorkspaceIndex
    ): Promise<{ path: string; content: string; }[]> {
        const files: { path: string; content: string; }[] = [];
        
        // Create feature directory
        const featureName = intent.fileName.replace(/\.(tsx|jsx|ts|js)$/, '');
        const featureDir = path.join(intent.suggestedPath, featureName);
        
        // Generate multiple related files for a feature
        const featurePrompt = `Generate a complete feature for: ${userPrompt}
        
This should include:
1. Main component file
2. Types/interfaces file
3. Hook file (if applicable)
4. Index file for exports

Follow the existing patterns in the codebase and create a well-structured feature module.`;
        
        const featureCode = await this.modelClient.generateCompletion(`${systemPrompt}\n\n${featurePrompt}`);
        
        if (featureCode) {
            // Parse the multi-file response and create individual files
            const parsedFiles = this.parseMultiFileResponse(featureCode, featureDir);
            files.push(...parsedFiles);
        }
        
        return files;
    }

    private async generatePageFiles(
        userPrompt: string,
        intent: IntentAnalysis,
        _patterns: CodebasePatterns,
        _contextInfo: any,
        systemPrompt: string,
        workspaceIndex: WorkspaceIndex
    ): Promise<{ path: string; content: string; }[]> {
        const files: { path: string; content: string; }[] = [];
        
        const pagePrompt = `Generate a page component for: ${userPrompt}
        
This should be a complete page with:
1. Page metadata (if Next.js)
2. Layout integration
3. SEO optimization
4. Loading states
5. Error handling

Follow the routing conventions for this project.`;
        
        const pageCode = await this.modelClient.generateCompletion(`${systemPrompt}\n\n${pagePrompt}`);
        
        if (pageCode) {
            const sanitizedCode = sanitize(pageCode);
            const validationResult = await this.codeValidator.validateAndFixGeneratedCode(sanitizedCode, workspaceIndex);
            
            if (validationResult.isValid) {
                const finalCode = sanitize(validationResult.fixedCode || sanitizedCode);
                const pagePath = path.join(intent.suggestedPath, intent.fileName);
                files.push({ path: pagePath, content: finalCode });
            }
        }
        
        return files;
    }

    private async generateSingleFile(
        userPrompt: string,
        intent: IntentAnalysis,
        patterns: CodebasePatterns,
        contextInfo: any,
        systemPrompt: string,
        workspaceIndex: WorkspaceIndex
    ): Promise<{ path: string; content: string; } | null> {
        const prompt = this.promptBuilder.buildComponentGenerationPrompt(
            userPrompt,
            [],
            {} as any,
            patterns,
            contextInfo
        );
        
        const code = await this.modelClient.generateCompletion(`${systemPrompt}\n\n${prompt}`);
        
        if (code) {
            const sanitizedCode = sanitize(code);
            const validationResult = await this.codeValidator.validateAndFixGeneratedCode(sanitizedCode, workspaceIndex);
            
            if (validationResult.isValid) {
                const finalCode = sanitize(validationResult.fixedCode || sanitizedCode);
                const filePath = path.join(intent.suggestedPath, intent.fileName);
                return { path: filePath, content: finalCode };
            }
        }
        
        return null;
    }

    private async generateStyleFile(
        userPrompt: string,
        intent: IntentAnalysis,
        componentCode: string
    ): Promise<{ path: string; content: string; } | null> {
        const styleReferences = this.extractStyleReferences(componentCode);
        
        if (styleReferences.length === 0) return null;
        
        const cssContent = await this.generateStylesForComponent(userPrompt, styleReferences);
        const stylePath = path.join(
            intent.suggestedPath,
            intent.fileName.replace(/\.(tsx|jsx)$/, '.module.css')
        );
        
        return { path: stylePath, content: cssContent };
    }

    private async generateStoriesFile(
        userPrompt: string,
        intent: IntentAnalysis,
        componentCode: string
    ): Promise<{ path: string; content: string; } | null> {
        const componentName = this.extractComponentName(componentCode);
        
        const storiesPrompt = `Generate a Storybook stories file for the ${componentName} component.
        
Component description: ${userPrompt}

Include:
1. Default story
2. Variant stories with different props
3. Interactive controls
4. Documentation

Generate only the stories file code:`;
        
        const storiesCode = await this.modelClient.generateCompletion(storiesPrompt);
        
        if (storiesCode) {
            const storiesPath = path.join(
                intent.suggestedPath,
                intent.fileName.replace(/\.(tsx|jsx)$/, '.stories.tsx')
            );
            
            return { path: storiesPath, content: storiesCode };
        }
        
        return null;
    }

    private async generateTestFile(
        userPrompt: string,
        intent: IntentAnalysis,
        componentCode: string
    ): Promise<{ path: string; content: string; } | null> {
        const componentName = this.extractComponentName(componentCode);
        
        const testPrompt = `Generate a test file for the ${componentName} component.
        
Component description: ${userPrompt}

Include:
1. Render tests
2. Props testing
3. User interaction tests
4. Accessibility tests

Use React Testing Library. Generate only the test file code:`;
        
        const testCode = await this.modelClient.generateCompletion(testPrompt);
        
        if (testCode) {
            const testPath = path.join(
                intent.suggestedPath,
                intent.fileName.replace(/\.(tsx|jsx)$/, '.test.tsx')
            );
            
            return { path: testPath, content: testCode };
        }
        
        return null;
    }

    private shouldGenerateStories(_patterns: CodebasePatterns): boolean {
        // Check if Storybook is configured in the project
        try {
            const packageJsonPath = path.join(vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '', 'package.json');
            if (fs.existsSync(packageJsonPath)) {
                const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
                const deps = { ...packageJson.dependencies, ...packageJson.devDependencies };
                return deps['@storybook/react'] || deps['@storybook/nextjs'];
            }
        } catch (error) {
            console.error('Error checking for Storybook:', error);
        }
        return false;
    }

    private shouldGenerateTests(_patterns: CodebasePatterns): boolean {
        // Check if testing framework is configured
        try {
            const packageJsonPath = path.join(vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '', 'package.json');
            if (fs.existsSync(packageJsonPath)) {
                const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
                const deps = { ...packageJson.dependencies, ...packageJson.devDependencies };
                return deps['@testing-library/react'] || deps['jest'] || deps['vitest'];
            }
        } catch (error) {
            console.error('Error checking for testing framework:', error);
        }
        return false;
    }

    private parseMultiFileResponse(response: string, baseDir: string): { path: string; content: string; }[] {
        const files: { path: string; content: string; }[] = [];
        
        // Simple parser for multi-file responses
        // This would need to be more sophisticated in a real implementation
        const fileBlocks = response.split(/```(?:typescript|tsx|jsx|ts|js)\n/);
        
        for (let i = 1; i < fileBlocks.length; i++) {
            const block = fileBlocks[i];
            const endIndex = block.indexOf('```');
            if (endIndex !== -1) {
                const content = block.substring(0, endIndex);
                const fileName = this.extractFileNameFromContent(content) || `file${i}.tsx`;
                const filePath = path.join(baseDir, fileName);
                files.push({ path: filePath, content: content.trim() });
            }
        }
        
        return files;
    }

    private extractFileNameFromContent(content: string): string | null {
        // Try to extract filename from comments or other indicators
        const fileNameMatch = content.match(/\/\/ (?:File|Filename): (.+)/);
        if (fileNameMatch) {
            return fileNameMatch[1];
        }
        
        // Try to extract from export statements
        const exportMatch = content.match(/export default (\w+)/);
        if (exportMatch) {
            return `${exportMatch[1]}.tsx`;
        }
        
        return null;
    }

    private extractComponentName(code: string): string {
        const componentNameMatch = code.match(/(?:function|const|class)\s+(\w+)/);
        return componentNameMatch?.[1] || 'Component';
    }

    private async ensureDirectoryExists(dirPath: string): Promise<void> {
        try {
            if (!fs.existsSync(dirPath)) {
                fs.mkdirSync(dirPath, { recursive: true });
            }
        } catch (error) {
            console.error('Error creating directory:', error);
        }
    }

    private async writeFileWithConfirmation(filePath: string, content: string): Promise<void> {
        if (fs.existsSync(filePath)) {
            const choice = await vscode.window.showWarningMessage(
                `File ${path.basename(filePath)} already exists. What would you like to do?`,
                'Overwrite',
                'Create with suffix',
                'Skip'
            );

            if (choice === 'Skip') {
                return;
            } else if (choice === 'Create with suffix') {
                const timestamp = Date.now();
                const ext = path.extname(filePath);
                const baseName = path.basename(filePath, ext);
                const dir = path.dirname(filePath);
                const newFileName = `${baseName}_${timestamp}${ext}`;
                filePath = path.join(dir, newFileName);
            }
        }

        await this.writeFile(filePath, content);
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