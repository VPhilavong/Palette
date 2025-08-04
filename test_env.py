#!/usr/bin/env python3
import os
import sys

print("Environment Test:")
print(f"OPENAI_API_KEY: {'Set' if os.getenv('OPENAI_API_KEY') else 'Not set'}")
print(f"ANTHROPIC_API_KEY: {'Set' if os.getenv('ANTHROPIC_API_KEY') else 'Not set'}")
print(f"Python executable: {sys.executable}")
print(f"Current directory: {os.getcwd()}")