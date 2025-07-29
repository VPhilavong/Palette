import * as vscode from 'vscode';
import { PalettePanel } from './PalettePanel';

export function activate(context: vscode.ExtensionContext) {
  context.subscriptions.push(
    vscode.commands.registerCommand('palette.openWebview', () => {
      PalettePanel.createOrShow(context.extensionUri);
    })
  );
}

PalettePanel.currentPanel?.sendToWebview([
  'Hello! Ask me to generate a React component!'
]);

export function deactivate() {}
