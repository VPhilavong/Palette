/**
 * Git Operations Tools
 * Tools for git version control operations
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { z } from 'zod';
import { 
    PaletteTool, 
    ToolExecutionContext, 
    ToolResult 
} from './types';

/**
 * Git status tool
 */
export const gitStatusTool: PaletteTool = {
    name: 'git_status',
    description: 'Get the current git repository status',
    category: 'git-operations',
    dangerLevel: 'safe',
    inputSchema: z.object({
        includeUntracked: z.boolean().optional().default(true).describe('Include untracked files'),
        short: z.boolean().optional().default(false).describe('Use short format')
    }),
    async execute(params, context: ToolExecutionContext): Promise<ToolResult> {
        if (!context.workspacePath) {
            return {
                success: false,
                error: {
                    code: 'NO_WORKSPACE',
                    message: 'No workspace folder is open',
                    recoverable: false
                }
            };
        }

        try {
            // Use VS Code's git extension API if available
            const gitExtension = vscode.extensions.getExtension('vscode.git')?.exports;
            if (gitExtension) {
                const git = gitExtension.getAPI(1);
                const repo = git.repositories[0];
                
                if (repo) {
                    const status = repo.state;
                    
                    return {
                        success: true,
                        data: {
                            branch: status.HEAD?.name || 'unknown',
                            changes: status.workingTreeChanges.length,
                            staged: status.indexChanges.length,
                            untracked: status.untrackedChanges?.length || 0,
                            ahead: status.HEAD?.ahead || 0,
                            behind: status.HEAD?.behind || 0,
                            files: {
                                modified: status.workingTreeChanges.map((c: any) => c.uri.fsPath),
                                staged: status.indexChanges.map((c: any) => c.uri.fsPath),
                                untracked: status.untrackedChanges?.map((c: any) => c.uri.fsPath) || []
                            }
                        },
                        followUpSuggestions: [
                            `On branch: ${status.HEAD?.name || 'unknown'}`,
                            `${status.workingTreeChanges.length} modified, ${status.indexChanges.length} staged`,
                            status.workingTreeChanges.length > 0 ? 'Use git_add to stage changes' : 'Working tree clean'
                        ]
                    };
                }
            }

            // Fallback to terminal command
            const terminal = vscode.window.createTerminal({
                name: 'Palette Git Status',
                cwd: context.workspacePath
            });

            const command = params.short ? 'git status --short' : 'git status';
            terminal.sendText(command);
            terminal.show();

            return {
                success: true,
                data: {
                    command,
                    message: 'Git status command executed in terminal'
                },
                followUpSuggestions: [
                    'Check terminal for git status output',
                    'Git status shows current repository state'
                ]
            };

        } catch (error: any) {
            return {
                success: false,
                error: {
                    code: 'GIT_STATUS_ERROR',
                    message: `Failed to get git status: ${error.message}`,
                    details: error,
                    recoverable: true
                }
            };
        }
    }
};

/**
 * Git add files tool
 */
export const gitAddTool: PaletteTool = {
    name: 'git_add',
    description: 'Stage files for git commit',
    category: 'git-operations',
    requiresApproval: true,
    dangerLevel: 'caution',
    inputSchema: z.object({
        files: z.array(z.string()).optional().describe('Files to stage (relative paths)'),
        all: z.boolean().optional().default(false).describe('Stage all changes (git add .)')
    }),
    async execute(params, context: ToolExecutionContext): Promise<ToolResult> {
        if (!context.workspacePath) {
            return {
                success: false,
                error: {
                    code: 'NO_WORKSPACE',
                    message: 'No workspace folder is open',
                    recoverable: false
                }
            };
        }

        try {
            const terminal = vscode.window.createTerminal({
                name: 'Palette Git Add',
                cwd: context.workspacePath
            });

            let command: string;
            if (params.all) {
                command = 'git add .';
            } else if (params.files && params.files.length > 0) {
                const filePaths = params.files.map((f: string) => `"${f}"`).join(' ');
                command = `git add ${filePaths}`;
            } else {
                return {
                    success: false,
                    error: {
                        code: 'INVALID_PARAMS',
                        message: 'Either specify files or set all=true',
                        recoverable: true
                    }
                };
            }

            terminal.sendText(command);
            terminal.show();

            return {
                success: true,
                data: {
                    command,
                    filesStaged: params.all ? 'all changes' : params.files?.length || 0
                },
                followUpSuggestions: [
                    `Staged ${params.all ? 'all changes' : `${params.files?.length || 0} files`}`,
                    'Files are now ready for commit',
                    'Use git_commit to create a commit'
                ]
            };

        } catch (error: any) {
            return {
                success: false,
                error: {
                    code: 'GIT_ADD_ERROR',
                    message: `Failed to stage files: ${error.message}`,
                    details: error,
                    recoverable: true
                }
            };
        }
    }
};

