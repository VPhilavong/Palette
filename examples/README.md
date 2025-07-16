# Examples

This directory contains example projects and configurations for testing Palette.

## Test CSS Files

Example CSS files with various @theme configurations for testing the analyzer:

- `basic-theme.css` - Simple color and typography tokens
- `tailwind-v4.css` - Tailwind v4 @theme example
- `complex-theme.css` - Complex design system with multiple token types

## Sample Projects

- `nextjs-basic/` - Basic Next.js project structure
- `react-tailwind/` - React project with Tailwind CSS
- `vue-project/` - Vue.js project example

## Usage

Use these examples to test Palette's analysis and generation capabilities:

```bash
# Analyze an example
cd examples/nextjs-basic
python3 ../../palette.py analyze

# Generate a component using example context
python3 ../../palette.py generate "button component"
```
