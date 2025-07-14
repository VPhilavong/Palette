/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import { createServiceIdentifier } from '../../../util/common/services';

export const IConfigurationService = createServiceIdentifier<IConfigurationService>('IConfigurationService');

export interface IConfigurationService {
	readonly _serviceBrand: undefined;
	
	getValue<T>(key: string): T | undefined;
	getValue<T>(key: string, defaultValue: T): T;
}