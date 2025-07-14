/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import { createServiceIdentifier, IDisposable } from '../../../util/common/services';

export const IToolsService = createServiceIdentifier<IToolsService>('IToolsService');

export interface IToolsService {
	readonly _serviceBrand: undefined;
	register(): IDisposable;
}