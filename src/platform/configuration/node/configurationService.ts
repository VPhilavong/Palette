/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';
import { IConfigurationService } from '../common/configurationService';

export class ConfigurationService implements IConfigurationService {
	declare readonly _serviceBrand: undefined;

	getValue<T>(key: string): T | undefined;
	getValue<T>(key: string, defaultValue: T): T;
	getValue<T>(key: string, defaultValue?: T): T | undefined {
		const config = vscode.workspace.getConfiguration();
		const value = config.get<T>(key);
		
		if (value !== undefined) {
			return value;
		}
		
		return defaultValue;
	}
}