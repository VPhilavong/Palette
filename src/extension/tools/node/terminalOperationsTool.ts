/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';
import { exec, spawn } from 'child_process';
import * as path from 'path';
import { ILogService } from '../../../platform/log/common/logService';

export interface CommandResult {
    success: boolean;
    command: string;
    stdout: string;
    stderr: string;
    exitCode: number;
    duration: number;
}

export interface PackageInfo {
    name: string;
    version: string;
    description?: string;
    dependencies?: { [key: string]: string };
    devDependencies?: { [key: string]: string };
    scripts?: { [key: string]: string };
}

export class TerminalOperationsTool {
    private terminals: Map<string, vscode.Terminal> = new Map();
    
    constructor(private readonly logService: ILogService) {}

    async executeCommand(command: string, workingDirectory?: string, timeout: number = 30000): Promise<CommandResult> {
        const startTime = Date.now();
        
        return new Promise((resolve, reject) => {
            const options: any = {
                cwd: workingDirectory || vscode.workspace.workspaceFolders?.[0]?.uri.fsPath,
                timeout
            };

            this.logService.info(`TerminalOperationsTool: Executing command: ${command}`, { workingDirectory });

            exec(command, options, (error, stdout, stderr) => {
                const duration = Date.now() - startTime;
                const exitCode = error?.code || 0;
                
                const result: CommandResult = {
                    success: !error || exitCode === 0,
                    command,
                    stdout: stdout.toString(),
                    stderr: stderr.toString(),
                    exitCode,
                    duration
                };

                this.logService.info(`TerminalOperationsTool: Command completed`, {
                    command,
                    success: result.success,
                    duration,
                    exitCode
                });

                resolve(result);
            });
        });
    }

    async executeInteractiveCommand(command: string, terminalName: string = 'Palette Agent'): Promise<vscode.Terminal> {
        let terminal = this.terminals.get(terminalName);
        
        if (!terminal || terminal.exitStatus) {
            terminal = vscode.window.createTerminal({
                name: terminalName,
                cwd: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath
            });
            this.terminals.set(terminalName, terminal);
        }

        terminal.show();
        terminal.sendText(command);

        return terminal;
    }

    // Package Management Operations
    async installPackages(packages: string[], isDev: boolean = false): Promise<CommandResult> {
        const packageManager = await this.detectPackageManager();
        let command: string;

        switch (packageManager) {
            case 'npm':
                command = `npm install ${isDev ? '--save-dev' : '--save'} ${packages.join(' ')}`;
                break;
            case 'yarn':
                command = `yarn add ${isDev ? '--dev' : ''} ${packages.join(' ')}`;
                break;
            case 'pnpm':
                command = `pnpm add ${isDev ? '--save-dev' : '--save'} ${packages.join(' ')}`;
                break;
            default:
                command = `npm install ${isDev ? '--save-dev' : '--save'} ${packages.join(' ')}`;
        }

        return await this.executeCommand(command);
    }

    async uninstallPackages(packages: string[]): Promise<CommandResult> {
        const packageManager = await this.detectPackageManager();
        let command: string;

        switch (packageManager) {
            case 'npm':
                command = `npm uninstall ${packages.join(' ')}`;
                break;
            case 'yarn':
                command = `yarn remove ${packages.join(' ')}`;
                break;
            case 'pnpm':
                command = `pnpm remove ${packages.join(' ')}`;
                break;
            default:
                command = `npm uninstall ${packages.join(' ')}`;
        }

        return await this.executeCommand(command);
    }

    async runScript(scriptName: string): Promise<CommandResult> {
        const packageManager = await this.detectPackageManager();
        let command: string;

        switch (packageManager) {
            case 'npm':
                command = `npm run ${scriptName}`;
                break;
            case 'yarn':
                command = `yarn ${scriptName}`;
                break;
            case 'pnpm':
                command = `pnpm run ${scriptName}`;
                break;
            default:
                command = `npm run ${scriptName}`;
        }

        return await this.executeCommand(command);
    }

    // Development Operations
    async startDevServer(): Promise<vscode.Terminal> {
        const packageInfo = await this.getPackageInfo();
        
        if (packageInfo?.scripts?.dev) {
            return await this.executeInteractiveCommand('npm run dev', 'Dev Server');
        } else if (packageInfo?.scripts?.start) {
            return await this.executeInteractiveCommand('npm run start', 'Dev Server');
        } else if (packageInfo?.scripts?.serve) {
            return await this.executeInteractiveCommand('npm run serve', 'Dev Server');
        } else {
            throw new Error('No dev server script found in package.json');
        }
    }

    async buildProject(): Promise<CommandResult> {
        const packageInfo = await this.getPackageInfo();
        
        if (packageInfo?.scripts?.build) {
            return await this.executeCommand('npm run build');
        } else {
            throw new Error('No build script found in package.json');
        }
    }

