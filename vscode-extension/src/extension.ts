import * as vscode from 'vscode';
import { PalettePanel } from './PalettePanel';
import { PaletteService } from './paletteService';
import * as path from 'path';
import * as dotenv from 'dotenv';
import * as fs from 'fs';

let paletteService: PaletteService;

export async function activate(context: vscode.ExtensionContext) {
  // Load API keys from VS Code settings first
  const config = vscode.workspace.getConfiguration('palette');
  const openaiKey = config.get<string>('openaiApiKey') || '';
  const anthropicKey = config.get<string>('anthropicApiKey') || '';
  
  console.log('Loading API keys from settings...');
  console.log(`OpenAI key from settings: ${openaiKey ? 'Found' : 'Not found'}`);
  console.log(`Anthropic key from settings: ${anthropicKey ? 'Found' : 'Not found'}`);
  
  // Debug: Also check if settings are being read correctly
  const allSettings = config.inspect('openaiApiKey');
  console.log('OpenAI key settings inspection:', allSettings);
  
  if (openaiKey && openaiKey.trim()) {
    process.env.OPENAI_API_KEY = openaiKey.trim();
    console.log('Set OPENAI_API_KEY in process.env from VS Code settings');
  }
  
  if (anthropicKey && anthropicKey.trim()) {
    process.env.ANTHROPIC_API_KEY = anthropicKey.trim();
    console.log('Set ANTHROPIC_API_KEY in process.env from VS Code settings');
  }
  
  // If no keys in settings, try loading from .env file
  if (!process.env.OPENAI_API_KEY && !process.env.ANTHROPIC_API_KEY) {
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    if (workspaceRoot) {
      const envPath = path.join(workspaceRoot, '.env');
      if (fs.existsSync(envPath)) {
        dotenv.config({ path: envPath });
        console.log('Loaded .env file from workspace root');
      }
      
      // Also check parent directory for Palette project .env
      const parentEnvPath = path.join(workspaceRoot, '..', '.env');
      if (fs.existsSync(parentEnvPath)) {
        dotenv.config({ path: parentEnvPath });
        console.log('Loaded .env file from parent directory');
      }
    }
  }

  // Initialize service
  paletteService = new PaletteService();
  
  // Log final environment state
  paletteService.getOutputChannel().appendLine('=== Extension Activation ===');
  paletteService.getOutputChannel().appendLine(`Environment variables after loading:`);
  paletteService.getOutputChannel().appendLine(`  OPENAI_API_KEY: ${process.env.OPENAI_API_KEY ? 'Set' : 'Not set'}`);
  paletteService.getOutputChannel().appendLine(`  ANTHROPIC_API_KEY: ${process.env.ANTHROPIC_API_KEY ? 'Set' : 'Not set'}`);
  
  // Check if Palette CLI is installed
  const isInstalled = await paletteService.checkInstallation();
  if (!isInstalled) {
    const action = await vscode.window.showWarningMessage(
      'Palette CLI not found. Please install it to use this extension.',
      'Show Instructions',
      'Show Output'
    );
    if (action === 'Show Instructions') {
      vscode.env.openExternal(vscode.Uri.parse('https://github.com/yourusername/palette#installation'));
    } else if (action === 'Show Output') {
      paletteService.getOutputChannel().show();
    }
  }

  // Check for API key
  if (!process.env.OPENAI_API_KEY && !process.env.ANTHROPIC_API_KEY) {
    const action = await vscode.window.showWarningMessage(
      'No API key found. Please configure in VS Code settings or add to .env file.',
      'Open Settings',
      'Show Output'
    );
    if (action === 'Open Settings') {
      vscode.commands.executeCommand('workbench.action.openSettings', 'palette.openaiApiKey');
    } else if (action === 'Show Output') {
      paletteService.getOutputChannel().show();
    }
  } else {
    // Show which API is configured and where it came from
    const apiProvider = process.env.OPENAI_API_KEY ? 'OpenAI' : 'Anthropic';
    const source = config.get<string>('openaiApiKey') || config.get<string>('anthropicApiKey') ? 'VS Code settings' : '.env file';
    paletteService.getOutputChannel().appendLine(`✅ Using ${apiProvider} API (loaded from ${source})`);
  }

  // Register commands
  context.subscriptions.push(
    vscode.commands.registerCommand('palette.openWebview', () => {
      PalettePanel.createOrShow(context.extensionUri, paletteService);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('palette.generate', async () => {
      // Get user input
      const prompt = await vscode.window.showInputBox({
        placeHolder: 'Describe the component you want to generate',
        prompt: 'E.g., "modern pricing section with three tiers"',
        validateInput: (value) => {
          return value && value.trim().length > 0 ? null : 'Please enter a description';
        }
      });

      if (!prompt) {
        return;
      }

      try {
        // Get current file's directory or workspace root
        const activeEditor = vscode.window.activeTextEditor;
        let outputPath: string | undefined;
        
        if (activeEditor) {
          outputPath = path.dirname(activeEditor.document.uri.fsPath);
        }

        // Get UI library preference from settings
        const config = vscode.workspace.getConfiguration('palette');
        const uiLibrary = config.get<string>('defaultUILibrary', 'auto-detect');
        const showWarnings = config.get<boolean>('showLibraryWarnings', true);

        // Generate component with UI library preference
        const result = await paletteService.generateWithProgress({
          prompt,
          outputPath,
          uiLibrary,
          showLibraryWarnings: showWarnings
        });

        // Show success message
        vscode.window.showInformationMessage('Component generated successfully!');
        
        // Show the output channel with results
        paletteService.getOutputChannel().show();
        
      } catch (error: any) {
        vscode.window.showErrorMessage(`Generation failed: ${error.message}`);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('palette.analyze', async () => {
      try {
        const result = await paletteService.analyzeProject();
        
        // Format the analysis results
        const items: string[] = [];
        if (result.framework) items.push(`Framework: ${result.framework}`);
        if (result.styling) items.push(`Styling: ${result.styling}`);
        if (result.hasTypeScript) items.push('TypeScript: ✓');
        if (result.hasTailwind) items.push('Tailwind: ✓');
        
        // Show results
        vscode.window.showInformationMessage(
          `Project Analysis: ${items.join(', ')}`
        );
        
        // Also show in output channel
        const channel = paletteService.getOutputChannel();
        channel.appendLine('\n=== Project Analysis ===');
        items.forEach(item => channel.appendLine(item));
        channel.show();
        
      } catch (error: any) {
        vscode.window.showErrorMessage(`Analysis failed: ${error.message}`);
      }
    })
  );

  // Test environment command
  context.subscriptions.push(
    vscode.commands.registerCommand('palette.testEnvironment', async () => {
      await paletteService.testEnvironment();
      paletteService.getOutputChannel().show();
    })
  );

  // Context menu command for folders
  context.subscriptions.push(
    vscode.commands.registerCommand('palette.generateInFolder', async (uri: vscode.Uri) => {
      const prompt = await vscode.window.showInputBox({
        placeHolder: 'Describe the component you want to generate',
        prompt: 'Component will be created in: ' + path.basename(uri.fsPath)
      });

      if (!prompt) {
        return;
      }

      try {
        // Get UI library preference from settings
        const config = vscode.workspace.getConfiguration('palette');
        const uiLibrary = config.get<string>('defaultUILibrary', 'auto-detect');
        const showWarnings = config.get<boolean>('showLibraryWarnings', true);

        await paletteService.generateWithProgress({
          prompt,
          outputPath: uri.fsPath,
          uiLibrary,
          showLibraryWarnings: showWarnings
        });
        
        vscode.window.showInformationMessage('Component generated successfully!');
        
      } catch (error: any) {
        vscode.window.showErrorMessage(`Generation failed: ${error.message}`);
      }
    })
  );
  
  // Listen for configuration changes
  context.subscriptions.push(
    vscode.workspace.onDidChangeConfiguration(e => {
      if (e.affectsConfiguration('palette.openaiApiKey') || e.affectsConfiguration('palette.anthropicApiKey')) {
        const config = vscode.workspace.getConfiguration('palette');
        const openaiKey = config.get<string>('openaiApiKey');
        const anthropicKey = config.get<string>('anthropicApiKey');
        
        // Update environment variables
        if (openaiKey && openaiKey.trim()) {
          process.env.OPENAI_API_KEY = openaiKey;
          vscode.window.showInformationMessage('OpenAI API key updated from settings');
        }
        
        if (anthropicKey && anthropicKey.trim()) {
          process.env.ANTHROPIC_API_KEY = anthropicKey;
          vscode.window.showInformationMessage('Anthropic API key updated from settings');
        }
        
        // Update the palette panel if it's open
        if (PalettePanel.currentPanel) {
          PalettePanel.currentPanel.sendToWebview('🔄 API keys updated from settings');
        }
      }
      
      // Handle UI library setting changes
      if (e.affectsConfiguration('palette.defaultUILibrary') || e.affectsConfiguration('palette.showLibraryWarnings')) {
        const config = vscode.workspace.getConfiguration('palette');
        const uiLibrary = config.get<string>('defaultUILibrary', 'auto-detect');
        
        // Show notification about UI library change
        vscode.window.showInformationMessage(`UI library preference updated to: ${uiLibrary}`);
        
        // Update the palette panel if it's open
        if (PalettePanel.currentPanel) {
          PalettePanel.currentPanel.sendToWebview(`🎨 UI library updated to: ${uiLibrary}`);
        }
      }
    })
  );
}

export function deactivate() {
  // Clean up
}
