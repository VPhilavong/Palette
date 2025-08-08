/**
 * Webview HTML Template Generator
 * Provides clean HTML generation for the chatbot panel
 */

export class WebviewTemplate {
    /**
     * Generate the complete HTML for the webview
     */
    static generateHTML(
        scriptUri: string,
        playgroundUri: string,
        styleUri: string,
        nonce: string
    ): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Palette AI Assistant</title>
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'nonce-${nonce}'; style-src 'unsafe-inline'; img-src https: data:; font-src data:;">
    <script type="module" nonce="${nonce}" src="${playgroundUri}"></script>
    <script type="module" nonce="${nonce}" src="${scriptUri}"></script>
    <link href="${styleUri}" rel="stylesheet">
</head>
<body>
    <div class="chat-container">
        ${this.generateToolbar()}
        ${this.generateMessagesArea()}
        ${this.generateInputArea()}
    </div>
    ${this.generateScript(nonce)}
</body>
</html>`;
    }

    /**
     * Generate toolbar HTML
     */
    private static generateToolbar(): string {
        return `
        <!-- Toolbar -->
        <div class="toolbar">
            <vscode-button id="toolsBtn" appearance="secondary" size="small">Tools</vscode-button>
            <vscode-button id="mcpBtn" appearance="secondary" size="small">MCP</vscode-button>
            <vscode-button id="clearBtn" appearance="secondary" size="small">Clear</vscode-button>
            
            <div class="status-indicators">
                <div class="status-indicator">
                    <span>🛠️</span>
                    <span id="toolCount">0</span>
                </div>
                <div class="status-indicator">
                    <span>🔌</span>
                    <span id="mcpCount">0</span>
                </div>
            </div>
        </div>`;
    }

    /**
     * Generate messages area HTML
     */
    private static generateMessagesArea(): string {
        return `
        <!-- Messages Area -->
        <div class="messages-area" id="messagesArea">
            <div class="welcome-message" id="welcomeMessage">
                <div class="welcome-title">Palette AI Assistant</div>
                <div>I can help you design components, build pages, and organize files in your project.</div>
                
                <div class="feature-grid">
                    <div class="feature-card" data-action="generate">
                        <div class="feature-title">🎨 Generate Components</div>
                        <div class="feature-desc">Create React components with TypeScript</div>
                    </div>
                    <div class="feature-card" data-action="analyze">
                        <div class="feature-title">🔍 Analyze Project</div>
                        <div class="feature-desc">Get insights about your codebase</div>
                    </div>
                    <div class="feature-card" data-action="tools">
                        <div class="feature-title">🛠️ Show Tools</div>
                        <div class="feature-desc">View available development tools</div>
                    </div>
                </div>
            </div>
        </div>`;
    }

    /**
     * Generate input area HTML
     */
    private static generateInputArea(): string {
        return `
        <!-- Input Area -->
        <div class="input-area">
            <div class="input-container">
                <vscode-textarea 
                    id="messageInput" 
                    placeholder="Ask me anything about your project..."
                    rows="1"
                    resize="vertical"
                    maxlength="4000">
                </vscode-textarea>
                <vscode-button id="sendBtn">Send</vscode-button>
            </div>
        </div>`;
    }

    /**
     * Generate JavaScript for the webview
     */
    private static generateScript(nonce: string): string {
        return `
    <script nonce="${nonce}">
        (function() {
            const vscode = acquireVsCodeApi();
            let messages = [];
            let isLoading = false;

            // DOM elements
            const messagesArea = document.getElementById('messagesArea');
            const messageInput = document.getElementById('messageInput');
            const sendBtn = document.getElementById('sendBtn');
            const welcomeMessage = document.getElementById('welcomeMessage');
            const toolsBtn = document.getElementById('toolsBtn');
            const mcpBtn = document.getElementById('mcpBtn');
            const clearBtn = document.getElementById('clearBtn');

            // Event listeners
            sendBtn.addEventListener('click', sendMessage);
            clearBtn.addEventListener('click', clearMessages);
            toolsBtn.addEventListener('click', showTools);
            mcpBtn.addEventListener('click', showMCPStatus);

            messageInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });

            // Feature card clicks
            document.addEventListener('click', (e) => {
                const featureCard = e.target.closest('.feature-card');
                if (featureCard) {
                    const action = featureCard.dataset.action;
                    if (action === 'tools') {
                        showTools();
                    } else if (action === 'generate') {
                        messageInput.value = 'Help me create a new React component';
                        messageInput.focus();
                    } else if (action === 'analyze') {
                        messageInput.value = 'Analyze my project structure';
                        messageInput.focus();
                    }
                }

                // Handle create file button clicks
                const createBtn = e.target.closest('.create-file-btn');
                if (createBtn) {
                    const code = createBtn.getAttribute('data-code');
                    const filename = createBtn.getAttribute('data-filename');
                    const language = createBtn.getAttribute('data-language');
                    vscode.postMessage({
                        type: 'createFile',
                        code: code,
                        filename: filename,
                        language: language
                    });
                }
            });

