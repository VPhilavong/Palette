// Types for the Palette AI Chatbot

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'error';
  content: string;
  timestamp: string;
  codeBlocks?: CodeBlock[];
}

export interface CodeBlock {
  language: string;
  code: string;
  filename?: string;
}

export interface ConversationState {
  messages: Message[];
  isLoading: boolean;
  connectionStatus: 'connected' | 'disconnected' | 'checking';
}

export interface BackendResponse {
  content: string;
  codeBlocks?: CodeBlock[];
  intent?: string;
  suggestedActions?: string[];
}

export interface BackendRequest {
  message: string;
  conversation_history: Array<{
    role: string;
    content: string;
  }>;
  project_context?: any;
  api_key?: string;
  model?: string;
}