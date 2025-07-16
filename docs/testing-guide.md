# Testing Guide for Code Palette

## 📁 **YES, Keep `app/` and `components/` Folders!**

These folders are **essential test fixtures** that serve specific purposes:

### 🎯 **Purpose of Test Folders**

#### `app/profile/page.tsx`

```tsx
const ProfilePage = () => {
  return (
    <div className="bg-background text-foreground">
      <h1>Profile Page</h1>
    </div>
  );
};
```

- **Framework Detection**: The `app/` directory signals Next.js 13+ app router
- **Color Analysis**: Extracts semantic colors like `bg-background`, `text-foreground`
- **Project Structure**: Helps analyzer understand modern React patterns

#### `components/Button.tsx`

```tsx
const Button = () => {
  return <button className="bg-primary text-white">Click me</button>;
};
```

- **Component Analysis**: Tests component parsing and name extraction
- **Color Detection**: Finds colors like `white`, `primary`
- **Design Tokens**: Builds design system understanding

## 🧪 **Test Files Overview**

### `tests/test_cli.py` ✅

- **Purpose**: Simple functional test script
- **Status**: WORKING (4/4 tests pass)
- **Usage**: `python3 tests/test_cli.py`

### `tests/test_palette.py` ✅

- **Purpose**: Comprehensive pytest suite
- **Status**: WORKING (16/16 tests pass)
- **Usage**: `python3 -m pytest tests/test_palette.py -v`

## 🔧 **Path Issues Resolved**

The "errors" you saw were VS Code import warnings, not runtime errors. Fixed with:

### VS Code Configuration

- **`.vscode/settings.json`** - Configures Python path resolution
- **`palette.code-workspace`** - Workspace-specific settings
- **`pyproject.toml`** - Pytest configuration with custom markers

### Python Path Setup

Both test files correctly add `src/` to Python path:

```python
# From tests/ directory, go up one level to root, then into src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
```

## 📊 **Test Results**

### ✅ **All Tests Pass**

```bash
# Simple test
$ python3 tests/test_cli.py
🧪 Testing Code Palette CLI Components
📊 Test Results: 4/4 tests passed
🎉 All tests passed! CLI is ready for use.

# Pytest suite
$ python3 -m pytest tests/test_palette.py -v
===================================================
16 passed in 1.73s
```

### 🎯 **What Tests Validate**

1. **Module Imports** - All package imports work correctly
2. **Project Analysis** - Framework and color detection
3. **Prompt Building** - LLM prompt generation
4. **File Management** - Component name extraction
5. **CLI Functionality** - Command-line interface
6. **Integration** - End-to-end workflow

## 🏗️ **Test Structure Benefits**

The test project simulates a real-world scenario:

- ✅ **Next.js project** with app router
- ✅ **React components** with styling
- ✅ **Design tokens** in className attributes
- ✅ **Component patterns** for analysis

## 💡 **Quick Commands**

```bash
# Run simple tests
python3 tests/test_cli.py

# Run comprehensive tests
python3 -m pytest tests/ -v

# Test CLI directly
python3 palette.py analyze

# Run linting
./scripts/quick-lint.sh
```

## ⚠️ **Important Notes**

1. **DON'T DELETE** `app/` and `components/` - they're test fixtures
2. **Editor warnings** about imports are cosmetic - tests actually work
3. **VS Code settings** should resolve path warnings
4. **Tests validate** that your CLI can analyze real projects

The test structure is working perfectly and validates that your Palette CLI can successfully analyze React projects! 🚀
