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

This is a VS Code extension called "UI Copilot" that provides AI-powered React/Vue component generation with intelligent codebase analysis.

### 6-Phase Development Plan

**Phase 1: Project Setup** ✅ COMPLETED
- Clean extension boilerplate with TypeScript configuration
- VSCode extension manifest and basic command registration

**Phase 2: Codebase Scanning & Framework Detection** ✅ COMPLETED
- File indexing with recursive traversal and smart exclusions
- Multi-framework detection (React, Vue.js, Next.js, VitePress)
- Package.json analysis with fallback to code-based detection

**Phase 3: Component Extraction & Analysis** ✅ COMPLETED
- Reliable regex-based component parsing (replaced AST for stability)
- Multi-framework support: React (JSX/TSX), Vue (SFC), Next.js patterns
- Hook detection (React hooks, Vue Composition API, custom hooks)
- Multi-component detection per file with deduplication

**Phase 4: Embeddings & Context Ranking** 🚧 PLANNED
- Embedding generation with OpenAI/sentence-transformers
- Similarity scoring and proximity-based context ranking

**Phase 5: LLM Prompt & Response** 📋 PLANNED
- Framework-specific prompt templates
- LLM integration (Claude, OpenAI, Gemini) with streaming support

**Phase 6: Editor Actions & UI** 📋 PLANNED
- VSCode commands, CodeLens, inline suggestions
- Live preview panel with WebviewPanel for component rendering

### 🏗️ Clean Directory Structure

```
src/
├── core/                    # Extension core
│   └── extension.ts         # Main entry point
├── codebase/               # Phase 2-3: Analysis & parsing
│   ├── fileIndexer.ts      # File discovery and indexing
│   ├── frameworkDetector.ts # Multi-framework detection
│   ├── componentAnalyzer.ts # Component analysis orchestrator
│   └── simpleComponentParser.ts # Regex-based component parsing
├── embeddings/             # Phase 4: Vector embeddings
│   ├── embeddingGenerator.ts
│   └── contextRanker.ts
├── llm/                    # Phase 5: AI integration
│   ├── promptBuilder.ts
│   ├── claudeClient.ts
│   ├── openaiClient.ts
│   └── geminiClient.ts
├── ui/                     # Phase 6: VSCode UI
│   ├── commandPalette.ts
│   └── livePreviewPanel.ts
├── utils/                  # Shared utilities
│   ├── config.ts           # Extension configuration
│   ├── logger.ts           # Centralized logging
│   └── fileUtils.ts        # File system helpers
└── types/                  # TypeScript definitions
    └── index.ts            # Shared type definitions
```

### 🚀 Current Capabilities (Phases 1-3)

**File Indexing**: Recursively scans workspace with smart exclusions (`node_modules`, `.git`, `dist`, `build`, `.next`)

**Framework Detection**: 
- **React**: JSX/TSX files, React imports, component exports
- **Vue.js**: SFC files, Vue imports, Composition API patterns  
- **Next.js**: Next-specific patterns, app/pages router detection
- **VitePress**: Vue-based static site generator patterns

**Component Parsing**: Reliable regex-based approach with patterns for:
- Component declarations: `function Component`, `const Component =`, `export default`
- Vue SFC: `<template>`, `<script setup>`, Composition API
- Export patterns: default exports, named exports, HOCs

**Hook Detection**: Comprehensive detection including:
- React hooks: `useState`, `useEffect`, `useContext`, etc.
- Vue Composition: `ref`, `reactive`, `computed`, `watch`
- Custom hooks: Auth0 hooks, application-specific patterns
- Framework hooks: Next.js router, VitePress utilities

**Multi-Component Support**: Detects multiple components per file with Set-based deduplication

### Key Implementation Details

**Component Analysis Flow**:
1. `extension.ts` → Coordinates overall extension lifecycle
2. `fileIndexer.ts` → Discovers and indexes workspace files  
3. `frameworkDetector.ts` → Identifies project frameworks
4. `componentAnalyzer.ts` → Orchestrates component analysis
5. `simpleComponentParser.ts` → Extracts component metadata

**Reliability Features**:
- **Error Handling**: Graceful fallbacks when files can't be read
- **Performance**: Skips large files (>100KB), batched analysis
- **Accuracy**: Framework-specific patterns prevent false positives
- **Debugging**: Comprehensive logging via centralized Logger utility

**Configuration System**: 
- Supports multiple AI providers (OpenAI, Gemini, Claude)
- Configurable indexing behavior and exclusion patterns
- Context limits and file processing constraints

### Recent Fixes & Optimizations

**AST Parser Replacement**: Replaced complex Babel AST traversal with reliable regex patterns to eliminate infinite recursion and crashes

**Vue.js Support Enhancement**: Added comprehensive Vue SFC support including `.vue` file detection, which increased component detection from 4 to 73 components in test repositories

**Framework Detection Accuracy**: Improved React vs Vue detection to prevent false positives, achieving 75%+ accuracy in multi-framework projects

**Import Path Updates**: Successfully reorganized entire codebase into clean directory structure with updated import statements

## Configuration

Extension settings (VS Code settings.json):
```json
{
  "ui-copilot.apiProvider": "gemini", // or "openai", "claude"
  "ui-copilot.geminiApiKey": "your-key",
  "ui-copilot.openaiApiKey": "your-key", 
  "ui-copilot.claudeApiKey": "your-key",
  "ui-copilot.indexing.enabled": true,
  "ui-copilot.indexing.maxFileSize": 102400,
  "ui-copilot.indexing.excludePatterns": ["node_modules", ".git"],
  "ui-copilot.context.maxTokens": 12000,
  "ui-copilot.context.maxFiles": 20
}
```

## Working with This Codebase

**Making Changes**:
1. Modify TypeScript source files in appropriate `src/` directory
2. Run `npm run compile` to build (entry point: `./out/core/extension.js`)
3. Test with `F5` to launch Extension Development Host
4. Extension auto-reloads when files change in watch mode

**Adding New Framework Support**:
1. Add detection patterns in `frameworkDetector.ts`
2. Add parsing patterns in `simpleComponentParser.ts`  
3. Update type definitions in `types/index.ts`
4. Test with representative repositories

**Performance Guidelines**:
- Keep component analysis under 50 components for initial load
- Use batched processing for large codebases
- Implement timeouts for long-running operations
- Cache results when possible to avoid re-analysis

### Next Development Priorities

**Phase 4 (Current)**: Implement embedding generation and context ranking system
**Phase 5**: Build LLM integration with framework-specific prompts
**Phase 6**: Create rich VSCode UI with live preview capabilities

### Debugging
- Console logs appear in Extension Development Host's Debug Console
- Use VS Code debugger with breakpoints in TypeScript source
- Check file watching behavior in Output panel
- Use centralized Logger utility for structured logging

## Dependencies

**Core Dependencies**:
- `@google/generative-ai` - Gemini AI integration
- `openai` - OpenAI API client  
- `chokidar` - File watching (for future real-time updates)

**Development Dependencies**:
- TypeScript, ESLint for code quality
- VSCode extension APIs for editor integration