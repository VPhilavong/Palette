import * as vscode from 'vscode';

// Import PaletteService for real AI generation
let PaletteService: any;
try {
    PaletteService = require('./paletteService').PaletteService;
    console.log('✅ PaletteService imported successfully');
} catch (error) {
    console.log('⚠️ PaletteService not available, using mock responses:', (error as Error).message);
}

export function activate(context: vscode.ExtensionContext) {
    console.log('🧪 Minimal Palette extension activated');

    // Initialize PaletteService if available
    let paletteService: any = null;
    if (PaletteService) {
        try {
            paletteService = new PaletteService();
            console.log('🎨 PaletteService initialized successfully');
        } catch (error) {
            console.log('⚠️ Failed to initialize PaletteService:', (error as Error).message);
        }
    }

    // Register the unified command with real AI generation
    const unifiedCommand = vscode.commands.registerCommand('palette.openUnified', async () => {
        try {
            const panel = vscode.window.createWebviewPanel(
                'paletteUnified',
                '🎨 Palette: Unified System',
                vscode.ViewColumn.One,
                {
                    enableScripts: true,
                    retainContextWhenHidden: true
                }
            );

            panel.webview.html = getMinimalWebviewHtml();
            
            // Handle messages from webview with real AI generation
            panel.webview.onDidReceiveMessage(async (message) => {
                if (message.type === 'user-message') {
                    console.log('📝 User message received:', message.content);
                    
                    // Update UI to show processing
                    panel.webview.postMessage({
                        type: 'status',
                        message: '🤖 AI is processing your request...',
                        timestamp: new Date().toISOString()
                    });

                    try {
                        if (paletteService) {
                            // Use real AI generation via PaletteService
                            console.log('🚀 Calling PaletteService.conversationalGenerate...');
                            const response = await paletteService.conversationalGenerate(message.content);
                            console.log('📦 Raw response:', JSON.stringify(response).substring(0, 200));
                            
                            // Extract the actual response content
                            let responseContent = '';
                            if (typeof response === 'string') {
                                responseContent = response;
                            } else if (response && typeof response === 'object') {
                                // Try different fields where content might be
                                responseContent = response.response || response.content || response.message || response.text || '';
                                
                                // If still empty, check for nested response
                                if (!responseContent && response.data) {
                                    responseContent = response.data.response || response.data.content || '';
                                }
                                
                                // If still empty, stringify the whole object
                                if (!responseContent) {
                                    responseContent = JSON.stringify(response, null, 2);
                                }
                            }
                            
                            console.log('📝 Extracted content:', responseContent.substring(0, 200));
                            
                            // Check if response contains code blocks for file creation
                            const codeBlockRegex = /```(?:tsx?|jsx?|javascript|typescript)?\n([\s\S]*?)```/g;
                            const codeBlocks = [];
                            let match;
                            
                            while ((match = codeBlockRegex.exec(responseContent)) !== null) {
                                codeBlocks.push({
                                    code: match[1].trim(),
                                    language: match[0].match(/```(\w+)/)?.[1] || 'typescript'
                                });
                            }
                            
                            // Send response to webview with proper formatting
                            if (codeBlocks.length > 0) {
                                // Response contains code - send with file creation option
                                panel.webview.postMessage({
                                    type: 'ai-response-with-code',
                                    content: responseContent,
                                    codeBlocks: codeBlocks,
                                    timestamp: new Date().toISOString(),
                                    metadata: { model: 'palette-ai', success: true, hasCode: true }
                                });
                            } else {
                                // Regular response without code
                                panel.webview.postMessage({
                                    type: 'ai-response',
                                    content: responseContent,
                                    timestamp: new Date().toISOString(),
                                    metadata: { model: 'palette-ai', success: true }
                                });
                            }
                            
                            console.log('✅ AI response sent successfully');
                        } else {
                            // Fallback: Enhanced mock response that simulates real AI
                            const mockResponse = generateMockAIResponse(message.content);
                            panel.webview.postMessage({
                                type: 'ai-response',
                                content: mockResponse,
                                timestamp: new Date().toISOString(),
                                metadata: { model: 'mock-ai', success: true }
                            });
                            console.log('🧪 Mock AI response sent');
                        }
                    } catch (error) {
                        console.error('❌ Error in AI generation:', error);
                        panel.webview.postMessage({
                            type: 'error',
                            error: `AI Generation Error: ${(error as Error).message}`,
                            timestamp: new Date().toISOString()
                        });
                    }
                } else if (message.type === 'approve-file-creation') {
                    // Handle file creation approval from user
                    console.log('📄 File creation approved:', message.filepath);
                    
                    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
                    if (workspaceFolder && message.filepath && message.content) {
                        try {
                            const fullPath = vscode.Uri.joinPath(workspaceFolder.uri, message.filepath);
                            
                            // Ensure directory exists
                            const dir = vscode.Uri.joinPath(fullPath, '..');
                            try {
                                await vscode.workspace.fs.createDirectory(dir);
                            } catch {}
                            
                            // Write file
                            await vscode.workspace.fs.writeFile(fullPath, Buffer.from(message.content, 'utf8'));
                            
                            // Open the created file
                            const doc = await vscode.workspace.openTextDocument(fullPath);
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
                }
            });

            vscode.window.showInformationMessage('🎨 Palette Unified System opened successfully!');
            console.log('✅ UnifiedPalettePanel opened successfully with AI integration');
        } catch (error) {
            console.error('❌ Error creating minimal UnifiedPalettePanel:', error);
            vscode.window.showErrorMessage(`Failed to open Palette: ${error}`);
        }
    });

    // Register a simple test command  
    const testCommand = vscode.commands.registerCommand('palette.test', () => {
        vscode.window.showInformationMessage('🧪 Palette extension is working!');
        console.log('✅ Test command executed successfully');
    });

    context.subscriptions.push(unifiedCommand, testCommand);
    console.log('🎉 Minimal Palette extension activation complete');
}

function generateMockAIResponse(userMessage: string): string {
    const message = userMessage.toLowerCase();
    
    // Intelligent mock responses based on user intent
    if (message.includes('create') || message.includes('build') || message.includes('generate')) {
        if (message.includes('component') || message.includes('button') || message.includes('card')) {
            return `# 🎨 Component Generated Successfully!

I understand you want to create a UI component. Here's what I would do:

## **What I'm creating:**
- Modern React component with TypeScript
- Responsive design with Tailwind CSS
- Clean, accessible code following best practices

## **Next steps to enable real AI generation:**
1. **Configure API Keys** - Set your OpenAI or Anthropic API key in VS Code settings
2. **Install Dependencies** - The Python backend needs to be properly configured
3. **Test Connection** - Once configured, I'll generate actual working code!

## **For now, here's a sample of what I would generate:**

\`\`\`tsx
import React from 'react';

export interface ComponentProps {
  title?: string;
  variant?: 'primary' | 'secondary';
}

export const GeneratedComponent: React.FC<ComponentProps> = ({ 
  title = "Generated Component", 
  variant = "primary" 
}) => {
  return (
    <div className={\`p-6 rounded-lg \${variant === 'primary' ? 'bg-blue-500 text-white' : 'bg-gray-100'}\`}>
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="mt-2">This component was generated by Palette AI!</p>
    </div>
  );
};
\`\`\`

**🔧 To enable real generation, please configure your API keys in VS Code settings.**`;
        } else if (message.includes('page') || message.includes('landing')) {
            return `# 🚀 Landing Page Design Ready!

I'm ready to create a complete landing page for you! Here's my approach:

## **Page Structure I'll Build:**
- Hero section with compelling headline
- Feature showcase with icons
- Social proof/testimonials  
- Call-to-action sections
- Responsive footer

## **Technologies I'll Use:**
- React + TypeScript
- Tailwind CSS for styling
- shadcn/ui components
- Framer Motion for animations

## **To generate the actual code:**
Please set up your API keys so I can create the real implementation!

**🎯 Once configured, just ask me:** "Create a SaaS landing page with pricing tiers" and I'll generate the complete code.`;
        }
    } else if (message.includes('help') || message.includes('what') || message.includes('how')) {
        return `# 👋 Welcome to Palette AI!

I'm your AI-powered design companion, ready to help you create amazing React components and pages!

## **What I can do:**
- **Generate React Components** - Buttons, cards, forms, navigation, etc.
- **Create Complete Pages** - Landing pages, dashboards, e-commerce layouts
- **Build Features** - Authentication forms, pricing sections, hero banners
- **Match Your Style** - I analyze your existing code to maintain consistency

## **To get started:**
1. **Set up API keys** - Configure OpenAI or Anthropic API key in VS Code settings
2. **Describe what you want** - "Create a pricing card with 3 tiers"
3. **I'll generate the code** - Complete, working React components
4. **Iterate together** - Refine and improve through conversation

## **Example requests:**
- "Create a modern hero section with gradient background"
- "Build a pricing table with monthly/yearly toggle"  
- "Generate a contact form with validation"
- "Design a product card for an e-commerce site"

**🔑 Configure your API key to unlock full AI generation capabilities!**`;
    }
    
    return `# 🤖 AI Response

I received your message: "${userMessage}"

**Current Status:** Mock mode - API keys not configured yet.

To enable real AI generation:
1. Set your **OPENAI_API_KEY** or **ANTHROPIC_API_KEY** in VS Code settings
2. The Python backend will then provide real AI-powered responses
3. Ask me to create components, pages, or features!

**Example:** "Create a modern button component with multiple variants"

**🔧 Configure API keys to unlock full capabilities!**`;
}

function getMinimalWebviewHtml(): string {
    return `
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Palette Unified System</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            color: var(--vscode-foreground);
            background: var(--vscode-editor-background);
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .chat-container {
            border: 1px solid var(--vscode-panel-border);
            border-radius: 8px;
            height: 400px;
            display: flex;
            flex-direction: column;
        }
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 15px;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 6px;
        }
        .user-message {
            background: var(--vscode-input-background);
            border-left: 3px solid var(--vscode-button-background);
        }
        .ai-message {
            background: var(--vscode-editor-selectionBackground);
            border-left: 3px solid var(--vscode-charts-blue);
        }
        .status-message {
            background: var(--vscode-inputValidation-warningBackground);
            color: var(--vscode-inputValidation-warningForeground);
            border-left: 3px solid var(--vscode-inputValidation-warningBorder);
            font-style: italic;
            padding: 8px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .error-message {
            background: var(--vscode-inputValidation-errorBackground);
            color: var(--vscode-inputValidation-errorForeground);
            border-left: 3px solid var(--vscode-inputValidation-errorBorder);
            padding: 8px;
            margin: 10px 0;
            border-radius: 4px;
        }
        /* Code blocks and markdown support */
        .message-content {
            line-height: 1.5;
        }
        .message-content h1, .message-content h2, .message-content h3 {
            margin: 10px 0 5px 0;
            color: var(--vscode-foreground);
        }
        .message-content pre {
            background: var(--vscode-textBlockQuote-background);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            padding: 10px;
            overflow-x: auto;
            margin: 10px 0;
        }
        .message-content code {
            background: var(--vscode-textBlockQuote-background);
            padding: 2px 4px;
            border-radius: 3px;
            font-family: monospace;
        }
        .message-content ul, .message-content ol {
            margin: 5px 0;
            padding-left: 20px;
        }
        /* File approval dialog */
        .file-approval {
            background: var(--vscode-editor-background);
            border: 2px solid var(--vscode-focusBorder);
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }
        .file-approval-header {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            font-weight: bold;
            color: var(--vscode-foreground);
        }
        .file-approval-path {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        .file-approval-path input {
            flex: 1;
            padding: 5px;
            background: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border: 1px solid var(--vscode-input-border);
            border-radius: 3px;
            margin-left: 10px;
        }
        .file-approval-code {
            background: var(--vscode-textBlockQuote-background);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            padding: 10px;
            max-height: 300px;
            overflow-y: auto;
            margin-bottom: 10px;
            font-family: monospace;
            font-size: 12px;
            white-space: pre;
        }
        .file-approval-actions {
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }
        .file-approval-actions button {
            padding: 6px 12px;
            border-radius: 4px;
            border: none;
            cursor: pointer;
            font-weight: 500;
        }
        .approve-btn {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
        }
        .approve-btn:hover {
            background: var(--vscode-button-hoverBackground);
        }
        .reject-btn {
            background: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
        }
        .reject-btn:hover {
            background: var(--vscode-button-secondaryHoverBackground);
        }
        .input-area {
            display: flex;
            padding: 15px;
            border-top: 1px solid var(--vscode-panel-border);
        }
        .input-area input {
            flex: 1;
            padding: 8px 12px;
            border: 1px solid var(--vscode-input-border);
            background: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border-radius: 4px;
            margin-right: 10px;
        }
        .input-area button {
            padding: 8px 16px;
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .input-area button:hover {
            background: var(--vscode-button-hoverBackground);
        }
        .status {
            text-align: center;
            padding: 10px;
            font-style: italic;
            color: var(--vscode-descriptionForeground);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎨 Palette: Unified System</h1>
            <p>Minimal working version - Dependencies fixed!</p>
        </div>
        
        <div class="status" id="status">
            ✅ System Ready - Type a message to test
        </div>
        
        <div class="chat-container">
            <div class="messages" id="messages">
                <div class="ai-message">
                    <strong>Palette AI:</strong> 🎨 Welcome! I'm your AI-powered design companion.
                    <br><br>
                    I can help you create React components, pages, and complete features. Just describe what you want to build!
                    <br><br>
                    <strong>Try asking me:</strong>
                    <br>• "Create a modern button component"
                    <br>• "Build a pricing card with 3 tiers" 
                    <br>• "Generate a hero section"
                    <br><br>
                    <em>💡 Configure your OpenAI/Anthropic API key in VS Code settings for real AI generation!</em>
                </div>
            </div>
            
            <div class="input-area">
                <input type="text" id="messageInput" placeholder="Type your message here..." />
                <button id="sendButton">Send</button>
            </div>
        </div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        
        function sendMessage() {
            console.log('sendMessage() called');
            const input = document.getElementById('messageInput');
            
            if (!input) {
                console.error('Input element not found!');
                return;
            }
            
            const message = input.value.trim();
            console.log('Message:', message);
            
            if (!message) {
                console.log('No message to send');
                return;
            }
            
            // Add user message to chat
            addMessage(message, 'user');
            
            // Send to extension
            vscode.postMessage({
                type: 'user-message',
                content: message
            });
            
            // Clear input
            input.value = '';
            
            // Update status
            const statusEl = document.getElementById('status');
            if (statusEl) {
                statusEl.textContent = '🤖 Processing...';
            }
            
            console.log('Message sent successfully');
        }
        
        function addMessage(content, sender, codeBlocks = null) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + sender + '-message';
            
            // Parse markdown-like content for better display
            let formattedContent = content;
            if (sender === 'ai') {
                formattedContent = parseMarkdown(content);
            }
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.innerHTML = '<strong>' + (sender === 'user' ? 'You' : 'Palette') + ':</strong><br>' + formattedContent;
            messageDiv.appendChild(contentDiv);
            
            // Add file approval UI if code blocks are present
            if (codeBlocks && codeBlocks.length > 0) {
                codeBlocks.forEach((block, index) => {
                    const approvalDiv = createFileApprovalUI(block.code, block.language, index);
                    messageDiv.appendChild(approvalDiv);
                });
            }
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function parseMarkdown(text) {
            // Basic markdown parsing
            return text
                // Headers
                .replace(/^### (.*$)/gim, '<h3>$1</h3>')
                .replace(/^## (.*$)/gim, '<h2>$1</h2>')
                .replace(/^# (.*$)/gim, '<h1>$1</h1>')
                // Bold
                .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
                // Italic
                .replace(/\*([^*]+)\*/g, '<em>$1</em>')
                // Code blocks
                .replace(/\`\`\`(\w+)?\n([\s\S]*?)\`\`\`/g, function(match, lang, code) {
                    return '<pre><code>' + escapeHtml(code) + '</code></pre>';
                })
                // Inline code
                .replace(/\`([^\`]+)\`/g, '<code>$1</code>')
                // Line breaks
                .replace(/\n/g, '<br>');
        }
        
        function escapeHtml(text) {
            const map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            };
            return text.replace(/[&<>"']/g, m => map[m]);
        }
        
        function createFileApprovalUI(code, language, index) {
            const div = document.createElement('div');
            div.className = 'file-approval';
            div.id = 'file-approval-' + index;
            
            // Create header
            const headerDiv = document.createElement('div');
            headerDiv.className = 'file-approval-header';
            headerDiv.textContent = '📄 Generated Code - Approve File Creation';
            div.appendChild(headerDiv);
            
            // Create path input section
            const pathDiv = document.createElement('div');
            pathDiv.className = 'file-approval-path';
            
            const pathLabel = document.createElement('label');
            pathLabel.textContent = 'Path:';
            pathDiv.appendChild(pathLabel);
            
            const pathInput = document.createElement('input');
            pathInput.type = 'text';
            pathInput.id = 'filepath-' + index;
            
            // Suggest a filename based on the code
            let suggestedPath = 'src/components/GeneratedComponent.tsx';
            const componentMatch = code.match(/(?:export\\s+)?(?:default\\s+)?(?:function|const)\\s+(\\w+)/);
            if (componentMatch) {
                suggestedPath = 'src/components/' + componentMatch[1] + '.tsx';
            }
            pathInput.value = suggestedPath;
            pathDiv.appendChild(pathInput);
            
            div.appendChild(pathDiv);
            
            // Create code display
            const codeDiv = document.createElement('div');
            codeDiv.className = 'file-approval-code';
            codeDiv.textContent = code;
            div.appendChild(codeDiv);
            
            // Create action buttons
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'file-approval-actions';
            
            const rejectBtn = document.createElement('button');
            rejectBtn.className = 'reject-btn';
            rejectBtn.textContent = 'Cancel';
            rejectBtn.onclick = function() { rejectFile(index); };
            actionsDiv.appendChild(rejectBtn);
            
            const approveBtn = document.createElement('button');
            approveBtn.className = 'approve-btn';
            approveBtn.textContent = 'Create File';
            approveBtn.onclick = function() { approveFile(index, code); };
            actionsDiv.appendChild(approveBtn);
            
            div.appendChild(actionsDiv);
            
            return div;
        }
        
        function approveFile(index, code) {
            const filepath = document.getElementById('filepath-' + index).value;
            if (!filepath) {
                alert('Please enter a file path');
                return;
            }
            
            // Send approval to extension
            vscode.postMessage({
                type: 'approve-file-creation',
                filepath: filepath,
                content: code,
                index: index
            });
            
            // Hide the approval UI
            const approvalDiv = document.getElementById('file-approval-' + index);
            if (approvalDiv) {
                approvalDiv.style.display = 'none';
            }
        }
        
        function rejectFile(index) {
            // Hide the approval UI
            const approvalDiv = document.getElementById('file-approval-' + index);
            if (approvalDiv) {
                approvalDiv.style.display = 'none';
            }
        }
        
        // Handle messages from extension
        window.addEventListener('message', event => {
            const message = event.data;
            
            switch (message.type) {
                case 'ai-response':
                    addMessage(message.content, 'ai');
                    document.getElementById('status').textContent = '✅ System Ready';
                    break;
                    
                case 'ai-response-with-code':
                    // AI response that contains code blocks for potential file creation
                    addMessage(message.content, 'ai', message.codeBlocks);
                    document.getElementById('status').textContent = '✅ System Ready - Code Generated';
                    break;
                    
                case 'status':
                    addStatusMessage(message.message);
                    break;
                    
                case 'error':
                    addErrorMessage(message.error);
                    document.getElementById('status').textContent = '❌ Error occurred';
                    break;
                    
                case 'file-created':
                    addStatusMessage('✅ File created: ' + message.filepath);
                    break;
                    
                default:
                    console.log('Unknown message type:', message.type);
            }
        });
        
        function addStatusMessage(message) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'status-message';
            messageDiv.innerHTML = message;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            // Remove status messages after 3 seconds
            setTimeout(() => {
                if (messageDiv.parentNode) {
                    messageDiv.parentNode.removeChild(messageDiv);
                }
            }, 3000);
        }
        
        function addErrorMessage(error) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'error-message';
            messageDiv.innerHTML = '<strong>Error:</strong> ' + error;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        // Set up event listeners when DOM is ready
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM loaded, setting up event listeners');
            
            // Button click handler
            const sendButton = document.getElementById('sendButton');
            if (sendButton) {
                sendButton.addEventListener('click', sendMessage);
                console.log('Send button click listener added');
            }
            
            // Enter key handler
            const messageInput = document.getElementById('messageInput');
            if (messageInput) {
                messageInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        sendMessage();
                    }
                });
                console.log('Enter key listener added');
            }
            
            console.log('All event listeners ready');
        });
        
        // Fallback: Set up events immediately in case DOMContentLoaded already fired
        setTimeout(function() {
            console.log('Running fallback event setup');
            const sendButton = document.getElementById('sendButton');
            const messageInput = document.getElementById('messageInput');
            
            if (sendButton && !sendButton.onclick) {
                console.log('Setting up fallback send button handler');
                sendButton.onclick = function() {
                    console.log('Fallback send button clicked');
                    sendMessage();
                };
            }
            
            if (messageInput && !messageInput.onkeypress) {
                console.log('Setting up fallback enter key handler');
                messageInput.onkeypress = function(e) {
                    console.log('Fallback key pressed:', e.key);
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        sendMessage();
                    }
                };
            }
            
            // Try to focus the input
            if (messageInput) {
                messageInput.focus();
                console.log('Input focused');
            }
        }, 200);
    </script>
</body>
</html>
    `;
}

export function deactivate() {
    console.log('🧪 Minimal Palette extension deactivated');
}