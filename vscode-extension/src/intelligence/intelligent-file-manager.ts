/**
 * Intelligent File Manager
 * Handles smart file creation, placement, and management using VS Code APIs
 * Following VS Code API best practices: https://code.visualstudio.com/api
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { ProjectStructure, ComponentType, analyzeWorkspaceProject } from './typescript-project-analyzer';

export interface FileCreationRequest {
    content: string;
    language: string;
    suggestedFileName?: string;
    componentType?: 'component' | 'page' | 'hook' | 'utility' | 'type';
}

export interface FileCreationResult {
    filePath: string;
    created: boolean;
    opened: boolean;
    suggestedActions: string[];
    relatedFiles?: string[];
}

export interface SmartFileContext {
    projectStructure: ProjectStructure | null;
    currentFile?: vscode.TextDocument;
    workspaceFolder: vscode.WorkspaceFolder;
}

export class IntelligentFileManager {
    private static instance: IntelligentFileManager;
    private context: SmartFileContext | null = null;

    private constructor() {}

    static getInstance(): IntelligentFileManager {
        if (!IntelligentFileManager.instance) {
            IntelligentFileManager.instance = new IntelligentFileManager();
        }
        return IntelligentFileManager.instance;
    }

    /**
     * Initialize the file manager with current workspace context
     */
    async initialize(): Promise<boolean> {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            vscode.window.showErrorMessage('No workspace folder found. Please open a project first.');
            return false;
        }

        try {
            const analysis = await analyzeWorkspaceProject();
            this.context = {
                projectStructure: analysis?.structure || null,
                currentFile: vscode.window.activeTextEditor?.document,
                workspaceFolder
            };
            return true;
        } catch (error) {
            console.error('Failed to initialize file manager:', error);
            return false;
        }
    }

    /**
     * Intelligently create a file with smart placement and naming
     */
    async createFile(request: FileCreationRequest): Promise<FileCreationResult> {
        if (!this.context) {
            const initialized = await this.initialize();
            if (!initialized) {
                throw new Error('Failed to initialize file manager');
            }
        }

        const { content, language, suggestedFileName, componentType } = request;
        const workspaceFolder = this.context!.workspaceFolder;

        // Determine smart file placement
        const smartPlacement = await this.determineSmartPlacement(content, language, componentType);
        
        // Generate intelligent file name
        const fileName = await this.generateIntelligentFileName(
            content, 
            language, 
            suggestedFileName, 
            smartPlacement.directory
        );

        // Ensure directory exists
        const fullDirectoryPath = path.join(workspaceFolder.uri.fsPath, smartPlacement.directory);
        await this.ensureDirectoryExists(fullDirectoryPath);

        // Create the file
        const fullFilePath = path.join(fullDirectoryPath, fileName);
        const fileUri = vscode.Uri.file(fullFilePath);

        // Check if file already exists
        const fileExists = await this.fileExists(fullFilePath);
        if (fileExists) {
            const choice = await vscode.window.showWarningMessage(
                `File "${fileName}" already exists in ${smartPlacement.directory}. What would you like to do?`,
                'Overwrite',
                'Create with different name',
                'Cancel'
            );

            if (choice === 'Cancel') {
                return {
                    filePath: fullFilePath,
                    created: false,
                    opened: false,
                    suggestedActions: []
                };
            } else if (choice === 'Create with different name') {
                const newFileName = await this.generateUniqueFileName(fullDirectoryPath, fileName);
                const newFullPath = path.join(fullDirectoryPath, newFileName);
                return await this.performFileCreation(
                    vscode.Uri.file(newFullPath),
                    content,
                    smartPlacement,
                    newFileName
                );
            }
        }

        return await this.performFileCreation(fileUri, content, smartPlacement, fileName);
    }

    /**
     * Perform the actual file creation with enhanced features
     */
    private async performFileCreation(
        fileUri: vscode.Uri,
        content: string,
        placement: { directory: string; reasoning: string },
        fileName: string
    ): Promise<FileCreationResult> {
        try {
            // Process content for intelligent enhancements
            const enhancedContent = await this.enhanceFileContent(content, fileName, placement.directory);

            // Write the file
            await vscode.workspace.fs.writeFile(fileUri, Buffer.from(enhancedContent, 'utf8'));

            // Open the file
            const document = await vscode.workspace.openTextDocument(fileUri);
            const editor = await vscode.window.showTextDocument(document);

            // Position cursor intelligently
            await this.positionCursorIntelligently(editor, enhancedContent);

            // Show success notification with options
            const action = await vscode.window.showInformationMessage(
                `✅ Created ${fileName} in ${placement.directory}`,
                'Show in Explorer',
                'Add to Git',
                'Create Related Files'
            );

            // Handle user action
            if (action === 'Show in Explorer') {
                await vscode.commands.executeCommand('revealFileInOS', fileUri);
            } else if (action === 'Add to Git') {
                await this.addToGit(fileUri);
            } else if (action === 'Create Related Files') {
                await this.suggestRelatedFiles(fileName, placement.directory, content);
            }

            // Determine suggested actions
            const suggestedActions = await this.generateSuggestedActions(fileName, content, placement.directory);

            // Find related files
            const relatedFiles = await this.findRelatedFiles(fileName, content);

            return {
                filePath: fileUri.fsPath,
                created: true,
                opened: true,
                suggestedActions,
                relatedFiles
            };

        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to create file: ${error.message}`);
            throw error;
        }
    }

    /**
     * Determine smart file placement based on content analysis
     */
    private async determineSmartPlacement(
        content: string,
        language: string,
        componentType?: string
    ): Promise<{ directory: string; reasoning: string }> {
        // Analyze content to determine optimal placement
        const isComponent = this.isReactComponent(content, language);
        const isPage = this.isPageComponent(content);
        const isHook = this.isReactHook(content);
        const isUtility = this.isUtilityFunction(content);
        const isTypeDefinition = this.isTypeDefinition(content, language);
        const isShadcnComponent = this.isShadcnUIComponent(content);

        // Check project structure for existing patterns
        const projectStructure = this.context?.projectStructure;
        const hasPages = projectStructure?.pages && projectStructure.pages.length > 0;
        const hasComponentsDir = projectStructure?.components && projectStructure.components.length > 0;

        // Determine placement based on analysis
        if (isShadcnComponent) {
            return {
                directory: 'src/components/ui',
                reasoning: 'Detected shadcn/ui component pattern'
            };
        }

        if (isPage) {
            const pageDir = hasPages && projectStructure?.pages[0].includes('app/') ? 'src/app' : 'src/pages';
            return {
                directory: pageDir,
                reasoning: 'Detected page component'
            };
        }

        if (isComponent) {
            return {
                directory: 'src/components',
                reasoning: 'Detected React component'
            };
        }

        if (isHook) {
            return {
                directory: 'src/hooks',
                reasoning: 'Detected custom React hook'
            };
        }

        if (isUtility) {
            return {
                directory: 'src/lib',
                reasoning: 'Detected utility function'
            };
        }

        if (isTypeDefinition) {
            return {
                directory: 'src/types',
                reasoning: 'Detected TypeScript type definitions'
            };
        }

        // Default fallback based on component type hint
        switch (componentType) {
            case 'component':
                return { directory: 'src/components', reasoning: 'User specified component type' };
            case 'page':
                return { directory: 'src/pages', reasoning: 'User specified page type' };
            case 'hook':
                return { directory: 'src/hooks', reasoning: 'User specified hook type' };
            case 'utility':
                return { directory: 'src/lib', reasoning: 'User specified utility type' };
            case 'type':
                return { directory: 'src/types', reasoning: 'User specified type definition' };
            default:
                return { directory: 'src/components', reasoning: 'Default component placement' };
        }
    }

    /**
     * Generate intelligent file name based on content analysis
     */
    private async generateIntelligentFileName(
        content: string,
        language: string,
        suggestedName?: string,
        targetDirectory?: string
    ): Promise<string> {
        // If user provided a name, use it (with proper extension)
        if (suggestedName) {
            return this.ensureProperExtension(suggestedName, language);
        }

        // Extract component name from content
        const extractedName = this.extractComponentNameFromContent(content);
        if (extractedName) {
            return this.ensureProperExtension(extractedName, language);
        }

        // Generate name based on directory context
        if (targetDirectory?.includes('hooks')) {
            return this.ensureProperExtension('useCustomHook', language);
        }

        if (targetDirectory?.includes('types')) {
            return this.ensureProperExtension('types', language);
        }

        if (targetDirectory?.includes('lib') || targetDirectory?.includes('utils')) {
            return this.ensureProperExtension('utils', language);
        }

        // Default naming
        return this.ensureProperExtension('Component', language);
    }

    /**
     * Enhance file content with intelligent imports and boilerplate
     */
    private async enhanceFileContent(content: string, fileName: string, directory: string): Promise<string> {
        let enhancedContent = content;

        // Add missing imports for React components
        if (this.isReactComponent(content, 'tsx') && !content.includes('import React')) {
            if (this.needsReactImport(content)) {
                enhancedContent = `import React from 'react';\n${enhancedContent}`;
            }
        }

        // Add shadcn/ui utility imports if needed
        if (this.isShadcnUIComponent(content) && !content.includes('import { cn }')) {
            enhancedContent = `import { cn } from "@/lib/utils";\n${enhancedContent}`;
        }

        // Add proper TypeScript imports
        if (fileName.endsWith('.tsx') || fileName.endsWith('.ts')) {
            enhancedContent = this.addTypeScriptEnhancements(enhancedContent);
        }

        return enhancedContent;
    }

    /**
     * Position cursor intelligently in the new file
     */
    private async positionCursorIntelligently(editor: vscode.TextEditor, content: string): Promise<void> {
        const lines = content.split('\n');
        
        // Find a good position for the cursor (inside component function, after props, etc.)
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            
            // Position cursor inside component function body
            if (line.includes('return (') || line.includes('return<')) {
                const position = new vscode.Position(i + 1, 4); // Indent by 4 spaces
                editor.selection = new vscode.Selection(position, position);
                return;
            }
            
            // Position cursor after interface definition
            if (line.includes('interface') && line.includes('Props')) {
                const position = new vscode.Position(i + 2, 0);
                editor.selection = new vscode.Selection(position, position);
                return;
            }
        }
    }

    /**
     * Generate suggested follow-up actions
     */
    private async generateSuggestedActions(fileName: string, content: string, directory: string): Promise<string[]> {
        const actions: string[] = [];

        if (this.isReactComponent(content, 'tsx')) {
            actions.push('Create Storybook story');
            actions.push('Generate component tests');
            actions.push('Add to component index');
        }

        if (this.isPageComponent(content)) {
            actions.push('Add to routing');
            actions.push('Create page metadata');
            actions.push('Generate SEO tags');
        }

        if (directory.includes('components')) {
            actions.push('Export from barrel file');
            actions.push('Create variant styles');
        }

        actions.push('Format with Prettier');
        actions.push('Run ESLint');

        return actions;
    }

    /**
     * Find files related to the newly created file
     */
    private async findRelatedFiles(fileName: string, content: string): Promise<string[]> {
        const relatedFiles: string[] = [];
        const baseName = path.basename(fileName, path.extname(fileName));
        const workspaceFolder = this.context?.workspaceFolder;

        if (!workspaceFolder) return relatedFiles;

        try {
            // Find test files
            const testFiles = await vscode.workspace.findFiles(
                new vscode.RelativePattern(workspaceFolder, `**/*${baseName}*.{test,spec}.{ts,tsx,js,jsx}`),
                null,
                5
            );
            relatedFiles.push(...testFiles.map(uri => uri.fsPath));

            // Find story files
            const storyFiles = await vscode.workspace.findFiles(
                new vscode.RelativePattern(workspaceFolder, `**/*${baseName}*.{story,stories}.{ts,tsx,js,jsx}`),
                null,
                5
            );
            relatedFiles.push(...storyFiles.map(uri => uri.fsPath));

            // Find style files
            const styleFiles = await vscode.workspace.findFiles(
                new vscode.RelativePattern(workspaceFolder, `**/*${baseName}*.{css,scss,module.css}`),
                null,
                5
            );
            relatedFiles.push(...styleFiles.map(uri => uri.fsPath));

        } catch (error) {
            console.log('Error finding related files:', error);
        }

        return relatedFiles;
    }

    // Utility methods for content analysis
    private isReactComponent(content: string, language: string): boolean {
        return (language === 'tsx' || language === 'jsx') &&
               (content.includes('export default') || content.includes('export const')) &&
               (content.includes('return (') || content.includes('return<') || content.includes('JSX.Element'));
    }

    private isPageComponent(content: string): boolean {
        const pageIndicators = ['Page', 'Screen', 'Route', 'View'];
        return pageIndicators.some(indicator => content.includes(indicator));
    }

    private isReactHook(content: string): boolean {
        return content.includes('use') && 
               (content.includes('useState') || content.includes('useEffect') || content.includes('export const use'));
    }

    private isUtilityFunction(content: string): boolean {
        return content.includes('export') &&
               (content.includes('function') || content.includes('=>')) &&
               !this.isReactComponent(content, 'tsx');
    }

    private isTypeDefinition(content: string, language: string): boolean {
        return language === 'ts' &&
               (content.includes('interface') || content.includes('type') || content.includes('enum'));
    }

    private isShadcnUIComponent(content: string): boolean {
        const shadcnPatterns = ['cn(', 'cva(', 'VariantProps', 'forwardRef', '@radix-ui'];
        return shadcnPatterns.some(pattern => content.includes(pattern));
    }

    private extractComponentNameFromContent(content: string): string | null {
        const patterns = [
            /export\s+default\s+function\s+(\w+)/,
            /export\s+const\s+(\w+):\s*React\.FC/,
            /export\s+const\s+(\w+)\s*=/,
            /const\s+(\w+):\s*React\.FC/,
            /function\s+(\w+)\s*\(/
        ];

        for (const pattern of patterns) {
            const match = content.match(pattern);
            if (match) return match[1];
        }

        return null;
    }

    private needsReactImport(content: string): boolean {
        return content.includes('JSX') || content.includes('<') || content.includes('React.');
    }

    private addTypeScriptEnhancements(content: string): string {
        // Add React types if component doesn't have them
        if (this.isReactComponent(content, 'tsx') && !content.includes('React.FC') && !content.includes(': FC')) {
            // Could add React.FC type annotations here
        }
        return content;
    }

    private ensureProperExtension(fileName: string, language: string): string {
        const extMap: Record<string, string> = {
            'tsx': '.tsx',
            'jsx': '.jsx',
            'ts': '.ts',
            'js': '.js',
            'typescript': '.ts',
            'javascript': '.js',
            'typescriptreact': '.tsx',
            'javascriptreact': '.jsx'
        };

        const extension = extMap[language] || '.tsx';
        
        if (fileName.endsWith('.tsx') || fileName.endsWith('.jsx') || 
            fileName.endsWith('.ts') || fileName.endsWith('.js')) {
            return fileName;
        }
        
        return fileName + extension;
    }

    private async generateUniqueFileName(directory: string, originalName: string): Promise<string> {
        const baseName = path.basename(originalName, path.extname(originalName));
        const extension = path.extname(originalName);
        let counter = 1;

        while (await this.fileExists(path.join(directory, `${baseName}-${counter}${extension}`))) {
            counter++;
        }

        return `${baseName}-${counter}${extension}`;
    }

    // VS Code API utility methods
    private async fileExists(filePath: string): Promise<boolean> {
        try {
            await vscode.workspace.fs.stat(vscode.Uri.file(filePath));
            return true;
        } catch {
            return false;
        }
    }

    private async ensureDirectoryExists(dirPath: string): Promise<void> {
        try {
            await vscode.workspace.fs.createDirectory(vscode.Uri.file(dirPath));
        } catch {
            // Directory might already exist
        }
    }

    private async addToGit(fileUri: vscode.Uri): Promise<void> {
        try {
            const terminal = vscode.window.createTerminal('Git Add');
            terminal.sendText(`git add "${fileUri.fsPath}"`);
            terminal.dispose();
        } catch {
            // Git might not be available
        }
    }

    private async suggestRelatedFiles(fileName: string, directory: string, content: string): Promise<void> {
        const suggestions: string[] = [];
        const baseName = path.basename(fileName, path.extname(fileName));

        if (this.isReactComponent(content, 'tsx')) {
            suggestions.push(`${baseName}.test.tsx`);
            suggestions.push(`${baseName}.stories.tsx`);
            suggestions.push(`${baseName}.module.css`);
        }

        if (suggestions.length > 0) {
            const choice = await vscode.window.showQuickPick(suggestions, {
                placeHolder: 'Select related files to create',
                canPickMany: true
            });

            // User can implement creation of selected related files
            if (choice) {
                vscode.window.showInformationMessage(`Selected: ${choice}`);
            }
        }
    }
}

// Factory function for easy access
export function getIntelligentFileManager(): IntelligentFileManager {
    return IntelligentFileManager.getInstance();
}