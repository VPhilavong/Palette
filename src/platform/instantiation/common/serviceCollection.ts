/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import { ServiceIdentifier, IDisposable } from '../../../util/common/services';

export interface IServiceCollection {
	set<T>(id: ServiceIdentifier<T>, instance: T): T;
	set<T>(id: ServiceIdentifier<T>, ctor: new (...args: any[]) => T): T;
	has(id: ServiceIdentifier<any>): boolean;
}

export class ServiceCollection implements IServiceCollection, IDisposable {
	private readonly _services = new Map<ServiceIdentifier<any>, any>();

	set<T>(id: ServiceIdentifier<T>, instanceOrCtor: T | (new (...args: any[]) => T)): T {
		const result = this._services.get(id);
		this._services.set(id, instanceOrCtor);
		return result;
	}

	has(id: ServiceIdentifier<any>): boolean {
		return this._services.has(id);
	}

	get<T>(id: ServiceIdentifier<T>): T | undefined {
		return this._services.get(id);
	}

	dispose(): void {
		for (const [, value] of this._services) {
			if (value && typeof value.dispose === 'function') {
				value.dispose();
			}
		}
		this._services.clear();
	}
}