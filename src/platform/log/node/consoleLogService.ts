/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import { ILogService, LogLevel } from '../common/logService';

export class ConsoleLogService implements ILogService {
	declare readonly _serviceBrand: undefined;

	constructor(private readonly logLevel: LogLevel = LogLevel.Info) { }

	private log(level: LogLevel, message: string, ...args: any[]): void {
		if (level <= this.logLevel) {
			const timestamp = new Date().toISOString();
			const levelName = LogLevel[level];
			console.log(`[${timestamp}] [${levelName}] ${message}`, ...args);
		}
	}

	trace(message: string, ...args: any[]): void {
		this.log(LogLevel.Trace, message, ...args);
	}

	debug(message: string, ...args: any[]): void {
		this.log(LogLevel.Debug, message, ...args);
	}

	info(message: string, ...args: any[]): void {
		this.log(LogLevel.Info, message, ...args);
	}

	warn(message: string, ...args: any[]): void {
		this.log(LogLevel.Warning, message, ...args);
	}

	error(message: string | Error, ...args: any[]): void {
		if (message instanceof Error) {
			this.log(LogLevel.Error, message.message, message.stack, ...args);
		} else {
			this.log(LogLevel.Error, message, ...args);
		}
	}

	critical(message: string | Error, ...args: any[]): void {
		if (message instanceof Error) {
			this.log(LogLevel.Critical, message.message, message.stack, ...args);
		} else {
			this.log(LogLevel.Critical, message, ...args);
		}
	}
}