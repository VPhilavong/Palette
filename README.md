# UI Copilot - VSCode Extension

AI-powered React component generation that understands your codebase and generates modern, context-aware React components.

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure AI Provider
Choose between OpenAI or Google Gemini:

**Option A: Google Gemini (Recommended - Free tier available)**
1. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Open VSCode Settings (Cmd/Ctrl + ,)
3. Search for "ui-copilot"
4. Set `ui-copilot.apiProvider` to "gemini"
5. Set your Gemini API key in `ui-copilot.geminiApiKey`

**Option B: OpenAI**
1. Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Open VSCode Settings (Cmd/Ctrl + ,)
3. Search for "ui-copilot"
4. Set `ui-copilot.apiProvider` to "openai"
5. Set your OpenAI API key in `ui-copilot.openaiApiKey`

### 3. Build the Extension
```bash
npm run compile
```

### 4. Test the Extension
1. Press F5 to open Extension Development Host window
2. In the new window, open a React/TypeScript project (or create a .tsx file)
3. Use `Ctrl+Shift+U` to generate a component
4. Or use Command Palette → "Generate UI Component"

## ✨ Features

- **🎯 Smart Component Generation**: Describe what you want and get production-ready React code
- **🧠 Codebase Aware**: Automatically detects your styling approach (Tailwind, styled-components, CSS modules, etc.)
- **🔄 Iterate on Code**: Select existing component code and modify it with natural language
- **⚡ TypeScript Support**: Generates proper TypeScript interfaces and types when detected
- **🎨 Styling Intelligence**: Adapts to your project's styling patterns
- **🚀 Dual AI Support**: Works with both OpenAI and Google Gemini

## 📖 Usage

### Generate New Component
1. Open a React file where you want to insert the component
2. Press `Ctrl+Shift+P`(Windows) or `Cmd+Shift+P`(Mac/Linux) and or use Command Palette → "Generate UI Component"
3. Type your description: "modern button component with loading state and variants"
4. Component code is inserted at cursor position and auto-formatted

### Modify Existing Component
1. Select the component code you want to modify
2. Run "Iterate on Component" command from Command Palette
3. Describe changes: "make it responsive" or "add loading state"
4. Selected code is replaced with modified version

### Example Prompts That Work Well
- "user profile card with avatar, name, and bio"
- "responsive navigation menu with mobile hamburger"
- "loading spinner with custom colors"
- "form input with validation states"
- "modal dialog with backdrop and close button"

## 🛠️ Development

### File Structure
```
src/
├── extension.ts          # Main extension entry point and command registration
├── componentGenerator.ts # AI integration (OpenAI + Gemini) and code generation
├── codebaseAnalyzer.ts   # Analyzes workspace for styling/TypeScript context
└── types.ts             # TypeScript type definitions
```

### 🎯 Current Status

**✅ Completed Features**
- VSCode extension setup with proper activation
- Dual AI provider support (OpenAI + Google Gemini)
- Intelligent codebase analysis (TypeScript, Tailwind, styled-components detection)
- Context-aware component generation
- Code iteration/modification functionality  
- Keyboard shortcuts (`Ctrl+Shift+U`) and command palette integration
- Automatic code formatting after generation
- Robust error handling and user feedback

**🔄 Working & Tested**
- Extension loads and activates properly
- Gemini AI integration generates quality React components
- Codebase analysis detects project patterns correctly
- Commands work via keyboard shortcuts and Command Palette
- Code insertion and formatting works smoothly

### 📋 Team Development Workflow

**For New Team Members:**
1. Clone repo and run setup steps above
2. Get your Gemini API key (free tier is generous)
3. Test basic generation with simple prompts first
4. Try on real React projects to see context awareness

**Development Best Practices:**
- Test extension changes by pressing F5 (launches Extension Development Host)
- Use `npm run compile` after TypeScript changes
- Test with both TypeScript and JavaScript React projects
- Try different styling setups (Tailwind, styled-components, plain CSS)

### 🚀 Next Priorities
1. **Improve Prompt Engineering**: Better system prompts for higher quality components
2. **Enhanced Styling Support**: Better detection of component libraries (MUI, Chakra, etc.)
3. **Smart File Creation**: Option to create new files instead of just inserting
4. **Context Improvements**: Better understanding of existing component patterns
5. **Error Recovery**: Better handling of malformed AI responses

### 🧪 Testing Checklist

**Basic Functionality**
- [x] Extension loads without errors
- [x] Can generate basic React components  
- [x] Gemini AI integration works
- [x] Commands appear in Command Palette
- [x] Keyboard shortcuts work (`Ctrl+Shift+P`)

**Codebase Intelligence**
- [x] Detects TypeScript projects correctly
- [x] Detects Tailwind CSS in dependencies
- [x] Detects styled-components setup
- [x] Generates appropriate code based on context

**Advanced Features**
- [x] Iteration feature works on selected code
- [x] Code formatting works after generation
- [x] Handles API errors gracefully
- [x] Works without workspace folder (fallback mode)

**Cross-Platform**
- [ ] Test on Windows
- [ ] Test on macOS  
- [ ] Test on Linux

### 🤝 Contributing

1. **Branch Naming**: `feature/description` or `fix/description`
2. **Testing**: Test your changes with F5 before submitting
3. **Documentation**: Update README if adding new features
4. **Code Style**: Follow existing TypeScript patterns

### 💡 Tips for Success

1. **Start Simple**: Test basic generation before complex prompts
2. **Use Real Projects**: Test on actual React codebases for best results
3. **Iterate on Prompts**: The system prompt in `componentGenerator.ts` is key
4. **Monitor Costs**: Gemini has generous free tier, but track usage
5. **Share Examples**: Document interesting prompts that work well

---

**Ready to generate some awesome React components? 🚀**
