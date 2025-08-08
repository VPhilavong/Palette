/**
 * Palette AI Extension - Clean Main Entry Point
 * Provides modern sidebar chatbot interface with AI assistance
 */

import * as vscode from 'vscode';
import { SettingsCommands } from './commands/settings-commands';
import { ConversationManager } from './conversation-manager';
import { IntegrationManager } from './initialization/integration-manager';
import { ModernChatbotPanel } from './ui/modern-chatbot-panel';

let conversationManager: ConversationManager;
let modernChatbotProvider: ModernChatbotPanel;
let settingsCommands: SettingsCommands;
let integrationManager: IntegrationManager;

export async function activate(context: vscode.ExtensionContext) {
    console.log('🎨 Palette AI: Extension activation started');
    
    // Initialize integration manager (tools and MCP)
    integrationManager = IntegrationManager.getInstance();
    
    try {
        await integrationManager.initialize(context.extensionUri, context);
        console.log('🎨 Integration system initialized');
    } catch (error) {
        console.error('🎨 Failed to initialize integration system:', error);
        vscode.window.showWarningMessage(`Palette AI integration system failed to start: ${error}`);
    }
    
    // Initialize conversation manager
    conversationManager = new ConversationManager(context);
    
    // Initialize modern chatbot panel provider (using VSCode Elements for native UI)
    console.log('🎨 Using VSCode Elements UI (native components)');
    modernChatbotProvider = new ModernChatbotPanel(context.extensionUri);
    
    // Register the modern webview panel
    const modernChatbotDisposable = vscode.window.registerWebviewViewProvider(
        ModernChatbotPanel.viewType, 
        modernChatbotProvider
    );
    
    // Initialize and register settings commands
    settingsCommands = new SettingsCommands();
    settingsCommands.registerCommands(context);
    
    try {
        // Register modern chatbot command
        const modernChatbotCommand = vscode.commands.registerCommand('palette.openModernChatbot', async () => {
            console.log('🎨 Opening Modern Palette Chatbot');
            await vscode.commands.executeCommand('palette.modernChatbot.focus');
        });
        
        context.subscriptions.push(
            modernChatbotCommand,
            modernChatbotDisposable
        );
        
        console.log('🎨 Palette AI: Commands registered successfully');
        vscode.window.showInformationMessage('🎨 Palette AI activated');
        
    } catch (error) {
        console.error('🎨 Palette AI: Activation failed:', error);
        vscode.window.showErrorMessage(`Palette AI activation failed: ${error}`);
    }
}

export async function deactivate() {
    console.log('🎨 Palette AI: Extension deactivation started');
    
    // Shutdown integration system
    if (integrationManager) {
        console.log('🎨 Shutting down integration system...');
        try {
            await integrationManager.shutdown();
            console.log('🎨 Integration system shutdown successfully');
        } catch (error) {
            console.error('🎨 Error shutting down integration system:', error);
        }
    }
    
    console.log('🎨 Palette AI: Extension deactivated');
}
