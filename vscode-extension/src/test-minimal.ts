// Minimal test extension to isolate activation issues
import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    console.log('🧪 TEST: Extension activation started');
    
    // Register a simple test command
    const disposable = vscode.commands.registerCommand('palette.test', () => {
        vscode.window.showInformationMessage('Test command works!');
        console.log('🧪 TEST: Command executed successfully');
    });
    
    context.subscriptions.push(disposable);
    
    // Test if we can register the unified command
    const unifiedDisposable = vscode.commands.registerCommand('palette.openUnified', () => {
        vscode.window.showInformationMessage('Unified command works!');
        console.log('🧪 TEST: Unified command executed successfully');
    });
    
    context.subscriptions.push(unifiedDisposable);
    
    console.log('🧪 TEST: Extension activation completed successfully');
    console.log('🧪 TEST: Registered commands:', ['palette.test', 'palette.openUnified']);
}

export function deactivate() {
    console.log('🧪 TEST: Extension deactivated');
}