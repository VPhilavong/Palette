import * as vscode from 'vscode';

/**
 * Centralized logging utility
 */
export class Logger {
    private static outputChannel: vscode.OutputChannel;

    static initialize(): void {
        Logger.outputChannel = vscode.window.createOutputChannel('UI Copilot');
    }

    static info(message: string, ...args: any[]): void {
        const formattedMessage = Logger.formatMessage('INFO', message, args);
        console.log(formattedMessage);
        Logger.outputChannel?.appendLine(formattedMessage);
    }

    static warn(message: string, ...args: any[]): void {
        const formattedMessage = Logger.formatMessage('WARN', message, args);
        console.warn(formattedMessage);
        Logger.outputChannel?.appendLine(formattedMessage);
    }

    static error(message: string, error?: Error, ...args: any[]): void {
        const formattedMessage = Logger.formatMessage('ERROR', message, args);
        console.error(formattedMessage, error);
        Logger.outputChannel?.appendLine(formattedMessage);
        if (error) {
            Logger.outputChannel?.appendLine(error.stack || error.message);
        }
    }

    static debug(message: string, ...args: any[]): void {
        const formattedMessage = Logger.formatMessage('DEBUG', message, args);
        console.debug(formattedMessage);
        Logger.outputChannel?.appendLine(formattedMessage);
    }

    private static formatMessage(level: string, message: string, args: any[]): string {
        const timestamp = new Date().toISOString();
        const argsStr = args.length > 0 ? ` ${JSON.stringify(args)}` : '';
        return `[${timestamp}] ${level}: ${message}${argsStr}`;
    }

    static show(): void {
        Logger.outputChannel?.show();
    }

    static dispose(): void {
        Logger.outputChannel?.dispose();
    }
}