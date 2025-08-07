import * as vscode from 'vscode';

export function getChatWebviewHtml(panel: vscode.WebviewPanel, extensionUri: vscode.Uri): string {
  const styleUri = panel.webview.asWebviewUri(
    vscode.Uri.joinPath(extensionUri, 'media', 'style.css')
  );
  const nonce = getNonce();

  return `<!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
      <meta http-equiv="Content-Security-Policy" content="default-src 'none'; 
          style-src ${panel.webview.cspSource} 'unsafe-inline'; 
          script-src 'nonce-${nonce}';
          connect-src ws: wss: http: https:;
          worker-src 'none';">
      <link href="${styleUri}" rel="stylesheet">
      <title>Palette</title>
      <style>
        body {
          margin: 0;
          padding: 0;
          background-color: #1e1e1e;
          font-family: "Segoe UI", sans-serif;
          color: #d4d4d4;
          display: flex;
          flex-direction: column;
          height: 100vh;
        }

        .header {
          padding: 1rem;
          font-weight: bold;
          font-size: 14px;
          border-bottom: 1px solid #333;
        }

        .chat-container {
          flex: 1;
          padding: 1rem;
          overflow-y: auto;
        }

        .message {
          padding: 0.75rem 1rem;
          border-radius: 8px;
          margin-bottom: 1rem;
          white-space: pre-wrap;
          overflow-x: auto;
        }

        .message.user {
          background: #1e3a5f;
          border-left: 3px solid #4a9eff;
          margin-left: 2rem;
          font-family: "Segoe UI", sans-serif;
        }

        .message.assistant {
          background: #2d2d2d;
          border-left: 3px solid #00b4d8;
          margin-right: 2rem;
          font-family: monospace;
        }
        
        .message pre {
          margin: 0;
          overflow-x: auto;
        }
        
        .message code {
          background: #1e1e1e;
          padding: 0.125rem 0.25rem;
          border-radius: 3px;
        }
        
        .message pre code {
          display: block;
          padding: 1rem;
          background: #1e1e1e;
          border: 1px solid #333;
          border-radius: 6px;
          overflow-x: auto;
        }
        
        .message.error {
          background: #5a1e1e;
          border: 1px solid #f14c4c;
          color: #f48771;
        }
        
        .message.stream {
          background: #1e2e3e;
          border: 1px solid #0e639c;
          color: #4fc3f7;
          font-size: 12px;
        }

        .input-box {
          display: flex;
          padding: 1rem;
          border-top: 1px solid #333;
          align-items: center;
          gap: 0.5rem;
        }

        #input {
          flex: 1;
          background: #252526;
          color: white;
          border: none;
          border-radius: 6px;
          padding: 0.6rem 1rem;
          font-size: 13px;
        }

        #sendBtn, #uploadBtn {
          background: #0e639c;
          color: white;
          border: none;
          padding: 0.6rem 1rem;
          border-radius: 6px;
          cursor: pointer;
        }

        #uploadBtn {
          font-size: 18px;
          display: flex;
          align-items: center;
          justify-content: center;
          width: 38px;
          height: 38px;
          padding: 0;
        }

        #imageInput {
          display: none;
        }

        .logo-container {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .lucide-icon {
          width: 32px;
          height: 32px;
          stroke: white;
        }

        .logo-text {
          font-weight: 700;
          font-size: 1.25rem;
          color: white;
          letter-spacing: 0.5px;
        }
      </style>
    </head>
    <body>
      <div class="header">
        <div class="logo-container">
          <div class="logo-icon" style="padding: 10px; background: linear-gradient(to bottom right, #ec4899, #8b5cf6, #6366f1); border-radius: 9999px; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 12px rgba(139, 92, 246, 0.6);">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 3C7 3 3 7 3 12c0 2.5 1.3 4.7 3.3 6a3 3 0 0 0 4.3-2.8c0-1.1.9-2 2-2h2a2 2 0 0 1 2 2 2 2 0 0 0 3 1.73A9 9 0 0 0 21 12c0-5-4-9-9-9z" />
              <circle cx="7.5" cy="10.5" r="1.2" />
              <circle cx="12" cy="7.5" r="1.2" />
              <circle cx="16.5" cy="10.5" r="1.2" />
            </svg>
          </div>
          <span class="logo-text">Palette</span>
        </div>
      </div>

      <div class="chat-container" id="chat"></div>
      <div class="input-box">
        <button id="uploadBtn">＋</button>
        <input type="file" id="imageInput" accept="image/*" />
        <input type="text" id="input" placeholder="Describe the UI component you want to create..." />
        <button id="sendBtn">➤</button>
      </div>

      <script nonce="${nonce}">
        const vscode = acquireVsCodeApi();
        let currentStreamMessage = null;

        function appendMessage(text, messageType = 'assistant', className = '') {
          const chat = document.getElementById('chat');
          const message = document.createElement('div');
          const fullClassName = 'message ' + messageType + (className ? ' ' + className : '');
          message.className = fullClassName;
          
          // Enhanced message formatting for UI development conversations
          if (messageType === 'user') {
            message.textContent = text;
          } else {
            message.textContent = text;
          }
          
          chat.appendChild(message);
          chat.scrollTop = chat.scrollHeight;
          return message;
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

        function updateStreamMessage(text) {
          // Check if this is a validation stage message
          if (text.includes('🎨') || text.includes('✅') || text.includes('🚀') || 
              text.includes('validation') || text.includes('quality')) {
            // Create a new message for each validation stage
            appendMessage(text, 'assistant', 'stream');
            currentStreamMessage = null;
          } else if (text.includes('code')) {
            // This is a code block, create a new message
            appendMessage(text, 'assistant');
            currentStreamMessage = null;
          } else if (!currentStreamMessage) {
            currentStreamMessage = appendMessage(text, 'assistant', 'stream');
          } else {
            // For regular streaming updates
            currentStreamMessage.textContent = text;
          }
        }

        window.addEventListener('message', event => {
          const message = event.data;
          
          switch (message.type) {
            case 'output':
              // Reset stream message when new output arrives
              currentStreamMessage = null;
              if (Array.isArray(message.suggestions)) {
                message.suggestions.forEach(s => appendMessage(s, 'assistant'));
              } else if (message.suggestions) {
                appendMessage(message.suggestions, 'assistant');
              }
              break;
              
            case 'stream':
              if (message.data) {
                updateStreamMessage(message.data);
              }
              break;
              
            case 'error':
              currentStreamMessage = null;
              appendMessage('❌ Error: ' + (message.error || 'An error occurred'), 'assistant', 'error');
              break;
              
            default:
              console.log('Unknown message type:', message.type);
          }
        });

        function sendMessage() {
          const input = document.getElementById('input');
          const value = input.value.trim();
          console.log('sendMessage called with value:', value);
          if (value) {
            appendMessage(value, 'user');
            console.log('Sending message to VS Code:', { command: 'userMessage', text: value });
            vscode.postMessage({ command: 'userMessage', text: value });
            input.value = '';
          } else {
            console.log('Empty value, not sending message');
          }
        }

        document.getElementById('sendBtn').addEventListener('click', sendMessage);
        
        document.getElementById('input').addEventListener('keypress', (e) => {
          console.log('Key pressed:', e.key);
          if (e.key === 'Enter') {
            console.log('Enter key detected, calling sendMessage');
            sendMessage();
          }
        });

        document.getElementById('uploadBtn').addEventListener('click', () => {
          document.getElementById('imageInput').click();
        });

        document.getElementById('imageInput').addEventListener('change', async (event) => {
          const file = event.target.files[0];
          if (file) {
            const reader = new FileReader();
            reader.onload = () => {
              vscode.postMessage({
                command: 'imageUpload',
                name: file.name,
                type: file.type,
                dataUrl: reader.result
              });
              appendMessage('[Image uploaded: ' + file.name + ']', 'user');
            };
            reader.readAsDataURL(file);
          }
        });
      </script>
    </body>
    </html>
  `;
}

function getNonce() {
  let text = '';
  const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  for (let i = 0; i < 32; i++) {
    text += possible.charAt(Math.floor(Math.random() * possible.length));
  }
  return text;
}
