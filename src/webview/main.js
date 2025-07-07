

// Get access to the VS Code API from within the webview context
const vscode = acquireVsCodeApi();

// DOM elements
const componentPrompt = document.getElementById('componentPrompt');
const generateBtn = document.getElementById('generateBtn');


const codeOutput = document.getElementById('codeOutput');
const copyBtn = document.getElementById('copyBtn');
const insertBtn = document.getElementById('insertBtn');
const progressIndicator = document.getElementById('progressIndicator');
const progressMessage = document.getElementById('progressMessage');
const errorMessage = document.getElementById('errorMessage');

let lastGeneratedCode = '';

// Event listeners
generateBtn.addEventListener('click', () => {
    const prompt = componentPrompt.value.trim();
    if (!prompt) {
        showError('Please enter a component description');
        return;
    }
    
    vscode.postMessage({
        command: 'generateComponent',
        prompt: prompt
    });
});



copyBtn.addEventListener('click', () => {
    if (lastGeneratedCode) {
        navigator.clipboard.writeText(lastGeneratedCode).then(() => {
            showSuccess('Code copied to clipboard!');
        }).catch(() => {
            showError('Failed to copy code to clipboard');
        });
    }
});

insertBtn.addEventListener('click', () => {
    if (lastGeneratedCode) {
        vscode.postMessage({
            command: 'insertCode',
            code: lastGeneratedCode
        });
    }
});

// Handle messages from the extension
window.addEventListener('message', event => {
    const message = event.data;
    
    switch (message.command) {
        case 'showProgress':
            showProgress(message.message);
            break;
            
        case 'componentGenerated':
            hideProgress();
            displayGeneratedCode(message.code);
            showSuccess('Component generated successfully!');
            break;
            

     
            
        case 'showError':
            hideProgress();
            showError(message.message);
            break;
    }
});

function showProgress(message) {
    progressMessage.textContent = message;
    progressIndicator.classList.remove('hidden');
    
    // Disable buttons during processing
    generateBtn.disabled = true;
  
  
}

function hideProgress() {
    progressIndicator.classList.add('hidden');
    
    // Re-enable buttons
    generateBtn.disabled = false;
    iterateBtn.disabled = false;
    analyzeBtn.disabled = false;
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        errorMessage.classList.add('hidden');
    }, 5000);
}

function showSuccess(message) {
    // Create a temporary success message
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.textContent = message;
    successDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: var(--success-background);
        color: white;
        padding: 15px;
        border-radius: 4px;
        z-index: 1001;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    `;
    
    document.body.appendChild(successDiv);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        document.body.removeChild(successDiv);
    }, 3000);
}

function displayGeneratedCode(code) {
    lastGeneratedCode = code;
    codeOutput.textContent = code;
    
    // Scroll to the output section
    document.querySelector('.output-section').scrollIntoView({ 
        behavior: 'smooth',
        block: 'nearest'
    });
}



// Auto-resize textareas
function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

// Add auto-resize to textareas
componentPrompt.addEventListener('input', () => autoResize(componentPrompt));



// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Focus on the first input
    componentPrompt.focus();
    
    // Set initial state
    codeOutput.textContent = 'Generated code will appear here...';
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Enter to generate component
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        if (document.activeElement === componentPrompt) {
            generateBtn.click();
        } 
    }
    
    // Escape to clear error messages
    if (e.key === 'Escape') {
        errorMessage.classList.add('hidden');
    }
});
