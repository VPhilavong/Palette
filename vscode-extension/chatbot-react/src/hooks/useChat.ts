import { useState, useEffect, useCallback } from 'react';
import type { Message, ConversationState } from '../types';
import { PaletteAPI } from '../services/api';
import { ConversationStorage } from '../services/storage';

// Read configuration from URL parameters (passed from VSCode extension)
const getConfigFromUrl = () => {
  const params = new URLSearchParams(window.location.search);
  return {
    apiKey: params.get('apiKey') || '',
    model: params.get('model') || 'gpt-4o-mini',
    backendUrl: params.get('backendUrl') || 'http://localhost:8765'
  };
};

export const useChat = () => {
  const [config] = useState(getConfigFromUrl());
  const [state, setState] = useState<ConversationState>({
    messages: [],
    isLoading: false,
    connectionStatus: 'disconnected'
  });

  // Load conversation history on mount
  useEffect(() => {
    const loadedMessages = ConversationStorage.loadMessages();
    setState(prev => ({ ...prev, messages: loadedMessages }));
    testConnection();
  }, []);

  // Save messages whenever they change
  useEffect(() => {
    if (state.messages.length > 0) {
      ConversationStorage.saveMessages(state.messages);
    }
  }, [state.messages]);

  /**
   * Test backend connection
   */
  const testConnection = useCallback(async () => {
    setState(prev => ({ ...prev, connectionStatus: 'checking' }));
    
    try {
      const isConnected = await PaletteAPI.testConnection();
      setState(prev => ({ 
        ...prev, 
        connectionStatus: isConnected ? 'connected' : 'disconnected' 
      }));
      return isConnected;
    } catch (error) {
      setState(prev => ({ ...prev, connectionStatus: 'disconnected' }));
      return false;
    }
  }, []);

  /**
   * Send a message and get AI response
   */
  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || state.isLoading) return;

    // Add user message
    const userMessage: Message = {
      id: ConversationStorage.generateMessageId(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString()
    };

    setState(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      isLoading: true
    }));

    try {
      // Prepare conversation history for backend
      const conversationHistory = [...state.messages, userMessage].map(msg => ({
        role: msg.role === 'error' ? 'assistant' : msg.role,
        content: msg.content
      }));

      // Generate AI response using config from VSCode
      const response = await PaletteAPI.generateResponse({
        message: content.trim(),
        conversation_history: conversationHistory,
        project_context: {},
        api_key: config.apiKey,
        model: config.model
      });

      // Add AI response
      const aiMessage: Message = {
        id: ConversationStorage.generateMessageId(),
        role: 'assistant',
        content: response.content,
        timestamp: new Date().toISOString(),
        codeBlocks: response.codeBlocks
      };

      setState(prev => ({
        ...prev,
        messages: [...prev.messages, aiMessage],
        isLoading: false,
        connectionStatus: 'connected'
      }));

    } catch (error: any) {
      console.error('Error sending message:', error);
      
      // Add error message
      const errorMessage: Message = {
        id: ConversationStorage.generateMessageId(),
        role: 'error',
        content: `Sorry, I encountered an error: ${error.message || 'Unknown error occurred'}`,
        timestamp: new Date().toISOString()
      };

      setState(prev => ({
        ...prev,
        messages: [...prev.messages, errorMessage],
        isLoading: false,
        connectionStatus: 'disconnected'
      }));
    }
  }, [state.messages, state.isLoading]);

  /**
   * Clear all messages
   */
  const clearMessages = useCallback(() => {
    setState(prev => ({
      ...prev,
      messages: []
    }));
    ConversationStorage.clearMessages();
  }, []);

  /**
   * Export conversation
   */
  const exportConversation = useCallback(() => {
    const exportText = ConversationStorage.exportMessages(state.messages);
    const blob = new Blob([exportText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `palette-conversation-${new Date().toISOString().slice(0, 19)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [state.messages]);

  /**
   * Add a message directly (for testing or special cases)
   */
  const addMessage = useCallback((message: Omit<Message, 'id' | 'timestamp'>) => {
    const fullMessage: Message = {
      ...message,
      id: ConversationStorage.generateMessageId(),
      timestamp: new Date().toISOString()
    };

    setState(prev => ({
      ...prev,
      messages: [...prev.messages, fullMessage]
    }));
  }, []);

  return {
    messages: state.messages,
    isLoading: state.isLoading,
    connectionStatus: state.connectionStatus,
    config,
    sendMessage,
    clearMessages,
    exportConversation,
    testConnection,
    addMessage
  };
};