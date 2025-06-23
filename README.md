# UI Copilot - VSCode Extension

AI-powered React component generation that understands your codebase.

## Setup Instructions

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure OpenAI API Key
1. Open VSCode Settings (Cmd/Ctrl + ,)
2. Search for "ui-copilot"
3. Set your OpenAI API key in `ui-copilot.openaiApiKey`

### 3. Build the Extension
```bash
npm run compile
```

### 4. Test the Extension
1. Press F5 to open a new Extension Development Host window
2. Open a React project
3. Use Cmd/Ctrl + Shift + U to generate a component
4. Or open Command Palette and search "Generate UI Component"

## Features

- **Generate Components**: Describe what you want and get React code
- **Codebase Aware**: Automatically detects your styling approach (Tailwind, styled-components, etc.)
- **Iterate on Code**: Select existing component code and modify it with natural language
- **TypeScript Support**: Generates proper TypeScript when detected

## Usage

### Generate New Component
1. Open a React file where you want to insert the component
2. Press `Cmd/Ctrl + Shift + U` or use Command Palette
3. Type your description: "user profile card with avatar and name"
4. Component code is inserted at cursor position

### Modify Existing Component
1. Select the component code you want to modify
2. Run "Iterate on Component" command
3. Describe changes: "make it responsive" or "add loading state"
4. Selected code is replaced with modified version

## Development

### File Structure
```
src/
├── extension.ts          # Main extension entry point
├── componentGenerator.ts # OpenAI integration and code generation
├── codebaseAnalyzer.ts   # Analyzes workspace for context
└── types.ts             # TypeScript type definitions
```

### Key Features Implemented
- ✅ Basic VSCode extension setup
- ✅ OpenAI API integration
- ✅ Codebase analysis (styling detection, TypeScript detection)
- ✅ Component generation with context
- ✅ Code iteration/modification
- ✅ Keyboard shortcuts and commands

### Next Steps for MVP
1. Test with real React projects
2. Improve prompt engineering for better code quality
3. Add error handling and user feedback
4. Support more styling approaches
5. Add component library detection

### Cost Management
- Using GPT-3.5-turbo to stay within budget
- Caching workspace analysis results
- Smart context truncation for large codebases

## Team Development Tips

1. **Start Simple**: Test basic generation first before adding complexity
2. **Use Real Projects**: Test on actual React codebases, not toy examples
3. **Iterate on Prompts**: The system prompt is key to good code generation
4. **Handle Edge Cases**: What happens with malformed prompts or API errors?
5. **Document Everything**: Keep notes on what works and what doesn't

## Testing Checklist

- [ ] Extension loads without errors
- [ ] Can generate basic React components
- [ ] Detects Tailwind CSS correctly
- [ ] Detects TypeScript projects
- [ ] Iteration feature works on selected code
- [ ] Handles API errors gracefully
- [ ] Code formatting works after generation# SAIL_Project
