/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import { ServiceIdentifier, createServiceIdentifier } from '../../../util/common/services';
import { ServiceCollection } from './serviceCollection';

export const IInstantiationService = createServiceIdentifier<IInstantiationService>('IInstantiationService');

export interface IInstantiationService {
	readonly _serviceBrand: undefined;
	
	createInstance<T>(ctor: new (...args: any[]) => T, ...args: any[]): T;
	invokeFunction<R>(fn: (accessor: ServicesAccessor) => R): R;
}

export interface ServicesAccessor {
	get<T>(id: ServiceIdentifier<T>): T;
}

export class InstantiationService implements IInstantiationService {
	declare readonly _serviceBrand: undefined;

	constructor(private readonly _services: ServiceCollection) { }

	createInstance<T>(ctor: new (...args: any[]) => T, ...args: any[]): T {
		// Simple instantiation - in a full implementation this would handle dependency injection
		if (typeof ctor !== 'function') {
			throw new Error('Constructor must be a function');
		}
		const instance = new ctor(...args);
		return instance;
	}

	invokeFunction<R>(fn: (accessor: ServicesAccessor) => R): R {
		const accessor: ServicesAccessor = {
			get: <T>(id: ServiceIdentifier<T>): T => {
				const service = this._services.get(id);
				if (!service) {
					throw new Error(`Service ${id.toString()} not found`);
				}
				if (typeof service === 'function') {
					// If it's a constructor, instantiate it
					return this.createInstance(service as new (...args: any[]) => T);
				}
				return service;
			}
		};
		return fn(accessor);
	}
}