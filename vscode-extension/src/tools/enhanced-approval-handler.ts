/**
 * Enhanced Approval Handler
 * GitHub Copilot-style approval system with rich UI and batch operations
 */

import * as vscode from 'vscode';
import { 
    UserApprovalHandler, 
    ApprovalRequest, 
    ApprovalResponse,
    FilePreview,
    PendingOperation,
    BatchOperation
} from './types';
import { FileApprovalPanel } from '../ui/file-approval-panel';

export class EnhancedApprovalHandler implements UserApprovalHandler {
    private fileApprovalPanel: FileApprovalPanel;
    private userPreferences: Map<string, boolean> = new Map();

    constructor(extensionUri: vscode.Uri) {
        this.fileApprovalPanel = new FileApprovalPanel(extensionUri);
        this.loadUserPreferences();
    }

    /**
     * Request approval for a single operation
     */
    async requestApproval(request: ApprovalRequest): Promise<ApprovalResponse> {
        // Check if user has opted to skip this type of operation
        const preferenceKey = `${request.operation}_${request.dangerLevel}`;
        if (this.userPreferences.has(preferenceKey) && this.userPreferences.get(preferenceKey)) {
            return {
                approved: true,
                skipInFuture: true
            };
        }

        // Show approval UI
        try {
            const response = await this.fileApprovalPanel.requestApproval(request);
            
            // Save user preference if they chose to skip in future
            if (response.skipInFuture) {
                this.userPreferences.set(preferenceKey, true);
                this.saveUserPreferences();
            }

            return response;
        } catch (error) {
            console.error('Error showing approval dialog:', error);
            return {
                approved: false,
                skipInFuture: false
            };
        }
    }

    /**
     * Request approval for batch operations
     */
    async requestBatchApproval(operations: PendingOperation[]): Promise<ApprovalResponse> {
        // Aggregate all files from all operations
        const allFiles: FilePreview[] = [];
        const operationNames = new Set<string>();

        for (const operation of operations) {
            allFiles.push(...operation.preview);
            operationNames.add(operation.tool);
        }

        // Determine overall danger level
        let maxDangerLevel: 'safe' | 'caution' | 'dangerous' = 'safe';
        for (const operation of operations) {
            // This would need to be implemented based on operation analysis
            // For now, assume 'caution' for batch operations
            if (maxDangerLevel === 'safe') {
                maxDangerLevel = 'caution';
            }
        }

        const batchRequest: ApprovalRequest = {
            operation: `Batch Operation (${operations.length} operations)`,
            description: `Execute ${operations.length} operations: ${Array.from(operationNames).join(', ')}`,
            files: allFiles,
            dangerLevel: maxDangerLevel,
            canSkipInFuture: false // Don't allow skipping batch operations
        };

        return this.requestApproval(batchRequest);
    }

    /**
     * Request approval for file creation with conflict resolution
     */
    async requestFileCreationApproval(
        files: Array<{ path: string; content: string; existingContent?: string }>
    ): Promise<ApprovalResponse & { resolvedFiles?: Array<{ path: string; content: string; action: 'overwrite' | 'merge' | 'skip' }> }> {
        const previews: FilePreview[] = files.map(file => ({
            path: file.path,
            operation: file.existingContent ? 'update' : 'create',
            content: file.content,
            exists: !!file.existingContent
        }));

        const conflicts = files.filter(f => f.existingContent);
        
        const request: ApprovalRequest = {
            operation: 'Create Multiple Files',
            description: `Create ${files.length} files. ${conflicts.length > 0 ? `${conflicts.length} files have conflicts.` : ''}`,
            files: previews,
            dangerLevel: conflicts.length > 0 ? 'caution' : 'safe',
            canSkipInFuture: conflicts.length === 0
        };

        // For now, use basic approval - could be enhanced with conflict resolution UI
        const response = await this.requestApproval(request);

        return {
            ...response,
            resolvedFiles: files.map(file => ({
                path: file.path,
                content: file.content,
                action: 'overwrite' as const // Could be enhanced with user choice
            }))
        };
    }

