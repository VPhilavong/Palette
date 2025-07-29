# Palette Professional Frontend MCP Servers

These Model Context Protocol (MCP) servers provide Palette with professional frontend development knowledge and capabilities, ensuring every generated component meets industry standards.

## Overview

The Professional Frontend MCP system consists of three specialized servers that work together during code generation:

### 1. UI Knowledge Server (`ui-knowledge/`)
**Purpose**: Provides comprehensive UI/UX knowledge and best practices

**Tools**:
- `get_component_patterns` - Patterns from top UI libraries (shadcn/ui, MUI, etc.)
- `get_design_principles` - UX principles, accessibility guidelines
- `get_styling_guide` - CSS best practices, Tailwind utilities
- `get_framework_patterns` - React hooks, Next.js patterns, etc.
- `search_ui_knowledge` - Natural language search
- `get_accessibility_guidelines` - WCAG compliance
- `get_performance_tips` - Optimization strategies
- `get_animation_patterns` - Animation best practices

### 2. Code Analysis Server (`code-analysis/`)
**Purpose**: Analyzes code for quality issues and improvements

**Tools**:
- `analyze_component` - Deep component analysis
- `suggest_refactoring` - Improvement opportunities
- `check_accessibility` - WCAG validation
- `analyze_performance` - Performance bottlenecks
- `detect_patterns` - Design patterns and anti-patterns
- `validate_best_practices` - Framework best practices
- `analyze_complexity` - Code complexity metrics

### 3. Design System Enforcer (`design-enforcer/`)
**Purpose**: Ensures consistency with project design system

**Tools**:
- `validate_component` - Check against design tokens
- `suggest_tokens` - Recommend appropriate tokens
- `check_consistency` - Naming and structure validation
- `generate_variants` - Create component variants
- `export_to_storybook` - Generate stories
- `get_design_system` - Retrieve design configuration
- `enforce_styling` - Apply consistent styling

## How It Works

When you generate a component with Palette:

1. **Before Generation**: UI Knowledge server provides patterns and best practices
2. **During Generation**: AI uses professional knowledge to write better code
3. **After Generation**: 
   - Code Analysis server checks for issues
   - Design Enforcer ensures consistency
   - Issues are automatically fixed using MCP feedback

## Installation

The MCP servers are automatically discovered when you run Palette. No additional installation needed!

## Usage

### Basic Generation (with MCP enhancement)
```bash
python palette.py generate "modal component with accessibility"
```

### Test the MCP System
```bash
python test_professional_mcp.py
```

### Run Individual Servers (for testing)
```bash
# Test UI Knowledge server
python mcp-servers/ui-knowledge/server.py --test

# Test Code Analysis server  
python mcp-servers/code-analysis/server.py --test

# Test Design Enforcer server
python mcp-servers/design-enforcer/server.py --test
```

## Architecture

```
Generation Flow with MCP:

User Request → Extract Requirements → Gather UI Knowledge (MCP)
                                           ↓
                                    Generate with Context
                                           ↓
                                    Analyze Code (MCP)
                                           ↓
                                    Enforce Design System (MCP)
                                           ↓
                                    Fix Issues with Knowledge
                                           ↓
                                    Professional Component ✓
```

## Knowledge Base

The UI Knowledge server includes patterns from:
- **Component Libraries**: shadcn/ui, MUI, Ant Design, Chakra UI
- **CSS Frameworks**: Tailwind CSS, CSS Modules, Styled Components  
- **Frameworks**: React, Next.js, Vue, Angular
- **Design Systems**: Material Design, Fluent UI, Carbon

## Benefits

1. **Professional Quality**: Every component follows industry best practices
2. **Consistency**: Automatic design system enforcement
3. **Accessibility**: Built-in WCAG compliance checking
4. **Performance**: Optimization suggestions included
5. **Learning System**: Analyzes your codebase to match patterns

## Configuration

MCP servers are configured in:
- `.palette/mcp-servers.json` - Project-specific servers
- `palette.json` - MCP section for project config
- Auto-discovered from `mcp-servers/` directory

## Development

To add new capabilities:

1. **Add new tool** to appropriate server
2. **Update knowledge base** in `data/` directories
3. **Test the tool** with `--test` flag
4. **Integrate** into generation flow

## Troubleshooting

**MCP SDK not installed warning**:
- This is optional. Palette works without it using fallback mode
- To install: `pip install mcp` (not required)

**Servers not discovered**:
- Check if `mcp-servers/` directory exists
- Verify Python is available
- Check logs for errors

**Generation not using MCP**:
- Ensure servers are enabled in config
- Check if running from project root
- Verify OpenAI API key is set

## Future Enhancements

- [ ] Visual design analysis from screenshots
- [ ] Component performance profiling
- [ ] Advanced animation generators
- [ ] Multi-framework support
- [ ] Custom knowledge base training