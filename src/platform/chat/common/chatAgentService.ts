/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import { createServiceIdentifier, IDisposable } from '../../../util/common/services';

export const IChatAgentService = createServiceIdentifier<IChatAgentService>('IChatAgentService');

export interface IChatAgentService {
	readonly _serviceBrand: undefined;
	register(): IDisposable;
}