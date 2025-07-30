import * as vscode from 'vscode';

export function getChatWebviewHtml(panel: vscode.WebviewPanel, extensionUri: vscode.Uri): string {
  const styleUri = panel.webview.asWebviewUri(
    vscode.Uri.joinPath(extensionUri, 'media', 'style.css')
  );

  return `
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
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
          background: #2d2d2d;
          padding: 0.75rem 1rem;
          border-radius: 8px;
          margin-bottom: 1rem;
          white-space: pre-wrap;
          font-family: monospace;
        }

        .input-box {
          display: flex;
          padding: 1rem;
          border-top: 1px solid #333;
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

        #sendBtn {
          background: #0e639c;
          color: white;
          border: none;
          margin-left: 0.5rem;
          padding: 0.6rem 1rem;
          border-radius: 6px;
          cursor: pointer;
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
        <div class="logo-container" style="display: flex; align-items: center; gap: 12px;">
  <div
    class="logo-icon"
    style="
      padding: 10px;
      background: linear-gradient(to bottom right, #ec4899, #8b5cf6, #6366f1);
      border-radius: 9999px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 12px rgba(139, 92, 246, 0.6);
    "
  >
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      width="32"
      height="32"
      fill="none"
      stroke="white"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <path d="M12 3C7 3 3 7 3 12c0 2.5 1.3 4.7 3.3 6a3 3 0 0 0 4.3-2.8c0-1.1.9-2 2-2h2a2 2 0 0 1 2 2 2 2 0 0 0 3 1.73A9 9 0 0 0 21 12c0-5-4-9-9-9z" />
      <circle cx="7.5" cy="10.5" r="1.2" />
      <circle cx="12" cy="7.5" r="1.2" />
      <circle cx="16.5" cy="10.5" r="1.2" />
    </svg>
  </div>
  <span class="logo-text" style="color: white; font-weight: bold; font-size: 18px;">
    Palette
  </span>
</div>

        
        </div>

        
        </div>
        </div>

      <div class="chat-container" id="chat"></div>
      <div class="input-box">
        <input type="text" id="input" placeholder="Ask Palette" />
        <button id="sendBtn">➤</button>
      </div>

      <script>
        const vscode = acquireVsCodeApi();

        function appendMessage(author, text) {
          const chat = document.getElementById('chat');
          const message = document.createElement('div');
          message.className = 'message';
          message.innerText = author + ': ' + text;
          chat.appendChild(message);
          chat.scrollTop = chat.scrollHeight;
        }

        window.addEventListener('message', event => {
          const { type, suggestions } = event.data;
          if (type === 'output') {
            if (Array.isArray(suggestions)) {
              suggestions.forEach(s => appendMessage('🤖 Palette', s));
            } else {
              appendMessage('🤖 Palette', suggestions);
            }
          }
        });

        document.getElementById('sendBtn').addEventListener('click', () => {
          const input = document.getElementById('input');
          const value = input.value.trim();
          if (value) {
            appendMessage('🧑‍💻 You', value);
            vscode.postMessage({ command: 'userMessage', text: value });
            input.value = '';
          }
        });
      </script>
    </body>
    </html>
  `;
}
