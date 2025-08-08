import React from 'react';
import type { Message } from '../types';
import CodeBlock from './CodeBlock';

interface ChatMessageProps {
  message: Message;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const getAvatar = () => {
    switch (message.role) {
      case 'user': return '👤';
      case 'assistant': return '🎨';
      case 'error': return '⚠️';
      default: return '💬';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  // Parse message content for code blocks
  const parseContent = (content: string) => {
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    const parts: Array<{ type: 'text' | 'code', content: string, language?: string }> = [];
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(content)) !== null) {
      // Add text before code block
      if (match.index > lastIndex) {
        const textContent = content.slice(lastIndex, match.index).trim();
        if (textContent) {
          parts.push({ type: 'text', content: textContent });
        }
      }

      // Add code block
      parts.push({
        type: 'code',
        content: match[2].trim(),
        language: match[1] || 'text'
      });

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < content.length) {
      const remainingText = content.slice(lastIndex).trim();
      if (remainingText) {
        parts.push({ type: 'text', content: remainingText });
      }
    }

    // If no code blocks found, return original content as text
    if (parts.length === 0) {
      parts.push({ type: 'text', content });
    }

    return parts;
  };

  const contentParts = parseContent(message.content);

  return (
    <div className={`message ${message.role}`}>
      <div className="message-header">
        <div className={`message-avatar ${message.role}-avatar`}>
          {getAvatar()}
        </div>
        <span className="message-time">
          {formatTimestamp(message.timestamp)}
        </span>
      </div>

      <div className="message-content">
        {contentParts.map((part, index) => (
          <div key={index}>
            {part.type === 'text' ? (
              <div className="message-text">
                {part.content.split('\n').map((line, lineIndex) => (
                  <React.Fragment key={lineIndex}>
                    {line}
                    {lineIndex < part.content.split('\n').length - 1 && <br />}
                  </React.Fragment>
                ))}
              </div>
            ) : (
              <CodeBlock
                code={part.content}
                language={part.language || 'text'}
                filename={`code.${part.language || 'txt'}`}
              />
            )}
          </div>
        ))}

        {/* Render additional code blocks from message metadata */}
        {message.codeBlocks && message.codeBlocks.map((block, index) => (
          <CodeBlock
            key={`extra-${index}`}
            code={block.code}
            language={block.language}
            filename={block.filename}
          />
        ))}
      </div>
    </div>
  );
};

export default ChatMessage;