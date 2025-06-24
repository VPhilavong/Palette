# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Build & Development
- `npm run compile` - Compile TypeScript to JavaScript (required after changes)
- `npm run watch` - Watch mode compilation during development
- `npm run vscode:prepublish` - Prepare for VS Code extension publishing

### Testing the Extension
1. Press `F5` in VS Code to launch Extension Development Host
2. In the new window, test the extension commands:
   - `Ctrl+Shift+U` (Mac: `Cmd+Shift+U`) - Generate UI Component
   - Command Palette → "Generate UI Component" or "Iterate on Component"

## Architecture Overview

This is a VS Code extension called "UI Copilot" that provides AI-powered React component generation with intelligent codebase analysis.

### Core Architecture

**Main Entry Point**: `src/extension.ts`
- Registers VS Code commands and handles user interactions
- Coordinates between ComponentGenerator and CodebaseAnalyzer

**Component Generation**: `src/componentGenerator.ts`
- Supports both OpenAI and Gemini AI providers
- Generates context-aware React components using workspace analysis
- Includes intelligent context integration and code cleanup

**Codebase Analysis**: `src/codebaseAnalyzer.ts`
- Comprehensive workspace analysis with AST parsing
- Dependency graph construction and pattern recognition
- Real-time file watching with cache management
- Advanced analysis including design systems and state management

### Supporting Modules

**AST Analysis**: `src/astAnalyzer.ts`
- Deep component analysis using Babel parser
- Extracts hooks, props, styling patterns, and complexity metrics

**Context Intelligence**: 
- `src/intelligentContextSelector.ts` - Selects most relevant context for generation
- `src/contextRanker.ts` - Ranks components by relevance to user prompts
- `src/advancedPatternAnalyzer.ts` - Identifies sophisticated code patterns
- `src/designSystemAnalyzer.ts` - Analyzes design system usage

**Utilities**: `src/analyzerUtils.ts` - Shared utility functions for analysis

### Key Features

1. **Dual AI Support**: OpenAI GPT models and Google Gemini
2. **Intelligent Context**: Analyzes existing codebase to generate matching components
3. **Pattern Recognition**: Identifies architectural patterns, state management, and styling approaches
4. **Real-time Analysis**: File watching with intelligent caching
5. **TypeScript Support**: Full TypeScript analysis and generation

## Configuration

Extension settings (VS Code settings.json):
- `ui-copilot.apiProvider`: "openai" or "gemini" (default: "gemini")
- `ui-copilot.openaiApiKey`: OpenAI API key
- `ui-copilot.geminiApiKey`: Google Gemini API key
- `ui-copilot.model`: AI model selection

## Key Implementation Details

### Component Generation Flow
1. User triggers command → `extension.ts` handles input
2. `codebaseAnalyzer.ts` analyzes workspace for context
3. `componentGenerator.ts` calls AI with intelligent context
4. Generated code is cleaned and inserted at cursor position

### Analysis Architecture
- **Parallel Processing**: Components analyzed in batches for performance
- **Caching Strategy**: File-based caching with timestamp validation
- **Pattern Recognition**: Multi-layered analysis from basic to sophisticated
- **Context Ranking**: AI-powered relevance scoring for examples

### Type System
Comprehensive TypeScript interfaces in `src/types.ts` covering:
- Workspace and component analysis results
- AST analysis structures
- Pattern recognition types
- Design system and state management analysis

## Working with This Codebase

### Making Changes
1. Modify TypeScript source files in `src/`
2. Run `npm run compile` to build
3. Test with `F5` to launch Extension Development Host
4. Extension auto-reloads when files change in watch mode

### Performance Optimizations (Recent Fixes)

**Analysis Timeout Protection:**
- Component analysis limited to 50 components max for performance
- 5-second timeout per component analysis to prevent hanging
- 10-second timeout for intelligent context generation
- Large files (>100KB) are skipped during AST analysis

**Fallback Strategy:**
- AST analysis failures fall back to basic component info
- Intelligent context failures fall back to standard generation
- Multiple layers of error handling prevent complete failure

**Batch Processing:**
- Components analyzed in batches of 5 (reduced from 10)
- Progress feedback during analysis
- Cache results to avoid re-analysis

### Enhanced Pattern Detection (Latest Updates)

**Framework Detection:**
- **Next.js**: Detects Next.js apps and includes "use client", Image component patterns
- **Shadcn/UI**: Detects shadcn/ui library and uses proper component imports
- **Lucide Icons**: Recognizes lucide-react usage for consistent icon patterns

**Advanced State Management:**
- **Caching**: Detects localStorage/sessionStorage usage for client-side caching
- **Promise Racing**: Identifies timeout handling patterns with Promise.race
- **Loading States**: Recognizes sophisticated loading state management
- **Performance**: Detects useCallback/useMemo optimization patterns
- **Error Handling**: Identifies error boundary and error state patterns

**Sophisticated Styling:**
- **Advanced Tailwind**: Complex responsive patterns, design system colors
- **UI Libraries**: Material-UI, Chakra UI, Ant Design, Mantine detection
- **Design Systems**: Theme detection and consistent styling patterns

### Key Areas for Enhancement
- **Pattern Recognition**: Extend `advancedPatternAnalyzer.ts` for new patterns
- **AI Integration**: Enhance prompts in `componentGenerator.ts`
- **Context Selection**: Improve relevance scoring in `contextRanker.ts`
- **Design System**: Expand `designSystemAnalyzer.ts` for more UI libraries

### Debugging
- Console logs appear in Extension Development Host's Debug Console
- Use VS Code debugger with breakpoints in TypeScript source
- Check file watching behavior in Output panel
- Look for "timeout" warnings if analysis is hanging

## Dependencies

### Core Dependencies
- `@google/generative-ai` - Gemini AI integration
- `openai` - OpenAI API client
- `@babel/parser`, `@babel/traverse` - AST analysis
- `chokidar` - File watching
- `axios` - HTTP requests

### Architecture Notes
- Extension follows VS Code extension patterns with proper activation/deactivation
- Modular design with clear separation of concerns
- Heavy use of TypeScript for type safety
- Async/await patterns throughout for performance