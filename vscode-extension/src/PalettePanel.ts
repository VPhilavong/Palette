import * as vscode from 'vscode';
import { getChatWebviewHtml } from './ui/chat'; 

export class PalettePanel {
  public static currentPanel: PalettePanel | undefined;

  private readonly _panel: vscode.WebviewPanel;
  private readonly _extensionUri: vscode.Uri;
  private readonly _disposables: vscode.Disposable[] = [];

  private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri) {
    this._panel = panel;
    this._extensionUri = extensionUri;

    this._panel.webview.html = getChatWebviewHtml(this._panel, this._extensionUri);


    this._panel.webview.onDidReceiveMessage(
        message => {
          switch (message.command) {
            case 'selectSuggestion':
              vscode.window.showInformationMessage(`You selected: ${message.text}`);
              break;
            case 'userMessage':
              vscode.window.showInformationMessage(`User asked: ${message.text}`);
              // TODO: Run your AI or CLI backend here and send output back
              break;
          }
        },
        null,
        []
      );
      this._panel.webview.onDidReceiveMessage(
        message => {
          switch (message.command) {
            case 'selectSuggestion':
              vscode.window.showInformationMessage(`You selected: ${message.text}`);
              break;
            case 'userMessage':
              vscode.window.showInformationMessage(`User asked: ${message.text}`);
              this.sendToWebview(`You said: ${message.text}`);
              break;
            case 'imageUpload':
              const info = `📷 Received image "${message.name}" (${message.type})`;
              vscode.window.showInformationMessage(info);
              this.sendToWebview(info);
              break;
          }
        },
        undefined,
        this._disposables
      );
      
      
    }


  public static createOrShow(extensionUri: vscode.Uri) {
    const column = vscode.ViewColumn.Beside;

    if (PalettePanel.currentPanel) {
      PalettePanel.currentPanel._panel.reveal(column);
    } else {
      const panel = vscode.window.createWebviewPanel(
        'copilotPanel',
        'Code Palette',
        column,
        {
          enableScripts: true,
          localResourceRoots: [vscode.Uri.joinPath(extensionUri, 'media')],
        }
      );
      
      PalettePanel.currentPanel = new PalettePanel(panel, extensionUri);
    }
  }

  public sendToWebview(suggestion: string) {
      this._panel.webview.postMessage({ type: 'output', suggestions: [suggestion] });
  }

  
}
