/**
 * Typed message interfaces for VS Code Messenger communication
 * between extension and webview
 */

// Base message types
export interface BaseMessage {
    id?: string;
    timestamp?: number;
}

// User input messages
export interface UserMessage extends BaseMessage {
    type: 'user-message';
    text: string;
    conversationId?: string;
}

export interface ImageUploadMessage extends BaseMessage {
    type: 'image-upload';
    name: string;
    mimeType: string;
    dataUrl: string;
}

// AI response messages
export interface AIResponseMessage extends BaseMessage {
    type: 'ai-response';
    content: string;
    isComplete: boolean;
    conversationId: string;
    metadata?: {
        intent?: string;
        componentCode?: string;
        filePath?: string;
        confidence?: number;
    };
}

export interface AIStreamMessage extends BaseMessage {
    type: 'ai-stream';
    chunk: string;
    conversationId: string;
    isFirst?: boolean;
    isLast?: boolean;
}

// System/status messages
export interface StatusMessage extends BaseMessage {
    type: 'status';
    status: 'connecting' | 'connected' | 'disconnected' | 'error' | 'generating' | 'ready';
    message?: string;
}

export interface ErrorMessage extends BaseMessage {
    type: 'error';
    error: string;
    details?: string;
    recoverable?: boolean;
    actions?: Array<{
        label: string;
        action: string;
    }>;
}

// Project analysis messages
export interface AnalyzeRequest extends BaseMessage {
    type: 'analyze-request';
    projectPath?: string;
}

export interface AnalyzeResponse extends BaseMessage {
    type: 'analyze-response';
    analysis: {
        framework: string;
        styling: string;
        hasTypeScript: boolean;
        hasTailwind: boolean;
        componentsPath?: string;
        pagesPath?: string;
    };
}

// File operation messages
export interface FileCreatedMessage extends BaseMessage {
    type: 'file-created';
    filePath: string;
    content: string;
    success: boolean;
}

export interface PreviewCodeMessage extends BaseMessage {
    type: 'preview-code';
    code: string;
    language: string;
    filePath?: string;
}

// Conversation management
export interface ConversationStarted extends BaseMessage {
    type: 'conversation-started';
    conversationId: string;
    projectPath: string;
}

export interface ConversationEnded extends BaseMessage {
    type: 'conversation-ended';
    conversationId: string;
}

// Configuration messages
export interface ConfigUpdateMessage extends BaseMessage {
    type: 'config-update';
    config: {
        apiProvider?: 'openai' | 'anthropic';
        model?: string;
        streaming?: boolean;
    };
}

// Union type for all possible messages
export type PaletteMessage = 
    | UserMessage
    | ImageUploadMessage
    | AIResponseMessage
    | AIStreamMessage
    | StatusMessage
    | ErrorMessage
    | AnalyzeRequest
    | AnalyzeResponse
    | FileCreatedMessage
    | PreviewCodeMessage
    | ConversationStarted
    | ConversationEnded
    | ConfigUpdateMessage;

// Extension to webview messages
export type ExtensionToWebviewMessage = 
    | AIResponseMessage
    | AIStreamMessage
    | StatusMessage
    | ErrorMessage
    | AnalyzeResponse
    | FileCreatedMessage
    | ConversationStarted
    | ConversationEnded
    | ConfigUpdateMessage;

// Webview to extension messages
export type WebviewToExtensionMessage = 
    | UserMessage
    | ImageUploadMessage
    | AnalyzeRequest
    | PreviewCodeMessage;

// SSE event types for Server-Sent Events
export interface SSEEvent {
    type: 'chunk' | 'complete' | 'error' | 'status';
    data: any;
    id?: string;
}

// HTTP API request/response types
export interface GenerateRequest {
    message: string;
    conversationId?: string;
    projectPath: string;
    conversationHistory?: Array<{
        role: 'user' | 'assistant';
        content: string;
    }>;
}

export interface GenerateResponse {
    response: string;
    conversationId: string;
    metadata?: {
        intent?: string;
        componentCode?: string;
        filePath?: string;
        confidence?: number;
    };
}

export interface StreamingResponse {
    conversationId: string;
    streamUrl: string; // URL for SSE connection
}