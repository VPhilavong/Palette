#!/bin/bash

# Test script to verify VS Code extension integration with Palette CLI

echo "🧪 Testing VS Code Extension Integration..."
echo "=========================================="

# Check if palette CLI is available
if ! command -v palette &> /dev/null; then
    echo "❌ Palette CLI not found in PATH"
    echo "Please ensure palette is installed and in your PATH"
    exit 1
fi

echo "✅ Palette CLI found"

# Create a test directory
TEST_DIR="/tmp/palette-vscode-test-$(date +%s)"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

echo "📁 Test directory: $TEST_DIR"

# Initialize a simple React project structure
mkdir -p src/components
echo '{
  "name": "test-project",
  "version": "1.0.0",
  "dependencies": {
    "react": "^18.0.0"
  }
}' > package.json

# Test the palette CLI directly first
echo ""
echo "1️⃣ Testing CLI directly..."
echo "------------------------"
palette generate "simple button component" --output src/components

# Check if file was created
if [ -f "src/components/Button.tsx" ]; then
    echo "✅ CLI generated Button.tsx successfully"
    echo "📄 Component preview:"
    head -n 20 src/components/Button.tsx
else
    echo "❌ CLI failed to generate component"
fi

echo ""
echo "2️⃣ Expected VS Code Extension behavior:"
echo "--------------------------------------"
echo "- Should capture the CLI output"
echo "- Should parse the file path from '✓ Created' messages"
echo "- Should read and display the generated component code"
echo "- Should show the file in a code block in the chat interface"

echo ""
echo "3️⃣ To test in VS Code:"
echo "---------------------"
echo "1. Open VS Code in this directory: code $TEST_DIR"
echo "2. Open the Palette panel (Ctrl+Shift+P -> 'Open Palette')"
echo "3. Type: 'create a navbar component'"
echo "4. Verify you see the generated code in the chat"

echo ""
echo "🧹 To clean up: rm -rf $TEST_DIR"