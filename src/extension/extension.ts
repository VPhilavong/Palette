/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';
import { ServiceCollection } from '../platform/instantiation/common/serviceCollection';
import { IInstantiationService, InstantiationService } from '../platform/instantiation/common/instantiationService';
import { ILogService, LogLevel } from '../platform/log/common/logService';
import { ConsoleLogService } from '../platform/log/node/consoleLogService';
import { IConfigurationService } from '../platform/configuration/common/configurationService';
import { ConfigurationService } from '../platform/configuration/node/configurationService';
import { IChatAgentService } from '../platform/chat/common/chatAgentService';
import { ChatAgentService } from './chat/chatAgentService';
import { IToolsService } from './tools/common/toolsService';
import { ToolsService } from './tools/node/toolsService';

let serviceCollection: ServiceCollection | undefined;
let instantiationService: IInstantiationService | undefined;

export async function activate(context: vscode.ExtensionContext): Promise<void> {
	// Initialize service collection
	serviceCollection = new ServiceCollection();
	
	// Core services
	const logService = new ConsoleLogService(LogLevel.Info);
	serviceCollection.set(ILogService, logService);
	
	const configurationService = new ConfigurationService();
	serviceCollection.set(IConfigurationService, configurationService);
	
	// Create instantiation service
	instantiationService = new InstantiationService(serviceCollection);
	serviceCollection.set(IInstantiationService, instantiationService);
	
	// Chat and tools services
	serviceCollection.set(IChatAgentService, ChatAgentService);
	serviceCollection.set(IToolsService, ToolsService);
	
	try {
		logService.info('Palette UI Agent: Starting activation');
		
		// Register chat agents
		const chatAgentService = new ChatAgentService(logService, configurationService);
		const chatAgentDisposable = chatAgentService.register();
		context.subscriptions.push(chatAgentDisposable);
		
		// Register tools
		const toolsService = new ToolsService(logService, configurationService);
		const toolsDisposable = toolsService.register();
		context.subscriptions.push(toolsDisposable);
		
		// Register commands
		registerCommands(context, chatAgentService, toolsService);
		
		logService.info('Palette UI Agent: Activation complete');
	} catch (error) {
		logService.error('Palette UI Agent: Activation failed', error);
		throw error;
	}
}

export function deactivate(): void {
	if (serviceCollection) {
		serviceCollection.dispose();
		serviceCollection = undefined;
	}
	instantiationService = undefined;
}

function registerCommands(
	context: vscode.ExtensionContext, 
	chatAgentService: ChatAgentService,
	toolsService: ToolsService
): void {
	// Analyze Component command
	const analyzeCommand = vscode.commands.registerCommand('palette.analyzeComponent', async (uri?: vscode.Uri) => {
		// Open chat and suggest analyze command
		await vscode.commands.executeCommand('workbench.panel.chat.view.copilot.focus');
		await vscode.commands.executeCommand('workbench.action.chat.newChat', '@ui /analyze');
	});
	
	// Generate Component command  
	const generateCommand = vscode.commands.registerCommand('palette.generateComponent', async () => {
		// Open chat and suggest generate command
		await vscode.commands.executeCommand('workbench.panel.chat.view.copilot.focus');
		await vscode.commands.executeCommand('workbench.action.chat.newChat', '@ui /generate');
	});
	
	// Critique Design command
	const critiqueCommand = vscode.commands.registerCommand('palette.critiqueDesign', async (uri?: vscode.Uri) => {
		// Open chat and suggest critique command
		await vscode.commands.executeCommand('workbench.panel.chat.view.copilot.focus');
		await vscode.commands.executeCommand('workbench.action.chat.newChat', '@ui /critique');
	});
	
	context.subscriptions.push(analyzeCommand, generateCommand, critiqueCommand);
}