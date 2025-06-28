import * as vscode from 'vscode';

/**
 * Centralized logging utility
 */
export class Logger {
    private static instance: Logger;
    private outputChannel: vscode.OutputChannel;

    private constructor() {
        this.outputChannel = vscode.window.createOutputChannel('UI Copilot');
    }

    static getInstance(): Logger {
        if (!Logger.instance) {
            Logger.instance = new Logger();
        }
        return Logger.instance;
    }

    static initialize(): void {
        Logger.getInstance();
    }

    info(message: string, ...args: any[]): void {
        const formattedMessage = Logger.formatMessage('INFO', message, args);
        console.log(formattedMessage);
        this.outputChannel?.appendLine(formattedMessage);
    }

    warn(message: string, ...args: any[]): void {
        const formattedMessage = Logger.formatMessage('WARN', message, args);
        console.warn(formattedMessage);
        this.outputChannel?.appendLine(formattedMessage);
    }

    error(message: string, error?: Error, ...args: any[]): void {
        const formattedMessage = Logger.formatMessage('ERROR', message, args);
        console.error(formattedMessage, error);
        this.outputChannel?.appendLine(formattedMessage);
        if (error) {
            this.outputChannel?.appendLine(error.stack || error.message);
        }
    }

    debug(message: string, ...args: any[]): void {
        const formattedMessage = Logger.formatMessage('DEBUG', message, args);
        console.debug(formattedMessage);
        this.outputChannel?.appendLine(formattedMessage);
    }

    private static formatMessage(level: string, message: string, args: any[]): string {
        const timestamp = new Date().toISOString();
        const argsStr = args.length > 0 ? ` ${JSON.stringify(args)}` : '';
        return `[${timestamp}] ${level}: ${message}${argsStr}`;
    }

    show(): void {
        this.outputChannel?.show();
    }

    dispose(): void {
        this.outputChannel?.dispose();
    }
}