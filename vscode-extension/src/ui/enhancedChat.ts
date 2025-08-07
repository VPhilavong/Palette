/**
 * Enhanced chat UI with rich formatting, code syntax highlighting,
 * streaming support, and interactive elements
 */

import * as vscode from 'vscode';

export function getEnhancedChatWebviewHtml(webview: vscode.Webview, extensionUri: vscode.Uri): string {
    const styleUri = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'media', 'enhanced-chat.css'));
    const nonce = getNonce();
    
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; 
        style-src ${webview.cspSource} 'unsafe-inline' https://cdnjs.cloudflare.com; 
        script-src 'nonce-${nonce}' https://cdnjs.cloudflare.com;
        connect-src ws: wss: http: https:;
        worker-src 'none';">
    <title>Palette AI Enhanced</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet">
    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            padding: 0;
            background: var(--vscode-editor-background);
            color: var(--vscode-editor-foreground);
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            display: flex;
            flex-direction: column;
            height: 100vh;
            overflow: hidden;
        }

        /* Header */
        .header {
            background: var(--vscode-titleBar-activeBackground);
            color: var(--vscode-titleBar-activeForeground);
            padding: 16px 20px;
            border-bottom: 1px solid var(--vscode-panel-border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            min-height: 60px;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .logo {
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white;
            font-size: 14px;
        }

        .title {
            font-weight: 600;
            font-size: 16px;
            margin: 0;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .header-btn {
            background: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            transition: background-color 0.2s;
        }

        .header-btn:hover {
            background: var(--vscode-button-secondaryHoverBackground);
        }

        /* Chat container */
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            scroll-behavior: smooth;
        }

        /* Messages */
        .message {
            margin-bottom: 20px;
            max-width: 100%;
        }

        .message-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
            font-size: 12px;
            color: var(--vscode-descriptionForeground);
        }

        .message-avatar {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
        }

        .user-avatar {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
        }

        .assistant-avatar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .system-avatar {
            background: var(--vscode-notificationsInfoIcon-foreground);
            color: var(--vscode-editor-background);
        }

        .message-content {
            background: var(--vscode-input-background);
            border: 1px solid var(--vscode-input-border);
            border-radius: 8px;
            padding: 16px;
            position: relative;
            line-height: 1.5;
        }

        .message.user .message-content {
            background: var(--vscode-button-secondaryBackground);
            border-color: var(--vscode-button-secondaryBackground);
            margin-left: 32px;
        }

        .message.assistant .message-content {
            background: var(--vscode-editor-background);
            border-color: var(--vscode-focusBorder);
        }

        .message.system .message-content {
            background: var(--vscode-notificationsInfoIcon-foreground);
            color: var(--vscode-editor-background);
            border-color: var(--vscode-notificationsInfoIcon-foreground);
            opacity: 0.9;
        }

        .message.error .message-content {
            background: var(--vscode-inputValidation-errorBackground);
            border-color: var(--vscode-inputValidation-errorBorder);
            color: var(--vscode-errorForeground);
        }

        /* Streaming message */
        .message.streaming .message-content {
            border-color: var(--vscode-progressBar-background);
            position: relative;
            overflow: hidden;
        }

        .message.streaming .message-content::after {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--vscode-progressBar-background), transparent);
            animation: shimmer 2s infinite;
        }

        @keyframes shimmer {
            0% { left: -100%; }
            100% { left: 100%; }
        }

        .typing-indicator {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            color: var(--vscode-descriptionForeground);
            font-style: italic;
        }

        .typing-dots {
            display: inline-flex;
            gap: 2px;
        }

        .typing-dot {
            width: 4px;
            height: 4px;
            background: var(--vscode-descriptionForeground);
            border-radius: 50%;
            animation: typing 1.4s infinite ease-in-out;
        }

        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }

        @keyframes typing {
            0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
            40% { transform: scale(1); opacity: 1; }
        }

        /* Progress bar */
        .progress-container {
            margin: 8px 0;
            padding: 8px;
            background: var(--vscode-editor-background);
            border-radius: 4px;
            border: 1px solid var(--vscode-input-border);
        }

        .progress-label {
            font-size: 12px;
            color: var(--vscode-descriptionForeground);
            margin-bottom: 4px;
        }

        .progress-bar {
            width: 100%;
            height: 4px;
            background: var(--vscode-input-background);
            border-radius: 2px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: var(--vscode-progressBar-background);
            border-radius: 2px;
            transition: width 0.3s ease;
        }

        /* Code blocks */
        .code-block {
            position: relative;
            margin: 12px 0;
        }

        .code-header {
            background: var(--vscode-titleBar-activeBackground);
            color: var(--vscode-titleBar-activeForeground);
            padding: 8px 12px;
            border-radius: 4px 4px 0 0;
            font-size: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border: 1px solid var(--vscode-input-border);
            border-bottom: none;
        }

        .code-language {
            font-weight: 500;
        }

        .code-copy-btn {
            background: transparent;
            border: none;
            color: inherit;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 11px;
            transition: background-color 0.2s;
        }

        .code-copy-btn:hover {
            background: var(--vscode-button-secondaryHoverBackground);
        }

        .code-content {
            background: var(--vscode-textCodeBlock-background);
            border: 1px solid var(--vscode-input-border);
            border-top: none;
            border-radius: 0 0 4px 4px;
            overflow: auto;
            max-height: 400px;
        }

        .code-content pre {
            margin: 0;
            padding: 16px;
            background: transparent;
            color: var(--vscode-editor-foreground);
            font-family: var(--vscode-editor-font-family);
            font-size: var(--vscode-editor-font-size);
            line-height: 1.4;
        }

        /* Inline code */
        code:not([class*="language-"]) {
            background: var(--vscode-textCodeBlock-background);
            color: var(--vscode-textPreformat-foreground);
            padding: 2px 6px;
            border-radius: 3px;
            font-family: var(--vscode-editor-font-family);
            font-size: 0.9em;
        }

        /* Action buttons */
        .message-actions {
            display: flex;
            gap: 8px;
            margin-top: 12px;
            flex-wrap: wrap;
        }

        .action-btn {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        .action-btn.secondary {
            background: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
        }

        .action-btn:hover {
            background: var(--vscode-button-hoverBackground);
            transform: translateY(-1px);
        }

        .action-btn.secondary:hover {
            background: var(--vscode-button-secondaryHoverBackground);
        }

        /* Component preview */
        .component-preview {
            margin: 16px 0;
            border: 1px solid var(--vscode-input-border);
            border-radius: 8px;
            overflow: hidden;
        }

        .preview-header {
            background: var(--vscode-titleBar-activeBackground);
            color: var(--vscode-titleBar-activeForeground);
            padding: 12px;
            font-weight: 500;
            display: flex;
            align-items: center;
            justify-content: between;
        }

        .preview-content {
            background: white;
            min-height: 200px;
            position: relative;
        }

        .preview-iframe {
            width: 100%;
            height: 300px;
            border: none;
        }

        /* Input area */
        .input-container {
            background: var(--vscode-input-background);
            border-top: 1px solid var(--vscode-panel-border);
            padding: 20px;
        }

        .input-wrapper {
            display: flex;
            gap: 12px;
            align-items: flex-end;
            max-width: 100%;
        }

        .input-field {
            flex: 1;
            background: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border: 1px solid var(--vscode-input-border);
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 14px;
            line-height: 1.4;
            resize: vertical;
            min-height: 44px;
            max-height: 120px;
            font-family: inherit;
            outline: none;
            transition: border-color 0.2s;
        }

        .input-field:focus {
            border-color: var(--vscode-focusBorder);
        }

        .input-field::placeholder {
            color: var(--vscode-input-placeholderForeground);
        }

        .send-btn {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            border-radius: 8px;
            padding: 12px 20px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.2s;
            min-width: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }

        .send-btn:hover:not(:disabled) {
            background: var(--vscode-button-hoverBackground);
            transform: translateY(-1px);
        }

        .send-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .upload-btn {
            background: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
            border: none;
            border-radius: 8px;
            padding: 12px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .upload-btn:hover {
            background: var(--vscode-button-secondaryHoverBackground);
            transform: translateY(-1px);
        }

        /* Scrollbar */
        .chat-container::-webkit-scrollbar {
            width: 8px;
        }

        .chat-container::-webkit-scrollbar-track {
            background: var(--vscode-scrollbarSlider-background);
        }

        .chat-container::-webkit-scrollbar-thumb {
            background: var(--vscode-scrollbarSlider-background);
            border-radius: 4px;
        }

        .chat-container::-webkit-scrollbar-thumb:hover {
            background: var(--vscode-scrollbarSlider-hoverBackground);
        }

        /* Markdown formatting */
        .message-content h1, .message-content h2, .message-content h3, 
        .message-content h4, .message-content h5, .message-content h6 {
            margin: 16px 0 8px 0;
            color: var(--vscode-editor-foreground);
        }

        .message-content p {
            margin: 8px 0;
        }

        .message-content ul, .message-content ol {
            margin: 8px 0;
            padding-left: 24px;
        }

        .message-content li {
            margin: 4px 0;
        }

        .message-content blockquote {
            margin: 12px 0;
            padding: 8px 16px;
            border-left: 4px solid var(--vscode-textBlockQuote-border);
            background: var(--vscode-textBlockQuote-background);
            color: var(--vscode-textPreformat-foreground);
        }

        .message-content strong {
            font-weight: 600;
            color: var(--vscode-editor-foreground);
        }

        .message-content em {
            font-style: italic;
            color: var(--vscode-descriptionForeground);
        }

        /* Feature plan */
        .feature-plan {
            background: var(--vscode-editor-background);
            border: 1px solid var(--vscode-focusBorder);
            border-radius: 8px;
            margin: 16px 0;
            overflow: hidden;
        }

        .plan-header {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            padding: 12px 16px;
            font-weight: 500;
        }

        .plan-steps {
            padding: 16px;
        }

        .plan-step {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 8px 0;
            border-bottom: 1px solid var(--vscode-input-border);
        }

        .step-number {
            background: var(--vscode-badge-background);
            color: var(--vscode-badge-foreground);
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 500;
            flex-shrink: 0;
        }

        .step-content {
            flex: 1;
            font-size: 14px;
        }

        /* Responsive */
        @media (max-width: 600px) {
            .header {
                padding: 12px 16px;
            }
            
            .chat-container {
                padding: 16px 12px;
            }
            
            .input-container {
                padding: 16px 12px;
            }
            
            .input-wrapper {
                gap: 8px;
            }
            
            .message.user .message-content {
                margin-left: 16px;
            }
        }

        /* Animations */
        .message {
            animation: slideIn 0.3s ease-out;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .action-btn {
            animation: fadeIn 0.5s ease-out;
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: scale(0.9);
            }
            to {
                opacity: 1;
                transform: scale(1);
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-left">
            <div class="logo">🎨</div>
            <h1 class="title">Palette AI</h1>
        </div>
        <div class="header-right">
            <button class="header-btn" onclick="clearConversation()">🗑️ Clear</button>
            <button class="header-btn" onclick="analyzeProject()">🔍 Analyze</button>
        </div>
    </div>

    <div class="chat-container" id="chatContainer"></div>

    <div class="input-container">
        <div class="input-wrapper">
            <button class="upload-btn" onclick="triggerImageUpload()">📎</button>
            <textarea 
                class="input-field" 
                id="messageInput" 
                placeholder="Describe the component you want to create... (e.g., 'Create a modern pricing card with three tiers')"
                rows="1"
            ></textarea>
            <button class="send-btn" id="sendBtn" onclick="sendMessage()">
                <span id="sendBtnText">Send</span>
                <span id="sendBtnIcon">🚀</span>
            </button>
        </div>
    </div>

    <input type="file" id="imageInput" accept="image/*" style="display: none;">

    <script nonce="${nonce}" src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-core.min.js"></script>
    <script nonce="${nonce}" src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>
    <script nonce="${nonce}" src="https://cdnjs.cloudflare.com/ajax/libs/marked/9.1.2/marked.min.js"></script>

    <script nonce="${nonce}">
        const vscode = acquireVsCodeApi();
        let isStreaming = false;
        let streamingMessageId = null;

        // Auto-resize textarea
        const messageInput = document.getElementById('messageInput');
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });

        // Send message on Enter (but allow Shift+Enter for new lines)
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message || isStreaming) return;
            
            vscode.postMessage({
                command: 'sendMessage',
                text: message
            });
            
            input.value = '';
            input.style.height = 'auto';
        }

        function clearConversation() {
            if (confirm('Clear conversation history?')) {
                vscode.postMessage({ command: 'clearConversation' });
                document.getElementById('chatContainer').innerHTML = '';
            }
        }

        function analyzeProject() {
            vscode.postMessage({ command: 'analyzeProject' });
        }

        function triggerImageUpload() {
            document.getElementById('imageInput').click();
        }

        document.getElementById('imageInput').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function() {
                    vscode.postMessage({
                        command: 'imageUpload',
                        name: file.name,
                        type: file.type,
                        dataUrl: reader.result
                    });
                };
                reader.readAsDataURL(file);
            }
        });

        function createMessage(content, type = 'assistant', metadata = null) {
            const chatContainer = document.getElementById('chatContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = \`message \${type}\`;
            
            let avatarText = '🤖';
            let roleName = 'Assistant';
            
            if (type === 'user') {
                avatarText = '👤';
                roleName = 'You';
            } else if (type === 'system') {
                avatarText = '💫';
                roleName = 'System';
            }
            
            const timestamp = new Date().toLocaleTimeString();
            
            messageDiv.innerHTML = \`
                <div class="message-header">
                    <div class="message-avatar \${type}-avatar">\${avatarText}</div>
                    <span class="message-role">\${roleName}</span>
                    <span class="message-time">\${timestamp}</span>
                </div>
                <div class="message-content">
                    <div class="message-text">\${parseMarkdown(content)}</div>
                </div>
            \`;
            
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            
            return messageDiv;
        }

        function parseMarkdown(text) {
            // Enhanced markdown parsing with code block handling
            return marked.parse(text, {
                highlight: function(code, lang) {
                    if (lang && Prism.languages[lang]) {
                        return Prism.highlight(code, Prism.languages[lang], lang);
                    }
                    return code;
                },
                breaks: true,
                gfm: true
            });
        }

        function createCodeBlock(code, language = 'javascript') {
            return \`
                <div class="code-block">
                    <div class="code-header">
                        <span class="code-language">\${language.toUpperCase()}</span>
                        <button class="code-copy-btn" onclick="copyCode(this)">📋 Copy</button>
                    </div>
                    <div class="code-content">
                        <pre><code class="language-\${language}">\${code}</code></pre>
                    </div>
                </div>
            \`;
        }

        function copyCode(button) {
            const codeBlock = button.closest('.code-block');
            const code = codeBlock.querySelector('code').textContent;
            navigator.clipboard.writeText(code).then(() => {
                button.textContent = '✅ Copied!';
                setTimeout(() => {
                    button.innerHTML = '📋 Copy';
                }, 2000);
            });
        }

        function createActionButtons(actions) {
            return actions.map(action => \`
                <button class="action-btn \${action.secondary ? 'secondary' : ''}" 
                        onclick="handleAction('\${action.id}', this)">
                    \${action.label}
                </button>
            \`).join('');
        }

        function handleAction(actionId, buttonElement) {
            const messageElement = buttonElement.closest('.message');
            
            switch (actionId) {
                case 'create-file':
                    const code = messageElement.querySelector('code')?.textContent;
                    if (code) {
                        createFile(code);
                    }
                    break;
                    
                case 'preview':
                    const previewCode = messageElement.querySelector('code')?.textContent;
                    if (previewCode) {
                        previewComponent(previewCode);
                    }
                    break;
                    
                case 'copy-code':
                    const copyCode = messageElement.querySelector('code')?.textContent;
                    if (copyCode) {
                        navigator.clipboard.writeText(copyCode);
                        buttonElement.textContent = '✅ Copied!';
                        setTimeout(() => {
                            buttonElement.innerHTML = '📋 Copy Code';
                        }, 2000);
                    }
                    break;
                    
                default:
                    vscode.postMessage({
                        command: 'action',
                        actionId: actionId
                    });
            }
        }

        function createFile(code) {
            // Get suggested filename
            let filename = 'Component.tsx';
            const match = code.match(/(?:export\\s+(?:default\\s+)?(?:function|const)\\s+)(\\w+)/);
            if (match) {
                filename = \`\${match[1]}.tsx\`;
            }
            
            const suggestedPath = prompt('Enter file path:', \`src/components/\${filename}\`);
            if (suggestedPath) {
                vscode.postMessage({
                    command: 'createFile',
                    operation: {
                        type: 'create',
                        filePath: suggestedPath,
                        content: code,
                        description: 'Generated component'
                    }
                });
            }
        }

        function previewComponent(code) {
            vscode.postMessage({
                command: 'previewComponent',
                code: code,
                options: {
                    size: 'desktop',
                    theme: 'light',
                    includeVariants: true
                }
            });
        }

        function updateSendButton(disabled, text = 'Send', icon = '🚀') {
            const btn = document.getElementById('sendBtn');
            const textEl = document.getElementById('sendBtnText');
            const iconEl = document.getElementById('sendBtnIcon');
            
            btn.disabled = disabled;
            textEl.textContent = text;
            iconEl.textContent = icon;
        }

        function createProgressBar(stage, progress) {
            return \`
                <div class="progress-container">
                    <div class="progress-label">\${stage}</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: \${progress}%"></div>
                    </div>
                </div>
            \`;
        }

        function createTypingIndicator() {
            return \`
                <div class="typing-indicator">
                    <span>Assistant is typing</span>
                    <div class="typing-dots">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            \`;
        }

        // Message handlers
        window.addEventListener('message', event => {
            const message = event.data;
            
            switch (message.type) {
                case 'userMessage':
                    createMessage(message.content, 'user');
                    isStreaming = true;
                    updateSendButton(true, 'Sending...', '⏳');
                    break;

                case 'startStreaming':
                    streamingMessageId = message.messageId;
                    const streamingMsg = createMessage(createTypingIndicator(), 'assistant');
                    streamingMsg.id = message.messageId;
                    streamingMsg.classList.add('streaming');
                    break;

                case 'streamingUpdate':
                    if (message.messageId === streamingMessageId) {
                        const msgEl = document.getElementById(message.messageId);
                        if (msgEl) {
                            const contentEl = msgEl.querySelector('.message-text');
                            contentEl.innerHTML = parseMarkdown(message.content);
                        }
                    }
                    break;

                case 'progressUpdate':
                    if (message.messageId === streamingMessageId) {
                        const msgEl = document.getElementById(message.messageId);
                        if (msgEl) {
                            const contentEl = msgEl.querySelector('.message-text');
                            contentEl.innerHTML = createProgressBar(message.stage, message.progress);
                        }
                    }
                    break;

                case 'completeStreaming':
                    if (message.messageId === streamingMessageId) {
                        const msgEl = document.getElementById(message.messageId);
                        if (msgEl) {
                            msgEl.classList.remove('streaming');
                            const contentEl = msgEl.querySelector('.message-text');
                            contentEl.innerHTML = parseMarkdown(message.content);
                            
                            // Add action buttons if component was generated
                            if (message.metadata && message.metadata.componentCode) {
                                const actionsDiv = document.createElement('div');
                                actionsDiv.className = 'message-actions';
                                actionsDiv.innerHTML = createActionButtons([
                                    { id: 'create-file', label: '📄 Create File', primary: true },
                                    { id: 'preview', label: '👁️ Preview', secondary: true },
                                    { id: 'copy-code', label: '📋 Copy Code', secondary: true }
                                ]);
                                msgEl.querySelector('.message-content').appendChild(actionsDiv);
                            }
                        }
                    }
                    isStreaming = false;
                    streamingMessageId = null;
                    updateSendButton(false);
                    break;

                case 'errorMessage':
                    if (message.messageId === streamingMessageId) {
                        const msgEl = document.getElementById(message.messageId);
                        if (msgEl) {
                            msgEl.className = 'message error';
                            const contentEl = msgEl.querySelector('.message-text');
                            contentEl.textContent = message.content;
                        }
                    } else {
                        createMessage(message.content, 'error');
                    }
                    isStreaming = false;
                    streamingMessageId = null;
                    updateSendButton(false);
                    break;

                case 'system':
                    createMessage(message.content, 'system');
                    break;

                case 'projectAnalysis':
                    createMessage(message.content, 'system');
                    break;

                case 'previewGenerated':
                    // Create preview iframe or display
                    const previewMsg = createMessage('🖼️ **Component Preview Generated!**', 'assistant');
                    // TODO: Implement actual preview display
                    break;

                case 'fileCreated':
                    createMessage(message.content, 'system');
                    break;

                case 'conversationCleared':
                    // Conversation was cleared, UI already updated
                    break;

                default:
                    console.log('Unknown message type:', message.type);
            }
        });

        // Initial welcome message
        setTimeout(() => {
            createMessage(
                \`👋 **Welcome to Palette AI!**

I'm your AI-powered UI development assistant. I can help you:

• **Create beautiful React components** with modern design patterns
• **Generate responsive layouts** that work on all devices  
• **Preview components** before you create them
• **Analyze your project** to match existing patterns
• **Create complete features** with multiple components

Just describe what you want to build, and I'll create it for you!

*Try: "Create a modern pricing card with three tiers" or "Build a hero section with gradient background"*\`, 
                'system'
            );
        }, 500);
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