#!/usr/bin/env python3
"""Test the simplified generation flow."""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Set dummy API key for testing
os.environ['OPENAI_API_KEY'] = 'sk-dummy-key-for-testing'

from src.palette.cli.main import main
import click.testing

def test_simplified_cli():
    """Test the CLI with simplified flow."""
    print("🧪 Testing Simplified Generation Flow")
    print("=" * 50)
    
    runner = click.testing.CliRunner()
    
    # Test basic generation
    result = runner.invoke(main, [
        'generate', 
        'create a simple button',
        '--framework', 'react',
        '--preview'
    ])
    
    print("Exit code:", result.exit_code)
    print("\nOutput:")
    print(result.output)
    
    # Check for key indicators
    if "Using Standard Generator with Enhanced Analysis" in result.output:
        print("\n✅ MCP integration successfully disabled")
    else:
        print("\n❌ MCP integration still active")
        
    if "Zero-Fix Pipeline" not in result.output:
        print("✅ Zero-Fix Pipeline successfully disabled")
    else:
        print("❌ Zero-Fix Pipeline still active")
        
    if "RuntimeWarning" not in result.output:
        print("✅ No async warnings")
    else:
        print("❌ Still has async warnings")
    
    print("\n" + "=" * 50)
    print("Simplified flow test completed")

if __name__ == "__main__":
    test_simplified_cli()