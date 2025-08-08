import React, { useState } from 'react';

interface CodeBlockProps {
  code: string;
  language: string;
  filename?: string;
}

// Message types for VSCode communication
declare global {
  interface Window {
    acquireVsCodeApi?: () => {
      postMessage(message: any): void;
      getState(): any;
      setState(state: any): void;
    };
  }
}

const CodeBlock: React.FC<CodeBlockProps> = ({ code, language, filename }) => {
  const [copied, setCopied] = useState(false);
  const [showFileInput, setShowFileInput] = useState(false);
  const [filePath, setFilePath] = useState(filename || '');
  const [isAddingFile, setIsAddingFile] = useState(false);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy code:', error);
      
      // Fallback for browsers that don't support clipboard API
      const textArea = document.createElement('textarea');
      textArea.value = code;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const addFileToProject = async () => {
    if (!filePath.trim()) {
      alert('Please enter a file path');
      return;
    }

    setIsAddingFile(true);
    
    try {
      console.log('🎯 Making HTTP request to create file:', filePath.trim());
      
      // Make HTTP request to our API
      const response = await fetch('/api/files/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          path: filePath.trim(),
          content: code,
          language: language
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log('✅ File created successfully:', result);
        
        // Show success message
        alert(`✅ Successfully ${result.data.action.toLowerCase()} file: ${result.data.path}\n\nThe file has been created in your workspace!`);
        
      } else {
        // Handle API error
        const errorData = await response.json();
        console.error('❌ API Error:', errorData);
        
        let errorMessage = `Failed to create file: ${errorData.error?.message || 'Unknown error'}`;
        
        // Provide specific help for common errors
        if (errorData.error?.code === 'WORKSPACE_NOT_FOUND') {
          errorMessage += '\n\n💡 Make sure you have a project folder open in VSCode.';
        } else if (errorData.error?.code === 'HANDLER_NOT_AVAILABLE') {
          errorMessage += '\n\n💡 The file creation service is not available. Try restarting the extension.';
        }
        
        const shouldCopy = confirm(
          `${errorMessage}\n\nWould you like to copy the code to clipboard instead?`
        );
        
        if (shouldCopy) {
          await copyToClipboard();
        }
      }
      
    } catch (error: any) {
      console.error('🔥 Network error:', error);
      
      // Handle network errors (server not available, etc.)
      const shouldCopy = confirm(
        `Network error: ${error.message}\n\nThis might happen if the chatbot server is not running.\n\nWould you like to copy the code to clipboard instead?`
      );
      
      if (shouldCopy) {
        await copyToClipboard();
      } else {
        // Offer download as alternative
        const shouldDownload = confirm('Would you like to download the file instead?');
        if (shouldDownload) {
          downloadAsFile();
        }
      }
      
    } finally {
      setIsAddingFile(false);
      setShowFileInput(false);
    }
  };

  const downloadAsFile = () => {
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filePath || `component.${language === 'tsx' ? 'tsx' : 'js'}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getSuggestedPath = () => {
    if (filename) return filename;
    
    // Try to detect component name from code
    const componentMatch = code.match(/(?:export\s+(?:default\s+)?(?:const|function)\s+|const\s+)(\w+)/);
    const componentName = componentMatch?.[1] || 'Component';
    
    // Suggest path based on code content
    if (code.includes('Page') || code.includes('Route')) {
      return `src/pages/${componentName}.tsx`;
    } else {
      return `src/components/${componentName}.tsx`;
    }
  };

  // Auto-suggest path when input is shown
  React.useEffect(() => {
    if (showFileInput && !filePath) {
      setFilePath(getSuggestedPath());
    }
  }, [showFileInput]);

  return (
    <div className="code-block">
      <div className="code-header">
        <span className="code-info">
          <span className="code-language">{language}</span>
          {filename && <span className="code-filename">• {filename}</span>}
        </span>
        <div className="code-actions">
          <button 
            className="copy-button"
            onClick={copyToClipboard}
            title="Copy to clipboard"
          >
            {copied ? '✓ Copied!' : '📋 Copy'}
          </button>
          <button 
            className="add-file-button"
            onClick={() => setShowFileInput(!showFileInput)}
            title="Add file to project"
          >
            📁 Add File
          </button>
        </div>
      </div>
      
      {showFileInput && (
        <div className="file-input-section">
          <div className="file-path-container">
            <input
              type="text"
              value={filePath}
              onChange={(e) => setFilePath(e.target.value)}
              placeholder="e.g., src/components/MyComponent.tsx"
              className="file-path-input"
              disabled={isAddingFile}
            />
            <div className="file-actions">
              <button 
                className="confirm-button"
                onClick={addFileToProject}
                disabled={isAddingFile || !filePath.trim()}
              >
                {isAddingFile ? '⏳ Adding...' : '✅ Create'}
              </button>
              <button 
                className="cancel-button"
                onClick={() => setShowFileInput(false)}
                disabled={isAddingFile}
              >
                ❌ Cancel
              </button>
            </div>
          </div>
          <div className="file-hint">
            💡 File will be created in your workspace. Existing files will be overwritten.
          </div>
        </div>
      )}
      <pre className="code-content">
        <code className={`language-${language}`}>
          {code}
        </code>
      </pre>
    </div>
  );
};

export default CodeBlock;