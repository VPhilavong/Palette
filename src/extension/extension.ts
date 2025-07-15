/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

// Load environment variables for development
try {
	const dotenv = require('dotenv');
	const path = require('path');
	
	// Load .env file from project root
	const result = dotenv.config({ 
		path: path.join(__dirname, '../../.env') 
	});
	
	if (result.parsed) {
		console.log('Palette: Loaded environment variables from .env file');
		console.log('Palette: Available env vars:', Object.keys(result.parsed));
	} else if (result.error) {
		console.log('Palette: .env file not found or error loading:', result.error.message);
	}
	
	// Also try loading from workspace root as fallback
	if (!result.parsed) {
		const workspaceResult = dotenv.config();
		if (workspaceResult.parsed) {
			console.log('Palette: Loaded environment variables from workspace .env file');
		}
	}
} catch (e) {
	console.log('Palette: dotenv not available, using system environment variables only');
}

import * as vscode from 'vscode';
import { ServiceCollection } from '../platform/instantiation/common/serviceCollection';
import { IInstantiationService, InstantiationService } from '../platform/instantiation/common/instantiationService';
import { ILogService, LogLevel } from '../platform/log/common/logService';
import { ConsoleLogService } from '../platform/log/node/consoleLogService';
import { IConfigurationService } from '../platform/configuration/common/configurationService';
import { ConfigurationService } from '../platform/configuration/node/configurationService';
import { PaletteSidebarProvider } from './sidebar/paletteSidebarProvider';

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
	
	try {
		logService.info('Palette UI Agent: Starting activation');
		
		// Register sidebar webview provider - this is your main interface
		const sidebarProvider = new PaletteSidebarProvider(context.extensionUri);
		context.subscriptions.push(
			vscode.window.registerWebviewViewProvider(
				PaletteSidebarProvider.viewType,
				sidebarProvider
			)
		);
		
		// Register commands
		registerCommands(context, logService);
		
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
	logService: ILogService
): void {
	// Focus Palette sidebar
	const focusCommand = vscode.commands.registerCommand('palette.focus', async () => {
		await vscode.commands.executeCommand('palette.sidebar.focus');
	});
	
	context.subscriptions.push(focusCommand);
}