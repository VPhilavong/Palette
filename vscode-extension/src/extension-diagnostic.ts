/**
 * Diagnostic Extension - Ultra-minimal version
 * Zero dependencies, pure VS Code API only
 * Purpose: Test basic extension activation and webview functionality
 */

import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    console.log('🩺 DIAGNOSTIC: Extension activation started');
    
    // Track activation success
    try {
        // Only register the commands we actually implement
        const diagnosticCommand = vscode.commands.registerCommand('palette.diagnostic', () => {
            console.log('🩺 DIAGNOSTIC: Command executed');
            vscode.window.showInformationMessage('✅ DIAGNOSTIC: Extension is working!');
        });
        
        const webviewCommand = vscode.commands.registerCommand('palette.openDiagnostic', () => {
            console.log('🩺 DIAGNOSTIC: Opening webview');
            openDiagnosticWebview();
        });
        
        context.subscriptions.push(diagnosticCommand, webviewCommand);
        
        console.log('🩺 DIAGNOSTIC: Commands registered successfully');
        console.log('🩺 DIAGNOSTIC: Extension activated successfully');
        
        // Show success message
        vscode.window.showInformationMessage('🩺 Diagnostic extension activated');
        
    } catch (error) {
        console.error('🩺 DIAGNOSTIC: Activation failed:', error);
        vscode.window.showErrorMessage(`Diagnostic activation failed: ${error}`);
    }
}

function openDiagnosticWebview() {
    console.log('🩺 DIAGNOSTIC: Creating webview panel');
    
    try {
        const panel = vscode.window.createWebviewPanel(
            'diagnosticWebview',
            '🎨 Palette AI (Diagnostic with AI)',
            vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );
        
        console.log('🩺 DIAGNOSTIC: Webview panel created');
        
        panel.webview.html = getDiagnosticHtml();
        console.log('🩺 DIAGNOSTIC: HTML set');
        
        // Handle messages from webview
        panel.webview.onDidReceiveMessage(
            async message => {
                console.log('🩺 DIAGNOSTIC: Received message from webview:', message);
                
                switch (message.type) {
                    case 'test-message':
                        console.log('🩺 DIAGNOSTIC: Test message received:', message.content);
                        
                        // Send processing status
                        panel.webview.postMessage({
                            type: 'status',
                            content: '🤖 AI is processing your request...',
                            timestamp: new Date().toISOString()
                        });
                        
                        // Generate intelligent AI response based on user input
                        const responseData = await generateIntelligentResponse(message.content);
                        
                        // Send AI response with potential file creation
                        panel.webview.postMessage({
                            type: 'ai-response-with-code',
                            content: responseData.content,
                            codeBlocks: responseData.codeBlocks,
                            timestamp: new Date().toISOString()
                        });
                        
                        console.log('🩺 DIAGNOSTIC: AI response sent');
                        break;
                    
                    case 'approve-file-creation':
                        console.log('🩺 DIAGNOSTIC: File creation approved:', message.filepath);
                        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
                        if (workspaceFolder && message.filepath && message.content) {
                            try {
                                // Check and install missing shadcn components BEFORE creating file
                                await checkAndInstallShadcnComponents(message.content, workspaceFolder);
                                
                                const fullPath = vscode.Uri.joinPath(workspaceFolder.uri, message.filepath);
                                // Ensure directory exists
                                const dir = vscode.Uri.joinPath(fullPath, '..');
                                try {
                                    await vscode.workspace.fs.createDirectory(dir);
                                } catch { }
                                // Write file
                                await vscode.workspace.fs.writeFile(fullPath, Buffer.from(message.content, 'utf8'));
                                
                                // Verify and rename file if needed based on actual component name
                                const actualComponentName = extractActualComponentName(message.content);
                                let finalPath = fullPath;
                                
                                if (actualComponentName && actualComponentName !== 'GeneratedComponent') {
                                    const currentFileName = message.filepath.split('/').pop()?.replace(/\.(tsx?|jsx?)$/, '');
                                    if (currentFileName !== actualComponentName) {
                                        // Rename file to match component name
                                        const newFilename = message.filepath.replace(currentFileName || 'GeneratedComponent', actualComponentName);
                                        const newPath = vscode.Uri.joinPath(workspaceFolder.uri, newFilename);
                                        
                                        try {
                                            await vscode.workspace.fs.rename(fullPath, newPath);
                                            finalPath = newPath;
                                            console.log(`✅ Renamed file to: ${newFilename}`);
                                            
                                            // Update the filepath for later use
                                            message.filepath = newFilename;
                                        } catch (error) {
                                            console.error('Failed to rename file:', error);
                                        }
                                    }
                                }
                                
                                // Handle route integration for page files AFTER file is fully created and renamed
                                if (message.filepath.includes('/pages/')) {
                                    console.log('🔀 Handling route integration for created page file...');
                                    await handleRouteIntegration([{
                                        code: message.content,
                                        language: 'tsx',
                                        filename: message.filepath
                                    }]);
                                }
                                
                                // Open the created file AFTER all operations are complete
                                const doc = await vscode.workspace.openTextDocument(finalPath);
                                await vscode.window.showTextDocument(doc);
                                
                                // Notify success
                                panel.webview.postMessage({
                                    type: 'file-created',
                                    filepath: message.filepath,
                                    timestamp: new Date().toISOString()
                                });
                                vscode.window.showInformationMessage(`✅ Created: ${message.filepath}`);
                            } catch (error) {
                                console.error('Failed to create file:', error);
                                vscode.window.showErrorMessage(`Failed to create file: ${(error as Error).message}`);
                            }
                        }
                        break;
                        
                    default:
                        console.log('🩺 DIAGNOSTIC: Unknown message type:', message.type);
                }
            },
            undefined,
            []
        );
        
        console.log('🩺 DIAGNOSTIC: Message handler set up');
        
        // Show success
        vscode.window.showInformationMessage('🎨 Palette AI diagnostic ready!');
        
    } catch (error) {
        console.error('🩺 DIAGNOSTIC: Webview creation failed:', error);
        vscode.window.showErrorMessage(`Webview failed: ${error}`);
    }
}