/**
 * Git commit tool
 */
export const gitCommitTool: PaletteTool = {
    name: 'git_commit',
    description: 'Create a git commit with staged changes',
    category: 'git-operations',
    requiresApproval: true,
    dangerLevel: 'caution',
    inputSchema: z.object({
        message: z.string().describe('Commit message'),
        addAll: z.boolean().optional().default(false).describe('Stage all changes before committing')
    }),
    async execute(params, context: ToolExecutionContext): Promise<ToolResult> {
        if (!context.workspacePath) {
            return {
                success: false,
                error: {
                    code: 'NO_WORKSPACE',
                    message: 'No workspace folder is open',
                    recoverable: false
                }
            };
        }

        try {
            const terminal = vscode.window.createTerminal({
                name: 'Palette Git Commit',
                cwd: context.workspacePath
            });

            let commands: string[] = [];
            
            if (params.addAll) {
                commands.push('git add .');
            }

            // Escape quotes in commit message
            const escapedMessage = params.message.replace(/"/g, '\\"');
            commands.push(`git commit -m "${escapedMessage}"`);

            commands.forEach(cmd => terminal.sendText(cmd));
            terminal.show();

            return {
                success: true,
                data: {
                    message: params.message,
                    commands,
                    addedAll: params.addAll
                },
                followUpSuggestions: [
                    'Git commit created successfully',
                    `Message: "${params.message}"`,
                    'Check terminal for commit details'
                ]
            };

        } catch (error: any) {
            return {
                success: false,
                error: {
                    code: 'GIT_COMMIT_ERROR',
                    message: `Failed to create commit: ${error.message}`,
                    details: error,
                    recoverable: true
                }
            };
        }
    }
};

/**
 * Git branch info tool
 */
export const gitBranchInfoTool: PaletteTool = {
    name: 'git_branch_info',
    description: 'Get information about git branches',
    category: 'git-operations',
    dangerLevel: 'safe',
    inputSchema: z.object({
        includeRemote: z.boolean().optional().default(false).describe('Include remote branches')
    }),
    async execute(params, context: ToolExecutionContext): Promise<ToolResult> {
        if (!context.workspacePath) {
            return {
                success: false,
                error: {
                    code: 'NO_WORKSPACE',
                    message: 'No workspace folder is open',
                    recoverable: false
                }
            };
        }

        try {
            // Use VS Code's git extension API if available
            const gitExtension = vscode.extensions.getExtension('vscode.git')?.exports;
            if (gitExtension) {
                const git = gitExtension.getAPI(1);
                const repo = git.repositories[0];
                
                if (repo) {
                    const refs = repo.state.refs;
                    const currentBranch = repo.state.HEAD?.name;
                    
                    const localBranches = refs
                        .filter((ref: any) => ref.type === 0) // Local branches
                        .map((ref: any) => ref.name);
                    
                    const remoteBranches = refs
                        .filter((ref: any) => ref.type === 1) // Remote branches
                        .map((ref: any) => ref.name);

                    return {
                        success: true,
                        data: {
                            current: currentBranch,
                            local: localBranches,
                            remote: params.includeRemote ? remoteBranches : undefined,
                            totalLocal: localBranches.length,
                            totalRemote: remoteBranches.length
                        },
                        followUpSuggestions: [
                            `Current branch: ${currentBranch || 'unknown'}`,
                            `${localBranches.length} local branches`,
                            params.includeRemote ? `${remoteBranches.length} remote branches` : 'Use includeRemote for remote branches'
                        ]
                    };
                }
            }

            // Fallback to terminal
            const terminal = vscode.window.createTerminal({
                name: 'Palette Git Branch',
                cwd: context.workspacePath
            });

            const command = params.includeRemote ? 'git branch -a' : 'git branch';
            terminal.sendText(command);
            terminal.show();

            return {
                success: true,
                data: {
                    command,
                    message: 'Git branch command executed in terminal'
                },
                followUpSuggestions: [
                    'Check terminal for branch information',
                    'Current branch marked with *'
                ]
            };

        } catch (error: any) {
            return {
                success: false,
                error: {
                    code: 'GIT_BRANCH_ERROR',
                    message: `Failed to get branch info: ${error.message}`,
                    details: error,
                    recoverable: true
                }
            };
        }
    }
};

/**
 * Git operations tools collection
 */
export class GitOperationsTools {
    static getAllTools(): PaletteTool[] {
        return [
            gitStatusTool,
            gitAddTool,
            gitCommitTool,
            gitBranchInfoTool
        ];
    }

    static registerAll(registry: any): void {
        this.getAllTools().forEach(tool => {
            registry.registerTool(tool, { enabled: true });
        });
        console.log('📝 Registered git operation tools');
    }
}