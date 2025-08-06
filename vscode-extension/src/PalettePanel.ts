import * as vscode from 'vscode';
import { getChatWebviewHtml } from './ui/chat';
import { PaletteService } from './paletteService';
export class PalettePanel {
  public static currentPanel: PalettePanel | undefined;
  public static getCurrentPanel(): PalettePanel | undefined {
    return PalettePanel.currentPanel;
  }
  private readonly _panel: vscode.WebviewPanel;
  private readonly _extensionUri: vscode.Uri;
  private readonly _disposables: vscode.Disposable[] = [];
  private readonly _paletteService: PaletteService;
  private readonly _conversationHistory: Array<{role: string, content: string}> = [];
  private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri, paletteService: PaletteService) {
    this._panel = panel;
    this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
    this._extensionUri = extensionUri;
    this._paletteService = paletteService;
    this._panel.webview.html = getChatWebviewHtml(this._panel, this._extensionUri);
    this._panel.webview.onDidReceiveMessage(
        async message => {
          switch (message.command) {
            case 'selectSuggestion':
              // Handle suggestion selection - run it as a generate command
              this.handleGenerate(message.text);
              break;
            case 'userMessage':
              // Handle user message - generate component
              console.log('Received userMessage:', message.text);
              this.sendToWebview(':speech_balloon: Message received, starting generation...');
              this.handleGenerate(message.text);
              break;
            case 'imageUpload':
              const info = `:camera: Received image "${message.name}" (${message.type})`;
              vscode.window.showInformationMessage(info);
              this.sendToWebview(info);
              // TODO: Implement image-based generation
              break;
            case 'analyze':
              // Handle project analysis
              this.handleAnalyze();
              break;
          }
        },
        undefined,
        this._disposables
      );
      // Send welcome message
      this.sendWelcomeMessage();
    }
  public static createOrShow(extensionUri: vscode.Uri, paletteService: PaletteService) {
    const column = vscode.ViewColumn.Beside;
    if (PalettePanel.currentPanel) {
      PalettePanel.currentPanel._panel.reveal(column);
    } else {
      const panel = vscode.window.createWebviewPanel(
        'palettePanel',
        'Code Palette',
        column,
        {
          enableScripts: true,
          localResourceRoots: [vscode.Uri.joinPath(extensionUri, 'media')],
        }
      );
      PalettePanel.currentPanel = new PalettePanel(panel, extensionUri, paletteService);
    }
  }
  public sendToWebview(suggestion: string) {
      this._panel.webview.postMessage({ type: 'output', suggestions: [suggestion] });
  }
  private async handleGenerate(prompt: string) {
    try {
      // Validate prompt
      if (!prompt || prompt.trim().length === 0) {
        this.sendToWebview('Please provide a component description');
        return;
      }

      // Add user message to conversation history
      this._conversationHistory.push({ role: 'user', content: prompt.trim() });

      // Send initial thinking message
      this.sendToWebview('Let me create that component for you...');

      // Use conversational generation
      const result = await this._paletteService.conversationalGenerate(
        prompt.trim(),
        this._conversationHistory
      );

      // Add assistant response to conversation history
      this._conversationHistory.push({ role: 'assistant', content: result.response });

      // Send the response to the webview
      this.sendToWebview(result.response);

      // If there's metadata (like component code), we could handle it specially
      if (result.metadata && result.metadata.component_code) {
        // Send as a structured message for potential UI enhancements
        this._panel.webview.postMessage({ 
          type: 'componentGenerated', 
          code: result.metadata.component_code,
          intent: result.metadata.intent 
        });
      }

    } catch (error: any) {
      // Parse error message for better user feedback
      let errorMessage = error.message;
      if (errorMessage.includes('No API key found')) {
        errorMessage = 'No API key found. Please configure your OpenAI or Anthropic API key in VS Code settings.';
      } else if (errorMessage.includes('conversation') || errorMessage.includes('Failed to process conversation')) {
        errorMessage = 'Failed to process conversation. Please check the Output panel for details.';
      } else if (errorMessage.includes('No output received')) {
        errorMessage = 'The conversation command produced no output. Please check your API keys and try again.';
      } else if (errorMessage.includes('Process exited with code')) {
        errorMessage = 'The conversation process failed. Please check the Output panel (View → Output → Code Palette) for details.';
      }
      
      // Send user-friendly error to webview
      this.sendToWebview(`❌ Error: ${errorMessage}`);
      
      // Log detailed error for debugging
      this._paletteService.getOutputChannel().appendLine(`❌ Detailed error: ${error.message}`);
      this._paletteService.getOutputChannel().appendLine(`❌ Error stack: ${error.stack || 'No stack trace'}`);
      this._paletteService.getOutputChannel().show();
      
      // Show error notification
      vscode.window.showErrorMessage(`Generation failed: ${errorMessage}`);
    }
  }
  private async handleAnalyze() {
    try {
      this.sendToWebview(':mag: Analyzing project...');
      const result = await this._paletteService.analyzeProject();
      // Format the analysis results
      const items: string[] = [':bar_chart: Project Analysis:'];
      if (result.framework) items.push(`  • Framework: ${result.framework}`);
      if (result.styling) items.push(`  • Styling: ${result.styling}`);
      if (result.hasTypeScript) items.push('  • TypeScript: ✓');
      if (result.hasTailwind) items.push('  • Tailwind: ✓');
      // Send formatted results
      items.forEach(item => this.sendToWebview(item));
    } catch (error: any) {
      this.sendToWebview(`:x: Analysis failed: ${error.message}`);
      vscode.window.showErrorMessage(`Analysis failed: ${error.message}`);
    }
  }
  private async sendWelcomeMessage() {
    setTimeout(async () => {
      this.sendToWebview('👋 Hi! I\'m your AI UI developer assistant.');
      this.sendToWebview('I can help you create, modify, and improve React components through natural conversation.');
      this.sendToWebview('Just describe what you want: "Create a pricing card with three tiers" or "Make this button more accessible"');
      
      // Run installation check and show status
      this.sendToWebview('🔍 Checking my setup...');
      try {
        const isInstalled = await this._paletteService.checkInstallation();
        if (isInstalled) {
          this.sendToWebview('✅ I\'m ready to help! What would you like to build?');
        } else {
          this.sendToWebview('❌ Setup incomplete. Please check the Output panel for details.');
          this.sendToWebview('💡 View → Output → Code Palette for troubleshooting info.');
        }
      } catch (error) {
        this.sendToWebview('❌ Installation check failed. Please check the Output panel.');
      }
    }, 500);
  }
  public dispose() {
    PalettePanel.currentPanel = undefined;
    this._panel.dispose();
    while (this._disposables.length) {
      const x = this._disposables.pop();
      if (x) {
        x.dispose();
      }
    }
  }
}






