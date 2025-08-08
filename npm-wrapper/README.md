# Palette AI NPM Wrapper

This is the npm wrapper for Palette AI, providing zero-friction installation and usage of the Python-based component generator.

## Features

- **Zero-friction installation**: `npm install -g @palette-ai/cli`
- **Automatic Python environment setup**
- **Dependency management**
- **API key configuration**
- **Seamless CLI experience**

## Quick Start

```bash
# Install globally
npm install -g @palette-ai/cli

# First run will set up everything
palette generate "hero section with gradient background"

# Check status
palette status

# Configure API keys
palette config
```

## Commands

### Core Commands

- `palette generate <description>` - Generate a React component
- `palette analyze` - Analyze current project  
- `palette status` - Check installation status
- `palette setup` - Run initial setup
- `palette config` - Configure settings

### Options

- `--framework <framework>` - Specify framework (react, nextjs)
- `--output <path>` - Set output path
- `--ui <library>` - Choose UI library (tailwind, chakra, material)

## Requirements

- Node.js 16+
- Python 3.9+
- npm 8+

## Configuration

The wrapper automatically:

1. Detects Python installation
2. Installs the `code-palette` Python package
3. Manages API keys securely
4. Forwards commands to the Python CLI

Configuration is stored in `~/.palette-npm/config.json`.

## Troubleshooting

### Python not found

```bash
# Check Python installation
python3 --version

# If missing, install from python.org or:
# macOS: brew install python3
# Ubuntu: sudo apt install python3
# Windows: choco install python3
```

### Reset configuration

```bash
palette config
# Choose "Reset Everything"
```

### Manual setup

```bash
pip install code-palette
palette setup
```