    /**
     * Show operation progress with ability to cancel
     */
    async showOperationProgress(
        operation: string,
        steps: string[],
        onCancel?: () => void
    ): Promise<void> {
        return vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: operation,
            cancellable: !!onCancel
        }, async (progress, token) => {
            if (onCancel) {
                token.onCancellationRequested(onCancel);
            }

            for (let i = 0; i < steps.length; i++) {
                progress.report({
                    message: steps[i],
                    increment: (100 / steps.length)
                });

                // Simulate step delay
                await new Promise(resolve => setTimeout(resolve, 500));

                if (token.isCancellationRequested) {
                    break;
                }
            }
        });
    }

    /**
     * Show summary of completed operations
     */
    async showOperationSummary(
        operation: string,
        results: {
            successful: string[];
            failed: Array<{ path: string; error: string }>;
            skipped: string[];
        }
    ): Promise<void> {
        const total = results.successful.length + results.failed.length + results.skipped.length;
        
        if (results.failed.length === 0) {
            vscode.window.showInformationMessage(
                `✅ ${operation} completed successfully! ${results.successful.length}/${total} operations succeeded.`
            );
        } else {
            const actions = ['Show Details', 'Dismiss'];
            const choice = await vscode.window.showWarningMessage(
                `⚠️ ${operation} completed with issues. ${results.successful.length} succeeded, ${results.failed.length} failed.`,
                ...actions
            );

            if (choice === 'Show Details') {
                const details = [
                    '=== Operation Summary ===',
                    `✅ Successful (${results.successful.length}):`,
                    ...results.successful.map(path => `  • ${path}`),
                    '',
                    `❌ Failed (${results.failed.length}):`,
                    ...results.failed.map(item => `  • ${item.path}: ${item.error}`),
                    ''
                ];

                if (results.skipped.length > 0) {
                    details.push(
                        `⏭️ Skipped (${results.skipped.length}):`,
                        ...results.skipped.map(path => `  • ${path}`),
                        ''
                    );
                }

                const document = await vscode.workspace.openTextDocument({
                    content: details.join('\n'),
                    language: 'plaintext'
                });
                await vscode.window.showTextDocument(document);
            }
        }
    }

    /**
     * Load user preferences from VS Code settings
     */
    private loadUserPreferences(): void {
        const config = vscode.workspace.getConfiguration('palette.approvals');
        const preferences = config.get<Record<string, boolean>>('skipPreferences', {});
        
        for (const [key, value] of Object.entries(preferences)) {
            this.userPreferences.set(key, value);
        }
    }

    /**
     * Save user preferences to VS Code settings
     */
    private saveUserPreferences(): void {
        const config = vscode.workspace.getConfiguration('palette.approvals');
        const preferences: Record<string, boolean> = {};
        
        for (const [key, value] of this.userPreferences) {
            preferences[key] = value;
        }

        config.update('skipPreferences', preferences, vscode.ConfigurationTarget.Global);
    }

    /**
     * Reset user preferences
     */
    async resetUserPreferences(): Promise<void> {
        this.userPreferences.clear();
        const config = vscode.workspace.getConfiguration('palette.approvals');
        await config.update('skipPreferences', {}, vscode.ConfigurationTarget.Global);
        
        vscode.window.showInformationMessage('Approval preferences reset. You will be asked for approval again.');
    }

    /**
     * Show current user preferences
     */
    async showUserPreferences(): Promise<void> {
        if (this.userPreferences.size === 0) {
            vscode.window.showInformationMessage('No approval preferences set.');
            return;
        }

        const preferences = Array.from(this.userPreferences.entries())
            .map(([key, value]) => `• ${key}: ${value ? 'Skip' : 'Ask'}`)
            .join('\n');

        const actions = ['Reset Preferences', 'Close'];
        const choice = await vscode.window.showInformationMessage(
            `Current Approval Preferences:\n\n${preferences}`,
            { modal: true },
            ...actions
        );

        if (choice === 'Reset Preferences') {
            await this.resetUserPreferences();
        }
    }

    /**
     * Dispose of resources
     */
    dispose(): void {
        this.fileApprovalPanel.dispose();
    }
}