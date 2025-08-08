# Changelog

All notable changes to the Palette AI NPM wrapper will be documented in this file.

## [1.0.0] - 2024-08-06

### Added
- Initial release of npm wrapper for Palette AI
- Zero-friction installation with automatic Python environment setup
- Cross-platform support (Windows, macOS, Linux)
- Automatic Python version detection (requires 3.9+)
- Secure API key management
- Configuration management in `~/.palette-npm/`
- Command forwarding to Python CLI
- Interactive setup wizard
- Status checking and diagnostics
- Comprehensive test suite

### Features
- `palette generate <description>` - Generate React components
- `palette analyze` - Analyze current project
- `palette status` - Check installation status
- `palette setup` - Run initial setup
- `palette config` - Configure settings
- Support for framework options (React, Next.js)
- Support for UI library options (Tailwind, Chakra, Material-UI)
- Auto-detection of Python installations
- Fallback to manual Python specification