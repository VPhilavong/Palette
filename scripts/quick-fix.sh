#!/bin/bash

# Quick fixes for common Python linting issues
# This script applies automated fixes for simple issues

cd "$(dirname "$0")/.."

echo "🔧 Applying quick fixes for linting issues..."

# Fix: Add missing final newlines
echo "📝 Adding missing final newlines..."
find src/ -name "*.py" -exec sed -i -e '$a\' {} \;

# Fix: Remove trailing whitespace  
echo "🧹 Removing trailing whitespace..."
find src/ -name "*.py" -exec sed -i 's/[[:space:]]*$//' {} \;

# Fix: Add explicit encoding to file opens
echo "📄 Adding explicit encoding declarations..."
find src/ -name "*.py" -exec sed -i "s/open(/open(encoding='utf-8', /g" {} \;
find src/ -name "*.py" -exec sed -i "s/open(encoding='utf-8', \([^,]*\), 'r')/open(\1, 'r', encoding='utf-8')/g" {} \;
find src/ -name "*.py" -exec sed -i "s/open(encoding='utf-8', \([^,]*\), 'w')/open(\1, 'w', encoding='utf-8')/g" {} \;

# Re-run black and isort after manual fixes
echo "🎨 Re-running Black formatter..."
black src/ palette.py --quiet

echo "📦 Re-running isort..."
isort src/ palette.py --quiet

echo "✅ Quick fixes applied successfully!"
echo "💡 Run ./scripts/lint.sh again to check remaining issues"