            // Handle messages from extension
            window.addEventListener('message', event => {
                const message = event.data;
                switch (message.type) {
                    case 'updateMessages':
                        messages = message.messages || [];
                        isLoading = message.isLoading || false;
                        renderMessages();
                        break;
                    case 'updateToolStatus':
                        updateToolStatus(message.availableTools, message.mcpServerStatus);
                        break;
                    case 'clearMessages':
                        clearMessagesUI();
                        break;
                }
            });

            function sendMessage() {
                const text = messageInput.value.trim();
                if (!text || isLoading) return;

                vscode.postMessage({
                    type: 'sendMessage',
                    message: text
                });

                messageInput.value = '';
            }

            function clearMessages() {
                vscode.postMessage({ type: 'clearMessages' });
            }

            function showTools() {
                vscode.postMessage({ type: 'listAvailableTools' });
            }

            function showMCPStatus() {
                vscode.postMessage({ type: 'showMCPStatus' });
            }

            function clearMessagesUI() {
                messages = [];
                renderMessages();
            }

            function renderMessages() {
                if (messages.length === 0) {
                    welcomeMessage.style.display = 'block';
                    // Clear any existing message bubbles
                    const existingBubbles = messagesArea.querySelectorAll('.message-bubble');
                    existingBubbles.forEach(bubble => bubble.remove());
                    return;
                }

                welcomeMessage.style.display = 'none';

                // Clear existing messages
                const existingBubbles = messagesArea.querySelectorAll('.message-bubble');
                existingBubbles.forEach(bubble => bubble.remove());

                // Render messages
                messages.forEach(message => {
                    const bubble = document.createElement('div');
                    bubble.className = 'message-bubble ' + message.role;
                    
                    if (message.metadata && message.metadata.codeBlocks && message.metadata.codeBlocks.length > 0) {
                        bubble.innerHTML = renderMessageWithCode(message);
                    } else {
                        bubble.innerHTML = '<div class="message-content">' + formatMessageContent(message.content) + '</div>';
                    }
                    
                    messagesArea.appendChild(bubble);
                });

                // Add typing indicator if loading
                if (isLoading) {
                    const typingBubble = document.createElement('div');
                    typingBubble.className = 'message-bubble assistant';
                    typingBubble.innerHTML = '<em>Thinking...</em>';
                    messagesArea.appendChild(typingBubble);
                }

                // Scroll to bottom
                messagesArea.scrollTop = messagesArea.scrollHeight;
            }

            function formatMessageContent(content) {
                // Convert newlines to <br> and handle basic formatting
                let formatted = escapeHtml(content)
                    .replace(/\\n/g, '<br>')
                    .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')  // **bold**
                    .replace(/\\*(.*?)\\*/g, '<em>$1</em>');              // *italic*
                
                return formatted;
            }

            function renderMessageWithCode(message) {
                // Simple approach: render text and code blocks separately
                if (!message.metadata || !message.metadata.codeBlocks || !message.metadata.codeBlocks.length) {
                    return '<div class="message-content">' + formatMessageContent(message.content) + '</div>';
                }

                let html = '';
                
                // For messages with code blocks, just show the content and code blocks
                html += '<div class="message-content">' + formatMessageContent(message.content) + '</div>';

                // Add each code block
                message.metadata.codeBlocks.forEach(block => {
                    html += '<div class="code-block">';
                    html += '<div class="code-header">';
                    html += '<span>' + (block.language || 'text');
                    if (block.filename) {
                        html += ' • ' + escapeHtml(block.filename);
                    }
                    html += '</span>';
                    html += '<vscode-button class="create-file-btn" data-code="' + 
                           escapeForAttribute(block.code) + '" data-filename="' +
                           escapeForAttribute(block.filename || '') + '" data-language="' +
                           escapeForAttribute(block.language || '') + '">Add File</vscode-button>';
                    html += '</div>';
                    html += '<div class="code-content">' + escapeHtml(block.code) + '</div>';
                    html += '</div>';
                });

                return html;
            }

            function escapeHtml(text) {
                if (!text) return '';
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }

            function escapeForAttribute(text) {
                if (!text) return '';
                return text
                    .replace(/&/g, '&amp;')
                    .replace(/"/g, '&quot;')
                    .replace(/'/g, '&#39;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;')
                    .replace(/\\n/g, '\\\\n')
                    .replace(/\\r/g, '\\\\r');
            }

            function updateToolStatus(availableTools, mcpServerStatus) {
                const toolCount = document.getElementById('toolCount');
                const mcpCount = document.getElementById('mcpCount');
                
                if (toolCount) toolCount.textContent = (availableTools && availableTools.length) || 0;
                if (mcpCount) mcpCount.textContent = Object.keys(mcpServerStatus || {}).length;
            }

            // Initialize
            vscode.postMessage({ type: 'refreshToolStatus' });
        })();
    </script>`;
    }
}