// Fetch project context from Python backend
async function fetchProjectContext(projectPath: string): Promise<any> {
    try {
        const response = await fetch('http://localhost:8765/api/context', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                projectPath: projectPath,
                analysisType: 'quick'
            })
        });
        
        if (!response.ok) {
            throw new Error(`Context API failed: ${response.status}`);
        }
        
        const result = await response.json();
        return result.success ? result.context : getFallbackContext(projectPath);
    } catch (error) {
        console.warn('🔄 Python backend unavailable, using fallback context:', error);
        return getFallbackContext(projectPath);
    }
}

function getFallbackContext(projectPath: string): any {
    return {
        project: {
            path: projectPath,
            framework: "vite",
            styling: "tailwind",
            hasTypeScript: true,
            hasTailwind: true,
            hasShadcnUI: true
        },
        existingComponents: {
            uiLibrary: ["button", "card", "input", "badge", "dialog"],
            custom: [],
            pages: []
        },
        recommendations: {
            importPatterns: [
                'import { Button } from "@/components/ui/button"',
                'import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"'
            ],
            bestPractices: [
                "Always use shadcn/ui components when available",
                "Use design tokens instead of hardcoded colors", 
                "Generate TypeScript code",
                "Follow React best practices"
            ]
        }
    };
}

async function generateWithAI(userMessage: string, context: any): Promise<string> {
    try {
        // Get API key and model from VS Code settings
        const config = vscode.workspace.getConfiguration('palette');
        const apiKey = config.get<string>('openaiApiKey');
    const modelName = config.get<string>('defaultModel') || 'gpt-5-mini-2025-08-07';
        
        if (!apiKey || apiKey.trim() === '') {
            throw new Error('OpenAI API key not configured. Please set it in VS Code settings: Palette > Openai Api Key');
        }
        
        // Import AI SDK - handle if not available
        const { createOpenAI } = await import('@ai-sdk/openai');
        const { generateText } = await import('ai');
        
        const systemPrompt = buildSystemPrompt(context);
        
        // Create OpenAI client with API key
        const openaiClient = createOpenAI({
            apiKey: apiKey
        });
        
        const result = await generateText({
            model: openaiClient('gpt-5-mini-2025-08-07'),
            system: systemPrompt,
            prompt: userMessage,
            temperature: 0.7
        });
        
        return result.text;
    } catch (error) {
        console.error('🤖 AI generation failed:', error);
        throw error;
    }
}

