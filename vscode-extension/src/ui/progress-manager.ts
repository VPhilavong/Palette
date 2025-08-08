/**
 * Progress Manager
 * Handles progress indicators, cancellation, and user feedback for long-running operations
 */

import * as vscode from 'vscode';

export interface ProgressOptions {
    title: string;
    location: vscode.ProgressLocation;
    cancellable?: boolean;
    autoClose?: boolean;
    showErrorNotification?: boolean;
}

export interface ProgressStep {
    message: string;
    increment?: number;
    totalSteps?: number;
    currentStep?: number;
}

export class ProgressManager {
    private static instance: ProgressManager;
    private activeOperations: Map<string, vscode.CancellationTokenSource> = new Map();

    private constructor() {}

    static getInstance(): ProgressManager {
        if (!ProgressManager.instance) {
            ProgressManager.instance = new ProgressManager();
        }
        return ProgressManager.instance;
    }

    /**
     * Show progress with automatic cancellation support
     */
    async withProgress<T>(
        options: ProgressOptions,
        task: (progress: vscode.Progress<ProgressStep>, token: vscode.CancellationToken) => Promise<T>,
        operationId?: string
    ): Promise<T> {
        const cancellationSource = new vscode.CancellationTokenSource();
        
        if (operationId) {
            // Cancel any existing operation with the same ID
            this.cancelOperation(operationId);
            this.activeOperations.set(operationId, cancellationSource);
        }

        try {
            const result = await vscode.window.withProgress({
                location: options.location,
                title: options.title,
                cancellable: options.cancellable ?? false
            }, async (progress, cancellationToken) => {
                // Handle cancellation from VS Code UI
                const combinedToken = this.createCombinedCancellationToken(
                    cancellationToken,
                    cancellationSource.token
                );

                return await task(progress, combinedToken);
            });

            if (options.autoClose !== false) {
                // Show completion notification
                vscode.window.showInformationMessage(`✅ ${options.title} completed successfully`);
            }

            return result;
        } catch (error: any) {
            if (this.isCancellationError(error)) {
                console.log(`📋 Operation cancelled: ${options.title}`);
                vscode.window.showWarningMessage(`Operation cancelled: ${options.title}`);
                throw new Error('Operation was cancelled');
            } else {
                console.error(`❌ Operation failed: ${options.title}`, error);
                if (options.showErrorNotification !== false) {
                    vscode.window.showErrorMessage(`Failed: ${options.title} - ${error.message}`);
                }
                throw error;
            }
        } finally {
            if (operationId) {
                this.activeOperations.delete(operationId);
            }
            cancellationSource.dispose();
        }
    }

    /**
     * Show project analysis progress
     */
    async showAnalysisProgress<T>(
        task: (progress: vscode.Progress<ProgressStep>, token: vscode.CancellationToken) => Promise<T>
    ): Promise<T> {
        return this.withProgress({
            title: 'Analyzing Project Structure',
            location: vscode.ProgressLocation.Notification,
            cancellable: true,
            showErrorNotification: true
        }, task, 'project-analysis');
    }

    /**
     * Show AI generation progress
     */
    async showGenerationProgress<T>(
        task: (progress: vscode.Progress<ProgressStep>, token: vscode.CancellationToken) => Promise<T>
    ): Promise<T> {
        return this.withProgress({
            title: 'Generating AI Response',
            location: vscode.ProgressLocation.Window,
            cancellable: true,
            autoClose: false // Let the chatbot handle completion feedback
        }, task, 'ai-generation');
    }

    /**
     * Show file operations progress
     */
    async showFileOperationProgress<T>(
        operation: string,
        task: (progress: vscode.Progress<ProgressStep>, token: vscode.CancellationToken) => Promise<T>
    ): Promise<T> {
        return this.withProgress({
            title: `${operation} Files`,
            location: vscode.ProgressLocation.Window,
            cancellable: false, // File operations shouldn't be cancelled mid-way
            showErrorNotification: true
        }, task);
    }

    /**
     * Show settings validation progress
     */
    async showValidationProgress<T>(
        task: (progress: vscode.Progress<ProgressStep>, token: vscode.CancellationToken) => Promise<T>
    ): Promise<T> {
        return this.withProgress({
            title: 'Validating Settings',
            location: vscode.ProgressLocation.Window,
            cancellable: false,
            autoClose: true
        }, task);
    }

    /**
     * Cancel a specific operation
     */
    cancelOperation(operationId: string): void {
        const cancellationSource = this.activeOperations.get(operationId);
        if (cancellationSource) {
            console.log(`🛑 Cancelling operation: ${operationId}`);
            cancellationSource.cancel();
            this.activeOperations.delete(operationId);
        }
    }

    /**
     * Cancel all active operations
     */
    cancelAllOperations(): void {
        console.log(`🛑 Cancelling all operations (${this.activeOperations.size})`);
        this.activeOperations.forEach((source, id) => {
            source.cancel();
        });
        this.activeOperations.clear();
    }

