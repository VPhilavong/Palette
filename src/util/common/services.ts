/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

export function createServiceIdentifier<T>(name: string): ServiceIdentifier<T> {
	return new ServiceIdentifier(name);
}

export class ServiceIdentifier<T> {
	constructor(private readonly _name: string) { }

	toString(): string {
		return this._name;
	}
}

export interface IDisposable {
	dispose(): void;
}

export class DisposableStore implements IDisposable {
	private readonly _disposables = new Set<IDisposable>();
	private _isDisposed = false;

	dispose(): void {
		if (this._isDisposed) {
			return;
		}

		this._isDisposed = true;
		this.clear();
	}

	clear(): void {
		try {
			for (const disposable of this._disposables) {
				disposable.dispose();
			}
		} finally {
			this._disposables.clear();
		}
	}

	add<T extends IDisposable>(disposable: T): T {
		if (!disposable) {
			return disposable;
		}
		if (this._isDisposed) {
			disposable.dispose();
		} else {
			this._disposables.add(disposable);
		}
		return disposable;
	}
}