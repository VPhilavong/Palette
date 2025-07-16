/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import { createServiceIdentifier } from '../../../util/common/services';

export const ILogService = createServiceIdentifier<ILogService>('ILogService');

export enum LogLevel {
	Off = 0,
	Critical = 1,
	Error = 2,
	Warning = 3,
	Info = 4,
	Debug = 5,
	Trace = 6
}

export interface ILogService {
	readonly _serviceBrand: undefined;
	
	trace(message: string, ...args: any[]): void;
	debug(message: string, ...args: any[]): void;
	info(message: string, ...args: any[]): void;
	warn(message: string, ...args: any[]): void;
	error(message: string | Error, ...args: any[]): void;
	critical(message: string | Error, ...args: any[]): void;
}