function buildSystemPrompt(context: any): string {
    const { project, existingComponents, recommendations } = context;
    
    return `You are Palette, an expert React/TypeScript code generator specializing in shadcn/ui components.

## PROJECT CONTEXT:
- Framework: ${project.framework}
- TypeScript: ${project.hasTypeScript ? 'Yes' : 'No'}  
- Tailwind CSS: ${project.hasTailwind ? 'Yes' : 'No'}
- shadcn/ui: ${project.hasShadcnUI ? 'Yes' : 'No'}

## AVAILABLE COMPONENTS:
- UI Library: ${existingComponents.uiLibrary.join(', ')}
- Custom Components: ${existingComponents.custom.join(', ') || 'None'}

## IMPORT PATTERNS:
${recommendations.importPatterns.join('\n')}

## REQUIREMENTS:
${recommendations.bestPractices.join('\n')}

## CODE GENERATION RULES:
1. Generate COMPLETE, working React components
2. Use shadcn/ui components exclusively
3. Include proper TypeScript interfaces
4. Use semantic HTML and proper accessibility
5. Return response in this format:

\`\`\`markdown
# [Component/Page Name]

[Brief description]

## Features:
- Feature 1
- Feature 2

## Usage:
[Usage instructions]

\`\`\`

\`\`\`tsx
[Complete TypeScript React code]
\`\`\`

IMPORTANT: Always generate complete, production-ready code that follows the project's patterns.`;
}

