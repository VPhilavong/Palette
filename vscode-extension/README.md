# 🎨 Palette AI - VS Code Extension

Generate React components and pages using AI directly in VS Code. **No backend setup required!**

## ✨ What's New

- **🚀 Direct AI Integration** - Works immediately without Python backend
- **🎯 Zero Configuration** - Just add your OpenAI API key and start
- **💡 Smart Context** - Automatically analyzes your project structure
- **🛠️ shadcn/ui Support** - Generate components using shadcn/ui patterns
- **📦 One-Click File Creation** - Add generated code directly to your project

## 🚀 Quick Start (< 1 minute!)

### 1. Install the Extension

```bash
# From VS Code Marketplace (coming soon)
1. Open Extensions (Ctrl+Shift+X)
2. Search for "Palette AI"
3. Click Install

# Or install from VSIX file
code --install-extension code-palette-chatbot-0.2.0.vsix
```

### 2. Add Your OpenAI API Key

1. Open VS Code Settings (`Ctrl+,`)
2. Search for "Palette"
3. Enter your OpenAI API key in the `Palette: Openai Api Key` field

> Get your API key from: https://platform.openai.com/api-keys

### 3. Start Generating!

1. Open Command Palette (`Ctrl+Shift+P`)
2. Run: `Palette: Open AI Chatbot`
3. Type your request and watch the magic happen!

## 💡 Example Requests

```
"Create a modern landing page with hero section and features"
"Build a contact form with email validation and Tailwind styling"
"Generate a dashboard sidebar with collapsible navigation"
"Make a product card component with image, price, and add to cart button"
"Create a pricing page with three tiers using shadcn/ui cards"
```

## 🎯 How It Works

1. **Analyzes Your Project**: Automatically reads your package.json, existing components, and project structure
2. **Builds Smart Context**: Detects React, Next.js, Vite, Tailwind CSS, and shadcn/ui usage
3. **Generates Production Code**: Uses OpenAI to create TypeScript components with proper types
4. **One-Click Integration**: Click "Add File" to save generated components to your project

## ⚙️ Configuration

### Supported Models

Configure your preferred model in VS Code settings:

- `gpt-4o-mini` (Default - Best balance of speed, quality, and cost)
- `gpt-4o` (More powerful, better for complex components)
- `gpt-3.5-turbo` (Fastest and most economical)
- `gpt-5` / `gpt-5-mini` / `gpt-5-nano` (Latest models with advanced capabilities)

### Token Optimization

The extension automatically optimizes token usage:
- Includes only relevant components (first 10) in context
- Uses last 3 conversation messages for continuity
- Limits project analysis to essential files
- Smart prompt compression for efficiency

## 🛠️ Features

### Component Generation
- TypeScript interfaces with proper types
- Responsive design with Tailwind breakpoints
- Accessibility with ARIA labels and semantic HTML
- Modern patterns with hover states and animations
- shadcn/ui component integration

### Project Intelligence
- Automatic framework detection (React, Next.js, Vite)
- Existing component awareness
- Design system pattern matching
- Import path resolution

### Chat Interface
- Natural language component requests
- Conversation history
- Code syntax highlighting
- One-click file creation

## 🔧 Troubleshooting

### "OpenAI API key not configured"
- Ensure you've added your API key in VS Code settings
- Check that the key starts with `sk-`
- Verify the key is active on OpenAI's platform

### "Rate limit exceeded"
**For GPT-5 (10,000 TPM limit):**
- Switch to `gpt-5-mini` (60,000 TPM) or `gpt-5-nano` (60,000 TPM)
- These models have 6x higher token limits

**For other models:**
- Wait a moment and try again
- Use a simpler request to reduce tokens
- Check your OpenAI usage dashboard

### "Model not found"
- Ensure you're using a valid model name
- Try `gpt-4o-mini` (most reliable)
- Check if you have access to the model in your OpenAI account

### Components not appearing in project
- Ensure you have a workspace folder open
- Check that the file path is valid
- Look for the file in your project explorer

## 🤝 Advanced Usage

### Using with Existing shadcn/ui Projects
The extension automatically detects installed shadcn/ui components and uses them in generated code:
```typescript
// Automatically uses your existing Button component
import { Button } from "@/components/ui/button"
```

### Custom Project Structures
The extension adapts to your project structure:
- Detects `src/components/ui` for shadcn/ui
- Finds `src/pages` for Next.js pages
- Recognizes `src/app` for App Router

## 📊 Privacy & Security

- **All code stays local** - No code is sent to Palette servers
- **Your API key** - You use your own OpenAI API key
- **No telemetry** - We don't track your usage
- **Open source** - Review the code yourself

## 🚧 Roadmap

- [ ] Support for more UI libraries (Material-UI, Chakra UI)
- [ ] Component testing generation
- [ ] Storybook integration
- [ ] Design-to-code from images
- [ ] Team collaboration features

## 📝 License

MIT - See LICENSE file for details

## 🤔 FAQ

**Q: Do I need to install Python or run a backend?**
A: No! Everything runs directly in VS Code.

**Q: Can I use this with my existing project?**
A: Yes! It works with any React, Next.js, or Vite project.

**Q: How much does it cost?**
A: The extension is free. You only pay for OpenAI API usage (~$0.01 per component).

**Q: Does it work offline?**
A: No, it requires an internet connection to reach OpenAI's API.

---

**Made with ❤️ by the Palette team**

Problems? Feature requests? [Open an issue on GitHub](https://github.com/your-repo/issues)