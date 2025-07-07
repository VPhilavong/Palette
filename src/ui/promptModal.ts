import * as vscode from 'vscode';

export class PromptModal {
    private static instance: PromptModal;
    private panel: vscode.WebviewPanel | undefined;

    public static getInstance(): PromptModal {
        if (!PromptModal.instance) {
            PromptModal.instance = new PromptModal();
        }
        return PromptModal.instance;
    }

    public async showPromptInput(): Promise<string | undefined> {
        const prompt = await vscode.window.showInputBox({
            title: 'Generate UI Component',
            prompt: 'Describe the component you want to create (e.g., "Make a pricing page with 3 plans", "Create a login form with validation")',
            placeHolder: 'A dashboard with charts and user stats...',
            ignoreFocusOut: true,
            validateInput: (value: string) => {
                if (!value || value.trim().length < 5) {
                    return 'Please provide a more detailed description (at least 5 characters)';
                }
                return null;
            }
        });

        return prompt?.trim();
    }

    public async showAdvancedPromptPanel(): Promise<string | undefined> {
        return new Promise((resolve) => {
            if (this.panel) {
                this.panel.dispose();
            }

            this.panel = vscode.window.createWebviewPanel(
                'uiCopilotPrompt',
                'Generate UI Component',
                vscode.ViewColumn.One,
                {
                    enableScripts: true,
                    retainContextWhenHidden: true
                }
            );

            this.panel.webview.html = this.getWebviewContent();

            this.panel.webview.onDidReceiveMessage(
                message => {
                    switch (message.command) {
                        case 'generate':
                            resolve(message.prompt);
                            this.panel?.dispose();
                            break;
                        case 'cancel':
                            resolve(undefined);
                            this.panel?.dispose();
                            break;
                    }
                }
            );

            this.panel.onDidDispose(() => {
                this.panel = undefined;
                resolve(undefined);
            });
        });
    }

    private getWebviewContent(): string {
        return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>UI Copilot - Generate Component</title>
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    color: var(--vscode-foreground);
                    background-color: var(--vscode-editor-background);
                    padding: 20px;
                    margin: 0;
                }
                .container {
                    max-width: 600px;
                    margin: 0 auto;
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                }
                .header h1 {
                    color: var(--vscode-textPreformat-foreground);
                    margin: 0 0 10px 0;
                }
                .header p {
                    color: var(--vscode-descriptionForeground);
                    margin: 0;
                }
                .input-section {
                    margin-bottom: 20px;
                }
                .input-section label {
                    display: block;
                    margin-bottom: 8px;
                    font-weight: bold;
                }
                #promptInput {
                    width: 100%;
                    min-height: 120px;
                    padding: 12px;
                    border: 1px solid var(--vscode-input-border);
                    background-color: var(--vscode-input-background);
                    color: var(--vscode-input-foreground);
                    font-family: var(--vscode-font-family);
                    font-size: 14px;
                    resize: vertical;
                    box-sizing: border-box;
                }
                #promptInput:focus {
                    outline: 1px solid var(--vscode-focusBorder);
                }
                .examples {
                    margin-bottom: 20px;
                    padding: 15px;
                    background-color: var(--vscode-textBlockQuote-background);
                    border-left: 4px solid var(--vscode-textBlockQuote-border);
                }
                .examples h3 {
                    margin: 0 0 10px 0;
                    font-size: 14px;
                }
                .example-item {
                    margin: 8px 0;
                    color: var(--vscode-textLink-foreground);
                    cursor: pointer;
                    font-size: 13px;
                }
                .example-item:hover {
                    text-decoration: underline;
                }
                .button-group {
                    display: flex;
                    gap: 10px;
                    justify-content: flex-end;
                }
                button {
                    padding: 8px 16px;
                    border: 1px solid var(--vscode-button-border);
                    background-color: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                    cursor: pointer;
                    font-family: var(--vscode-font-family);
                }
                button:hover {
                    background-color: var(--vscode-button-hoverBackground);
                }
                button.primary {
                    background-color: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                }
                button.secondary {
                    background-color: var(--vscode-button-secondaryBackground);
                    color: var(--vscode-button-secondaryForeground);
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎨 Generate UI Component</h1>
                    <p>Describe what you want to build and let AI create it for you</p>
                </div>
                
                <div class="input-section">
                    <label for="promptInput">What would you like to create?</label>
                    <textarea 
                        id="promptInput" 
                        placeholder="E.g., A pricing page with 3 tiers (Basic, Pro, Enterprise) with feature comparisons and a call-to-action button..."
                        autofocus
                    ></textarea>
                </div>

                <div class="examples">
                    <h3>💡 Example prompts:</h3>
                    <div class="example-item" onclick="setExample('A modern pricing page with 3 plans: Basic ($9/mo), Pro ($29/mo), and Enterprise ($99/mo). Include feature comparisons, popular badges, and CTA buttons.')">
                        📄 Pricing page with 3 plans and feature comparison
                    </div>
                    <div class="example-item" onclick="setExample('A user dashboard with sidebar navigation, welcome header, stats cards showing metrics, and a recent activity feed.')">
                        📊 User dashboard with stats and activity feed
                    </div>
                    <div class="example-item" onclick="setExample('A login form with email/password fields, remember me checkbox, forgot password link, and social login buttons (Google, GitHub).')">
                        🔐 Login form with social authentication
                    </div>
                    <div class="example-item" onclick="setExample('A product card grid showing items with images, titles, prices, ratings, and add to cart buttons. Include hover effects.')">
                        🛍️ Product card grid for e-commerce
                    </div>
                    <div class="example-item" onclick="setExample('A contact form with name, email, subject, message fields, and a submit button. Include form validation and success state.')">
                        📧 Contact form with validation
                    </div>
                </div>

                <div class="button-group">
                    <button class="secondary" onclick="cancel()">Cancel</button>
                    <button class="primary" onclick="generate()">Generate Component</button>
                </div>
            </div>

            <script>
                const vscode = acquireVsCodeApi();
                
                function setExample(text) {
                    document.getElementById('promptInput').value = text;
                    document.getElementById('promptInput').focus();
                }
                
                function generate() {
                    const prompt = document.getElementById('promptInput').value.trim();
                    if (!prompt || prompt.length < 5) {
                        alert('Please provide a more detailed description (at least 5 characters)');
                        return;
                    }
                    vscode.postMessage({
                        command: 'generate',
                        prompt: prompt
                    });
                }
                
                function cancel() {
                    vscode.postMessage({
                        command: 'cancel'
                    });
                }
                
                // Handle Enter key
                document.getElementById('promptInput').addEventListener('keydown', function(e) {
                    if (e.ctrlKey && e.key === 'Enter') {
                        generate();
                    }
                });
            </script>
        </body>
        </html>`;
    }
}