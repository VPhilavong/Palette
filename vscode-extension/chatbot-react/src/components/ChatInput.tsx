import React, { useState, useRef, useEffect } from 'react';
import type { KeyboardEvent } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  connectionStatus: 'connected' | 'disconnected' | 'checking';
}

const ChatInput: React.FC<ChatInputProps> = ({ onSend, isLoading, connectionStatus }) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-focus on mount - this should work perfectly in React!
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  }, []);

  const handleSend = () => {
    if (!message.trim() || isLoading) return;
    
    onSend(message);
    setMessage('');
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    
    // Auto-resize textarea
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
  };

  const isDisabled = isLoading || connectionStatus === 'checking';

  return (
    <div className="chat-input-container">
      <div className="input-box">
        <textarea
          ref={textareaRef}
          className="message-input"
          placeholder="Ask Palette to generate components, pages, or help with your UI..."
          value={message}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          disabled={isDisabled}
          rows={1}
        />
        <div className="input-actions">
          <button 
            className="send-button"
            onClick={handleSend}
            disabled={!message.trim() || isDisabled}
            title={isDisabled ? 'Please wait...' : 'Send message (Enter)'}
          >
            {isLoading ? (
              <div className="loading-spinner">⟳</div>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22,2 15,22 11,13 2,9"/>
              </svg>
            )}
          </button>
        </div>
      </div>
      
      {connectionStatus === 'disconnected' && (
        <div className="connection-warning">
          ⚠️ Backend disconnected - responses will be limited until connection is restored
        </div>
      )}
    </div>
  );
};

export default ChatInput;