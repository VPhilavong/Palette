#!/bin/bash

# 🚀 Quick Bundle Test - Just test if we can create a working bundle

echo "🚀 Quick Bundle Test"
echo "==================="

cd "$(dirname "$0")/.."
BUNDLE_DIR="vscode-extension/bundled"

# Create simple bundle structure
mkdir -p "$BUNDLE_DIR"
cp -r src "$BUNDLE_DIR/"

# Test the bundle launcher
cat > "$BUNDLE_DIR/test-bundle.py" << 'EOF'
#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add bundle source to path
bundle_dir = Path(__file__).parent
sys.path.insert(0, str(bundle_dir / "src"))

# Test import
try:
    from palette.cli.main import main
    print("✅ Bundle import successful")
    
    # Test basic CLI functionality
    sys.argv = ['palette', '--help']
    main()
    
except Exception as e:
    print(f"❌ Bundle test failed: {e}")
    sys.exit(1)
EOF

chmod +x "$BUNDLE_DIR/test-bundle.py"

# Test it
python3 "$BUNDLE_DIR/test-bundle.py"

if [[ $? -eq 0 ]]; then
    echo "✅ Bundle test passed!"
    echo "📁 Bundle size: $(du -sh "$BUNDLE_DIR" | cut -f1)"
else
    echo "❌ Bundle test failed"
fi