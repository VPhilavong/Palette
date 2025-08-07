/**
 * Webview HTML for streaming chat with VS Code Messenger
 */

import * as vscode from 'vscode';

export function getStreamingChatWebviewHtml(panel: vscode.WebviewPanel, extensionUri: vscode.Uri): string {
    // Generate CSP nonce
    const nonce = getNonce();

    return `<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="Content-Security-Policy" content="default-src 'none'; 
            style-src ${panel.webview.cspSource} 'unsafe-inline'; 
            script-src 'nonce-${nonce}';
            connect-src ws: wss: http: https:;
            worker-src 'none';">
        <title>Palette Chat</title>
        <style>
            body {
                margin: 0;
                padding: 0;
                background-color: var(--vscode-editor-background);
                color: var(--vscode-editor-foreground);
                font-family: var(--vscode-font-family);
                font-size: var(--vscode-font-size);
                display: flex;
                flex-direction: column;
                height: 100vh;
            }

            .header {
                padding: 16px;
                border-bottom: 1px solid var(--vscode-panel-border);
                background: var(--vscode-sideBar-background);
            }

            .logo-container {
                display: flex;
                align-items: center;
                gap: 12px;
            }

            .logo-icon {
                padding: 8px;
                background: linear-gradient(135deg, #ec4899, #8b5cf6, #6366f1);
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
            }

            .logo-text {
                font-weight: 600;
                font-size: 18px;
                letter-spacing: 0.5px;
            }

            .status-bar {
                padding: 8px 16px;
                background: var(--vscode-statusBar-background);
                border-bottom: 1px solid var(--vscode-panel-border);
                display: flex;
                align-items: center;
                gap: 8px;
                min-height: 24px;
            }

            .status-indicator {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: var(--vscode-statusBarItem-errorBackground);
            }

            .status-indicator.ready { background: #22c55e; }
            .status-indicator.connecting { background: #f59e0b; }
            .status-indicator.generating { 
                background: #3b82f6;
                animation: pulse 1.5s infinite;
            }
            .status-indicator.error { background: #ef4444; }

            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }

            .status-text {
                font-size: 12px;
                color: var(--vscode-descriptionForeground);
            }

            .chat-container {
                flex: 1;
                padding: 16px;
                overflow-y: auto;
                display: flex;
                flex-direction: column;
                gap: 16px;
            }

            .message {
                max-width: 80%;
                padding: 12px 16px;
                border-radius: 12px;
                line-height: 1.5;
                word-wrap: break-word;
            }

            .message.user {
                align-self: flex-end;
                background: var(--vscode-button-background);
                color: var(--vscode-button-foreground);
                border-bottom-right-radius: 4px;
            }

            .message.assistant {
                align-self: flex-start;
                background: var(--vscode-input-background);
                border: 1px solid var(--vscode-input-border);
                border-bottom-left-radius: 4px;
            }

            .message.stream {
                background: var(--vscode-editor-selectionBackground);
                border: 1px solid var(--vscode-focusBorder);
                opacity: 0.8;
            }

            .message pre {
                background: var(--vscode-textCodeBlock-background);
                padding: 12px;
                border-radius: 6px;
                overflow-x: auto;
                font-family: var(--vscode-editor-font-family);
                font-size: var(--vscode-editor-font-size);
            }

            .message code {
                background: var(--vscode-textCodeBlock-background);
                padding: 2px 6px;
                border-radius: 3px;
                font-family: var(--vscode-editor-font-family);
            }

            .error-message {
                background: var(--vscode-inputValidation-errorBackground);
                border: 1px solid var(--vscode-inputValidation-errorBorder);
                color: var(--vscode-errorForeground);
                padding: 12px;
                border-radius: 6px;
                margin: 8px 0;
            }

            .error-actions {
                margin-top: 8px;
                display: flex;
                gap: 8px;
            }

            .error-action {
                background: var(--vscode-button-secondaryBackground);
                color: var(--vscode-button-secondaryForeground);
                border: none;
                padding: 4px 12px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
            }

            .error-action:hover {
                background: var(--vscode-button-secondaryHoverBackground);
            }

            .input-container {
                padding: 16px;
                border-top: 1px solid var(--vscode-panel-border);
                background: var(--vscode-sideBar-background);
            }

            .input-box {
                display: flex;
                gap: 8px;
                align-items: flex-end;
            }

            .input-textarea {
                flex: 1;
                background: var(--vscode-input-background);
                color: var(--vscode-input-foreground);
                border: 1px solid var(--vscode-input-border);
                border-radius: 6px;
                padding: 12px;
                font-family: var(--vscode-font-family);
                font-size: var(--vscode-font-size);
                resize: none;
                min-height: 20px;
                max-height: 120px;
                line-height: 1.4;
            }

            .input-textarea:focus {
                outline: none;
                border-color: var(--vscode-focusBorder);
                box-shadow: 0 0 0 1px var(--vscode-focusBorder);
            }

            .send-button, .attach-button, .analyze-button {
                background: var(--vscode-button-background);
                color: var(--vscode-button-foreground);
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                display: flex;
                align-items: center;
                gap: 6px;
            }

            .send-button:hover, .attach-button:hover, .analyze-button:hover {
                background: var(--vscode-button-hoverBackground);
            }

            .send-button:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }

            .attach-button {
                background: var(--vscode-button-secondaryBackground);
                color: var(--vscode-button-secondaryForeground);
            }

            .analyze-button {
                background: var(--vscode-button-secondaryBackground);
                color: var(--vscode-button-secondaryForeground);
            }

            .input-actions {
                display: flex;
                gap: 4px;
            }

            .typing-indicator {
                display: none;
                align-items: center;
                gap: 8px;
                padding: 8px 16px;
                color: var(--vscode-descriptionForeground);
                font-style: italic;
                font-size: 14px;
            }

            .typing-indicator.active {
                display: flex;
            }

            .typing-dots {
                display: flex;
                gap: 4px;
            }

            .typing-dot {
                width: 6px;
                height: 6px;
                background: var(--vscode-descriptionForeground);
                border-radius: 50%;
                animation: typing 1.4s infinite ease-in-out;
            }

            .typing-dot:nth-child(1) { animation-delay: -0.32s; }
            .typing-dot:nth-child(2) { animation-delay: -0.16s; }

            @keyframes typing {
                0%, 80%, 100% { transform: scale(0); opacity: 0.5; }
                40% { transform: scale(1); opacity: 1; }
            }

            /* Scrollbar styling */
            .chat-container::-webkit-scrollbar {
                width: 8px;
            }

            .chat-container::-webkit-scrollbar-track {
                background: var(--vscode-scrollbarSlider-background);
            }

            .chat-container::-webkit-scrollbar-thumb {
                background: var(--vscode-scrollbarSlider-hoverBackground);
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="logo-container">
                <div class="logo-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                        <path d="M12 3C7 3 3 7 3 12c0 2.5 1.3 4.7 3.3 6a3 3 0 0 0 4.3-2.8c0-1.1.9-2 2-2h2a2 2 0 0 1 2 2 2 2 0 0 0 3 1.73A9 9 0 0 0 21 12c0-5-4-9-9-9z"/>
                        <circle cx="7.5" cy="10.5" r="1.2"/>
                        <circle cx="12" cy="7.5" r="1.2"/>
                        <circle cx="16.5" cy="10.5" r="1.2"/>
                    </svg>
                </div>
                <span class="logo-text">Palette</span>
            </div>
        </div>

        <div class="status-bar">
            <div class="status-indicator" id="statusIndicator"></div>
            <span class="status-text" id="statusText">Initializing...</span>
        </div>

        <div class="chat-container" id="chatContainer"></div>

        <div class="typing-indicator" id="typingIndicator">
            <span>Palette is thinking</span>
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>

        <div class="input-container">
            <div class="input-box">
                <textarea 
                    id="messageInput" 
                    class="input-textarea"
                    placeholder="Describe the component you want to create..."
                    rows="1"
                ></textarea>
                <div class="input-actions">
                    <button id="analyzeButton" class="analyze-button" title="Analyze Project">
                        📊
                    </button>
                    <button id="attachButton" class="attach-button" title="Attach Image">
                        📎
                    </button>
                    <button id="sendButton" class="send-button">
                        <span>Send</span>
                        <span>➤</span>
                    </button>
                </div>
            </div>
        </div>

        <input type="file" id="fileInput" accept="image/*" style="display: none;">

        <script nonce="${nonce}">
            // Streaming chat logic with basic postMessage
            const vscode = acquireVsCodeApi();
            let isGenerating = false;
            let currentStreamContent = '';

            // Initialize when page loads
            window.addEventListener('load', () => {
                setupUIEvents();
                setupMessageHandling();
                console.log('✅ Streaming chat initialized');
            });

            function setupMessageHandling() {
                // Handle messages from extension
                window.addEventListener('message', event => {
                    const message = event.data;
                    if (message.type === 'message') {
                        handleExtensionMessage(message.data);
                    }
                });
            }

            function setupUIEvents() {
                const messageInput = document.getElementById('messageInput');
                const sendButton = document.getElementById('sendButton');
                const analyzeButton = document.getElementById('analyzeButton');
                const attachButton = document.getElementById('attachButton');
                const fileInput = document.getElementById('fileInput');

                // Send message
                sendButton.addEventListener('click', sendMessage);
                
                // Send on Enter (but allow Shift+Enter for new lines)
                messageInput.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendMessage();
                    }
                });

                // Auto-resize textarea
                messageInput.addEventListener('input', autoResizeTextarea);

                // Analyze project
                analyzeButton.addEventListener('click', () => {
                    vscode.postMessage({
                        type: 'analyze-request'
                    });
                });

                // Attach file
                attachButton.addEventListener('click', () => {
                    fileInput.click();
                });

                fileInput.addEventListener('change', handleFileUpload);
            }

            function sendMessage() {
                if (isGenerating) return;

                const input = document.getElementById('messageInput');
                const text = input.value.trim();
                
                if (!text) return;

                // Add user message to chat
                addMessage(text, 'user');

                // Clear input
                input.value = '';
                autoResizeTextarea({ target: input });

                // Send to extension
                vscode.postMessage({
                    type: 'user-message',
                    text: text,
                    timestamp: Date.now()
                });

                isGenerating = true;
                updateSendButton();
            }

            function handleExtensionMessage(message) {
                console.log('📨 Received message:', message.type);

                switch (message.type) {
                    case 'status':
                        updateStatus(message.status, message.message);
                        if (message.status === 'generating') {
                            showTypingIndicator(true);
                        } else if (message.status === 'ready') {
                            showTypingIndicator(false);
                            isGenerating = false;
                            updateSendButton();
                        }
                        break;

                    case 'ai-stream':
                        handleStreamChunk(message.chunk, message.isFirst);
                        break;

                    case 'ai-response':
                        if (message.isComplete) {
                            showTypingIndicator(false);
                            if (currentStreamContent) {
                                // Update existing stream message
                                updateLastStreamMessage(message.content);
                            } else {
                                // Add new complete message
                                addMessage(message.content, 'assistant');
                            }
                            currentStreamContent = '';
                        }
                        break;

                    case 'error':
                        showTypingIndicator(false);
                        addErrorMessage(message.error, message.details, message.actions);
                        isGenerating = false;
                        updateSendButton();
                        break;
                }
            }

            function addMessage(content, role, isStream = false) {
                const chatContainer = document.getElementById('chatContainer');
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message ' + role + (isStream ? ' stream' : '');
                
                // Process markdown-like formatting
                const processedContent = processMessageContent(content);
                messageDiv.innerHTML = processedContent;
                
                chatContainer.appendChild(messageDiv);
                scrollToBottom();
                
                return messageDiv;
            }

            function handleStreamChunk(chunk, isFirst) {
                if (isFirst || !currentStreamContent) {
                    // Start new stream message
                    currentStreamContent = chunk;
                    addMessage(chunk, 'assistant', true);
                } else {
                    // Update existing stream message
                    currentStreamContent += chunk;
                    updateLastStreamMessage(currentStreamContent);
                }
            }

            function updateLastStreamMessage(content) {
                const chatContainer = document.getElementById('chatContainer');
                const messages = chatContainer.getElementsByClassName('message');
                const lastMessage = messages[messages.length - 1];
                
                if (lastMessage && lastMessage.classList.contains('stream')) {
                    const processedContent = processMessageContent(content);
                    lastMessage.innerHTML = processedContent;
                    lastMessage.classList.remove('stream'); // Make it permanent
                }
            }

            function addErrorMessage(error, details, actions) {
                const chatContainer = document.getElementById('chatContainer');
                const errorDiv = document.createElement('div');
                errorDiv.className = 'error-message';
                
                let html = '<strong>❌ ' + error + '</strong>';
                if (details) {
                    html += '<br><small>' + details + '</small>';
                }
                
                if (actions && actions.length > 0) {
                    html += '<div class="error-actions">';
                    actions.forEach(action => {
                        html += '<button class="error-action" onclick="handleErrorAction(\\''+action.action+'\\')">'+action.label+'</button>';
                    });
                    html += '</div>';
                }
                
                errorDiv.innerHTML = html;
                chatContainer.appendChild(errorDiv);
                scrollToBottom();
            }

            function handleErrorAction(action) {
                switch (action) {
                    case 'retry-connection':
                        location.reload();
                        break;
                    case 'show-output':
                        // This would be handled by extension
                        break;
                }
            }

            function updateStatus(status, message) {
                const indicator = document.getElementById('statusIndicator');
                const text = document.getElementById('statusText');
                
                indicator.className = 'status-indicator ' + status;
                text.textContent = message || getStatusText(status);
            }

            function getStatusText(status) {
                switch (status) {
                    case 'ready': return 'Ready';
                    case 'connecting': return 'Connecting...';
                    case 'generating': return 'Generating...';
                    case 'error': return 'Error';
                    default: return 'Unknown';
                }
            }

            function showTypingIndicator(show) {
                const indicator = document.getElementById('typingIndicator');
                indicator.classList.toggle('active', show);
            }

            function updateSendButton() {
                const sendButton = document.getElementById('sendButton');
                sendButton.disabled = isGenerating;
                sendButton.textContent = isGenerating ? 'Generating...' : 'Send';
            }

            function autoResizeTextarea(event) {
                const textarea = event.target;
                textarea.style.height = 'auto';
                textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
            }

            function handleFileUpload(event) {
                const file = event.target.files[0];
                if (!file) return;

                const reader = new FileReader();
                reader.onload = function(e) {
                    vscode.postMessage({
                        type: 'image-upload',
                        name: file.name,
                        mimeType: file.type,
                        dataUrl: e.target.result
                    });
                };
                reader.readAsDataURL(file);
                
                // Clear the input
                event.target.value = '';
            }

            function processMessageContent(content) {
                // Simple markdown-like processing
                let processed = content;
                
                // Code blocks
                processed = processed.replace(/\`\`\`(\w*)\n?(.*?)\`\`\`/gs, '<pre><code>$2</code></pre>');
                
                // Inline code
                processed = processed.replace(/\`([^\`]+)\`/g, '<code>$1</code>');
                
                // Bold
                processed = processed.replace(/\*\*([^\*]+)\*\*/g, '<strong>$1</strong>');
                
                // Newlines
                processed = processed.replace(/\\n/g, '<br>');
                
                return processed;
            }

            function scrollToBottom() {
                const chatContainer = document.getElementById('chatContainer');
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        </script>
    </body>
    </html>`;
}

function getNonce() {
    let text = '';
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (let i = 0; i < 32; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}