    /**
     * Get status of active operations
     */
    getActiveOperations(): string[] {
        return Array.from(this.activeOperations.keys());
    }

    /**
     * Create progress reporter with step tracking
     */
    createStepTracker(totalSteps: number): {
        reportStep: (message: string, increment?: number) => void;
        complete: () => void;
        currentStep: number;
    } {
        let currentStep = 0;
        
        return {
            reportStep: (message: string, increment: number = 1) => {
                currentStep += increment;
                const percentage = Math.round((currentStep / totalSteps) * 100);
                console.log(`📋 Step ${currentStep}/${totalSteps} (${percentage}%): ${message}`);
            },
            complete: () => {
                console.log(`✅ Completed all ${totalSteps} steps`);
            },
            currentStep
        };
    }

    /**
     * Show indeterminate progress (spinning indicator)
     */
    async showIndeterminateProgress<T>(
        title: string,
        task: () => Promise<T>,
        cancellable: boolean = false
    ): Promise<T> {
        return vscode.window.withProgress({
            location: vscode.ProgressLocation.Window,
            title,
            cancellable
        }, async (progress) => {
            // Show spinning indicator
            progress.report({ increment: -1 });
            return await task();
        });
    }

    /**
     * Helper methods
     */
    private createCombinedCancellationToken(
        token1: vscode.CancellationToken,
        token2: vscode.CancellationToken
    ): vscode.CancellationToken {
        const source = new vscode.CancellationTokenSource();
        
        token1.onCancellationRequested(() => source.cancel());
        token2.onCancellationRequested(() => source.cancel());
        
        return source.token;
    }

    private isCancellationError(error: any): boolean {
        return error && (
            error.message === 'Operation was cancelled' ||
            error.name === 'Cancelled' ||
            error.code === 'Cancelled'
        );
    }

    /**
     * Dispose of resources
     */
    dispose(): void {
        this.cancelAllOperations();
    }
}

// Progress utilities for common operations
export class ProgressUtils {
    static async withRetry<T>(
        operation: () => Promise<T>,
        options: {
            retries: number;
            delay: number;
            progressTitle?: string;
        }
    ): Promise<T> {
        const progressManager = ProgressManager.getInstance();
        
        if (options.progressTitle) {
            return progressManager.withProgress({
                title: options.progressTitle,
                location: vscode.ProgressLocation.Window,
                cancellable: false
            }, async (progress) => {
                return this.executeWithRetry(operation, options, progress);
            });
        } else {
            return this.executeWithRetry(operation, options);
        }
    }

    private static async executeWithRetry<T>(
        operation: () => Promise<T>,
        options: { retries: number; delay: number },
        progress?: vscode.Progress<ProgressStep>
    ): Promise<T> {
        let lastError: any;
        
        for (let attempt = 1; attempt <= options.retries + 1; attempt++) {
            try {
                if (progress) {
                    progress.report({
                        message: `Attempt ${attempt}${options.retries > 0 ? ` of ${options.retries + 1}` : ''}`,
                        increment: attempt > 1 ? 20 : 0
                    });
                }
                
                return await operation();
            } catch (error) {
                lastError = error;
                
                if (attempt <= options.retries) {
                    console.log(`Attempt ${attempt} failed, retrying in ${options.delay}ms...`, error);
                    await new Promise(resolve => setTimeout(resolve, options.delay));
                } else {
                    console.log(`All ${attempt} attempts failed`, error);
                }
            }
        }
        
        throw lastError;
    }

    /**
     * Create a progress reporter for streaming operations
     */
    static createStreamingProgress(title: string): {
        start: () => void;
        update: (message: string, tokensGenerated?: number) => void;
        complete: (totalTokens?: number) => void;
        error: (error: string) => void;
    } {
        let isActive = false;
        
        return {
            start: () => {
                isActive = true;
                console.log(`🌊 Starting streaming operation: ${title}`);
            },
            update: (message: string, tokensGenerated?: number) => {
                if (isActive) {
                    const tokenInfo = tokensGenerated ? ` (${tokensGenerated} tokens)` : '';
                    console.log(`🌊 ${title}: ${message}${tokenInfo}`);
                }
            },
            complete: (totalTokens?: number) => {
                if (isActive) {
                    const tokenInfo = totalTokens ? ` Generated ${totalTokens} tokens.` : '';
                    console.log(`✅ Completed: ${title}.${tokenInfo}`);
                    isActive = false;
                }
            },
            error: (error: string) => {
                if (isActive) {
                    console.error(`❌ Failed: ${title} - ${error}`);
                    isActive = false;
                }
            }
        };
    }
}

// Factory function
export function getProgressManager(): ProgressManager {
    return ProgressManager.getInstance();
}