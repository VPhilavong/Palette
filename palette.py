#!/usr/bin/env python3
"""
Palette CLI Entry Point

This script provides the main entry point for the Palette CLI tool.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from palette.cli.main import main

if __name__ == "__main__":
    main()
