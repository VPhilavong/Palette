import React from 'react';
import { useChat } from '../hooks/useChat';
import ChatHeader from './ChatHeader';
import ChatToolbar from './ChatToolbar';
import ChatContainer from './ChatContainer';
import ChatInput from './ChatInput';
import './ChatbotInterface.css';

const ChatbotInterface: React.FC = () => {
  const {
    messages,
    isLoading,
    connectionStatus,
    config,
    sendMessage,
    clearMessages,
    exportConversation,
    testConnection
  } = useChat();

  return (
    <div className="chatbot-interface">
      <ChatHeader 
        connectionStatus={connectionStatus}
        config={config}
        onTestConnection={testConnection}
      />
      
      <ChatToolbar 
        onClear={clearMessages}
        onExport={exportConversation}
        messageCount={messages.length}
      />
      
      <ChatContainer 
        messages={messages}
        isLoading={isLoading}
      />
      
      <ChatInput 
        onSend={sendMessage}
        isLoading={isLoading}
        connectionStatus={connectionStatus}
      />
    </div>
  );
};

export default ChatbotInterface;