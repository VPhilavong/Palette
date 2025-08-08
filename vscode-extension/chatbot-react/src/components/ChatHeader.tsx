import React from 'react';

interface ChatHeaderProps {
  connectionStatus: 'connected' | 'disconnected' | 'checking';
  config: { apiKey: string; model: string; backendUrl: string };
  onTestConnection: () => void;
}

const ChatHeader: React.FC<ChatHeaderProps> = ({ connectionStatus, config, onTestConnection }) => {
  const getStatusIcon = () => {
    switch (connectionStatus) {
      case 'connected': return '●';
      case 'disconnected': return '●';
      case 'checking': return '●';
      default: return '●';
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return 'Connected';
      case 'disconnected': return 'Disconnected';
      case 'checking': return 'Checking...';
      default: return 'Unknown';
    }
  };

  return (
    <div className="chat-header">
      <div className="logo-container">
        <div className="logo-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 3C7 3 3 7 3 12c0 2.5 1.3 4.7 3.3 6a3 3 0 0 0 4.3-2.8c0-1.1.9-2 2-2h2a2 2 0 0 1 2 2 2 2 0 0 0 3 1.73A9 9 0 0 0 21 12c0-5-4-9-9-9z" />
            <circle cx="7.5" cy="10.5" r="1.2" />
            <circle cx="12" cy="7.5" r="1.2" />
            <circle cx="16.5" cy="10.5" r="1.2" />
          </svg>
        </div>
        <span className="logo-text">Palette AI - React Chat</span>
        
        <div className="status-container">
          <button 
            className={`connection-status ${connectionStatus}`}
            onClick={onTestConnection}
            title="Click to test connection"
          >
            <span className="status-indicator">{getStatusIcon()}</span>
            <span className="status-text">{getStatusText()}</span>
          </button>
          
          {config.apiKey ? (
            <div className="api-status api-configured" title={`Model: ${config.model}`}>
              <span className="status-indicator">🔑</span>
              <span className="status-text">API Ready</span>
            </div>
          ) : (
            <div className="api-status api-missing" title="API key not configured">
              <span className="status-indicator">⚠️</span>
              <span className="status-text">No API Key</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatHeader;