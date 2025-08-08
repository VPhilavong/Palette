import React from 'react';

interface ChatToolbarProps {
  onClear: () => void;
  onExport: () => void;
  messageCount: number;
}

const ChatToolbar: React.FC<ChatToolbarProps> = ({ onClear, onExport, messageCount }) => {
  const handleClear = () => {
    if (messageCount === 0) {
      return;
    }
    
    if (confirm('Are you sure you want to clear the conversation?')) {
      onClear();
    }
  };

  const handleExport = () => {
    if (messageCount === 0) {
      alert('No conversation to export');
      return;
    }
    onExport();
  };

  return (
    <div className="chat-toolbar">
      <button 
        className="toolbar-button"
        onClick={handleClear}
        disabled={messageCount === 0}
        title={messageCount === 0 ? 'No messages to clear' : 'Clear conversation'}
      >
        🗑️ Clear Chat ({messageCount})
      </button>
      
      <button 
        className="toolbar-button"
        onClick={handleExport}
        disabled={messageCount === 0}
        title={messageCount === 0 ? 'No messages to export' : 'Export conversation'}
      >
        📤 Export Chat
      </button>
    </div>
  );
};

export default ChatToolbar;