/**
 * Settings Commands
 * Provides command handlers for settings management
 */

import * as vscode from 'vscode';
import { getSettingsManager, PaletteSettings } from '../settings/settings-manager';

export class SettingsCommands {
    private settingsManager = getSettingsManager();

    /**
     * Register all settings-related commands
     */
    registerCommands(context: vscode.ExtensionContext): void {
        const commands = [
            vscode.commands.registerCommand('palette.openSettings', () => this.openSettings()),
            vscode.commands.registerCommand('palette.configureApiKeys', () => this.configureApiKeys()),
            vscode.commands.registerCommand('palette.selectModel', () => this.selectModel()),
            vscode.commands.registerCommand('palette.validateSettings', () => this.validateSettings()),
            vscode.commands.registerCommand('palette.exportSettings', () => this.exportSettings()),
            vscode.commands.registerCommand('palette.resetSettings', () => this.resetSettings()),
            vscode.commands.registerCommand('palette.showSettingsMenu', () => this.showSettingsMenu())
        ];

        context.subscriptions.push(...commands);
        console.log('⚙️ Settings commands registered');
    }

    private async openSettings(): Promise<void> {
        await vscode.commands.executeCommand('workbench.action.openSettings', '@ext:palette');
    }

    private async configureApiKeys(): Promise<void> {
        await this.settingsManager.showSettingsUI();
    }

    private async selectModel(): Promise<void> {
        await this.settingsManager.showSettingsUI();
    }

    private async validateSettings(): Promise<void> {
        await this.settingsManager.showSettingsUI();
    }

    private async exportSettings(): Promise<void> {
        await this.settingsManager.exportSettings();
    }

    private async resetSettings(): Promise<void> {
        await this.settingsManager.resetSettings();
    }

    private async showSettingsMenu(): Promise<void> {
        await this.settingsManager.showSettingsUI();
    }
}