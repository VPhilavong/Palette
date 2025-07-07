# UI Copilot Webview Interface

This folder contains the webview implementation for the UI Copilot extension, providing a modern graphic interface that runs inside VS Code.

## Files Overview

- **`UICopilotPanel.ts`** - Main webview panel class that manages the VS Code webview
- **`main.js`** - Frontend JavaScript that handles user interactions in the webview
- **`main.css`** - Main styles for the webview interface
- **`vscode.css`** - VS Code theme-aware styles and variables
- **`reset.css`** - CSS reset for consistent styling across VS Code themes

## Features

### 🎨 Component Generation
- Text input for describing components you want to generate
- Real-time progress indication during generation
- Syntax-highlighted code output

### 🔄 Component Iteration
- Textarea for pasting existing component code
- Input for describing modifications you want to make
- Live code modification with AI assistance

### 📊 Workspace Analysis
- Button to analyze current workspace structure
- Display of detected frameworks, styling solutions, and existing components
- JSON-formatted workspace information

### 💻 Code Management
- Copy generated code to clipboard
- Insert code directly into the active editor
- Auto-formatting after code insertion

## Usage

1. **Open the Panel**: Use the command palette (`Ctrl+Shift+P`) and search for "Open UI Copilot Panel"
2. **Generate Components**: Enter a description of what you want to build and click "Generate Component"
3. **Iterate on Code**: Paste existing code, describe changes, and click "Modify Component"
4. **Analyze Workspace**: Click "Analyze Current Workspace" to see your project structure

## Keyboard Shortcuts

- `Ctrl+Enter` (or `Cmd+Enter` on Mac) - Generate component when focused on description input
- `Ctrl+Enter` (or `Cmd+Enter` on Mac) - Modify component when focused on modification input
- `Escape` - Close error messages

## Theme Support

The interface automatically adapts to your current VS Code theme, supporting:
- Light themes
- Dark themes
- High contrast themes
- Custom themes

All colors and styling are derived from VS Code's theme variables for a seamless experience.
