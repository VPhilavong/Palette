import * as vscode from 'vscode';

export async function activate(context: vscode.ExtensionContext) {
  console.log('🎨 Palette Extension activating...');
  
  // Register test command first
  context.subscriptions.push(
    vscode.commands.registerCommand('palette.test', () => {
      vscode.window.showInformationMessage('✅ Palette extension is working! Commands are registered.');
      console.log('✅ palette.test command executed');
    })
  );

  // Register enhanced webview command with gradual loading
  context.subscriptions.push(
    vscode.commands.registerCommand('palette.openEnhancedWebview', async () => {
      try {
        vscode.window.showInformationMessage('🎨 Loading Enhanced Palette Panel...');
        
        // Dynamically import the EnhancedPalettePanel to avoid startup issues
        const { EnhancedPalettePanel } = await import('./EnhancedPalettePanel');
        EnhancedPalettePanel.createOrShow(context.extensionUri, context);
      } catch (error: any) {
        vscode.window.showErrorMessage(`Failed to load Enhanced Panel: ${error.message}`);
        console.error('Enhanced panel import error:', error);
        
        // Fallback to basic panel
        try {
          const { PalettePanel } = await import('./PalettePanel');
          const { PaletteService } = await import('./paletteService');
          const paletteService = new PaletteService();
          PalettePanel.createOrShow(context.extensionUri, paletteService);
        } catch (fallbackError: any) {
          vscode.window.showErrorMessage(`Fallback also failed: ${fallbackError.message}`);
        }
      }
    })
  );

  // Register other commands with error handling
  context.subscriptions.push(
    vscode.commands.registerCommand('palette.generate', async () => {
      const prompt = await vscode.window.showInputBox({
        placeHolder: 'Describe the component you want to generate',
        prompt: 'E.g., "modern pricing section with three tiers"',
        validateInput: (value) => {
          return value && value.trim().length > 0 ? null : 'Please enter a description';
        }
      });
      if (!prompt) return;

      try {
        const { PaletteService } = await import('./paletteService');
        const paletteService = new PaletteService();
        await paletteService.generateComponent({ prompt });
        vscode.window.showInformationMessage(`Component generated successfully!`);
      } catch (error: any) {
        vscode.window.showErrorMessage(`Generation failed: ${error.message}`);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('palette.analyze', async () => {
      try {
        const { PaletteService } = await import('./paletteService');
        const paletteService = new PaletteService();
        await paletteService.analyzeProject();
        vscode.window.showInformationMessage('Project analysis completed!');
      } catch (error: any) {
        vscode.window.showErrorMessage(`Analysis failed: ${error.message}`);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('palette.generateInFolder', async (uri: vscode.Uri) => {
      const prompt = await vscode.window.showInputBox({
        placeHolder: 'Describe the component you want to generate',
        prompt: 'Component will be generated in the selected folder'
      });
      if (!prompt) return;

      try {
        const { PaletteService } = await import('./paletteService');
        const paletteService = new PaletteService();
        await paletteService.generateComponent({ 
          prompt, 
          outputPath: uri.fsPath 
        });
        vscode.window.showInformationMessage(`Component generated in ${uri.fsPath}`);
      } catch (error: any) {
        vscode.window.showErrorMessage(`Generation failed: ${error.message}`);
      }
    })
  );

  console.log('🎨 Palette Extension activated successfully with commands registered');
}

export function deactivate() {
  console.log('🎨 Palette Extension deactivated');
}