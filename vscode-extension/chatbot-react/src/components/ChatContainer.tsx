import React, { useEffect, useRef } from 'react';
import type { Message } from '../types';
import ChatMessage from './ChatMessage';

interface ChatContainerProps {
  messages: Message[];
  isLoading: boolean;
}

const ChatContainer: React.FC<ChatContainerProps> = ({ messages, isLoading }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  return (
    <div className="chat-container" ref={containerRef}>
      {messages.length === 0 ? (
        <div className="empty-state">
          <div className="welcome-icon">🎨</div>
          <div className="welcome-text">Welcome to Palette AI!</div>
          <div className="welcome-subtitle">
            Ask me to generate React components, pages, or help with your UI development.
          </div>
          <div className="welcome-features">
            <p>Running in <strong>React + VSCode Simple Browser</strong> mode</p>
            <p>✅ Perfect input handling • ✅ Component state management • ✅ Real-time updates</p>
          </div>
        </div>
      ) : (
        <div className="messages-list">
          {messages.map((message) => (
            <ChatMessage 
              key={message.id} 
              message={message} 
            />
          ))}
          
          {isLoading && (
            <div className="typing-indicator">
              <div className="typing-dots">
                <div className="dot"></div>
                <div className="dot"></div>
                <div className="dot"></div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ChatContainer;