function parseAIResponse(aiResponse: string): {content: string, codeBlocks: Array<{code: string, language: string, filename: string}>} {
    const codeBlocks: Array<{code: string, language: string, filename: string}> = [];
    
    // Extract code blocks from AI response
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    let match;
    
    while ((match = codeBlockRegex.exec(aiResponse)) !== null) {
        const language = match[1] || 'tsx';
        const code = match[2].trim();
        
        if (code.length > 0) {
            // Extract component name with multiple patterns
            let componentName = 'GeneratedComponent';
            
            // Try different patterns to extract component name
            const patterns = [
                // export const ComponentName: React.FC<Props> = 
                /export\s+const\s+(\w+):\s*React\.FC(?:<\w+>)?\s*=/,
                // export const ComponentName: FC<Props> = 
                /export\s+const\s+(\w+):\s*FC(?:<\w+>)?\s*=/,
                // const ComponentName: React.FC = (without export, common pattern)
                /const\s+(\w+):\s*React\.FC\s*=/,
                // export default function ComponentName
                /export\s+default\s+function\s+(\w+)/,
                // export function ComponentName  
                /export\s+function\s+(\w+)/,
                // export const ComponentName = 
                /export\s+const\s+(\w+)\s*=/,
                // function ComponentName (for export default at end)
                /function\s+(\w+)\s*\(/,
                // const ComponentName = (arrow function)
                /const\s+(\w+)\s*=\s*\(/,
                // Handle JSX components (look for JSX return)
                /const\s+(\w+)\s*=.*?=>\s*\(/s,
                // Look for export default ComponentName at the end
                /export\s+default\s+(\w+)$/m
            ];
            
            for (const pattern of patterns) {
                const match = code.match(pattern);
                if (match && match[1] && match[1] !== 'App' && /^[A-Z]\w*/.test(match[1])) {
                    componentName = match[1];
                    console.log(`📝 Extracted component name: ${componentName} using pattern: ${pattern}`);
                    break;
                }
            }
            
            console.log(`📄 Component name extraction result: ${componentName}`);
            if (componentName === 'GeneratedComponent') {
                console.warn('⚠️  Could not extract component name, using default. Code preview:');
                console.warn(code.substring(0, 200) + '...');
            }
            
            // Determine file extension
            const isTypescript = language === 'tsx' || language === 'ts';
            const extension = isTypescript ? '.tsx' : '.jsx';
            
            // Determine file path based on content and component name
            let filepath = `src/components/${componentName}${extension}`;
            
            // Check if this should be a page component
            if (componentName.toLowerCase().includes('page') || 
                componentName.toLowerCase().includes('dashboard') || 
                componentName.toLowerCase().includes('profile') ||
                code.includes('export default')) {
                filepath = `src/pages/${componentName}${extension}`;
            }
            
            codeBlocks.push({
                code,
                language,
                filename: filepath
            });
        }
    }
    
    // Clean up content (remove code blocks)
    const cleanContent = aiResponse.replace(codeBlockRegex, '').trim();
    
    return {
        content: cleanContent || "## Generated successfully!\n\nYour component has been created with shadcn/ui integration.",
        codeBlocks
    };
}

async function handleRouteIntegration(codeBlocks: Array<{code: string, language: string, filename: string}>): Promise<void> {
    console.log('🔀 handleRouteIntegration called with', codeBlocks.length, 'code blocks');
    
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        console.log('❌ No workspace folder found');
        return;
    }

    const projectPath = workspaceFolder.uri.fsPath;
    console.log('🔍 Project path:', projectPath);

    // Check for page components that need route registration
    for (const block of codeBlocks) {
        console.log('📄 Checking block:', {
            filename: block.filename,
            hasExportDefault: block.code.includes('export default'),
            hasConst: block.code.includes('const'),
            hasPage: block.code.includes('Page')
        });
        
        if (block.filename.includes('/pages/')) {
            console.log('✅ Found page component in block:', block.filename);
            
            // Extract component name for route creation (reuse the same logic)
            let componentName = 'UnknownPage';
            
            const routePatterns = [
                // export const ComponentName: React.FC<Props> = 
                /export\s+const\s+(\w+):\s*React\.FC(?:<\w+>)?\s*=/,
                // export const ComponentName: FC<Props> = 
                /export\s+const\s+(\w+):\s*FC(?:<\w+>)?\s*=/,
                // const ComponentName: React.FC = (without export, common pattern)
                /const\s+(\w+):\s*React\.FC\s*=/,
                // export default function ComponentName
                /export\s+default\s+function\s+(\w+)/,
                // export function ComponentName
                /export\s+function\s+(\w+)/,
                // export const ComponentName = 
                /export\s+const\s+(\w+)\s*=/,
                // function ComponentName (in case of export default at the end)
                /function\s+(\w+)\s*\(/,
                // const ComponentName = (arrow function)
                /const\s+(\w+)\s*=\s*\(/,
                // Handle JSX components
                /const\s+(\w+)\s*=.*?=>\s*\(/s,
                // Look for export default ComponentName at the end
                /export\s+default\s+(\w+)$/m
            ];
            
            for (const pattern of routePatterns) {
                const match = block.code.match(pattern);
                if (match && match[1] && match[1] !== 'App' && /^[A-Z]\w*/.test(match[1])) {
                    componentName = match[1];
                    console.log(`🔀 Route component name extracted: ${componentName}`);
                    break;
                }
            }
            
            console.log(`🔀 Final route component name: ${componentName}`);
            
            // Generate route path from component name
            let routePath = '/' + componentName.toLowerCase().replace('page', '');
            if (routePath === '/home' || routePath === '/' || componentName.toLowerCase() === 'home') {
                routePath = '/';
            }
            
            // For nested routes, also generate the relative path
            const relativePath = routePath === '/' ? '' : routePath.substring(1);
            
            // Generate label from component name
            const label = componentName.replace('Page', '').replace(/([A-Z])/g, ' $1').trim();
            
            // Create import path from filename
            const importPath = './' + block.filename.replace('src/', '').replace(/\.(tsx?|jsx?)$/, '');
            
            try {
                console.log(`🔀 Adding route: ${routePath} -> ${componentName}`, {
                    projectPath,
                    route: routePath,
                    component: componentName,
                    importPath: importPath,
                    label: label
                });
                
                // Use Node.js http module instead of fetch for VS Code compatibility
                const http = await import('http');
                
                const postData = JSON.stringify({
                    projectPath,
                    route: routePath,
                    component: componentName,
                    importPath: importPath,
                    label: null, // Don't auto-add to navigation
                    appPath: 'src/App.tsx',
                    navigationPath: 'src/components/Navigation.tsx',
                    index: routePath === '/'
                });
                
                const result = await new Promise<any>((resolve, reject) => {
                    const options = {
                        hostname: 'localhost',
                        port: 8765,
                        path: '/api/routes/add',
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Content-Length': Buffer.byteLength(postData)
                        }
                    };
                    
                    const req = http.request(options, (res) => {
                        let data = '';
                        res.on('data', (chunk) => {
                            data += chunk;
                        });
                        res.on('end', () => {
                            try {
                                resolve(JSON.parse(data));
                            } catch (e) {
                                reject(new Error(`Failed to parse response: ${data}`));
                            }
                        });
                    });
                    
                    req.on('error', (e) => {
                        reject(e);
                    });
                    
                    req.write(postData);
                    req.end();
                });
                console.log('🔀 Route API response:', result);
                
                if (result.success) {
                    console.log(`✅ Route added successfully: ${routePath}`);
                    
                    // Show success message to user
                    vscode.window.showInformationMessage(
                        `✅ Route added: ${routePath} → ${componentName} (Navigation not auto-updated)`,
                        'Open App.tsx'
                    ).then(selection => {
                        if (selection === 'Open App.tsx') {
                            const appPath = vscode.Uri.joinPath(workspaceFolder.uri, 'src/App.tsx');
                            vscode.window.showTextDocument(appPath);
                        }
                    });
                } else {
                    console.error('❌ Route API returned error:', result.error);
                    vscode.window.showWarningMessage(`Failed to add route: ${result.error}`);
                }
                
            } catch (error) {
                console.error('❌ Failed to add route:', error);
                vscode.window.showWarningMessage(`Failed to add route for ${componentName}: ${error}`);
            }
        }
    }
}

async function checkAndInstallShadcnComponents(code: string, workspaceFolder: vscode.WorkspaceFolder): Promise<void> {
    console.log('🔍 Checking for missing shadcn/ui components...');
    
    try {
        // Extract all @/components/ui imports
        const importRegex = /@\/components\/ui\/(\w+)/g;
        const imports = new Set<string>();
        let match;
        
        while ((match = importRegex.exec(code)) !== null) {
            imports.add(match[1]);
        }
        
        if (imports.size === 0) {
            console.log('✅ No shadcn/ui components to check');
            return;
        }
        
        // Check which components exist
        const missing: string[] = [];
        for (const component of imports) {
            const componentPath = vscode.Uri.joinPath(workspaceFolder.uri, `src/components/ui/${component}.tsx`);
            try {
                await vscode.workspace.fs.stat(componentPath);
                console.log(`✅ Component exists: ${component}`);
            } catch {
                missing.push(component);
                console.log(`❌ Component missing: ${component}`);
            }
        }
        
        // Auto-install missing components
        if (missing.length > 0) {
            const installMessage = `Installing missing shadcn components: ${missing.join(', ')}`;
            console.log(`📦 ${installMessage}`);
            
            // Show progress notification and get user confirmation
            const install = await vscode.window.showInformationMessage(
                `Missing shadcn/ui components: ${missing.join(', ')}. Install automatically?`,
                'Yes, Install',
                'No, Skip'
            );
            
            if (install === 'Yes, Install') {
                // Execute installation command in terminal
                const terminal = vscode.window.createTerminal({
                    name: 'shadcn installer',
                    cwd: workspaceFolder.uri.fsPath
                });
                
                terminal.show();
                
                // Install components one by one to avoid issues
                for (const component of missing) {
                    terminal.sendText(`npx shadcn-ui@latest add ${component}`);
                    // Small delay between commands
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
                
                vscode.window.showInformationMessage(
                    `📦 Installing shadcn components in terminal. Check terminal for progress.`
                );
            } else {
                vscode.window.showWarningMessage(
                    `⚠️ Missing components not installed. You may need to install manually: ${missing.join(', ')}`
                );
            }
        } else {
            console.log('✅ All required shadcn/ui components are already installed');
        }
    } catch (error) {
        console.error('❌ Error checking shadcn components:', error);
        vscode.window.showWarningMessage(
            `Failed to check shadcn components: ${error}. You may need to install them manually.`
        );
    }
}

async function generateIntelligentResponse(userMessage: string): Promise<{content: string, codeBlocks: Array<{code: string, language: string, filename: string}>}> {
    console.log('🧠 HYBRID: Processing AI request with Python context:', userMessage);
    
    try {
        // Step 1: Fetch project context from Python backend
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        const projectPath = workspaceFolder?.uri.fsPath || '/home/vphilavong/Projects/test-project-palette';
        
        console.log('🔍 Fetching context for project:', projectPath);
        const context = await fetchProjectContext(projectPath);
        console.log('✅ Context received:', context);
        
        // Step 2: Generate with AI using context
        console.log('🤖 Generating with AI...');
        const aiResponse = await generateWithAI(userMessage, context);
        console.log('✅ AI response received');
        
        // Step 3: Parse response into content + code blocks
        const parsed = parseAIResponse(aiResponse);
        console.log('✅ Response parsed, found', parsed.codeBlocks.length, 'code blocks');
        
        // Step 4: Handle route integration for page components
        if (parsed.codeBlocks.length > 0) {
            console.log('🔀 Checking for page components to register routes...');
            await handleRouteIntegration(parsed.codeBlocks);
        }
        
        return parsed;
        
    } catch (error) {
        console.error('❌ Hybrid generation failed:', error);
        
        // Fallback to simple response
        return {
            content: `# ⚠️ Generation Error

I encountered an error while generating your request: "${userMessage}"

**Error:** ${error instanceof Error ? error.message : 'Unknown error'}

**Possible Solutions:**
- Ensure Python backend is running: \`uvicorn main:app --port 8765\`
- Check VS Code settings for API keys
- Try a simpler request to test connectivity

**Fallback:** I can still help you with basic guidance - please let me know what you'd like to create!`,
            codeBlocks: []
        };
    }
}

function extractActualComponentName(code: string): string | null {
    // Enhanced patterns to extract actual component name from code
    const patterns = [
        // export const ComponentName: React.FC<Props> = 
        /export\s+const\s+(\w+):\s*React\.FC(?:<\w+>)?\s*=/,
        // export const ComponentName: FC<Props> = 
        /export\s+const\s+(\w+):\s*FC(?:<\w+>)?\s*=/,
        // const ComponentName: React.FC = (without export, common pattern)
        /const\s+(\w+):\s*React\.FC\s*=/,
        // export default function ComponentName
        /export\s+default\s+function\s+(\w+)/,
        // export function ComponentName  
        /export\s+function\s+(\w+)/,
        // export const ComponentName = 
        /export\s+const\s+(\w+)\s*=/,
        // function ComponentName (for export default at end)
        /function\s+(\w+)\s*\(/,
        // const ComponentName = (arrow function)
        /const\s+(\w+)\s*=\s*\(/,
        // Look for export default ComponentName at the end
        /export\s+default\s+(\w+)$/m
    ];
    
    for (const pattern of patterns) {
        const match = code.match(pattern);
        if (match && match[1] && match[1] !== 'App' && /^[A-Z]\w*/.test(match[1])) {
            console.log(`✅ Extracted actual component name: ${match[1]}`);
            return match[1];
        }
    }
    
    console.log('⚠️ Could not extract actual component name from code');
    return null;
}

function extractComponentName(message: string): string {
    // Extract potential component names from the message
    const words = message.split(/\s+/);
    const componentWords = words.filter(word => 
        ['button', 'card', 'form', 'input', 'modal', 'header', 'footer', 'nav', 'menu'].includes(word.toLowerCase())
    );
    
    if (componentWords.length > 0) {
        const name = componentWords[0];
        return name.charAt(0).toUpperCase() + name.slice(1).toLowerCase();
    }
    
    return 'GeneratedComponent';
}

function getDiagnosticHtml(): string {
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Diagnostic Extension</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            color: var(--vscode-foreground);
            background: var(--vscode-editor-background);
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
        }
        .status {
            background: var(--vscode-inputValidation-infoBackground);
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .test-area {
            background: var(--vscode-input-background);
            border: 1px solid var(--vscode-input-border);
            border-radius: 5px;
            padding: 20px;
            margin: 20px 0;
        }
        input {
            width: 100%;
            padding: 10px;
            background: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border: 1px solid var(--vscode-input-border);
            border-radius: 3px;
            margin: 10px 0;
        }
        button {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 10px 20px;
            border-radius: 3px;
            cursor: pointer;
            margin: 5px;
        }
        button:hover {
            background: var(--vscode-button-hoverBackground);
        }
        #messages {
            background: var(--vscode-editor-background);
            border: 1px solid var(--vscode-input-border);
            min-height: 200px;
            padding: 15px;
            margin: 20px 0;
            font-family: monospace;
            white-space: pre-wrap;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🩺 Diagnostic Extension Test</h1>
        
        <div class="status">
            <strong>Status:</strong> <span id="status">Initializing...</span>
        </div>
        
        <div class="test-area">
            <h3>Message Test</h3>
            <p>Type a message and click send to test webview communication:</p>
            
            <input type="text" id="messageInput" placeholder="Type test message here..." />
            <br>
            <button id="sendButton">Send Test Message</button>
            <button id="clearButton">Clear Messages</button>
        </div>
        
        <div>
            <h3>Communication Log</h3>
            <div id="messages"></div>
        </div>
    </div>

    <script>
        console.log('🩺 DIAGNOSTIC: Webview script starting');
        
        const vscode = acquireVsCodeApi();
        const statusEl = document.getElementById('status');
        const messagesEl = document.getElementById('messages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const clearButton = document.getElementById('clearButton');
        
        // Update status
        statusEl.textContent = 'Ready';
        logMessage('WEBVIEW: Script loaded successfully');
        
        function logMessage(message) {
            const timestamp = new Date().toLocaleTimeString();
            messagesEl.textContent += timestamp + ' - ' + message + '\\n';
            messagesEl.scrollTop = messagesEl.scrollHeight;
            console.log('🩺 DIAGNOSTIC:', message);
        }
        
        function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) {
                logMessage('WEBVIEW: No message to send');
                return;
            }
            
            logMessage('WEBVIEW: Sending message: ' + message);
            
            vscode.postMessage({
                type: 'test-message',
                content: message
            });
            
            messageInput.value = '';
            statusEl.textContent = 'Message sent, waiting for response...';
        }
        
        function clearMessages() {
            messagesEl.textContent = '';
            logMessage('WEBVIEW: Messages cleared');
        }
        
        // Event listeners
        sendButton.addEventListener('click', sendMessage);
        clearButton.addEventListener('click', clearMessages);
        
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        // Handle messages from extension
        window.addEventListener('message', event => {
            const message = event.data;
            logMessage('WEBVIEW: Received from extension: ' + message.type);
            
            switch (message.type) {
                case 'echo-response':
                    statusEl.textContent = 'Response received';
                    logMessage('EXTENSION ECHO: ' + message.content);
                    break;
                    
                case 'status':
                    statusEl.textContent = 'AI Processing...';
                    logMessage('STATUS: ' + message.content);
                    break;
                    
                case 'ai-response':
                case 'ai-response-with-code':
                    statusEl.textContent = 'Ready';
                    logMessage('AI RESPONSE RECEIVED (' + message.content.length + ' characters)');
                    
                    // Display the AI response in a formatted way
                    const responseDiv = document.createElement('div');
                    responseDiv.style.cssText = 'background: var(--vscode-editor-background); border: 1px solid var(--vscode-input-border); border-radius: 5px; padding: 15px; margin: 20px 0; max-height: 600px; overflow-y: auto; font-family: -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.5;';
                    
                    // Basic markdown rendering
                    let htmlContent = message.content
                        .replace(/^# (.*$)/gim, '<h1 style="color: var(--vscode-textLink-foreground); margin: 15px 0 10px 0; font-size: 1.5em;">$1</h1>')
                        .replace(/^## (.*$)/gim, '<h2 style="color: var(--vscode-textLink-foreground); margin: 15px 0 8px 0; font-size: 1.3em;">$2</h2>')
                        .replace(/^### (.*$)/gim, '<h3 style="color: var(--vscode-textLink-foreground); margin: 10px 0 6px 0; font-size: 1.1em;">$3</h3>')
                        .replace(/\\*\\*(.*?)\\*\\*/g, '<strong style="color: var(--vscode-textLink-foreground);">$1</strong>')
                        .replace(/\\*(.*?)\\*/g, '<em>$1</em>')
                        .replace(/\`\`\`[\\w]*\\n([\\s\\S]*?)\`\`\`/g, '<pre style="background: var(--vscode-textBlockQuote-background); padding: 12px; border-radius: 4px; overflow-x: auto; margin: 10px 0;"><code>$1</code></pre>')
                        .replace(/\`([^\`]+)\`/g, '<code style="background: var(--vscode-textBlockQuote-background); padding: 2px 4px; border-radius: 3px;">$1</code>')
                        .replace(/- \\*\\*(.*?)\\*\\*/g, '<li style="margin: 4px 0;"><strong style="color: var(--vscode-textLink-foreground);">$1</strong></li>')
                        .replace(/- (.*)/g, '<li style="margin: 4px 0;">$1</li>')
                        .replace(/\\n/g, '<br>');
                    
                    responseDiv.innerHTML = htmlContent;
                    
                    // Add file creation UI if code blocks are present
                    if (message.codeBlocks && message.codeBlocks.length > 0) {
                        message.codeBlocks.forEach((block, index) => {
                            const fileApprovalDiv = createFileApprovalUI(block.code, block.language, block.filename, index);
                            responseDiv.appendChild(fileApprovalDiv);
                        });
                    }
                    
                    messagesEl.appendChild(responseDiv);
                    messagesEl.scrollTop = messagesEl.scrollHeight;
                    break;
                    
                case 'file-created':
                    logMessage('FILE CREATED: ' + message.filepath);
                    const successDiv = document.createElement('div');
                    successDiv.style.cssText = 'background: var(--vscode-inputValidation-infoBackground); color: var(--vscode-inputValidation-infoForeground); padding: 10px; border-radius: 4px; margin: 10px 0; border-left: 3px solid var(--vscode-inputValidation-infoBorder);';
                    successDiv.innerHTML = '✅ <strong>File created:</strong> ' + message.filepath;
                    messagesEl.appendChild(successDiv);
                    messagesEl.scrollTop = messagesEl.scrollHeight;
                    break;
                    
                default:
                    logMessage('WEBVIEW: Unknown message type: ' + message.type);
            }
        });
        
        function createFileApprovalUI(code, language, suggestedFilename, index) {
            const div = document.createElement('div');
            div.style.cssText = 'background: var(--vscode-input-background); border: 2px solid var(--vscode-focusBorder); border-radius: 8px; padding: 15px; margin: 15px 0;';
            
            // Header
            const headerDiv = document.createElement('div');
            headerDiv.style.cssText = 'display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; font-weight: bold; color: var(--vscode-foreground);';
            headerDiv.innerHTML = '📄 Generated Code - Ready to Create File';
            
            // Filename input
            const pathDiv = document.createElement('div');
            pathDiv.style.cssText = 'display: flex; align-items: center; margin-bottom: 10px;';
            
            const pathLabel = document.createElement('label');
            pathLabel.textContent = 'File path: ';
            pathLabel.style.cssText = 'margin-right: 10px; color: var(--vscode-foreground);';
            
            const pathInput = document.createElement('input');
            pathInput.type = 'text';
            pathInput.value = suggestedFilename;
            pathInput.id = 'filepath-' + index;
            pathInput.style.cssText = 'flex: 1; padding: 5px 8px; background: var(--vscode-input-background); color: var(--vscode-input-foreground); border: 1px solid var(--vscode-input-border); border-radius: 3px;';
            
            pathDiv.appendChild(pathLabel);
            pathDiv.appendChild(pathInput);
            
            // Code display
            const codeDiv = document.createElement('div');
            codeDiv.style.cssText = 'background: var(--vscode-textBlockQuote-background); border: 1px solid var(--vscode-panel-border); border-radius: 4px; padding: 12px; max-height: 300px; overflow-y: auto; margin-bottom: 10px; font-family: monospace; font-size: 13px; white-space: pre-wrap;';
            codeDiv.textContent = code;
            
            // Action buttons
            const actionsDiv = document.createElement('div');
            actionsDiv.style.cssText = 'display: flex; gap: 10px; justify-content: flex-end;';
            
            const cancelBtn = document.createElement('button');
            cancelBtn.textContent = 'Cancel';
            cancelBtn.style.cssText = 'padding: 6px 12px; border-radius: 4px; border: none; cursor: pointer; font-weight: 500; background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground);';
            cancelBtn.onclick = function() { div.style.display = 'none'; };
            
            const createBtn = document.createElement('button');
            createBtn.textContent = '✅ Create File';
            createBtn.style.cssText = 'padding: 6px 12px; border-radius: 4px; border: none; cursor: pointer; font-weight: 500; background: var(--vscode-button-background); color: var(--vscode-button-foreground);';
            createBtn.onclick = function() {
                const filepath = pathInput.value.trim();
                if (!filepath) {
                    alert('Please enter a file path');
                    return;
                }
                
                vscode.postMessage({
                    type: 'approve-file-creation',
                    filepath: filepath,
                    content: code,
                    index: index
                });
                
                div.style.display = 'none';
                logMessage('FILE CREATION APPROVED: ' + filepath);
            };
            
            actionsDiv.appendChild(cancelBtn);
            actionsDiv.appendChild(createBtn);
            
            div.appendChild(headerDiv);
            div.appendChild(pathDiv);
            div.appendChild(codeDiv);
            div.appendChild(actionsDiv);
            
            return div;
        }
        
        logMessage('WEBVIEW: Event listeners set up');
        messageInput.focus();
    </script>
</body>
</html>`;
}

export function deactivate() {
    console.log('🩺 DIAGNOSTIC: Extension deactivated');
}