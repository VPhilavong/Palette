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

  private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri, paletteService: PaletteService) {
    this._panel = panel;
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
              this.sendToWebview('💬 Message received, starting generation...');
              this.handleGenerate(message.text);
              break;
            case 'imageUpload':
              const info = `📷 Received image "${message.name}" (${message.type})`;
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
        this.sendToWebview('❌ Please provide a component description');
        return;
      }
      
      // Send initial message
      this.sendToWebview(`🚀 Generating component for: "${prompt}"`);
      this.sendToWebview(`📡 Starting Palette CLI...`);
      
      let hasReceivedData = false;
      let messageCount = 0;
      
      // Add timeout to prevent hanging
      const timeout = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Generation timed out after 3 minutes')), 180000);
      });
      
      // Stream the generation with timeout
      await Promise.race([
        this._paletteService.streamGenerate(
          { prompt: prompt.trim() },
          (data) => {
            hasReceivedData = true;
            messageCount++;
            // Send streaming data to webview
            this._panel.webview.postMessage({ type: 'stream', data });
          },
          (error) => {
            // Send error to webview
            this._panel.webview.postMessage({ type: 'error', error });
          }
        ),
        timeout
      ]);
      
      // Send completion message
      if (hasReceivedData) {
        this.sendToWebview(`✅ Generation complete! (${messageCount} messages received)`);
      } else {
        this.sendToWebview('⚠️ Generation completed but no output was captured.');
        this.sendToWebview('🔍 Check the Output panel (View > Output > Code Palette) for details.');
      }
      
    } catch (error: any) {
      // Parse error message for better user feedback
      let errorMessage = error.message;
      if (errorMessage.includes('No API key found')) {
        errorMessage = 'No API key found. Please configure your OpenAI or Anthropic API key in VS Code settings.';
      } else if (errorMessage.includes('palette generate')) {
        errorMessage = 'Failed to generate component. Please check the Output panel for details.';
      }
      
      this._panel.webview.postMessage({ type: 'error', error: errorMessage });
      vscode.window.showErrorMessage(`Generation failed: ${errorMessage}`);
    }
  }

  private async handleAnalyze() {
    try {
      this.sendToWebview('🔍 Analyzing project...');
      
      const result = await this._paletteService.analyzeProject();
      
      // Format the analysis results
      const items: string[] = ['📊 Project Analysis:'];
      if (result.framework) items.push(`  • Framework: ${result.framework}`);
      if (result.styling) items.push(`  • Styling: ${result.styling}`);
      if (result.hasTypeScript) items.push('  • TypeScript: ✓');
      if (result.hasTailwind) items.push('  • Tailwind: ✓');
      
      // Send formatted results
      items.forEach(item => this.sendToWebview(item));
      
    } catch (error: any) {
      this.sendToWebview(`❌ Analysis failed: ${error.message}`);
      vscode.window.showErrorMessage(`Analysis failed: ${error.message}`);
    }
  }

  private async sendWelcomeMessage() {
    setTimeout(async () => {
      this.sendToWebview('👋 Welcome to Palette!');
      this.sendToWebview('I can help you generate React components with AI.');
      this.sendToWebview('Try: "create a modern hero section with gradient background"');
      
      // Run installation check and show status
      this.sendToWebview('🔍 Checking installation...');
      
      try {
        const isInstalled = await this._paletteService.checkInstallation();
        if (isInstalled) {
          this.sendToWebview('✅ Palette is ready! You can start generating components.');
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

    // Clean up resources
    this._panel.dispose();

    while (this._disposables.length) {
      const x = this._disposables.pop();
      if (x) {
        x.dispose();
      }
    }
  }
}
