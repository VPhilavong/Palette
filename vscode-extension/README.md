# Code Palette - VS Code Extension

AI-powered design-to-code tool for React components. Generate beautiful, responsive components directly in VS Code.

## Features

- **🎨 Component Generation**: Natural language to React components
- **👀 Live Preview**: See components before creating files
- **📊 Project Analysis**: Automatic framework and design system detection
- **⚡ Fast Integration**: Wraps the proven Code Palette CLI
- **🎯 Smart Placement**: Automatically places components in the right directories

## Commands

- **Palette: Generate Component** - Generate a new React component
- **Palette: Preview Component** - Preview component without creating file
- **Palette: Analyze Project** - Analyze current project setup

## Quick Start

1. **Install Prerequisites**
   ```bash
   # Install the Code Palette CLI first
   pip install -e /path/to/code-palette
   
   # Configure your OpenAI API key
   export OPENAI_API_KEY="your-key-here"
   ```

2. **Open a React Project**
   - Open any React/Next.js project in VS Code
   - Ensure you have TypeScript and Tailwind CSS configured

3. **Generate Your First Component**
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type "Palette: Generate Component"
   - Enter description: "modern button with hover effects"
   - Choose "Create" to save the component

## Usage Examples

### Generate Components
```
Command: Palette: Generate Component
Input: "pricing section with three tiers and glassmorphism"
Result: Creates src/components/pricing-section.tsx
```

### Preview Before Creating
```
Command: Palette: Preview Component  
Input: "contact form with validation"
Result: Opens preview in new tab
```

### Analyze Project
```
Command: Palette: Analyze Project
Result: Shows detected framework, styling, libraries
```

## Context Menu Integration

Right-click on any folder in the Explorer to generate components directly in that location.

## Configuration

Configure the extension in VS Code Settings:

- **Palette: CLI Path** - Path to palette command (default: "palette")
- **Palette: Default Model** - AI model to use (default: "gpt-4o-2024-08-06")

## Requirements

- **VS Code**: Version 1.60.0 or higher
- **Code Palette CLI**: Must be installed and accessible
- **OpenAI API Key**: Required for component generation
- **React Project**: Works with Next.js, Vite, Create React App

## Supported File Types

- TypeScript React (`.tsx`)
- JavaScript React (`.jsx`)
- TypeScript (`.ts`)
- JavaScript (`.js`)

## Generated Component Features

✅ **TypeScript interfaces** with proper types  
✅ **Responsive design** with Tailwind breakpoints  
✅ **Accessibility** with ARIA labels and semantic HTML  
✅ **Modern patterns** with hover states and animations  
✅ **Component variants** with union types  
✅ **JSDoc documentation** for complex props  

## Example Generated Component

```typescript
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  onClick?: () => void;
  children: React.ReactNode;
}

const Button: React.FC<ButtonProps> = ({ 
  variant = 'primary', 
  size = 'md', 
  disabled = false,
  onClick,
  children 
}) => {
  return (
    <button
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${
        disabled ? 'opacity-50 cursor-not-allowed' : 'hover:scale-105'
      }`}
      onClick={onClick}
      disabled={disabled}
      aria-disabled={disabled}
    >
      {children}
    </button>
  );
};
```

## Troubleshooting

### "Palette CLI not found"
- Install the CLI: `pip install -e /path/to/code-palette`
- Update the CLI path in VS Code settings

### "OpenAI API key not configured"
- Set environment variable: `export OPENAI_API_KEY="your-key"`
- Restart VS Code after setting the key

### Component not generating
- Check that you're in a React project
- Verify API key is valid
- Check VS Code Output panel for detailed errors

## Development

To work on this extension:

```bash
git clone <repository>
cd vscode-extension
npm install
npm run compile
# Press F5 to launch Extension Development Host
```

## License

MIT - See LICENSE file for details

---

**Made with ❤️ by the SAIL Project**