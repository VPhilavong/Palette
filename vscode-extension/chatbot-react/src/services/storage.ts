import type { Message } from '../types';

const STORAGE_KEY = 'palette_conversation_history';
const MAX_MESSAGES = 100;

export class ConversationStorage {
  /**
   * Save conversation history to localStorage
   */
  static saveMessages(messages: Message[]): void {
    try {
      // Keep only the most recent messages to prevent storage bloat
      const messagesToSave = messages.slice(-MAX_MESSAGES);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messagesToSave));
    } catch (error) {
      console.warn('Failed to save conversation history:', error);
    }
  }

  /**
   * Load conversation history from localStorage
   */
  static loadMessages(): Message[] {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const messages = JSON.parse(stored);
        // Validate the loaded messages
        if (Array.isArray(messages)) {
          return messages.filter(msg => 
            msg && 
            typeof msg === 'object' && 
            msg.id && 
            msg.role && 
            msg.content && 
            msg.timestamp
          );
        }
      }
    } catch (error) {
      console.warn('Failed to load conversation history:', error);
    }
    return [];
  }

  /**
   * Clear all conversation history
   */
  static clearMessages(): void {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (error) {
      console.warn('Failed to clear conversation history:', error);
    }
  }

  /**
   * Export conversation history as text
   */
  static exportMessages(messages: Message[]): string {
    const header = `# Palette AI Conversation Export
Export Date: ${new Date().toISOString()}
Messages: ${messages.length}

---

`;

    const content = messages.map(msg => {
      const timestamp = new Date(msg.timestamp).toLocaleString();
      let messageText = `## ${msg.role.toUpperCase()} [${timestamp}]

${msg.content}

`;

      // Add code blocks if present
      if (msg.codeBlocks && msg.codeBlocks.length > 0) {
        msg.codeBlocks.forEach(block => {
          messageText += `\`\`\`${block.language}
${block.code}
\`\`\`

`;
        });
      }

      return messageText + '---\n\n';
    }).join('');

    return header + content;
  }

  /**
   * Generate a unique message ID
   */
  static generateMessageId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  }

  /**
   * Get conversation statistics
   */
  static getStats(messages: Message[]): {
    totalMessages: number;
    userMessages: number;
    assistantMessages: number;
    errorMessages: number;
    oldestMessage?: string;
    newestMessage?: string;
  } {
    const stats = {
      totalMessages: messages.length,
      userMessages: messages.filter(m => m.role === 'user').length,
      assistantMessages: messages.filter(m => m.role === 'assistant').length,
      errorMessages: messages.filter(m => m.role === 'error').length,
      oldestMessage: messages.length > 0 ? messages[0].timestamp : undefined,
      newestMessage: messages.length > 0 ? messages[messages.length - 1].timestamp : undefined,
    };

    return stats;
  }
}