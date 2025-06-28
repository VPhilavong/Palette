import * as vscode from 'vscode';
import * as path from 'path';

/**
 * File system utilities
 */
export class FileUtils {
    /**
     * Safely read file content
     */
    static async readFile(uri: vscode.Uri): Promise<string | null> {
        try {
            const content = await vscode.workspace.fs.readFile(uri);
            return content.toString();
        } catch (error) {
            console.warn(`Failed to read file ${uri.fsPath}:`, error);
            return null;
        }
    }

    /**
     * Write content to file
     */
    static async writeFile(uri: vscode.Uri, content: string): Promise<boolean> {
        try {
            await vscode.workspace.fs.writeFile(uri, Buffer.from(content, 'utf8'));
            return true;
        } catch (error) {
            console.error(`Failed to write file ${uri.fsPath}:`, error);
            return false;
        }
    }

    /**
     * Get relative path from workspace
     */
    static getRelativePath(filePath: string): string {
        return vscode.workspace.asRelativePath(filePath);
    }

    /**
     * Get file extension
     */
    static getExtension(filePath: string): string {
        return path.extname(filePath);
    }

    /**
     * Check if file exists
     */
    static async exists(uri: vscode.Uri): Promise<boolean> {
        try {
            await vscode.workspace.fs.stat(uri);
            return true;
        } catch {
            return false;
        }
    }
}