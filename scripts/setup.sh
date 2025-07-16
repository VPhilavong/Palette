#!/bin/bash

# Development setup script for Palette
echo "🎨 Setting up Palette development environment..."

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "📍 Python version: $python_version"

if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 9) else 1)'; then
    echo "✅ Python version is compatible"
else
    echo "❌ Python 3.9+ required"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Set up environment file
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please add your API keys to .env file"
else
    echo "✅ .env file already exists"
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x palette.py
chmod +x scripts/quick-clean.sh
chmod +x scripts/sanitize.py

# Test basic functionality
echo "🧪 Testing basic functionality..."
if python3 palette.py --help > /dev/null 2>&1; then
    echo "✅ CLI working"
else
    echo "❌ CLI test failed"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Add your API keys to .env file"
echo "2. Test with: python3 palette.py analyze"
echo "3. See docs/ for more information"
