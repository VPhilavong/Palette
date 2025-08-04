# VS Code Extension Integration Guide

This guide explains how the VS Code extension integrates with the main Palette CLI.

## Architecture Overview

The VS Code extension acts as a bridge between the VS Code interface and the Palette CLI:

```
VS Code UI → Extension → PaletteService → Palette CLI → AI Generation
```

## Key Components

### 1. **PaletteService** (`src/paletteService.ts`)
- Manages communication with the Palette CLI
- Handles command execution and output streaming
- Provides methods for:
  - `checkInstallation()` - Verifies CLI is available
  - `analyzeProject()` - Analyzes current workspace
  - `generateComponent()` - Generates components via CLI
  - `streamGenerate()` - Streams generation output in real-time

### 2. **Extension Commands** (`src/extension.ts`)
- `palette.openWebview` - Opens the Palette chat interface
- `palette.generate` - Quick component generation via input box
- `palette.analyze` - Analyzes current project setup
- `palette.generateInFolder` - Context menu generation for folders

### 3. **PalettePanel** (`src/PalettePanel.ts`)
- Manages the webview panel UI
- Handles real-time streaming of generation output
- Processes user messages and image uploads

## Configuration

Users can configure the extension via VS Code settings:

```json
{
  "palette.cliPath": "/path/to/palette",
  "palette.defaultModel": "gpt-4o-2024-08-06"
}
```

## CLI Communication

The extension communicates with the CLI using:
1. **Child Process Execution** - For single commands with JSON output
2. **Process Spawning** - For streaming output during generation

Example CLI commands used:
```bash
palette --version                    # Check installation
palette analyze --json               # Analyze project
palette generate "prompt" --json     # Generate component
```

## Data Flow

### Component Generation Flow:
1. User enters prompt in VS Code
2. Extension analyzes workspace context
3. Calls Palette CLI with prompt and context
4. Streams output back to VS Code
5. Displays results in webview or creates files

### Project Analysis Flow:
1. User triggers analyze command
2. Extension runs `palette analyze` in workspace
3. Parses results (framework, styling, etc.)
4. Displays formatted analysis to user

## Error Handling

The extension handles common errors:
- Missing Palette CLI installation
- Missing API keys (OPENAI_API_KEY)
- Invalid workspace configuration
- Generation failures

## Environment Variables

The extension respects environment variables:
- `OPENAI_API_KEY` - Required for OpenAI models
- `ANTHROPIC_API_KEY` - For Anthropic models
- `PALETTE_*` - Any Palette-specific configs

## Development Tips

1. **Testing Integration**: 
   ```bash
   # Test CLI directly
   cd test-project
   palette generate "test component"
   ```

2. **Debugging**:
   - Check Output panel → "Code Palette" for logs
   - Enable verbose logging in Palette CLI

3. **Custom CLI Path**:
   - Set `palette.cliPath` in settings
   - Useful for development versions

## Future Enhancements

- [ ] Image-based generation support
- [ ] Multi-file component generation
- [ ] Live preview before saving
- [ ] Custom templates support
- [ ] Project-wide refactoring tools