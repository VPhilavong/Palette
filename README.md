# Palette - AI-Powered Component Generator

🎨 **Smart component generation that understands your design system**

Palette analyzes your project's design patterns, color schemes, and component structure to generate React components that perfectly match your existing codebase.

## ✨ Features

- 🔍 **Smart Project Analysis** - Automatically detects colors, typography, and design patterns
- 🎯 **Context-Aware Generation** - Components match your existing design system
- 🎨 **Design Token Extraction** - Supports Tailwind v4 @theme blocks and traditional configs
- 🚀 **Multiple Frameworks** - Next.js, React, Vue.js support
- 🛠️ **VS Code Extension** - Integrated development experience

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/VPhilavong/palette.git
cd palette

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Add your OpenAI/Anthropic API keys to .env
```

### Basic Usage

```bash
# Analyze your project
python3 palette.py analyze

# Generate a component
python3 palette.py generate "hero section with gradient background"
```

## 📁 Project Structure

```
palette/
├── 📁 src/palette/         # Main package
│   ├── 📁 analysis/        # Project analysis
│   ├── 📁 generation/      # Component generation
│   ├── 📁 cli/            # Command-line interface
│   └── 📁 utils/          # Utilities and helpers
├── 📁 docs/               # Documentation
├── 📁 examples/           # Example projects and CSS
├── 📁 scripts/            # Utility scripts
├── 📁 tests/              # Test files
├── 📁 templates/          # Component templates
├── 📁 vscode-extension/   # VS Code extension
└── palette.py             # CLI entry point
```

## 🎯 How It Works

1. **Analysis Phase**: Palette scans your project for:
   - CSS files and @theme blocks
   - Component usage patterns
   - Color schemes and design tokens
   - Typography scales and spacing

2. **Context Building**: Creates a comprehensive design system profile

3. **Generation Phase**: Uses AI to generate components that:
   - Match your color palette
   - Follow your naming conventions
   - Use your preferred component patterns
   - Integrate seamlessly with existing code

## 🔧 Advanced Usage

### Project Analysis
```bash
# Detailed analysis
python3 palette.py analyze

# Analyze specific directory
cd your-project && python3 /path/to/palette/palette.py analyze
```

### Component Generation
```bash
# Generate with context
python3 palette.py generate "responsive card component with image"

# Specify framework
python3 palette.py generate "navigation bar" --framework next.js
```

### Cleanup & Testing
```bash
# Quick cleanup between tests
./scripts/quick-clean.sh

# Full repository sanitization
python3 scripts/sanitize.py
```

## 🎨 Supported Design Systems

- ✅ **Tailwind CSS v3 & v4** - Including @theme blocks
- ✅ **CSS Custom Properties** - Automatic detection
- ✅ **Component Libraries** - Automatic inference
- ✅ **Design Tokens** - Colors, typography, spacing

## 📚 Documentation

- [Getting Started](docs/README.md)
- [Development Guide](docs/development.md)
- [Cleanup Scripts](docs/CLEANUP.md)
- [Examples](examples/README.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with example projects
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE.md](LICENSE.md) for details

## 🚀 VS Code Extension

Palette also includes a VS Code extension for integrated development:

```bash
cd vscode-extension
npm install
npm run compile
```

See [vscode-extension/README.md](vscode-extension/README.md) for extension-specific documentation.
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
- **Advanced codebase analysis** with sophisticated pattern detection
- **Framework-aware generation** (Next.js, Shadcn/UI, Lucide Icons)
- **State management pattern matching** (caching, Promise.race, loading states)
- Context-aware component generation with **timeout protection**
- Code iteration/modification functionality  
- Keyboard shortcuts (`Ctrl+Shift+U`) and command palette integration
- Automatic code formatting after generation
- **Performance optimizations** to prevent hanging during analysis
- Robust error handling and user feedback

**🔄 Working & Tested**
- Extension loads and activates properly without hanging
- **Enhanced pattern detection** recognizes modern React patterns
- Generates components that **match sophisticated codebases**
- Gemini AI integration with **intelligent context selection**
- Codebase analysis detects **Next.js, Shadcn/UI, and advanced patterns**
- Commands work via keyboard shortcuts and Command Palette
- Code insertion and formatting works smoothly

**🚀 Recent Major Improvements**
- **Fixed hanging analysis** with timeout protection and batch processing
- **Enhanced pattern detection** for modern frameworks and libraries
- **Sophisticated state management** pattern recognition
- **Advanced Tailwind** and design system support
- **Performance optimizations** with component limits and caching

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