    async runTests(): Promise<CommandResult> {
        const packageInfo = await this.getPackageInfo();
        
        if (packageInfo?.scripts?.test) {
            return await this.executeCommand('npm run test');
        } else {
            throw new Error('No test script found in package.json');
        }
    }

    async lintCode(): Promise<CommandResult> {
        const packageInfo = await this.getPackageInfo();
        
        if (packageInfo?.scripts?.lint) {
            return await this.executeCommand('npm run lint');
        } else if (packageInfo?.scripts?.['lint:fix']) {
            return await this.executeCommand('npm run lint:fix');
        } else {
            throw new Error('No lint script found in package.json');
        }
    }

    async formatCode(): Promise<CommandResult> {
        const packageInfo = await this.getPackageInfo();
        
        if (packageInfo?.scripts?.format) {
            return await this.executeCommand('npm run format');
        } else if (packageInfo?.scripts?.prettier) {
            return await this.executeCommand('npm run prettier');
        } else {
            return await this.executeCommand('npx prettier --write .');
        }
    }

    // Git Operations
    async gitStatus(): Promise<CommandResult> {
        return await this.executeCommand('git status --porcelain');
    }

    async gitAdd(files: string[] = ['.']): Promise<CommandResult> {
        return await this.executeCommand(`git add ${files.join(' ')}`);
    }

    async gitCommit(message: string): Promise<CommandResult> {
        return await this.executeCommand(`git commit -m "${message}"`);
    }

    async gitPush(branch?: string): Promise<CommandResult> {
        const command = branch ? `git push origin ${branch}` : 'git push';
        return await this.executeCommand(command);
    }

    async gitBranch(branchName?: string): Promise<CommandResult> {
        if (branchName) {
            return await this.executeCommand(`git checkout -b ${branchName}`);
        } else {
            return await this.executeCommand('git branch -a');
        }
    }

    // Utility Methods
    private async detectPackageManager(): Promise<'npm' | 'yarn' | 'pnpm'> {
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        if (!workspaceRoot) return 'npm';

        // Check for lock files
        const fs = require('fs');
        const yarnLock = path.join(workspaceRoot, 'yarn.lock');
        const pnpmLock = path.join(workspaceRoot, 'pnpm-lock.yaml');
        
        if (fs.existsSync(pnpmLock)) {
            return 'pnpm';
        } else if (fs.existsSync(yarnLock)) {
            return 'yarn';
        } else {
            return 'npm';
        }
    }

    private async getPackageInfo(): Promise<PackageInfo | null> {
        try {
            const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            if (!workspaceRoot) return null;

            const packageJsonPath = path.join(workspaceRoot, 'package.json');
            const fs = require('fs');
            
            if (!fs.existsSync(packageJsonPath)) return null;

            const packageJsonContent = fs.readFileSync(packageJsonPath, 'utf8');
            return JSON.parse(packageJsonContent) as PackageInfo;
        } catch (error) {
            this.logService.error('Failed to read package.json', error);
            return null;
        }
    }

    async updatePackageJson(updates: Partial<PackageInfo>): Promise<CommandResult> {
        try {
            const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            if (!workspaceRoot) {
                throw new Error('No workspace found');
            }

            const packageJsonPath = path.join(workspaceRoot, 'package.json');
            const fs = require('fs');
            
            if (!fs.existsSync(packageJsonPath)) {
                throw new Error('package.json not found');
            }

            const packageJsonContent = fs.readFileSync(packageJsonPath, 'utf8');
            const packageInfo = JSON.parse(packageJsonContent);
            
            // Merge updates
            const updatedPackageInfo = { ...packageInfo, ...updates };
            
            // Write back to file
            fs.writeFileSync(packageJsonPath, JSON.stringify(updatedPackageInfo, null, 2), 'utf8');

            return {
                success: true,
                command: 'updatePackageJson',
                stdout: 'package.json updated successfully',
                stderr: '',
                exitCode: 0,
                duration: 0
            };
        } catch (error) {
            return {
                success: false,
                command: 'updatePackageJson',
                stdout: '',
                stderr: error instanceof Error ? error.message : 'Unknown error',
                exitCode: 1,
                duration: 0
            };
        }
    }

    // Framework-specific operations
    async createNextjsProject(projectName: string): Promise<CommandResult> {
        return await this.executeCommand(`npx create-next-app@latest ${projectName} --typescript --tailwind --eslint`);
    }

    async createReactProject(projectName: string): Promise<CommandResult> {
        return await this.executeCommand(`npx create-react-app ${projectName} --template typescript`);
    }

    async createViteProject(projectName: string, template: string = 'react-ts'): Promise<CommandResult> {
        return await this.executeCommand(`npm create vite@latest ${projectName} -- --template ${template}`);
    }

    // Cleanup
    dispose(): void {
        for (const terminal of this.terminals.values()) {
            terminal.dispose();
        }
        this.terminals.clear();
    }
}